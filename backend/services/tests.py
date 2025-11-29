"""
Tests for business logic services.

Following TDD approach - write tests first, then implement.
"""

import subprocess
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.gis.geos import Point
from django.utils import timezone

from core.models import (
    Event,
    EventCluster,
    SeverityChoices,
)


# ============================================================================
# Storage Service Tests
# ============================================================================


class TestStorageService:
    """Tests for the StorageService class."""

    def test_storage_service_init(self, settings):
        """StorageService initializes with settings."""
        from services.storage import StorageService

        settings.MINIO_ENDPOINT = "test-endpoint:9000"
        settings.MINIO_ACCESS_KEY = "test-key"
        settings.MINIO_SECRET_KEY = "test-secret"  # pragma: allowlist secret
        settings.MINIO_USE_SSL = False
        settings.MINIO_BUCKET = "test-bucket"

        with patch("services.storage.Minio") as mock_minio:
            service = StorageService()

        mock_minio.assert_called_once_with(
            "test-endpoint:9000",
            access_key="test-key",
            secret_key="test-secret",  # pragma: allowlist secret
            secure=False,
        )
        assert service.client is not None

    def test_ensure_bucket_creates_if_not_exists(self, settings):
        """ensure_bucket creates bucket if it doesn't exist."""
        from services.storage import StorageService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "test-bucket"
        settings.MINIO_USE_SSL = False

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False

        with patch("services.storage.Minio", return_value=mock_client):
            service = StorageService()
            service.ensure_bucket()

        mock_client.bucket_exists.assert_called_once_with("test-bucket")
        mock_client.make_bucket.assert_called_once_with("test-bucket")

    def test_ensure_bucket_skips_if_exists(self, settings):
        """ensure_bucket skips creation if bucket exists."""
        from services.storage import StorageService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "test-bucket"
        settings.MINIO_USE_SSL = False

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True

        with patch("services.storage.Minio", return_value=mock_client):
            service = StorageService()
            service.ensure_bucket()

        mock_client.make_bucket.assert_not_called()

    def test_upload_media_returns_url(self, settings):
        """upload_media uploads to MinIO and returns URL."""
        from services.storage import StorageService

        settings.MINIO_BUCKET = "events"
        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_USE_SSL = False

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True

        with patch("services.storage.Minio", return_value=mock_client):
            service = StorageService()
            url = service.upload_media("123", b"test data", "image/png")

        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args[0][0] == "events"  # bucket
        assert "events/123/media" in call_args[0][1]  # object_name
        assert url == "http://localhost:9000/events/events/123/media"

    def test_upload_media_uses_https_when_ssl(self, settings):
        """upload_media uses https when SSL is enabled."""
        from services.storage import StorageService

        settings.MINIO_BUCKET = "events"
        settings.MINIO_ENDPOINT = "storage.example.com"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_USE_SSL = True

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True

        with patch("services.storage.Minio", return_value=mock_client):
            service = StorageService()
            url = service.upload_media("123", b"data", "image/png")

        assert url.startswith("https://")

    def test_upload_thumbnail(self, settings):
        """upload_thumbnail uploads thumbnail with _thumb suffix."""
        from services.storage import StorageService

        settings.MINIO_BUCKET = "events"
        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_USE_SSL = False

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True

        with patch("services.storage.Minio", return_value=mock_client):
            service = StorageService()
            service.upload_thumbnail("123", b"thumb data")

        call_args = mock_client.put_object.call_args
        assert "_thumb" in call_args[0][1]


# ============================================================================
# Classification Service Tests
# ============================================================================


class TestClassificationService:
    """Tests for the ClassificationService class."""

    def test_classification_service_init_without_api_key(self, settings):
        """ClassificationService initializes without API key."""
        from services.classification import ClassificationService

        settings.OPENROUTER_API_KEY = ""

        service = ClassificationService()
        assert service.client is None

    def test_classification_service_init_with_api_key(self, settings):
        """ClassificationService initializes with API key."""
        from services.classification import ClassificationService

        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret
        settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

        with patch("openai.OpenAI") as mock_openai:
            ClassificationService()

        mock_openai.assert_called_once_with(
            api_key="test-key",  # pragma: allowlist secret
            base_url="https://openrouter.ai/api/v1",
        )

    def test_classify_returns_default_without_client(self, settings):
        """classify returns default classification when no API key."""
        from services.classification import ClassificationService

        settings.OPENROUTER_API_KEY = ""

        service = ClassificationService()
        result = service.classify("Fire at the corner")

        assert result["category"] == "informational"
        assert result["severity"] == 1
        assert "not configured" in result["reasoning"]

    def test_classify_calls_openrouter(self, settings, mock_openrouter):
        """classify calls OpenRouter API with proper prompt."""
        from services.classification import ClassificationService

        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret
        settings.OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
        settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

        with patch("openai.OpenAI", return_value=mock_openrouter):
            service = ClassificationService()
            result = service.classify("Fire at the corner")

        mock_openrouter.chat.completions.create.assert_called_once()
        call_args = mock_openrouter.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "google/gemini-2.5-flash-lite"
        assert "Fire at the corner" in call_args.kwargs["messages"][0]["content"]

        assert result["category"] == "emergency"
        assert result["severity"] == 4

    def test_classify_handles_markdown_response(self, settings):
        """classify handles markdown-wrapped JSON response."""
        from services.classification import ClassificationService

        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret
        settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

        mock_client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = """```json
{
    "category": "traffic",
    "subcategory": "accident",
    "severity": 3,
    "confidence": 0.85,
    "reasoning": "Car accident detected"
}
```"""
        mock_client.chat.completions.create.return_value = response

        with patch("openai.OpenAI", return_value=mock_client):
            service = ClassificationService()
            result = service.classify("Car crash on highway")

        assert result["category"] == "traffic"
        assert result["severity"] == 3

    def test_classify_handles_api_error(self, settings):
        """classify returns default on API error."""
        from services.classification import ClassificationService

        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret
        settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch("openai.OpenAI", return_value=mock_client):
            service = ClassificationService()
            result = service.classify("Test description")

        assert result["category"] == "informational"
        assert "failed" in result["reasoning"].lower()


