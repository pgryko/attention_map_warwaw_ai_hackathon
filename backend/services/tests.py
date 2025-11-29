"""
Tests for business logic services.

Following TDD approach - write tests first, then implement.
"""

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
