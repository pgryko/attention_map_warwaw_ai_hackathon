"""
Tests for Celery tasks.

Following TDD approach - write tests first, then verify implementation.
"""

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.utils import timezone

from core.models import (
    Event,
    EventCluster,
    SeverityChoices,
)
from tasks.processing import (
    broadcast_event,
    classify_event,
    cluster_events,
    extract_keyframe,
    process_event,
    store_media,
    transcribe_audio,
)


# ============================================================================
# Store Media Task Tests
# ============================================================================


class TestStoreMediaTask:
    """Tests for the store_media Celery task."""

    def test_store_media_uploads_to_minio(self, db, settings, mock_minio):
        """Media is uploaded to MinIO storage."""
        event_id = str(uuid4())
        media_data = b"fake image data"

        with patch("minio.Minio", return_value=mock_minio):
            store_media(event_id, media_data)

        # Verify upload was called
        mock_minio.put_object.assert_called_once()
        call_args = mock_minio.put_object.call_args
        assert settings.MINIO_BUCKET in call_args[0]
        assert f"events/{event_id}/media" in call_args[0]

    def test_store_media_returns_url(self, db, settings, mock_minio):
        """Returns the URL of the stored media."""
        event_id = str(uuid4())

        with patch("minio.Minio", return_value=mock_minio):
            url = store_media(event_id, b"data")

        assert settings.MINIO_ENDPOINT in url
        assert settings.MINIO_BUCKET in url
        assert event_id in url

    def test_store_media_creates_bucket_if_not_exists(self, db, mock_minio):
        """Bucket is created if it doesn't exist."""
        mock_minio.bucket_exists.return_value = False

        with patch("minio.Minio", return_value=mock_minio):
            store_media(str(uuid4()), b"data")

        mock_minio.make_bucket.assert_called_once()


# ============================================================================
# Extract Keyframe Task Tests
# ============================================================================


class TestExtractKeyframeTask:
    """Tests for the extract_keyframe Celery task."""

    def test_extract_keyframe_not_implemented(self, db):
        """Keyframe extraction returns empty string (not yet implemented)."""
        result = extract_keyframe("https://minio.local/bucket/video.mp4")

        # Currently returns empty as not implemented
        assert result == ""


# ============================================================================
# Transcribe Audio Task Tests
# ============================================================================


class TestTranscribeAudioTask:
    """Tests for the transcribe_audio Celery task."""

    def test_transcribe_audio_no_api_key(self, db, settings):
        """Returns empty string when no Groq API key configured."""
        settings.GROQ_API_KEY = ""

        result = transcribe_audio(b"audio data")

        assert result == ""

    def test_transcribe_audio_with_groq(self, db, settings):
        """Transcribes audio using Groq API."""
        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("groq.Groq") as mock_groq:
            mock_client = MagicMock()
            mock_client.audio.transcriptions.create.return_value = "Test transcription"
            mock_groq.return_value = mock_client

            result = transcribe_audio(b"audio data", "test.mp3")

        assert result == "Test transcription"


# ============================================================================
# Classify Event Task Tests
# ============================================================================


class TestClassifyEventTask:
    """Tests for the classify_event Celery task."""

    def test_classify_event_no_api_key(self, db, settings, event):
        """Returns default classification when no API key configured."""
        settings.OPENROUTER_API_KEY = ""

        result = classify_event(event)

        assert result["category"] == "informational"
        assert result["severity"] == 1
        assert "not configured" in result["reasoning"]

    def test_classify_event_with_openrouter(self, db, settings, event, mock_openrouter):
        """Classifies event using OpenRouter API."""
        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("openai.OpenAI", return_value=mock_openrouter):
            result = classify_event(event)

        assert result["category"] == "emergency"
        assert result["subcategory"] == "fire"
        assert result["severity"] == 4
        assert result["confidence"] == 0.95

    def test_classify_event_handles_markdown_response(self, db, settings, event):
        """Handles markdown-wrapped JSON response from LLM."""
        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("openai.OpenAI") as mock:
            client = MagicMock()
            response = MagicMock()
            response.choices = [MagicMock()]
            # Response wrapped in markdown code block
            response.choices[0].message.content = """```json
{"category": "traffic", "subcategory": "accident", "severity": 3,
"confidence": 0.8, "reasoning": "Car crash detected"}
```"""
            client.chat.completions.create.return_value = response
            mock.return_value = client

            result = classify_event(event)

        assert result["category"] == "traffic"
        assert result["severity"] == 3

    def test_classify_event_handles_api_error(self, db, settings, event):
        """Returns default classification on API error."""
        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("openai.OpenAI") as mock:
            client = MagicMock()
            client.chat.completions.create.side_effect = Exception("API error")
            mock.return_value = client

            result = classify_event(event)

        assert result["category"] == "informational"
        assert "failed" in result["reasoning"].lower()


# ============================================================================
# Cluster Events Task Tests
# ============================================================================