# ============================================================================
# Clustering Service Tests
# ============================================================================


class TestClusteringService:
    """Tests for the ClusteringService class."""

    def test_find_nearby_events_returns_within_radius(
        self, db, warsaw_location: Point, warsaw_nearby_location: Point
    ):
        """find_nearby_events returns events within radius."""
        from services.clustering import ClusteringService

        event1 = Event.objects.create(location=warsaw_location, description="Event 1")
        Event.objects.create(location=warsaw_nearby_location, description="Event 2")

        service = ClusteringService()
        nearby = service.find_nearby_events(event1, radius_meters=200)

        assert nearby.count() == 1
        assert nearby.first().description == "Event 2"

    def test_find_nearby_events_excludes_old_events(
        self, db, warsaw_location: Point, warsaw_nearby_location: Point
    ):
        """find_nearby_events excludes events older than time window."""
        from services.clustering import ClusteringService

        event1 = Event.objects.create(location=warsaw_location)
        old_event = Event.objects.create(location=warsaw_nearby_location)

        # Make the second event old
        Event.objects.filter(id=old_event.id).update(
            created_at=timezone.now() - timedelta(hours=2)
        )

        service = ClusteringService(time_window_minutes=30)
        nearby = service.find_nearby_events(event1, radius_meters=200)

        assert nearby.count() == 0

    def test_find_nearby_events_excludes_self(self, db, warsaw_location: Point):
        """find_nearby_events excludes the source event."""
        from services.clustering import ClusteringService

        event = Event.objects.create(location=warsaw_location)

        service = ClusteringService()
        nearby = service.find_nearby_events(event, radius_meters=1000)

        assert event not in nearby

    def test_create_cluster_creates_new(self, db, warsaw_location: Point):
        """create_cluster creates a new cluster for events."""
        from services.clustering import ClusteringService

        event = Event.objects.create(
            location=warsaw_location,
            severity=SeverityChoices.MEDIUM,
        )

        service = ClusteringService()
        cluster = service.create_cluster(event, [])

        assert cluster is not None
        assert cluster.event_count == 1
        event.refresh_from_db()
        assert event.cluster == cluster

    def test_create_cluster_includes_nearby_events(
        self, db, warsaw_location: Point, warsaw_nearby_location: Point
    ):
        """create_cluster includes nearby events in the cluster."""
        from services.clustering import ClusteringService

        event1 = Event.objects.create(location=warsaw_location)
        event2 = Event.objects.create(location=warsaw_nearby_location)

        service = ClusteringService()
        cluster = service.create_cluster(event1, [event2])

        assert cluster.event_count == 2
        event2.refresh_from_db()
        assert event2.cluster == cluster

    def test_add_to_existing_cluster(
        self, db, warsaw_location: Point, event_cluster: EventCluster
    ):
        """add_to_cluster adds event to existing cluster."""
        from services.clustering import ClusteringService

        event = Event.objects.create(location=warsaw_location)

        service = ClusteringService()
        service.add_to_cluster(event, event_cluster)

        event.refresh_from_db()
        assert event.cluster == event_cluster
        event_cluster.refresh_from_db()
        assert event_cluster.event_count >= 1

    def test_cluster_escalates_severity_at_threshold(
        self, db, warsaw_location: Point, warsaw_nearby_location: Point
    ):
        """Cluster severity escalates when event count reaches threshold."""
        from services.clustering import ClusteringService

        # Create initial events
        events = []
        for i in range(4):
            events.append(
                Event.objects.create(
                    location=warsaw_location,
                    severity=SeverityChoices.LOW,
                )
            )

        # Create cluster with 4 events
        service = ClusteringService()
        cluster = service.create_cluster(events[0], events[1:])
        assert cluster.event_count == 4

        # Add 5th event - should trigger escalation
        event5 = Event.objects.create(
            location=warsaw_nearby_location,
            severity=SeverityChoices.LOW,
        )
        service.add_to_cluster(event5, cluster)

        cluster.refresh_from_db()
        assert cluster.event_count == 5
        assert cluster.computed_severity == SeverityChoices.CRITICAL

    def test_process_event_creates_cluster_when_nearby_exists(
        self, db, warsaw_location: Point, warsaw_nearby_location: Point
    ):
        """process_event creates cluster when nearby events exist."""
        from services.clustering import ClusteringService

        Event.objects.create(location=warsaw_location)
        event2 = Event.objects.create(location=warsaw_nearby_location)

        service = ClusteringService()
        service.process_event(event2)

        assert EventCluster.objects.count() == 1

    def test_process_event_no_cluster_when_no_nearby(
        self, db, warsaw_location: Point, london_location: Point
    ):
        """process_event doesn't create cluster when no nearby events."""
        from services.clustering import ClusteringService

        Event.objects.create(location=warsaw_location)
        event2 = Event.objects.create(location=london_location)

        service = ClusteringService()
        service.process_event(event2)

        event2.refresh_from_db()
        assert event2.cluster is None


# ============================================================================
# Event Processing Service Tests
# ============================================================================


