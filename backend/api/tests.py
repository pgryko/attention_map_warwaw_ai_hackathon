"""
Tests for API endpoints.

Following TDD approach - write tests first, then verify implementation.
"""

import json
from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client
from django.utils import timezone

from core.models import (
    CategoryChoices,
    Event,
    EventCluster,
    SeverityChoices,
    StatusChoices,
)


# ============================================================================
# Event Upload Tests
# ============================================================================


class TestEventUploadEndpoint:
    """Tests for POST /events/upload endpoint."""

    @pytest.fixture
    def upload_url(self):
        return "/api/v1/events/upload"

    @pytest.fixture
    def mock_process_event(self):
        """Mock the Celery task to avoid external dependencies."""
        from unittest.mock import patch

        with patch("tasks.processing.process_event") as mock_task:
            mock_task.delay.return_value = None
            yield mock_task

    def test_upload_event_with_image(
        self, db, django_client: Client, sample_image, upload_url, mock_process_event
    ):
        """Successfully upload an event with an image."""
        response = django_client.post(
            upload_url,
            data={
                "latitude": 52.2297,
                "longitude": 21.0122,
                "description": "Fire at the corner",
                "media": sample_image,
            },
            format="multipart",
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert data["status"] == "processing"

        # Verify event was created
        event = Event.objects.get(id=data["id"])
        assert event.description == "Fire at the corner"
        assert event.media_type == "image"
        assert event.status == StatusChoices.NEW

        # Verify task was triggered
        mock_process_event.delay.assert_called_once()

    def test_upload_event_with_video(
        self, db, django_client: Client, sample_video, upload_url, mock_process_event
    ):
        """Successfully upload an event with a video."""
        response = django_client.post(
            upload_url,
            data={
                "latitude": 52.2297,
                "longitude": 21.0122,
                "description": "Car accident",
                "media": sample_video,
            },
            format="multipart",
        )

        assert response.status_code == 202
        data = response.json()
        event = Event.objects.get(id=data["id"])
        assert event.media_type == "video"

    def test_upload_event_anonymous(
        self, db, django_client: Client, sample_image, upload_url, mock_process_event
    ):
        """Anonymous users can upload events."""
        response = django_client.post(
            upload_url,
            data={
                "latitude": 52.2297,
                "longitude": 21.0122,
                "description": "Anonymous report",
                "media": sample_image,
            },
            format="multipart",
        )

        assert response.status_code == 202
        event = Event.objects.get(id=response.json()["id"])
        assert event.reporter is None

    def test_upload_event_authenticated(
        self,
        db,
        django_client: Client,
        user: User,
        sample_image,
        upload_url,
        mock_process_event,
    ):
        """Authenticated user's reporter field is set."""
        django_client.force_login(user)

        response = django_client.post(
            upload_url,
            data={
                "latitude": 52.2297,
                "longitude": 21.0122,
                "description": "Authenticated report",
                "media": sample_image,
            },
            format="multipart",
        )

        assert response.status_code == 202
        event = Event.objects.get(id=response.json()["id"])
        assert event.reporter == user

    def test_upload_event_invalid_media_type(
        self, db, django_client: Client, invalid_file, upload_url
    ):
        """Reject non-image/video files."""
        response = django_client.post(
            upload_url,
            data={
                "latitude": 52.2297,
                "longitude": 21.0122,
                "description": "Test",
                "media": invalid_file,
            },
            format="multipart",
        )

        assert response.status_code == 400
        assert "image or video" in response.json()["detail"]

    def test_upload_event_invalid_latitude(
        self, db, django_client: Client, sample_image, upload_url
    ):
        """Reject invalid latitude values."""
        response = django_client.post(
            upload_url,
            data={
                "latitude": 100.0,  # Invalid: > 90
                "longitude": 21.0122,
                "description": "Test",
                "media": sample_image,
            },
            format="multipart",
        )

        assert response.status_code == 400
        assert "Latitude" in response.json()["detail"]

    def test_upload_event_invalid_longitude(
        self, db, django_client: Client, sample_image, upload_url
    ):
        """Reject invalid longitude values."""
        response = django_client.post(
            upload_url,
            data={
                "latitude": 52.2297,
                "longitude": 200.0,  # Invalid: > 180
                "description": "Test",
                "media": sample_image,
            },
            format="multipart",
        )

        assert response.status_code == 400
        assert "Longitude" in response.json()["detail"]

    def test_upload_event_location_stored_correctly(
        self, db, django_client: Client, sample_image, upload_url, mock_process_event
    ):
        """GPS coordinates are stored correctly."""
        response = django_client.post(
            upload_url,
            data={
                "latitude": 52.2297,
                "longitude": 21.0122,
                "description": "Test",
                "media": sample_image,
            },
            format="multipart",
        )

        assert response.status_code == 202
        event = Event.objects.get(id=response.json()["id"])
        assert abs(event.location.y - 52.2297) < 0.0001
        assert abs(event.location.x - 21.0122) < 0.0001


# ============================================================================
# Event List Tests
# ============================================================================


class TestEventListEndpoint:
    """Tests for GET /events endpoint."""

    @pytest.fixture
    def list_url(self):
        return "/api/v1/events"

    def test_list_events_empty(self, db, django_client: Client, list_url):
        """Return empty list when no events."""
        response = django_client.get(list_url)

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0

    def test_list_events_returns_all(
        self, db, django_client: Client, multiple_events, list_url
    ):
        """Return all events without filters."""
        response = django_client.get(list_url)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["events"]) == 3

    def test_list_events_filter_by_status(
        self, db, django_client: Client, warsaw_location: Point, list_url
    ):
        """Filter events by status."""
        Event.objects.create(location=warsaw_location, status=StatusChoices.NEW)
        Event.objects.create(location=warsaw_location, status=StatusChoices.VERIFIED)
        Event.objects.create(location=warsaw_location, status=StatusChoices.RESOLVED)

        response = django_client.get(f"{list_url}?status=new,verified")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        statuses = {e["status"] for e in data["events"]}
        assert statuses == {"new", "verified"}

    def test_list_events_filter_by_severity(
        self, db, django_client: Client, warsaw_location: Point, list_url
    ):
        """Filter events by severity."""
        Event.objects.create(location=warsaw_location, severity=SeverityChoices.LOW)
        Event.objects.create(
            location=warsaw_location, severity=SeverityChoices.CRITICAL
        )

        response = django_client.get(f"{list_url}?severity=4")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["severity"] == 4

    def test_list_events_filter_by_category(
        self, db, django_client: Client, warsaw_location: Point, list_url
    ):
        """Filter events by category."""
        Event.objects.create(
            location=warsaw_location, category=CategoryChoices.EMERGENCY
        )
        Event.objects.create(location=warsaw_location, category=CategoryChoices.TRAFFIC)
        Event.objects.create(
            location=warsaw_location, category=CategoryChoices.INFRASTRUCTURE
        )

        response = django_client.get(f"{list_url}?category=emergency,traffic")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        categories = {e["category"] for e in data["events"]}
        assert categories == {"emergency", "traffic"}

    def test_list_events_filter_by_bounds(
        self,
        db,
        django_client: Client,
        warsaw_location: Point,
        london_location: Point,
        list_url,
    ):
        """Filter events by bounding box."""
        Event.objects.create(location=warsaw_location, description="Warsaw")
        Event.objects.create(location=london_location, description="London")

        # Bounding box around Warsaw
        bounds = "52.0,20.5,52.5,21.5"
        response = django_client.get(f"{list_url}?bounds={bounds}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["description"] == "Warsaw"

    def test_list_events_filter_by_since(
        self, db, django_client: Client, warsaw_location: Point, list_url
    ):
        """Filter events created after a timestamp."""
        old_event = Event.objects.create(location=warsaw_location, description="Old")
        # Manually set created_at to past
        Event.objects.filter(id=old_event.id).update(
            created_at=timezone.now() - timedelta(hours=2)
        )

        Event.objects.create(location=warsaw_location, description="New")

        # Use ISO format with Z suffix for UTC
        since = (timezone.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = django_client.get(f"{list_url}?since={since}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["description"] == "New"

    def test_list_events_pagination(
        self, db, django_client: Client, warsaw_location: Point, list_url
    ):
        """Test pagination with limit and offset."""
        for i in range(10):
            Event.objects.create(location=warsaw_location, description=f"Event {i}")

        response = django_client.get(f"{list_url}?limit=3&offset=2")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["events"]) == 3
        assert data["limit"] == 3
        assert data["offset"] == 2

    def test_list_events_max_limit(
        self, db, django_client: Client, warsaw_location: Point, list_url
    ):
        """Limit is capped at 500."""
        Event.objects.create(location=warsaw_location)

        response = django_client.get(f"{list_url}?limit=1000")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 500

    def test_list_events_ordered_by_created_at_desc(
        self, db, django_client: Client, warsaw_location: Point, list_url
    ):
        """Events are ordered by created_at descending."""
        Event.objects.create(location=warsaw_location, description="First")
        Event.objects.create(location=warsaw_location, description="Second")
        Event.objects.create(location=warsaw_location, description="Third")

        response = django_client.get(list_url)

        assert response.status_code == 200
        data = response.json()
        descriptions = [e["description"] for e in data["events"]]
        assert descriptions == ["Third", "Second", "First"]


# ============================================================================
# Event Detail Tests
# ============================================================================


class TestEventDetailEndpoint:
    """Tests for GET /events/{event_id} endpoint."""

    def test_get_event_success(
        self, db, django_client: Client, classified_event: Event
    ):
        """Successfully retrieve event details."""
        response = django_client.get(f"/api/v1/events/{classified_event.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(classified_event.id)
        assert data["category"] == "emergency"
        assert data["severity"] == 4

    def test_get_event_not_found(self, db, django_client: Client):
        """Return 404 for non-existent event."""
        fake_id = uuid4()
        response = django_client.get(f"/api/v1/events/{fake_id}")

        assert response.status_code == 404

    def test_get_event_includes_all_fields(
        self, db, django_client: Client, classified_event: Event
    ):
        """Response includes all required fields."""
        response = django_client.get(f"/api/v1/events/{classified_event.id}")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "id",
            "created_at",
            "latitude",
            "longitude",
            "description",
            "media_url",
            "media_type",
            "category",
            "subcategory",
            "severity",
            "ai_confidence",
            "status",
        ]
        for field in required_fields:
            assert field in data


# ============================================================================
# Event Status Update Tests
# ============================================================================


class TestEventStatusUpdateEndpoint:
    """Tests for PATCH /events/{event_id}/status endpoint."""

    @pytest.fixture
    def mock_broadcast(self):
        """Mock the SSE broadcast to avoid external dependencies."""
        from unittest.mock import patch

        with patch("api.streaming.broadcast_status_change") as mock_broadcast:
            yield mock_broadcast

    def test_update_status_to_verified(
        self, db, django_client: Client, event: Event, mock_broadcast
    ):
        """Successfully update event status to verified."""
        response = django_client.patch(
            f"/api/v1/events/{event.id}/status",
            data=json.dumps({"status": "verified"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verified"

        event.refresh_from_db()
        assert event.status == StatusChoices.VERIFIED

        # Verify SSE broadcast was called
        mock_broadcast.assert_called_once()

    def test_update_status_to_resolved(
        self, db, django_client: Client, event: Event, mock_broadcast
    ):
        """Successfully update event status to resolved."""
        response = django_client.patch(
            f"/api/v1/events/{event.id}/status",
            data=json.dumps({"status": "resolved"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        event.refresh_from_db()
        assert event.status == StatusChoices.RESOLVED

    def test_update_status_to_false_alarm(
        self, db, django_client: Client, event: Event, mock_broadcast
    ):
        """Successfully update event status to false_alarm."""
        response = django_client.patch(
            f"/api/v1/events/{event.id}/status",
            data=json.dumps({"status": "false_alarm"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        event.refresh_from_db()
        assert event.status == StatusChoices.FALSE_ALARM

    def test_update_status_sets_reviewed_at(
        self, db, django_client: Client, event: Event, mock_broadcast
    ):
        """Reviewed_at is set when status is updated."""
        before = timezone.now()

        response = django_client.patch(
            f"/api/v1/events/{event.id}/status",
            data=json.dumps({"status": "verified"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        event.refresh_from_db()
        assert event.reviewed_at is not None
        assert event.reviewed_at >= before

    def test_update_status_sets_reviewed_by(
        self,
        db,
        django_client: Client,
        event: Event,
        operator_user: User,
        mock_broadcast,
    ):
        """Reviewed_by is set to the authenticated user."""
        django_client.force_login(operator_user)

        response = django_client.patch(
            f"/api/v1/events/{event.id}/status",
            data=json.dumps({"status": "verified"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        event.refresh_from_db()
        assert event.reviewed_by == operator_user

    def test_update_status_not_found(self, db, django_client: Client, mock_broadcast):
        """Return 404 for non-existent event."""
        fake_id = uuid4()

        response = django_client.patch(
            f"/api/v1/events/{fake_id}/status",
            data=json.dumps({"status": "verified"}),
            content_type="application/json",
        )

        assert response.status_code == 404


# ============================================================================
# Cluster List Tests
# ============================================================================


class TestClusterListEndpoint:
    """Tests for GET /clusters endpoint."""

    @pytest.fixture
    def clusters_url(self):
        return "/api/v1/clusters"

    def test_list_clusters_empty(self, db, django_client: Client, clusters_url):
        """Return empty list when no clusters with multiple events."""
        response = django_client.get(clusters_url)

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_clusters_only_multi_event(
        self, db, django_client: Client, warsaw_location: Point, clusters_url
    ):
        """Only return clusters with event_count > 1."""
        # Single event cluster (should not be returned)
        EventCluster.objects.create(centroid=warsaw_location, event_count=1)
        # Multi-event cluster (should be returned)
        EventCluster.objects.create(centroid=warsaw_location, event_count=3)

        response = django_client.get(clusters_url)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["event_count"] == 3

    def test_list_clusters_filter_by_bounds(
        self,
        db,
        django_client: Client,
        warsaw_location: Point,
        london_location: Point,
        clusters_url,
    ):
        """Filter clusters by bounding box."""
        EventCluster.objects.create(centroid=warsaw_location, event_count=3)
        EventCluster.objects.create(centroid=london_location, event_count=2)

        bounds = "52.0,20.5,52.5,21.5"
        response = django_client.get(f"{clusters_url}?bounds={bounds}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_clusters_includes_all_fields(
        self, db, django_client: Client, warsaw_location: Point, clusters_url
    ):
        """Cluster response includes all required fields."""
        EventCluster.objects.create(
            centroid=warsaw_location,
            event_count=5,
            computed_severity=SeverityChoices.CRITICAL,
        )

        response = django_client.get(clusters_url)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        required_fields = [
            "id",
            "latitude",
            "longitude",
            "event_count",
            "computed_severity",
            "first_event_at",
            "last_event_at",
        ]
        for field in required_fields:
            assert field in data[0]


# ============================================================================
# Stats Endpoint Tests
# ============================================================================


class TestStatsEndpoint:
    """Tests for GET /stats/summary endpoint."""

    @pytest.fixture
    def stats_url(self):
        return "/api/v1/stats/summary"

    def test_stats_empty(self, db, django_client: Client, stats_url):
        """Return zero counts when no events."""
        response = django_client.get(stats_url)

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 0
        assert data["active_clusters"] == 0

    def test_stats_total_events(
        self, db, django_client: Client, multiple_events, stats_url
    ):
        """Return correct total event count."""
        response = django_client.get(stats_url)

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 3

    def test_stats_events_by_status(
        self, db, django_client: Client, warsaw_location: Point, stats_url
    ):
        """Return events grouped by status."""
        Event.objects.create(location=warsaw_location, status=StatusChoices.NEW)
        Event.objects.create(location=warsaw_location, status=StatusChoices.NEW)
        Event.objects.create(location=warsaw_location, status=StatusChoices.VERIFIED)

        response = django_client.get(stats_url)

        assert response.status_code == 200
        data = response.json()
        assert data["events_by_status"]["new"] == 2
        assert data["events_by_status"]["verified"] == 1

    def test_stats_events_by_category(
        self, db, django_client: Client, warsaw_location: Point, stats_url
    ):
        """Return events grouped by category."""
        Event.objects.create(
            location=warsaw_location, category=CategoryChoices.EMERGENCY
        )
        Event.objects.create(
            location=warsaw_location, category=CategoryChoices.EMERGENCY
        )
        Event.objects.create(location=warsaw_location, category=CategoryChoices.TRAFFIC)

        response = django_client.get(stats_url)

        assert response.status_code == 200
        data = response.json()
        assert data["events_by_category"]["emergency"] == 2
        assert data["events_by_category"]["traffic"] == 1

    def test_stats_events_by_severity(
        self, db, django_client: Client, warsaw_location: Point, stats_url
    ):
        """Return events grouped by severity."""
        Event.objects.create(location=warsaw_location, severity=SeverityChoices.LOW)
        Event.objects.create(
            location=warsaw_location, severity=SeverityChoices.CRITICAL
        )
        Event.objects.create(
            location=warsaw_location, severity=SeverityChoices.CRITICAL
        )

        response = django_client.get(stats_url)

        assert response.status_code == 200
        data = response.json()
        assert data["events_by_severity"]["1"] == 1
        assert data["events_by_severity"]["4"] == 2

    def test_stats_active_clusters(
        self, db, django_client: Client, warsaw_location: Point, stats_url
    ):
        """Return count of active clusters (event_count > 1)."""
        EventCluster.objects.create(centroid=warsaw_location, event_count=1)
        EventCluster.objects.create(centroid=warsaw_location, event_count=3)
        EventCluster.objects.create(centroid=warsaw_location, event_count=5)

        response = django_client.get(stats_url)

        assert response.status_code == 200
        data = response.json()
        assert data["active_clusters"] == 2


# ============================================================================
# SSE Streaming Tests
# ============================================================================


class TestSSEStreaming:
    """Tests for Server-Sent Events streaming functionality."""

    def test_get_redis_client(self, settings):
        """get_redis_client returns a Redis client configured from settings."""
        from unittest.mock import patch

        from api.streaming import get_redis_client

        settings.REDIS_URL = "redis://test-host:6379/1"

        mock_client = object()
        with patch("redis.from_url", return_value=mock_client) as mock_from_url:
            client = get_redis_client()

        mock_from_url.assert_called_once_with("redis://test-host:6379/1")
        assert client is mock_client

    def test_stream_events_returns_streaming_response(self, db):
        """stream_events returns a StreamingHttpResponse with correct headers."""
        from unittest.mock import MagicMock, patch

        from django.http import StreamingHttpResponse

        from api.streaming import stream_events

        mock_request = MagicMock()
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_pubsub.listen.return_value = iter([])

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            response = stream_events(mock_request)

        assert isinstance(response, StreamingHttpResponse)
        assert response["Content-Type"] == "text/event-stream"
        assert response["Cache-Control"] == "no-cache"
        assert response["X-Accel-Buffering"] == "no"

    def test_event_stream_sends_connected_message(self, db):
        """event_stream sends initial connected event."""
        from unittest.mock import MagicMock, patch

        from api.streaming import event_stream

        mock_request = MagicMock()
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_pubsub.listen.return_value = iter([])

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            gen = event_stream(mock_request)
            first_message = next(gen)

        assert "event: connected" in first_message
        assert '"status": "connected"' in first_message
        assert first_message.endswith("\n\n")

    def test_event_stream_yields_messages_from_pubsub(self, db):
        """event_stream yields formatted SSE messages from Redis pub/sub."""
        from unittest.mock import MagicMock, patch

        from api.streaming import event_stream

        mock_request = MagicMock()
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub

        # Simulate pub/sub messages
        messages = [
            {"type": "subscribe", "data": None},  # Subscribe confirmation
            {"type": "message", "data": b'{"type": "new_event", "event_id": "123"}'},
            {"type": "message", "data": '{"type": "status_change", "event_id": "456"}'},
        ]
        mock_pubsub.listen.return_value = iter(messages)

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            gen = event_stream(mock_request)
            results = list(gen)

        # First message is connected
        assert "event: connected" in results[0]

        # Second message is the first event (bytes)
        assert "event: event_update" in results[1]
        assert '"type": "new_event"' in results[1]

        # Third message is the second event (string)
        assert "event: event_update" in results[2]
        assert '"type": "status_change"' in results[2]

    def test_event_stream_subscribes_to_correct_channel(self, db):
        """event_stream subscribes to the events:updates channel."""
        from unittest.mock import MagicMock, patch

        from api.streaming import EVENTS_CHANNEL, event_stream

        mock_request = MagicMock()
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_pubsub.listen.return_value = iter([])

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            gen = event_stream(mock_request)
            # Consume the generator to trigger subscription
            list(gen)

        mock_pubsub.subscribe.assert_called_once_with(EVENTS_CHANNEL)

    def test_event_stream_unsubscribes_on_cleanup(self, db):
        """event_stream properly cleans up pub/sub on generator close."""
        from unittest.mock import MagicMock, patch

        from api.streaming import EVENTS_CHANNEL, event_stream

        mock_request = MagicMock()
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_pubsub.listen.return_value = iter([])

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            gen = event_stream(mock_request)
            # Consume the generator
            list(gen)

        mock_pubsub.unsubscribe.assert_called_once_with(EVENTS_CHANNEL)
        mock_pubsub.close.assert_called_once()

    def test_broadcast_event_update_publishes_to_redis(self, db, settings):
        """broadcast_event_update publishes JSON to Redis channel."""
        from unittest.mock import MagicMock, patch

        from api.streaming import EVENTS_CHANNEL, broadcast_event_update

        settings.REDIS_URL = "redis://localhost:6379/0"
        mock_redis = MagicMock()

        event_data = {"type": "test", "event_id": "123"}

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            broadcast_event_update(event_data)

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == EVENTS_CHANNEL
        assert '"type": "test"' in call_args[0][1]

    def test_broadcast_event_update_handles_redis_error(self, db, settings, caplog):
        """broadcast_event_update logs error if Redis fails."""
        import logging
        from unittest.mock import MagicMock, patch

        from api.streaming import broadcast_event_update

        settings.REDIS_URL = "redis://localhost:6379/0"
        mock_redis = MagicMock()
        mock_redis.publish.side_effect = Exception("Redis connection failed")

        with caplog.at_level(logging.ERROR):
            with patch("api.streaming.get_redis_client", return_value=mock_redis):
                broadcast_event_update({"test": "data"})

        assert "Failed to broadcast" in caplog.text

    def test_broadcast_new_event(self, db, classified_event: Event, settings):
        """broadcast_new_event broadcasts event with type 'new_event'."""
        from unittest.mock import MagicMock, patch

        from api.streaming import broadcast_new_event

        settings.REDIS_URL = "redis://localhost:6379/0"
        mock_redis = MagicMock()

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            broadcast_new_event(classified_event)

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        published_data = json.loads(call_args[0][1])

        assert published_data["type"] == "new_event"
        assert "event" in published_data
        assert published_data["event"]["id"] == str(classified_event.id)

    def test_broadcast_status_change(self, db, event: Event, settings):
        """broadcast_status_change broadcasts event with type 'status_change'."""
        from unittest.mock import MagicMock, patch

        from api.streaming import broadcast_status_change

        settings.REDIS_URL = "redis://localhost:6379/0"
        mock_redis = MagicMock()

        with patch("api.streaming.get_redis_client", return_value=mock_redis):
            broadcast_status_change(event)

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        published_data = json.loads(call_args[0][1])

        assert published_data["type"] == "status_change"
        assert "event" in published_data
        assert published_data["event"]["id"] == str(event.id)

    def test_events_channel_constant(self):
        """EVENTS_CHANNEL is defined correctly."""
        from api.streaming import EVENTS_CHANNEL

        assert EVENTS_CHANNEL == "events:updates"