class TestClusterEventsTask:
    """Tests for the cluster_events Celery task."""

    def test_cluster_events_no_nearby(self, db, warsaw_location, london_location):
        """No cluster created when no nearby events."""
        Event.objects.create(location=warsaw_location)
        event2 = Event.objects.create(location=london_location)

        cluster_events(event2)

        event2.refresh_from_db()
        assert event2.cluster is None

    def test_cluster_events_creates_cluster(
        self, db, warsaw_location, warsaw_nearby_location
    ):
        """Cluster is created when nearby events exist."""
        event1 = Event.objects.create(location=warsaw_location)
        event2 = Event.objects.create(location=warsaw_nearby_location)

        cluster_events(event2)

        event1.refresh_from_db()
        event2.refresh_from_db()

        assert event1.cluster is not None
        assert event2.cluster is not None
        assert event1.cluster == event2.cluster
        assert event1.cluster.event_count == 2

    def test_cluster_events_joins_existing_cluster(
        self, db, warsaw_location, warsaw_nearby_location
    ):
        """Event joins existing cluster when one exists."""
        # Create existing cluster with event
        cluster = EventCluster.objects.create(
            centroid=warsaw_location,
            event_count=1,
        )
        Event.objects.create(location=warsaw_location, cluster=cluster)
        event2 = Event.objects.create(location=warsaw_nearby_location)

        cluster_events(event2)

        event2.refresh_from_db()
        cluster.refresh_from_db()

        assert event2.cluster == cluster
        assert cluster.event_count == 2

    def test_cluster_events_boosts_severity_on_count(
        self, db, warsaw_location, warsaw_nearby_location
    ):
        """Cluster severity is boosted when count threshold reached."""
        cluster = EventCluster.objects.create(
            centroid=warsaw_location,
            event_count=4,
            computed_severity=SeverityChoices.MEDIUM,
        )

        # Add 4 existing events
        for _ in range(4):
            Event.objects.create(location=warsaw_location, cluster=cluster)

        # 5th event triggers CRITICAL
        new_event = Event.objects.create(location=warsaw_nearby_location)
        cluster_events(new_event)

        cluster.refresh_from_db()
        assert cluster.computed_severity == SeverityChoices.CRITICAL

    def test_cluster_events_only_recent_events(self, db, warsaw_location):
        """Only events within 30 minutes are clustered."""
        # Old event (outside time window)
        old_event = Event.objects.create(location=warsaw_location)
        Event.objects.filter(id=old_event.id).update(
            created_at=timezone.now() - timedelta(hours=1)
        )

        # New event
        new_event = Event.objects.create(location=warsaw_location)

        cluster_events(new_event)

        new_event.refresh_from_db()
        assert new_event.cluster is None  # No cluster, old event is outside window


# ============================================================================
# Broadcast Event Task Tests
# ============================================================================


class TestBroadcastEventTask:
    """Tests for the broadcast_event Celery task."""

    def test_broadcast_event_publishes_to_redis(self, db, event, mock_redis):
        """Event is published to Redis channel."""
        with patch("redis.from_url", return_value=mock_redis):
            broadcast_event(event)

        mock_redis.publish.assert_called_once()

    def test_broadcast_event_includes_event_data(
        self, db, classified_event, mock_redis
    ):
        """Published message includes event data."""
        with patch("redis.from_url", return_value=mock_redis):
            broadcast_event(classified_event)

        call_args = mock_redis.publish.call_args
        published_data = json.loads(call_args[0][1])

        assert published_data["type"] == "new_event"
        assert "event" in published_data
        assert published_data["event"]["category"] == "emergency"


# ============================================================================
# Process Event Pipeline Tests
# ============================================================================


class TestProcessEventTask:
    """Tests for the main process_event pipeline task."""

    def test_process_event_not_found(self, db):
        """Returns error when event doesn't exist."""
        fake_id = str(uuid4())

        result = process_event(fake_id)

        assert result["status"] == "error"
        assert "not found" in result["message"]

    def test_process_event_stores_media(
        self, db, event, mock_minio, mock_openrouter, mock_redis
    ):
        """Media is stored when provided."""
        media_data = b"test image data"

        with (
            patch("minio.Minio", return_value=mock_minio),
            patch("openai.OpenAI", return_value=mock_openrouter),
            patch("redis.from_url", return_value=mock_redis),
        ):
            process_event(str(event.id), media_data)

        event.refresh_from_db()
        assert event.media_url is not None

    def test_process_event_classifies_event(
        self, db, event, mock_openrouter, mock_redis, settings
    ):
        """Event is classified by AI."""
        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        with (
            patch("openai.OpenAI", return_value=mock_openrouter),
            patch("redis.from_url", return_value=mock_redis),
        ):
            process_event(str(event.id))

        event.refresh_from_db()
        assert event.category == "emergency"
        assert event.severity == 4
        assert event.ai_confidence == 0.95

    def test_process_event_returns_success(
        self, db, event, mock_openrouter, mock_redis, settings
    ):
        """Returns success status on completion."""
        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        with (
            patch("openai.OpenAI", return_value=mock_openrouter),
            patch("redis.from_url", return_value=mock_redis),
        ):
            result = process_event(str(event.id))

        assert result["status"] == "success"
        assert result["event_id"] == str(event.id)

    def test_process_event_extracts_keyframe_for_video(
        self, db, warsaw_location, mock_openrouter, mock_redis, settings
    ):
        """Keyframe extraction is attempted for video events."""
        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        video_event = Event.objects.create(
            location=warsaw_location,
            media_type="video",
            media_url="https://minio.local/bucket/video.mp4",
        )

        with (
            patch("openai.OpenAI", return_value=mock_openrouter),
            patch("redis.from_url", return_value=mock_redis),
            patch("tasks.processing.extract_keyframe") as mock_extract,
        ):
            mock_extract.return_value = "https://minio.local/bucket/thumb.jpg"
            process_event(str(video_event.id))

        mock_extract.assert_called_once()

    def test_process_event_broadcasts_update(
        self, db, event, mock_openrouter, mock_redis, settings
    ):
        """Event update is broadcast to SSE clients."""
        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        with (
            patch("openai.OpenAI", return_value=mock_openrouter),
            patch("redis.from_url", return_value=mock_redis),
        ):
            process_event(str(event.id))

        mock_redis.publish.assert_called()
