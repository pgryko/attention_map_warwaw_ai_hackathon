"""
Celery tasks for event processing pipeline.
"""

import logging
from uuid import UUID

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_event(self, event_id: str, media_data: bytes | None = None) -> dict:
    """
    Main event processing pipeline.

    Steps:
    1. Store media in MinIO
    2. Extract keyframe (if video)
    3. Classify with AI
    4. Apply spatial clustering
    5. Broadcast to SSE clients
    """
    from core.models import Event

    try:
        event = Event.objects.get(id=UUID(event_id))
        logger.info(f"Processing event {event_id}")

        # Step 1: Store media
        if media_data:
            media_url = store_media(event_id, media_data)
            event.media_url = media_url
            event.save()

        # Step 2: Extract keyframe (if video)
        if event.media_type == "video" and event.media_url:
            thumbnail_url = extract_keyframe(event.media_url)
            event.thumbnail_url = thumbnail_url
            event.save()

        # Step 3: AI Classification
        classification = classify_event(event)
        event.category = classification.get("category", "")
        event.subcategory = classification.get("subcategory", "")
        event.severity = classification.get("severity", 1)
        event.ai_confidence = classification.get("confidence")
        event.ai_reasoning = classification.get("reasoning", "")
        event.save()

        # Step 4: Spatial clustering
        cluster_events(event)

        # Step 5: Broadcast to SSE
        broadcast_event(event)

        logger.info(f"Successfully processed event {event_id}")
        return {"status": "success", "event_id": event_id}

    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {"status": "error", "message": "Event not found"}
    except Exception as e:
        logger.error(f"Error processing event {event_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def store_media(event_id: str, media_data: bytes) -> str:
    """Store media file in MinIO and return URL."""
    from minio import Minio

    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )

    # Ensure bucket exists
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)

    # Upload file
    import io

    object_name = f"events/{event_id}/media"
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        io.BytesIO(media_data),
        len(media_data),
    )

    # Return URL
    protocol = "https" if settings.MINIO_USE_SSL else "http"
    return (
        f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
    )


@shared_task
def extract_keyframe(video_url: str) -> str:
    """
    Extract a keyframe from video using ffmpeg.
    Returns URL of the thumbnail.
    """
    # TODO: Implement ffmpeg keyframe extraction
    # For now, return empty string
    logger.info(f"Keyframe extraction not yet implemented for {video_url}")
    return ""


@shared_task
def classify_event(event) -> dict:
    """
    Classify event using OpenAI API.
    Combines text description and image analysis.
    """
    from openai import OpenAI

    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured, skipping classification")
        return {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": "Classification skipped - API key not configured",
        }

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""Analyze this incident report and classify it.

Description: {event.description or "No description provided"}

Classify into one of these categories:
- emergency: Fire, explosion, collapse
- security: Drone activity, suspicious activity
- traffic: Accident, road blockage
- protest: March, demonstration, gathering
- infrastructure: Pothole, broken streetlight, damage
- environmental: Pollution, fallen tree, flooding
- informational: General observation

Also assign severity (1-4):
- 1 (Low): Informational only
- 2 (Medium): Needs attention, not urgent
- 3 (High): Urgent, requires response
- 4 (Critical): Life-threatening emergency

Respond in JSON format:
{{"category": "...", "subcategory": "...", "severity": N, "confidence": 0.0-1.0, "reasoning": "..."}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        import json

        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": f"Classification failed: {e}",
        }


@shared_task
def cluster_events(event) -> None:
    """
    Apply spatial clustering to group nearby events.
    Events within 100m and 30 minutes are grouped.
    """
    from datetime import timedelta

    from django.contrib.gis.db.models.functions import Distance
    from django.contrib.gis.measure import D
    from django.utils import timezone

    from core.models import Event, EventCluster, SeverityChoices

    time_threshold = timezone.now() - timedelta(minutes=30)

    # Find nearby recent events
    nearby_events = (
        Event.objects.filter(
            created_at__gte=time_threshold,
            location__distance_lte=(event.location, D(m=100)),
        )
        .exclude(id=event.id)
        .annotate(distance=Distance("location", event.location))
    )

    if nearby_events.exists():
        # Check if any are already in a cluster
        existing_cluster = None
        for nearby in nearby_events:
            if nearby.cluster:
                existing_cluster = nearby.cluster
                break

        if existing_cluster:
            # Add to existing cluster
            event.cluster = existing_cluster
            event.save()

            # Update cluster stats
            existing_cluster.event_count = existing_cluster.events.count()
            existing_cluster.last_event_at = timezone.now()

            # Boost severity based on event count
            if existing_cluster.event_count >= 5:
                existing_cluster.computed_severity = SeverityChoices.CRITICAL
            elif existing_cluster.event_count >= 3:
                existing_cluster.computed_severity = max(
                    existing_cluster.computed_severity, SeverityChoices.HIGH
                )

            existing_cluster.save()
        else:
            # Create new cluster
            cluster = EventCluster.objects.create(
                centroid=event.location,
                event_count=nearby_events.count() + 1,
                computed_severity=event.severity,
            )

            # Assign all nearby events to cluster
            event.cluster = cluster
            event.save()

            for nearby in nearby_events:
                nearby.cluster = cluster
                nearby.save()


@shared_task
def broadcast_event(event) -> None:
    """Broadcast event to SSE clients."""
    from api.streaming import broadcast_new_event

    broadcast_new_event(event)
