"""
Core models for Attention Map.
"""

import uuid

from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.db import models


class CategoryChoices(models.TextChoices):
    """Event category choices."""

    EMERGENCY = "emergency", "Emergency"
    SECURITY = "security", "Security"
    TRAFFIC = "traffic", "Traffic"
    PROTEST = "protest", "Protest/Gathering"
    INFRASTRUCTURE = "infrastructure", "Infrastructure"
    ENVIRONMENTAL = "environmental", "Environmental"
    INFORMATIONAL = "informational", "Informational"


class SeverityChoices(models.IntegerChoices):
    """Event severity levels."""

    LOW = 1, "Low"
    MEDIUM = 2, "Medium"
    HIGH = 3, "High"
    CRITICAL = 4, "Critical"


class StatusChoices(models.TextChoices):
    """Event status choices."""

    NEW = "new", "New"
    REVIEWING = "reviewing", "Reviewing"
    VERIFIED = "verified", "Verified"
    RESOLVED = "resolved", "Resolved"
    FALSE_ALARM = "false_alarm", "False Alarm"


class MediaTypeChoices(models.TextChoices):
    """Media type choices."""

    IMAGE = "image", "Image"
    VIDEO = "video", "Video"


class EventCluster(models.Model):
    """
    Groups nearby events for priority escalation.
    Multiple events in the same area (100m) within 30 minutes = higher priority.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    centroid = gis_models.PointField(srid=4326)
    radius_meters = models.IntegerField(default=100)
    event_count = models.IntegerField(default=1)
    first_event_at = models.DateTimeField(auto_now_add=True)
    last_event_at = models.DateTimeField(auto_now=True)
    computed_severity = models.IntegerField(
        choices=SeverityChoices.choices,
        default=SeverityChoices.LOW,
        help_text="Boosted severity based on event count",
    )

    class Meta:
        db_table = "event_cluster"
        ordering = ["-computed_severity", "-last_event_at"]
        indexes = [
            gis_models.Index(fields=["centroid"], name="idx_cluster_centroid"),
            models.Index(fields=["-computed_severity"], name="idx_cluster_severity"),
        ]

    def __str__(self) -> str:
        return f"Cluster {self.id} ({self.event_count} events)"


class Event(models.Model):
    """
    Core event model representing a citizen-reported incident.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Location
    location = gis_models.PointField(srid=4326)
    address = models.CharField(max_length=500, blank=True)

    # Content
    description = models.TextField(blank=True)
    media_url = models.URLField(max_length=500, blank=True)
    media_type = models.CharField(
        max_length=10,
        choices=MediaTypeChoices.choices,
        blank=True,
    )
    thumbnail_url = models.URLField(max_length=500, blank=True)

    # Audio transcription (from video/audio files)
    transcription = models.TextField(
        blank=True,
        help_text="AI-generated transcription of audio content",
    )

    # AI Classification
    category = models.CharField(
        max_length=50,
        choices=CategoryChoices.choices,
        blank=True,
    )
    subcategory = models.CharField(max_length=50, blank=True)
    severity = models.IntegerField(
        choices=SeverityChoices.choices,
        default=SeverityChoices.LOW,
    )
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_reasoning = models.TextField(blank=True)

    # Clustering
    cluster = models.ForeignKey(
        EventCluster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # Triage
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_events",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "event"
        ordering = ["-created_at"]
        indexes = [
            gis_models.Index(fields=["location"], name="idx_event_location"),
            models.Index(fields=["-created_at"], name="idx_event_created_at"),
            models.Index(
                fields=["status", "-severity"], name="idx_event_status_severity"
            ),
            models.Index(fields=["category"], name="idx_event_category"),
        ]

    def __str__(self) -> str:
        return f"Event {self.id} - {self.category or 'Unclassified'}"


class UserProfile(models.Model):
    """
    Extended user profile for gamification.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    reports_submitted = models.IntegerField(default=0)
    reports_verified = models.IntegerField(default=0)
    badges = models.JSONField(default=list, blank=True)
    reputation_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_profile"

    def __str__(self) -> str:
        return f"Profile for {self.user.username}"
