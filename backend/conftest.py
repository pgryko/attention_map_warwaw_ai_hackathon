"""
Pytest configuration and fixtures for Attention Map backend.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from ninja.testing import TestClient

from api.routes import router
from core.models import (
    CategoryChoices,
    Event,
    EventCluster,
    SeverityChoices,
    StatusChoices,
    UserProfile,
)


# ============================================================================
# Database fixtures
# ============================================================================


@pytest.fixture
def api_client() -> TestClient:
    """Django Ninja test client for API testing."""
    return TestClient(router)


@pytest.fixture
def django_client() -> Client:
    """Standard Django test client."""
    return Client()


# ============================================================================
# User fixtures
# ============================================================================


@pytest.fixture
def user(db) -> User:
    """Create a regular user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",  # noqa: S106  # pragma: allowlist secret
    )


@pytest.fixture
def operator_user(db) -> User:
    """Create an operator user with staff permissions."""
    return User.objects.create_user(
        username="operator",
        email="operator@city.gov",
        password="operatorpass",  # noqa: S106  # pragma: allowlist secret
        is_staff=True,
    )


@pytest.fixture
def user_profile(db, user: User) -> UserProfile:
    """Create a user profile with some badges."""
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "badges": ["first_report"],
            "reports_submitted": 1,
        },
    )
    return profile


# ============================================================================
# Location fixtures
# ============================================================================


@pytest.fixture
def warsaw_location() -> Point:
    """Warsaw city center location."""
    return Point(21.0122, 52.2297, srid=4326)


@pytest.fixture
def warsaw_nearby_location() -> Point:
    """Location 50m from Warsaw city center (within clustering range)."""
    return Point(21.0127, 52.2300, srid=4326)


@pytest.fixture
def london_location() -> Point:
    """London location (far from Warsaw)."""
    return Point(-0.1276, 51.5074, srid=4326)


# ============================================================================
# Event fixtures
# ============================================================================


@pytest.fixture
def event_cluster(db, warsaw_location: Point) -> EventCluster:
    """Create an event cluster."""
    return EventCluster.objects.create(
        centroid=warsaw_location,
        event_count=1,
        computed_severity=SeverityChoices.MEDIUM,
    )


@pytest.fixture
def event(db, warsaw_location: Point) -> Event:
    """Create a basic event without classification."""
    return Event.objects.create(
        location=warsaw_location,
        description="Test incident report",
        status=StatusChoices.NEW,
    )


@pytest.fixture
def classified_event(db, warsaw_location: Point) -> Event:
    """Create a fully classified event."""
    return Event.objects.create(
        location=warsaw_location,
        description="Fire at building on Main Street",
        category=CategoryChoices.EMERGENCY,
        subcategory="fire",
        severity=SeverityChoices.CRITICAL,
        ai_confidence=0.95,
        ai_reasoning="Detected fire-related keywords and urgency indicators",
        status=StatusChoices.VERIFIED,
    )


@pytest.fixture
def clustered_event(db, warsaw_location: Point, event_cluster: EventCluster) -> Event:
    """Create an event that belongs to a cluster."""
    return Event.objects.create(
        location=warsaw_location,
        description="Another incident in the area",
        cluster=event_cluster,
        category=CategoryChoices.EMERGENCY,
        severity=SeverityChoices.HIGH,
        status=StatusChoices.NEW,
    )


@pytest.fixture
def multiple_events(
    db, warsaw_location: Point, warsaw_nearby_location: Point
) -> list[Event]:
    """Create multiple events for testing filtering and clustering."""
    events = []
    categories = [
        (CategoryChoices.EMERGENCY, SeverityChoices.CRITICAL),
        (CategoryChoices.TRAFFIC, SeverityChoices.MEDIUM),
        (CategoryChoices.INFRASTRUCTURE, SeverityChoices.LOW),
    ]

    for i, (category, severity) in enumerate(categories):
        location = warsaw_location if i % 2 == 0 else warsaw_nearby_location
        events.append(
            Event.objects.create(
                location=location,
                description=f"Test event {i + 1}",
                category=category,
                severity=severity,
                status=StatusChoices.NEW,
            )
        )
    return events


# ============================================================================
# Media fixtures
# ============================================================================


@pytest.fixture
def sample_image() -> SimpleUploadedFile:
    """Create a sample image file for upload testing."""
    # 1x1 red PNG image
    image_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03"
        b"\x00\x01\x00\x05\xfe\xd4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return SimpleUploadedFile(
        name="test_image.png",
        content=image_data,
        content_type="image/png",
    )


@pytest.fixture
def sample_video() -> SimpleUploadedFile:
    """Create a sample video file for upload testing."""
    # Minimal MP4 header (not a real video, just for testing)
    video_data = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41"
    return SimpleUploadedFile(
        name="test_video.mp4",
        content=video_data,
        content_type="video/mp4",
    )


@pytest.fixture
def invalid_file() -> SimpleUploadedFile:
    """Create an invalid file type for rejection testing."""
    return SimpleUploadedFile(
        name="test.txt",
        content=b"This is not a valid media file",
        content_type="text/plain",
    )


# ============================================================================
# Mock fixtures for external services
# ============================================================================


@pytest.fixture
def mock_minio():
    """Mock MinIO client for storage tests."""
    client = MagicMock()
    client.bucket_exists.return_value = True
    client.put_object.return_value = None
    return client


@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter API for classification tests."""
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = """{
        "category": "emergency",
        "subcategory": "fire",
        "severity": 4,
        "confidence": 0.95,
        "reasoning": "Fire detected in description"
    }"""
    client.chat.completions.create.return_value = response
    return client


@pytest.fixture
def mock_redis():
    """Mock Redis client for pub/sub tests."""
    client = MagicMock()
    return client


# ============================================================================
# Celery fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def celery_task_always_eager(settings):
    """Configure Celery to run tasks synchronously during tests."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


# ============================================================================
# Request fixtures for API testing
# ============================================================================


@pytest.fixture
def event_upload_data() -> dict[str, Any]:
    """Standard event upload request data."""
    return {
        "latitude": 52.2297,
        "longitude": 21.0122,
        "description": "Fire at the corner of Main St",
    }


@pytest.fixture
def status_update_data() -> dict[str, str]:
    """Status update request data."""
    return {
        "status": "verified",
    }
