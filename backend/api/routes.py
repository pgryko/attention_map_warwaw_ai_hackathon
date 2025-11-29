"""
API routes for Attention Map.
"""

from datetime import datetime

from django.utils import timezone
from typing import Annotated
from uuid import UUID

from django.contrib.gis.geos import Point
from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import File, Form, Query, Router
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth

from core.models import Event, EventCluster, SeverityChoices, StatusChoices, UserProfile
from services.gamification import GamificationService

from .schemas import (
    ClusterOut,
    ErrorOut,
    EventListOut,
    EventOut,
    EventStatusUpdateIn,
    EventUploadOut,
    StatsOut,
)

router = Router()


# ─────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────


def event_to_schema(event: Event) -> EventOut:
    """Convert Event model to output schema."""
    return EventOut(
        id=event.id,
        created_at=event.created_at,
        latitude=event.location.y,
        longitude=event.location.x,
        address=event.address,
        description=event.description,
        media_url=event.media_url,
        media_type=event.media_type,
        thumbnail_url=event.thumbnail_url,
        transcription=event.transcription,
        category=event.category,
        subcategory=event.subcategory,
        severity=event.severity,
        ai_confidence=event.ai_confidence,
        cluster_id=event.cluster_id,
        status=event.status,
        reviewed_by_id=event.reviewed_by_id,
        reviewed_at=event.reviewed_at,
    )


def cluster_to_schema(cluster: EventCluster) -> ClusterOut:
    """Convert EventCluster model to output schema."""
    return ClusterOut(
        id=cluster.id,
        latitude=cluster.centroid.y,
        longitude=cluster.centroid.x,
        event_count=cluster.event_count,
        computed_severity=cluster.computed_severity,
        first_event_at=cluster.first_event_at,
        last_event_at=cluster.last_event_at,
    )


# ─────────────────────────────────────────────────────────────
# Upload Endpoints
# ─────────────────────────────────────────────────────────────