class TestEventProcessingService:
    """Tests for the EventProcessingService orchestrator."""

    def test_process_event_stores_media(self, db, event: Event, settings):
        """process_event stores media when provided."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/media.jpg"

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": "Test",
        }

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            service.process_event(event, media_data=b"test media")

        mock_storage.upload_media.assert_called_once()
        event.refresh_from_db()
        assert event.media_url == "http://storage/media.jpg"

    def test_process_event_classifies(self, db, event: Event, settings):
        """process_event classifies the event."""
        from services.processing import EventProcessingService

        settings.OPENROUTER_API_KEY = "test-key"  # pragma: allowlist secret

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "emergency",
            "subcategory": "fire",
            "severity": 4,
            "confidence": 0.95,
            "reasoning": "Fire detected",
        }

        with (
            patch("services.processing.StorageService"),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            service.process_event(event)

        event.refresh_from_db()
        assert event.category == "emergency"
        assert event.severity == 4
        assert event.ai_confidence == 0.95

    def test_process_event_clusters(self, db, event: Event, settings):
        """process_event applies spatial clustering."""
        from services.processing import EventProcessingService

        settings.OPENROUTER_API_KEY = ""

        mock_clustering = MagicMock()

        with (
            patch("services.processing.StorageService"),
            patch("services.processing.ClassificationService"),
            patch(
                "services.processing.ClusteringService", return_value=mock_clustering
            ),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            service.process_event(event)

        mock_clustering.process_event.assert_called_once_with(event)

    def test_process_event_broadcasts(self, db, event: Event, settings):
        """process_event broadcasts to SSE clients."""
        from services.processing import EventProcessingService

        settings.OPENROUTER_API_KEY = ""

        with (
            patch("services.processing.StorageService"),
            patch("services.processing.ClassificationService"),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event") as mock_broadcast,
        ):
            service = EventProcessingService()
            service.process_event(event)

        mock_broadcast.assert_called_once_with(event)


# ============================================================================
# Keyframe Service Tests
# ============================================================================


class TestKeyframeService:
    """Tests for the KeyframeService class."""

    def test_keyframe_service_init(self, settings):
        """KeyframeService initializes with settings."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "/usr/bin/ffmpeg"
        settings.FFPROBE_PATH = "/usr/bin/ffprobe"
        settings.THUMBNAIL_WIDTH = 800
        settings.THUMBNAIL_QUALITY = 90

        service = KeyframeService()

        assert service.ffmpeg_path == "/usr/bin/ffmpeg"
        assert service.ffprobe_path == "/usr/bin/ffprobe"
        assert service.thumbnail_width == 800
        assert service.thumbnail_quality == 90

    def test_keyframe_service_default_settings(self, settings):
        """KeyframeService uses defaults when settings not present."""
        from services.keyframe import KeyframeService

        # Remove settings to test defaults
        if hasattr(settings, "FFMPEG_PATH"):
            delattr(settings, "FFMPEG_PATH")
        if hasattr(settings, "FFPROBE_PATH"):
            delattr(settings, "FFPROBE_PATH")
        if hasattr(settings, "THUMBNAIL_WIDTH"):
            delattr(settings, "THUMBNAIL_WIDTH")
        if hasattr(settings, "THUMBNAIL_QUALITY"):
            delattr(settings, "THUMBNAIL_QUALITY")

        service = KeyframeService()

        assert service.ffmpeg_path == "ffmpeg"
        assert service.ffprobe_path == "ffprobe"
        assert service.thumbnail_width == 640
        assert service.thumbnail_quality == 85

    def test_is_available_returns_true_when_ffmpeg_exists(self, settings):
        """is_available returns True when FFmpeg is installed."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            service = KeyframeService()
            result = service.is_available()

        assert result is True
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["ffmpeg", "-version"]

    def test_is_available_returns_false_when_ffmpeg_not_found(self, settings):
        """is_available returns False when FFmpeg is not installed."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"

        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            service = KeyframeService()
            result = service.is_available()

        assert result is False

    def test_is_available_returns_false_on_subprocess_error(self, settings):
        """is_available returns False on subprocess error."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"

        with patch("subprocess.run", side_effect=subprocess.SubprocessError("Error")):
            service = KeyframeService()
            result = service.is_available()

        assert result is False

    def test_get_video_duration_parses_ffprobe_output(self, settings):
        """get_video_duration correctly parses FFprobe output."""
        from services.keyframe import KeyframeService

        settings.FFPROBE_PATH = "ffprobe"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "10.5\n"

        with patch("subprocess.run", return_value=mock_result):
            service = KeyframeService()
            duration = service.get_video_duration(b"fake video data")

        assert duration == 10.5

    def test_get_video_duration_returns_none_on_failure(self, settings):
        """get_video_duration returns None when FFprobe fails."""
        from services.keyframe import KeyframeService

        settings.FFPROBE_PATH = "ffprobe"

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            service = KeyframeService()
            duration = service.get_video_duration(b"fake video data")

        assert duration is None

    def test_extract_keyframe_returns_none_when_ffmpeg_unavailable(self, settings):
        """extract_keyframe returns None when FFmpeg is not available."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"

        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            service = KeyframeService()
            result = service.extract_keyframe(b"fake video data")

        assert result is None

    def test_extract_keyframe_calls_ffmpeg_correctly(self, settings):
        """extract_keyframe calls FFmpeg with correct arguments."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"
        settings.FFPROBE_PATH = "ffprobe"
        settings.THUMBNAIL_WIDTH = 640
        settings.THUMBNAIL_QUALITY = 85

        # First call: is_available (version check)
        # Second call: get_video_duration (ffprobe)
        # Third call: actual extraction (ffmpeg)
        mock_calls = []

        def mock_run(args, **kwargs):
            mock_calls.append(args)
            result = MagicMock()
            if "ffprobe" in str(args):
                result.returncode = 0
                result.stdout = "5.0\n"
            else:
                result.returncode = 0
            return result

        with (
            patch("subprocess.run", side_effect=mock_run),
            patch("pathlib.Path.read_bytes", return_value=b"fake jpeg data"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            service = KeyframeService()
            result = service.extract_keyframe(b"fake video data")

        assert result == b"fake jpeg data"
        # Check that ffmpeg was called for extraction (the command contains ffmpeg)
        ffmpeg_calls = [c for c in mock_calls if "ffmpeg" in str(c[0])]
        assert len(ffmpeg_calls) >= 1

    def test_extract_keyframe_uses_timestamp_parameter(self, settings):
        """extract_keyframe uses provided timestamp."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"
        settings.FFPROBE_PATH = "ffprobe"
        settings.THUMBNAIL_WIDTH = 640
        settings.THUMBNAIL_QUALITY = 85

        captured_args = []

        def mock_run(args, **kwargs):
            captured_args.append(args)
            result = MagicMock()
            result.returncode = 0
            return result

        with (
            patch("subprocess.run", side_effect=mock_run),
            patch("pathlib.Path.read_bytes", return_value=b"fake jpeg data"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            service = KeyframeService()
            service.extract_keyframe(b"fake video data", timestamp=3.5)

        # Find the ffmpeg call for extraction (not version check)
        ffmpeg_call = None
        for args in captured_args:
            if "-vframes" in args:
                ffmpeg_call = args
                break

        assert ffmpeg_call is not None
        ss_index = ffmpeg_call.index("-ss")
        assert ffmpeg_call[ss_index + 1] == "3.5"

    def test_extract_keyframe_returns_none_on_ffmpeg_failure(self, settings):
        """extract_keyframe returns None when FFmpeg fails."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"

        call_count = [0]

        def mock_run(args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:  # version check
                result.returncode = 0
            else:  # extraction
                result.returncode = 1
                result.stderr = b"Error"
            return result

        with patch("subprocess.run", side_effect=mock_run):
            service = KeyframeService()
            result = service.extract_keyframe(b"fake video data", timestamp=1.0)

        assert result is None

    def test_extract_multiple_keyframes(self, settings):
        """extract_multiple_keyframes extracts frames at different timestamps."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"
        settings.FFPROBE_PATH = "ffprobe"

        timestamps_used = []

        def mock_run(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "ffprobe" in str(args):
                result.stdout = "12.0\n"  # 12 second video
            else:
                # Capture timestamp
                if "-ss" in args:
                    idx = args.index("-ss")
                    timestamps_used.append(float(args[idx + 1]))
            return result

        with (
            patch("subprocess.run", side_effect=mock_run),
            patch("pathlib.Path.read_bytes", return_value=b"fake jpeg"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            service = KeyframeService()
            frames = service.extract_multiple_keyframes(b"fake video", count=3)

        assert len(frames) == 3
        # Should extract at 25%, 50%, 75% of duration (3, 6, 9 seconds)
        assert len(timestamps_used) == 3
        assert timestamps_used[0] == 3.0  # 12 * 1/4
        assert timestamps_used[1] == 6.0  # 12 * 2/4
        assert timestamps_used[2] == 9.0  # 12 * 3/4

    def test_extract_multiple_keyframes_handles_partial_failure(self, settings):
        """extract_multiple_keyframes handles partial extraction failures."""
        from services.keyframe import KeyframeService

        settings.FFMPEG_PATH = "ffmpeg"
        settings.FFPROBE_PATH = "ffprobe"

        call_count = [0]

        def mock_run(args, **kwargs):
            result = MagicMock()
            if "ffprobe" in str(args):
                result.returncode = 0
                result.stdout = "12.0\n"
            elif "-version" in args:
                result.returncode = 0
            else:
                call_count[0] += 1
                # Fail every other extraction
                result.returncode = 0 if call_count[0] % 2 == 1 else 1
                result.stderr = b"" if call_count[0] % 2 == 1 else b"Error"
            return result

        def mock_exists():
            return call_count[0] % 2 == 1

        with (
            patch("subprocess.run", side_effect=mock_run),
            patch("pathlib.Path.read_bytes", return_value=b"fake jpeg"),
            patch("pathlib.Path.exists", side_effect=mock_exists),
        ):
            service = KeyframeService()
            frames = service.extract_multiple_keyframes(b"fake video", count=3)

        # Only some extractions succeeded
        assert len(frames) <= 3


# ============================================================================
# Event Processing Service with Keyframe Tests
# ============================================================================


class TestEventProcessingServiceWithKeyframe:
    """Tests for EventProcessingService keyframe integration."""

    def test_process_event_extracts_keyframe_for_video(
        self, db, warsaw_location: Point, settings
    ):
        """process_event extracts keyframe for video events."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Video event",
            media_type="video",
        )

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/video.mp4"
        mock_storage.upload_thumbnail.return_value = "http://storage/thumb.jpg"

        mock_keyframe = MagicMock()
        mock_keyframe.extract_keyframe.return_value = b"fake thumbnail data"

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": "Test",
        }

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch("services.processing.KeyframeService", return_value=mock_keyframe),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            result = service.process_event(
                event, media_data=b"fake video data", media_content_type="video/mp4"
            )

        assert "extract_keyframe" in result["steps_completed"]
        mock_keyframe.extract_keyframe.assert_called_once_with(b"fake video data")
        mock_storage.upload_thumbnail.assert_called_once()
        event.refresh_from_db()
        assert event.thumbnail_url == "http://storage/thumb.jpg"

    def test_process_event_skips_keyframe_for_image(
        self, db, warsaw_location: Point, settings
    ):
        """process_event skips keyframe extraction for image events."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Image event",
            media_type="image",
        )

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/image.jpg"

        mock_keyframe = MagicMock()

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": "Test",
        }

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch("services.processing.KeyframeService", return_value=mock_keyframe),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            result = service.process_event(
                event, media_data=b"fake image data", media_content_type="image/png"
            )

        assert "extract_keyframe" not in result["steps_completed"]
        mock_keyframe.extract_keyframe.assert_not_called()

    def test_process_event_continues_on_keyframe_failure(
        self, db, warsaw_location: Point, settings
    ):
        """process_event continues processing if keyframe extraction fails."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Video event",
            media_type="video",
        )

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/video.mp4"

        mock_keyframe = MagicMock()
        mock_keyframe.extract_keyframe.return_value = None  # Extraction failed

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": "Test",
        }

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch("services.processing.KeyframeService", return_value=mock_keyframe),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            result = service.process_event(
                event, media_data=b"fake video data", media_content_type="video/mp4"
            )

        # Keyframe extraction was attempted but failed
        assert "extract_keyframe" not in result["steps_completed"]
        # But other processing continued
        assert "classify" in result["steps_completed"]
        assert "broadcast" in result["steps_completed"]


# ============================================================================
# Transcription Service Tests
# ============================================================================


class TestTranscriptionService:
    """Tests for the TranscriptionService class."""

    def test_transcription_service_init_without_api_key(self, settings):
        """TranscriptionService initializes without API key."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = ""

        service = TranscriptionService()
        assert service.client is None
        assert service.is_available() is False

    def test_transcription_service_init_with_api_key(self, settings):
        """TranscriptionService initializes with API key."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret
        settings.GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"

        with patch("groq.Groq") as mock_groq:
            service = TranscriptionService()

        mock_groq.assert_called_once_with(
            api_key="test-key"  # pragma: allowlist secret
        )
        assert service.model == "whisper-large-v3-turbo"

    def test_is_available_returns_true_when_client_exists(self, settings):
        """is_available returns True when Groq client is configured."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("groq.Groq"):
            service = TranscriptionService()
            assert service.is_available() is True

    def test_is_ffmpeg_available_returns_true(self, settings):
        """_is_ffmpeg_available returns True when FFmpeg is installed."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = ""
        settings.FFMPEG_PATH = "ffmpeg"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            service = TranscriptionService()
            assert service._is_ffmpeg_available() is True

    def test_is_ffmpeg_available_returns_false_when_not_found(self, settings):
        """_is_ffmpeg_available returns False when FFmpeg not found."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = ""
        settings.FFMPEG_PATH = "ffmpeg"

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            service = TranscriptionService()
            assert service._is_ffmpeg_available() is False

    def test_extract_audio_returns_none_when_ffmpeg_unavailable(self, settings):
        """extract_audio returns None when FFmpeg is not available."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = ""

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            service = TranscriptionService()
            result = service.extract_audio(b"fake video data")

        assert result is None

    def test_extract_audio_calls_ffmpeg_correctly(self, settings):
        """extract_audio calls FFmpeg with correct arguments."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = ""
        settings.FFMPEG_PATH = "ffmpeg"

        captured_args = []

        def mock_run(args, **kwargs):
            captured_args.append(args)
            result = MagicMock()
            result.returncode = 0
            return result

        with (
            patch("subprocess.run", side_effect=mock_run),
            patch("pathlib.Path.read_bytes", return_value=b"fake mp3 data"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            mock_stat.return_value.st_size = 1000
            service = TranscriptionService()
            result = service.extract_audio(b"fake video data")

        assert result == b"fake mp3 data"
        # Find the ffmpeg call
        ffmpeg_call = [c for c in captured_args if "-vn" in c]
        assert len(ffmpeg_call) == 1
        assert "-acodec" in ffmpeg_call[0]
        assert "libmp3lame" in ffmpeg_call[0]

    def test_transcribe_returns_none_without_client(self, settings):
        """transcribe returns None when no API key configured."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = ""

        service = TranscriptionService()
        result = service.transcribe(b"fake audio data")

        assert result is None

    def test_transcribe_returns_none_with_empty_data(self, settings):
        """transcribe returns None when audio data is empty."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("groq.Groq"):
            service = TranscriptionService()
            result = service.transcribe(b"")

        assert result is None

    def test_transcribe_calls_groq_api(self, settings):
        """transcribe calls Groq Whisper API correctly."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret
        settings.GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Hello, this is a test."

        with patch("groq.Groq", return_value=mock_client):
            service = TranscriptionService()
            result = service.transcribe(b"fake audio data", language="en")

        assert result == "Hello, this is a test."
        mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == "whisper-large-v3-turbo"
        assert call_kwargs["language"] == "en"
        assert call_kwargs["response_format"] == "text"

    def test_transcribe_handles_api_error(self, settings):
        """transcribe returns None on API error."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")

        with patch("groq.Groq", return_value=mock_client):
            service = TranscriptionService()
            result = service.transcribe(b"fake audio data")

        assert result is None

    def test_transcribe_video_extracts_and_transcribes(self, settings):
        """transcribe_video extracts audio and transcribes it."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret
        settings.FFMPEG_PATH = "ffmpeg"

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Video transcription"

        def mock_run(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            return result

        with (
            patch("groq.Groq", return_value=mock_client),
            patch("subprocess.run", side_effect=mock_run),
            patch("pathlib.Path.read_bytes", return_value=b"fake mp3"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            mock_stat.return_value.st_size = 1000
            service = TranscriptionService()
            result = service.transcribe_video(b"fake video data")

        assert result == "Video transcription"

    def test_transcribe_video_returns_none_on_extraction_failure(self, settings):
        """transcribe_video returns None when audio extraction fails."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        with (
            patch("groq.Groq"),
            patch("subprocess.run", side_effect=FileNotFoundError()),
        ):
            service = TranscriptionService()
            result = service.transcribe_video(b"fake video data")

        assert result is None

    def test_transcribe_media_routes_video(self, settings):
        """transcribe_media routes video to transcribe_video."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("groq.Groq"):
            service = TranscriptionService()
            with patch.object(
                service, "transcribe_video", return_value="video text"
            ) as mock_video:
                result = service.transcribe_media(b"data", "video")

        mock_video.assert_called_once_with(b"data", language=None)
        assert result == "video text"

    def test_transcribe_media_routes_audio(self, settings):
        """transcribe_media routes audio to transcribe."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("groq.Groq"):
            service = TranscriptionService()
            with patch.object(
                service, "transcribe", return_value="audio text"
            ) as mock_audio:
                result = service.transcribe_media(b"data", "audio")

        mock_audio.assert_called_once_with(b"data", language=None)
        assert result == "audio text"

    def test_transcribe_media_returns_none_for_image(self, settings):
        """transcribe_media returns None for unsupported media types."""
        from services.transcription import TranscriptionService

        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        with patch("groq.Groq"):
            service = TranscriptionService()
            result = service.transcribe_media(b"data", "image")

        assert result is None


# ============================================================================
# Event Processing Service with Transcription Tests
# ============================================================================


class TestEventProcessingServiceWithTranscription:
    """Tests for EventProcessingService transcription integration."""

    def test_process_event_transcribes_video(
        self, db, warsaw_location: Point, settings
    ):
        """process_event transcribes video events."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""
        settings.GROQ_API_KEY = "test-key"  # pragma: allowlist secret

        event = Event.objects.create(
            location=warsaw_location,
            description="Video event",
            media_type="video",
        )

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/video.mp4"
        mock_storage.upload_thumbnail.return_value = "http://storage/thumb.jpg"

        mock_keyframe = MagicMock()
        mock_keyframe.extract_keyframe.return_value = b"fake thumbnail"

        mock_transcription = MagicMock()
        mock_transcription.transcribe_media.return_value = "I see a fire here!"

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "emergency",
            "subcategory": "fire",
            "severity": 4,
            "confidence": 0.95,
            "reasoning": "Fire detected from transcription",
        }

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch("services.processing.KeyframeService", return_value=mock_keyframe),
            patch(
                "services.processing.TranscriptionService",
                return_value=mock_transcription,
            ),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            result = service.process_event(
                event, media_data=b"fake video data", media_content_type="video/mp4"
            )

        assert "transcribe" in result["steps_completed"]
        assert result["transcription"] == "I see a fire here!"
        mock_transcription.transcribe_media.assert_called_once_with(
            b"fake video data", media_type="video"
        )
        event.refresh_from_db()
        assert event.transcription == "I see a fire here!"

    def test_process_event_skips_transcription_for_image(
        self, db, warsaw_location: Point, settings
    ):
        """process_event skips transcription for image events."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Image event",
            media_type="image",
        )

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/image.jpg"

        mock_transcription = MagicMock()

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": "Test",
        }

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch("services.processing.KeyframeService"),
            patch(
                "services.processing.TranscriptionService",
                return_value=mock_transcription,
            ),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            result = service.process_event(
                event, media_data=b"fake image data", media_content_type="image/png"
            )

        assert "transcribe" not in result["steps_completed"]
        mock_transcription.transcribe_media.assert_not_called()

    def test_process_event_uses_transcription_for_classification(
        self, db, warsaw_location: Point, settings
    ):
        """process_event combines description and transcription for classification."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Something happened",
            media_type="video",
        )

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/video.mp4"
        mock_storage.upload_thumbnail.return_value = "http://storage/thumb.jpg"

        mock_keyframe = MagicMock()
        mock_keyframe.extract_keyframe.return_value = b"fake thumbnail"

        mock_transcription = MagicMock()
        mock_transcription.transcribe_media.return_value = "There is a car accident!"

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "traffic",
            "subcategory": "accident",
            "severity": 3,
            "confidence": 0.9,
            "reasoning": "Accident detected",
        }

        captured_classify_text = []

        def capture_classify(text):
            captured_classify_text.append(text)
            return mock_classification.classify.return_value

        mock_classification.classify.side_effect = capture_classify

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch("services.processing.KeyframeService", return_value=mock_keyframe),
            patch(
                "services.processing.TranscriptionService",
                return_value=mock_transcription,
            ),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            service.process_event(
                event, media_data=b"fake video data", media_content_type="video/mp4"
            )

        # Verify classification received combined text
        assert len(captured_classify_text) == 1
        classify_text = captured_classify_text[0]
        assert "Something happened" in classify_text
        assert "There is a car accident!" in classify_text

    def test_process_event_continues_on_transcription_failure(
        self, db, warsaw_location: Point, settings
    ):
        """process_event continues if transcription fails."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Video event",
            media_type="video",
        )

        mock_storage = MagicMock()
        mock_storage.upload_media.return_value = "http://storage/video.mp4"
        mock_storage.upload_thumbnail.return_value = "http://storage/thumb.jpg"

        mock_keyframe = MagicMock()
        mock_keyframe.extract_keyframe.return_value = b"fake thumbnail"

        mock_transcription = MagicMock()
        mock_transcription.transcribe_media.return_value = None  # Failed

        mock_classification = MagicMock()
        mock_classification.classify.return_value = {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": "Test",
        }

        with (
            patch("services.processing.StorageService", return_value=mock_storage),
            patch("services.processing.KeyframeService", return_value=mock_keyframe),
            patch(
                "services.processing.TranscriptionService",
                return_value=mock_transcription,
            ),
            patch(
                "services.processing.ClassificationService",
                return_value=mock_classification,
            ),
            patch("services.processing.ClusteringService"),
            patch("services.processing.broadcast_new_event"),
        ):
            service = EventProcessingService()
            result = service.process_event(
                event, media_data=b"fake video data", media_content_type="video/mp4"
            )

        # Transcription was attempted but failed
        assert "transcribe" not in result["steps_completed"]
        # But other processing continued
        assert "classify" in result["steps_completed"]
        assert "broadcast" in result["steps_completed"]


