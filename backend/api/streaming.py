"""
Server-Sent Events (SSE) streaming for real-time updates.
"""

import json
import logging
from collections.abc import Generator

import redis
from django.conf import settings
from django.http import HttpRequest, StreamingHttpResponse

logger = logging.getLogger(__name__)

# Redis channel for event updates
EVENTS_CHANNEL = "events:updates"


def get_redis_client() -> redis.Redis:
    """Get Redis client for pub/sub."""
    return redis.from_url(settings.REDIS_URL)


def event_stream(request: HttpRequest) -> Generator[str, None, None]:
    """
    Generator that yields SSE-formatted events from Redis pub/sub.
    """
    client = get_redis_client()
    pubsub = client.pubsub()
    pubsub.subscribe(EVENTS_CHANNEL)

    try:
        # Send initial connection message
        yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"

        # Listen for messages
        for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                yield f"event: event_update\ndata: {data}\n\n"

    except GeneratorExit:
        logger.info("SSE client disconnected")
    finally:
        pubsub.unsubscribe(EVENTS_CHANNEL)
        pubsub.close()


def stream_events(request: HttpRequest) -> StreamingHttpResponse:
    """
    SSE endpoint for real-time event updates.

    Usage:
        const eventSource = new EventSource('/api/v1/events/stream');
        eventSource.addEventListener('event_update', (e) => {
            const event = JSON.parse(e.data);
            // Handle new/updated event
        });
    """
    response = StreamingHttpResponse(
        event_stream(request),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


def broadcast_event_update(event_data: dict) -> None:
    """
    Broadcast an event update to all connected SSE clients.

    Args:
        event_data: Dictionary containing event information
    """
    try:
        client = get_redis_client()
        client.publish(EVENTS_CHANNEL, json.dumps(event_data))
    except Exception as e:
        logger.error(f"Failed to broadcast event update: {e}")


def broadcast_new_event(event) -> None:
    """
    Broadcast a new event to all connected clients.

    Args:
        event: Event model instance
    """
    from .routes import event_to_schema

    event_data = {
        "type": "new_event",
        "event": event_to_schema(event).model_dump(mode="json"),
    }
    broadcast_event_update(event_data)


def broadcast_status_change(event) -> None:
    """
    Broadcast an event status change to all connected clients.

    Args:
        event: Event model instance
    """
    from .routes import event_to_schema

    event_data = {
        "type": "status_change",
        "event": event_to_schema(event).model_dump(mode="json"),
    }
    broadcast_event_update(event_data)
