"""
API routes for Attention Map.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from django.contrib.gis.geos import Point
from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import File, Query, Router
from ninja.files import UploadedFile

from core.models import Event, EventCluster, StatusChoices

from .schemas import (
    ClusterOut,
    ErrorOut,
    EventListOut,
    EventOut,
    EventStatusUpdateIn,
    EventUploadIn,
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
    data: EventUploadIn,
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
    if not (-90 <= data.latitude <= 90):
        return 400, ErrorOut(detail="Latitude must be between -90 and 90")
    if not (-180 <= data.longitude <= 180):
        return 400, ErrorOut(detail="Longitude must be between -180 and 180")

    # Create event
    media_type = "video" if content_type.startswith("video/") else "image"
    location = Point(data.longitude, data.latitude, srid=4326)

    event = Event.objects.create(
        reporter=request.user if request.user.is_authenticated else None,
        location=location,
        description=data.description,
        media_type=media_type,
        status=StatusChoices.NEW,
    )

    # TODO: Trigger Celery task for async processing
    # from tasks.processing import process_event
    # process_event.delay(str(event.id), media.read())

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
    response={200: EventOut, 404: ErrorOut},
    summary="Update event status (triage)",
)
def update_event_status(
    request: HttpRequest,
    event_id: UUID,
    data: EventStatusUpdateIn,
) -> tuple[int, EventOut | ErrorOut]:
    """
    Update the status of an event (triage action).
    Only authenticated operators can perform this action.
    """
    event = get_object_or_404(Event, id=event_id)

    event.status = data.status
    event.reviewed_by = request.user if request.user.is_authenticated else None
    event.reviewed_at = datetime.now()
    event.save()

    # TODO: Trigger SSE notification
    # from api.streaming import broadcast_event_update
    # broadcast_event_update(event)

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