@router.post(
    "/events/upload",
    response={202: EventUploadOut, 400: ErrorOut},
    summary="Submit a new event with media",
)
def upload_event(
    request: HttpRequest,
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: str = Form(""),
    media: UploadedFile = File(...),
) -> tuple[int, EventUploadOut | ErrorOut]:
    """
    Submit a new event report with media file.

    The event will be processed asynchronously:
    1. Media stored in MinIO
    2. AI classification performed
    3. Spatial clustering applied
    4. Real-time notification sent
    """
    # Validate media type
    content_type = media.content_type or ""
    if not content_type.startswith(("image/", "video/")):
        return 400, ErrorOut(detail="Media must be an image or video file")

    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return 400, ErrorOut(detail="Latitude must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        return 400, ErrorOut(detail="Longitude must be between -180 and 180")

    # Create event
    media_type = "video" if content_type.startswith("video/") else "image"
    location = Point(longitude, latitude, srid=4326)

    # Determine reporter (supports both session and JWT auth)
    reporter = None
    if request.user.is_authenticated:
        reporter = request.user
    elif hasattr(request, "auth") and request.auth:
        reporter = request.auth

    event = Event.objects.create(
        reporter=reporter,
        location=location,
        description=description,
        media_type=media_type,
        status=StatusChoices.NEW,
    )

    # Increment reporter's submission count and check for badges
    if reporter:
        try:
            profile, _ = UserProfile.objects.get_or_create(user=reporter)
            profile.reports_submitted += 1
            profile.save(update_fields=["reports_submitted"])

            # Check for new badges
            gamification = GamificationService()
            gamification.on_report_submitted(profile)
        except Exception:
            pass  # Don't fail upload if profile update fails

    # Trigger Celery task for async processing
    from tasks.processing import process_event

    process_event.delay(str(event.id), media.read())

    return 202, EventUploadOut(
        id=event.id,
        status="processing",
        message="Event received, processing...",
    )


# ─────────────────────────────────────────────────────────────
# Event List/Detail Endpoints
# ─────────────────────────────────────────────────────────────


@router.get(
    "/events",
    response=EventListOut,
    summary="List events with filters",
)
def list_events(
    request: HttpRequest,
    bounds: Annotated[str | None, Query(description="lat1,lng1,lat2,lng2")] = None,
    status: Annotated[str | None, Query(description="Comma-separated statuses")] = None,
    severity: Annotated[
        str | None, Query(description="Comma-separated severities")
    ] = None,
    category: Annotated[
        str | None, Query(description="Comma-separated categories")
    ] = None,
    since: Annotated[
        datetime | None, Query(description="Events after this time")
    ] = None,
    limit: int = 100,
    offset: int = 0,
) -> EventListOut:
    """
    List events with optional filters for map display and feed.
    """
    queryset = Event.objects.all()

    # Apply spatial filter (bounds)
    if bounds:
        try:
            lat1, lng1, lat2, lng2 = map(float, bounds.split(","))
            from django.contrib.gis.geos import Polygon

            bbox = Polygon.from_bbox((lng1, lat1, lng2, lat2))
            bbox.srid = 4326
            queryset = queryset.filter(location__within=bbox)
        except (ValueError, TypeError):
            pass  # Invalid bounds, skip filter

    # Apply status filter
    if status:
        statuses = [s.strip() for s in status.split(",")]
        queryset = queryset.filter(status__in=statuses)

    # Apply severity filter
    if severity:
        try:
            severities = [int(s.strip()) for s in severity.split(",")]
            queryset = queryset.filter(severity__in=severities)
        except ValueError:
            pass

    # Apply category filter
    if category:
        categories = [c.strip() for c in category.split(",")]
        queryset = queryset.filter(category__in=categories)

    # Apply time filter
    if since:
        queryset = queryset.filter(created_at__gte=since)

    # Get total count before pagination
    total = queryset.count()

    # Apply pagination
    limit = min(limit, 500)  # Max 500
    events = queryset[offset : offset + limit]

    return EventListOut(
        events=[event_to_schema(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/events/{event_id}",
    response={200: EventOut, 404: ErrorOut},
    summary="Get event details",
)
def get_event(request: HttpRequest, event_id: UUID) -> tuple[int, EventOut | ErrorOut]:
    """Get details of a specific event."""
    event = get_object_or_404(Event, id=event_id)
    return 200, event_to_schema(event)


@router.patch(
    "/events/{event_id}/status",
    auth=JWTAuth(),
    response={200: EventOut, 403: ErrorOut, 404: ErrorOut},
    summary="Update event status (triage)",
)
def update_event_status(
    request: HttpRequest,
    event_id: UUID,
    data: EventStatusUpdateIn,
) -> tuple[int, EventOut | ErrorOut]:
    """
    Update the status of an event (triage action).
    Only authenticated staff/operators can perform this action.
    """
    # Check if user is staff (operator)
    if not request.auth.is_staff:
        return 403, ErrorOut(detail="Only operators can update event status")

    event = get_object_or_404(Event, id=event_id)

    # Track status changes for gamification
    was_verified = data.status == "verified" and event.status != "verified"
    was_rejected = data.status == "false_alarm" and event.status != "false_alarm"
    is_critical = event.severity == SeverityChoices.CRITICAL

    event.status = data.status
    event.reviewed_by = request.auth
    event.reviewed_at = timezone.now()
    event.save()

    # Handle gamification for reporter
    if event.reporter:
        try:
            profile = event.reporter.profile
            gamification = GamificationService()

            if was_verified:
                profile.reports_verified += 1
                profile.save(update_fields=["reports_verified"])
                gamification.on_report_verified(profile, is_critical=is_critical)

            elif was_rejected:
                gamification.on_report_rejected(profile)

        except UserProfile.DoesNotExist:
            pass

    # Trigger SSE notification for status change
    from api.streaming import broadcast_status_change

    broadcast_status_change(event)

    return 200, event_to_schema(event)


# ─────────────────────────────────────────────────────────────
# Cluster Endpoints
# ─────────────────────────────────────────────────────────────


@router.get(
    "/clusters",
    response=list[ClusterOut],
    summary="List active clusters",
)
def list_clusters(
    request: HttpRequest,
    bounds: Annotated[str | None, Query(description="lat1,lng1,lat2,lng2")] = None,
) -> list[ClusterOut]:
    """List active event clusters for map display."""
    queryset = EventCluster.objects.filter(event_count__gt=1)

    if bounds:
        try:
            lat1, lng1, lat2, lng2 = map(float, bounds.split(","))
            from django.contrib.gis.geos import Polygon

            bbox = Polygon.from_bbox((lng1, lat1, lng2, lat2))
            bbox.srid = 4326
            queryset = queryset.filter(centroid__within=bbox)
        except (ValueError, TypeError):
            pass

    return [cluster_to_schema(c) for c in queryset[:100]]


# ─────────────────────────────────────────────────────────────
# Stats Endpoint
# ─────────────────────────────────────────────────────────────


@router.get(
    "/stats/summary",
    response=StatsOut,
    summary="Get dashboard statistics",
)
def get_stats(request: HttpRequest) -> StatsOut:
    """Get summary statistics for the dashboard."""
    total_events = Event.objects.count()

    # Events by status
    status_counts = dict(
        Event.objects.values("status")
        .annotate(count=Count("id"))
        .values_list("status", "count")
    )

    # Events by category
    category_counts = dict(
        Event.objects.exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .values_list("category", "count")
    )

    # Events by severity
    severity_counts = dict(
        Event.objects.values("severity")
        .annotate(count=Count("id"))
        .values_list("severity", "count")
    )
    severity_counts = {str(k): v for k, v in severity_counts.items()}

    # Active clusters
    active_clusters = EventCluster.objects.filter(event_count__gt=1).count()

    return StatsOut(
        total_events=total_events,
        events_by_status=status_counts,
        events_by_category=category_counts,
        events_by_severity=severity_counts,
        active_clusters=active_clusters,
    )