# ============================================================================
# Build Classification Text Tests
# ============================================================================


class TestBuildClassificationText:
    """Tests for the _build_classification_text helper."""

    def test_build_classification_text_with_both(
        self, db, warsaw_location: Point, settings
    ):
        """_build_classification_text combines description and transcription."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Fire spotted",
            transcription="I can see flames and smoke",
        )

        with (
            patch("services.processing.StorageService"),
            patch("services.processing.KeyframeService"),
            patch("services.processing.TranscriptionService"),
            patch("services.processing.ClassificationService"),
            patch("services.processing.ClusteringService"),
        ):
            service = EventProcessingService()
            text = service._build_classification_text(event)

        assert "User description: Fire spotted" in text
        assert "Audio transcription: I can see flames and smoke" in text

    def test_build_classification_text_description_only(
        self, db, warsaw_location: Point, settings
    ):
        """_build_classification_text works with description only."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="Fire spotted",
            transcription="",
        )

        with (
            patch("services.processing.StorageService"),
            patch("services.processing.KeyframeService"),
            patch("services.processing.TranscriptionService"),
            patch("services.processing.ClassificationService"),
            patch("services.processing.ClusteringService"),
        ):
            service = EventProcessingService()
            text = service._build_classification_text(event)

        assert "User description: Fire spotted" in text
        assert "transcription" not in text.lower()

    def test_build_classification_text_transcription_only(
        self, db, warsaw_location: Point, settings
    ):
        """_build_classification_text works with transcription only."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="",
            transcription="I can see flames",
        )

        with (
            patch("services.processing.StorageService"),
            patch("services.processing.KeyframeService"),
            patch("services.processing.TranscriptionService"),
            patch("services.processing.ClassificationService"),
            patch("services.processing.ClusteringService"),
        ):
            service = EventProcessingService()
            text = service._build_classification_text(event)

        assert "Audio transcription: I can see flames" in text
        assert "description" not in text.lower()

    def test_build_classification_text_empty(
        self, db, warsaw_location: Point, settings
    ):
        """_build_classification_text returns empty string when no content."""
        from services.processing import EventProcessingService

        settings.MINIO_ENDPOINT = "localhost:9000"
        settings.MINIO_ACCESS_KEY = "test"
        settings.MINIO_SECRET_KEY = "test"  # pragma: allowlist secret
        settings.MINIO_BUCKET = "events"
        settings.MINIO_USE_SSL = False
        settings.OPENROUTER_API_KEY = ""

        event = Event.objects.create(
            location=warsaw_location,
            description="",
            transcription="",
        )

        with (
            patch("services.processing.StorageService"),
            patch("services.processing.KeyframeService"),
            patch("services.processing.TranscriptionService"),
            patch("services.processing.ClassificationService"),
            patch("services.processing.ClusteringService"),
        ):
            service = EventProcessingService()
            text = service._build_classification_text(event)

        assert text == ""


# ============================================================================
# Gamification Service Tests
# ============================================================================


class TestGamificationServiceBadges:
    """Tests for badge definitions and awards."""

    def test_gamification_service_init(self):
        """GamificationService initializes with badge definitions."""
        from services.gamification import BADGE_DEFINITIONS, GamificationService

        service = GamificationService()

        assert service.badges == BADGE_DEFINITIONS
        assert len(service.badges) > 0

    def test_get_badge_definition(self):
        """get_badge_definition returns badge by ID."""
        from services.gamification import GamificationService

        service = GamificationService()
        badge = service.get_badge_definition("first_report")

        assert badge is not None
        assert badge.id == "first_report"
        assert badge.name == "First Reporter"
        assert badge.threshold == 1

    def test_get_badge_definition_unknown(self):
        """get_badge_definition returns None for unknown badge."""
        from services.gamification import GamificationService

        service = GamificationService()
        badge = service.get_badge_definition("nonexistent_badge")

        assert badge is None

    def test_get_all_badges(self):
        """get_all_badges returns all badge definitions as dicts."""
        from services.gamification import GamificationService

        service = GamificationService()
        badges = service.get_all_badges()

        assert len(badges) >= 13  # At least 13 defined badges
        assert all("id" in b for b in badges)
        assert all("name" in b for b in badges)
        assert all("category" in b for b in badges)

    def test_check_and_award_badges_first_report(self, db):
        """check_and_award_badges awards first_report badge."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="testuser1", password="testpass")
        profile = UserProfile.objects.create(user=user, reports_submitted=1)

        service = GamificationService()
        awarded = service.check_and_award_badges(profile)

        assert "first_report" in awarded
        profile.refresh_from_db()
        assert "first_report" in profile.badges

    def test_check_and_award_badges_multiple(self, db):
        """check_and_award_badges awards multiple badges at once."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="testuser2", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_submitted=10,
            reports_verified=1,
            reputation_score=100,
        )

        service = GamificationService()
        awarded = service.check_and_award_badges(profile)

        assert "first_report" in awarded
        assert "reporter_10" in awarded
        assert "first_verified" in awarded
        assert "reputation_100" in awarded

    def test_check_and_award_badges_no_duplicates(self, db):
        """check_and_award_badges doesn't award existing badges."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="testuser3", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_submitted=10,
            badges=["first_report", "reporter_10"],
        )

        service = GamificationService()
        awarded = service.check_and_award_badges(profile)

        assert "first_report" not in awarded
        assert "reporter_10" not in awarded
        assert len(awarded) == 0

    def test_award_special_badge(self, db):
        """award_special_badge awards special badges."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="testuser4", password="testpass")
        profile = UserProfile.objects.create(user=user)

        service = GamificationService()
        result = service.award_special_badge(profile, "early_adopter")

        assert result is True
        profile.refresh_from_db()
        assert "early_adopter" in profile.badges

    def test_award_special_badge_already_has(self, db):
        """award_special_badge returns False if already has badge."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="testuser5", password="testpass")
        profile = UserProfile.objects.create(user=user, badges=["early_adopter"])

        service = GamificationService()
        result = service.award_special_badge(profile, "early_adopter")

        assert result is False

    def test_award_special_badge_unknown(self, db):
        """award_special_badge returns False for unknown badge."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="testuser6", password="testpass")
        profile = UserProfile.objects.create(user=user)

        service = GamificationService()
        result = service.award_special_badge(profile, "nonexistent_badge")

        assert result is False


class TestGamificationServiceReputation:
    """Tests for reputation point management."""

    def test_add_reputation_positive(self, db):
        """add_reputation adds positive points."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="repuser1", password="testpass")
        profile = UserProfile.objects.create(user=user, reputation_score=50)

        service = GamificationService()
        new_score = service.add_reputation(profile, 10, "test_addition")

        assert new_score == 60
        profile.refresh_from_db()
        assert profile.reputation_score == 60

    def test_add_reputation_negative(self, db):
        """add_reputation subtracts negative points."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="repuser2", password="testpass")
        profile = UserProfile.objects.create(user=user, reputation_score=50)

        service = GamificationService()
        new_score = service.add_reputation(profile, -5, "penalty")

        assert new_score == 45
        profile.refresh_from_db()
        assert profile.reputation_score == 45

    def test_add_reputation_triggers_badge_check(self, db):
        """add_reputation checks for reputation badges."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="repuser3", password="testpass")
        profile = UserProfile.objects.create(user=user, reputation_score=95)

        service = GamificationService()
        service.add_reputation(profile, 10, "reaching_100")

        profile.refresh_from_db()
        assert "reputation_100" in profile.badges


class TestGamificationServiceEvents:
    """Tests for gamification event handlers."""

    def test_on_report_submitted(self, db):
        """on_report_submitted checks for report badges."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="eventuser1", password="testpass")
        profile = UserProfile.objects.create(user=user, reports_submitted=1)

        service = GamificationService()
        awarded = service.on_report_submitted(profile)

        assert "first_report" in awarded

    def test_on_report_verified(self, db):
        """on_report_verified adds points and checks badges."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import REPUTATION_POINTS, GamificationService

        user = User.objects.create_user(username="eventuser2", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_verified=1,
            reputation_score=0,
        )

        service = GamificationService()
        service.on_report_verified(profile, is_critical=False)

        profile.refresh_from_db()
        assert profile.reputation_score == REPUTATION_POINTS["report_verified"]
        # Badge is awarded via add_reputation -> check_and_award_badges chain
        assert "first_verified" in profile.badges

    def test_on_report_verified_critical(self, db):
        """on_report_verified adds bonus points for critical."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import REPUTATION_POINTS, GamificationService

        user = User.objects.create_user(username="eventuser3", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_verified=1,
            reputation_score=0,
        )

        service = GamificationService()
        service.on_report_verified(profile, is_critical=True)

        profile.refresh_from_db()
        expected = (
            REPUTATION_POINTS["report_verified"]
            + REPUTATION_POINTS["critical_verified"]
        )
        assert profile.reputation_score == expected
        assert "emergency_responder" in profile.badges

    def test_on_report_rejected(self, db):
        """on_report_rejected deducts reputation."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import REPUTATION_POINTS, GamificationService

        user = User.objects.create_user(username="eventuser4", password="testpass")
        profile = UserProfile.objects.create(user=user, reputation_score=50)

        service = GamificationService()
        service.on_report_rejected(profile)

        profile.refresh_from_db()
        assert profile.reputation_score == 50 + REPUTATION_POINTS["report_false_alarm"]


class TestGamificationServiceLeaderboard:
    """Tests for leaderboard functionality."""

    def test_get_leaderboard(self, db):
        """get_leaderboard returns top users."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        # Create multiple users with different scores
        for i, score in enumerate([100, 50, 200, 25]):
            user = User.objects.create_user(username=f"lbuser{i}", password="testpass")
            UserProfile.objects.create(user=user, reputation_score=score)

        service = GamificationService()
        leaderboard = service.get_leaderboard(limit=10)

        assert len(leaderboard) == 4
        # Should be ordered by score descending
        assert leaderboard[0]["reputation_score"] == 200
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[1]["reputation_score"] == 100
        assert leaderboard[1]["rank"] == 2

    def test_get_leaderboard_respects_limit(self, db):
        """get_leaderboard respects limit parameter."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        for i in range(5):
            user = User.objects.create_user(username=f"limuser{i}", password="testpass")
            UserProfile.objects.create(user=user, reputation_score=i * 10)

        service = GamificationService()
        leaderboard = service.get_leaderboard(limit=3)

        assert len(leaderboard) == 3

    def test_get_user_rank(self, db):
        """get_user_rank returns correct rank."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        users = []
        for i, score in enumerate([100, 200, 50]):
            user = User.objects.create_user(
                username=f"rankuser{i}",
                password="testpass",  # pragma: allowlist secret
            )
            profile = UserProfile.objects.create(user=user, reputation_score=score)
            users.append(profile)

        service = GamificationService()

        # User with score 200 should be rank 1
        assert service.get_user_rank(users[1]) == 1
        # User with score 100 should be rank 2
        assert service.get_user_rank(users[0]) == 2
        # User with score 50 should be rank 3
        assert service.get_user_rank(users[2]) == 3


class TestGamificationServiceStats:
    """Tests for user statistics."""

    def test_get_user_stats(self, db):
        """get_user_stats returns comprehensive stats."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="statsuser1", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_submitted=20,
            reports_verified=15,
            reputation_score=150,
            badges=["first_report", "reporter_10"],
        )

        service = GamificationService()
        stats = service.get_user_stats(profile)

        assert stats["reports_submitted"] == 20
        assert stats["reports_verified"] == 15
        assert stats["verification_rate"] == 75.0  # 15/20 * 100
        assert stats["reputation_score"] == 150
        assert stats["rank"] == 1
        assert stats["badge_count"] == 2
        assert len(stats["badges"]) == 2

    def test_get_user_stats_verification_rate_zero_reports(self, db):
        """get_user_stats handles zero reports for verification rate."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="statsuser2", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_submitted=0,
            reports_verified=0,
        )

        service = GamificationService()
        stats = service.get_user_stats(profile)

        assert stats["verification_rate"] == 0.0

    def test_get_user_stats_next_badges(self, db):
        """get_user_stats includes next badge progress."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="statsuser3", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_submitted=5,
            reports_verified=0,
        )

        service = GamificationService()
        stats = service.get_user_stats(profile)

        # Should show progress toward reporter_10 (threshold 10)
        assert stats["next_report_badge"] is not None
        assert stats["next_report_badge"]["threshold"] == 10
        assert stats["next_report_badge"]["progress"] == 5
        assert stats["next_report_badge"]["remaining"] == 5

        # Should show progress toward first_verified (threshold 1)
        assert stats["next_verified_badge"] is not None
        assert stats["next_verified_badge"]["threshold"] == 1
        assert stats["next_verified_badge"]["remaining"] == 1

    def test_get_user_stats_all_badges_earned(self, db):
        """get_user_stats returns None when all badges earned."""
        from django.contrib.auth.models import User

        from core.models import UserProfile
        from services.gamification import GamificationService

        user = User.objects.create_user(username="statsuser4", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            reports_submitted=100,
            reports_verified=50,
        )

        service = GamificationService()
        stats = service.get_user_stats(profile)

        # All report badges earned
        assert stats["next_report_badge"] is None
        # All verified badges earned
        assert stats["next_verified_badge"] is None
