"""
Tests for core models: Event, EventCluster, UserProfile.

Following TDD approach - write tests first, then verify implementation.
"""

from uuid import UUID

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.db import IntegrityError
from django.utils import timezone

from core.models import (
    CategoryChoices,
    Event,
    EventCluster,
    MediaTypeChoices,
    SeverityChoices,
    StatusChoices,
    UserProfile,
)


# ============================================================================
# Event Model Tests
# ============================================================================


class TestEventModel:
    """Tests for the Event model."""

    def test_create_event_with_minimum_fields(self, db, warsaw_location: Point):
        """Event can be created with just location."""
        event = Event.objects.create(location=warsaw_location)

        assert event.id is not None
        assert isinstance(event.id, UUID)
        assert event.location == warsaw_location
        assert event.status == StatusChoices.NEW
        assert event.severity == SeverityChoices.LOW
        assert event.created_at is not None

    def test_event_uuid_is_auto_generated(self, db, warsaw_location: Point):
        """Event UUID is automatically generated."""
        event1 = Event.objects.create(location=warsaw_location)
        event2 = Event.objects.create(location=warsaw_location)

        assert event1.id != event2.id
        assert isinstance(event1.id, UUID)
        assert isinstance(event2.id, UUID)

    def test_event_with_all_fields(self, db, user: User, warsaw_location: Point):
        """Event can be created with all fields populated."""
        event = Event.objects.create(
            reporter=user,
            location=warsaw_location,
            address="Main Street 123, Warsaw",
            description="Fire at building entrance",
            media_url="https://minio.local/bucket/events/123/media",
            media_type=MediaTypeChoices.VIDEO,
            thumbnail_url="https://minio.local/bucket/events/123/thumb.jpg",
            category=CategoryChoices.EMERGENCY,
            subcategory="fire",
            severity=SeverityChoices.CRITICAL,
            ai_confidence=0.95,
            ai_reasoning="Fire-related keywords detected",
            status=StatusChoices.VERIFIED,
        )

        assert event.reporter == user
        assert event.address == "Main Street 123, Warsaw"
        assert event.media_type == MediaTypeChoices.VIDEO
        assert event.category == CategoryChoices.EMERGENCY
        assert event.severity == SeverityChoices.CRITICAL
        assert event.ai_confidence == 0.95
        assert event.status == StatusChoices.VERIFIED

    def test_event_reporter_can_be_null(self, db, warsaw_location: Point):
        """Anonymous events have null reporter."""
        event = Event.objects.create(
            location=warsaw_location,
            description="Anonymous report",
        )

        assert event.reporter is None

    def test_event_location_is_required(self, db):
        """Event cannot be created without location."""
        with pytest.raises(IntegrityError):
            Event.objects.create(description="No location")

    def test_event_ordering_by_created_at_desc(self, db, warsaw_location: Point):
        """Events are ordered by created_at descending (newest first)."""
        event1 = Event.objects.create(location=warsaw_location, description="First")
        event2 = Event.objects.create(location=warsaw_location, description="Second")
        event3 = Event.objects.create(location=warsaw_location, description="Third")

        events = list(Event.objects.all())
        assert events[0] == event3
        assert events[1] == event2
        assert events[2] == event1

    def test_event_str_representation(self, classified_event: Event):
        """Event string representation includes ID and category."""
        expected = f"Event {classified_event.id} - emergency"
        assert str(classified_event) == expected

    def test_event_str_unclassified(self, event: Event):
        """Unclassified event shows 'Unclassified' in string."""
        assert "Unclassified" in str(event)

    def test_event_cluster_relationship(
        self, db, warsaw_location: Point, event_cluster: EventCluster
    ):
        """Event can be assigned to a cluster."""
        event = Event.objects.create(
            location=warsaw_location,
            cluster=event_cluster,
        )

        assert event.cluster == event_cluster
        assert event in event_cluster.events.all()

    def test_event_status_transitions(self, event: Event):
        """Event status can be updated through valid transitions."""
        assert event.status == StatusChoices.NEW

        event.status = StatusChoices.REVIEWING
        event.save()
        event.refresh_from_db()
        assert event.status == StatusChoices.REVIEWING

        event.status = StatusChoices.VERIFIED
        event.save()
        event.refresh_from_db()
        assert event.status == StatusChoices.VERIFIED

        event.status = StatusChoices.RESOLVED
        event.save()
        event.refresh_from_db()
        assert event.status == StatusChoices.RESOLVED

    def test_event_reviewed_fields(self, event: Event, operator_user: User):
        """Reviewed fields are set when operator reviews event."""
        review_time = timezone.now()

        event.reviewed_by = operator_user
        event.reviewed_at = review_time
        event.status = StatusChoices.VERIFIED
        event.save()
        event.refresh_from_db()

        assert event.reviewed_by == operator_user
        assert event.reviewed_at is not None

    def test_reporter_deletion_sets_null(self, db, user: User, warsaw_location: Point):
        """Deleting reporter sets event.reporter to null (SET_NULL)."""
        event = Event.objects.create(
            reporter=user,
            location=warsaw_location,
        )
        user_id = user.id
        user.delete()

        event.refresh_from_db()
        assert event.reporter is None
        assert not User.objects.filter(id=user_id).exists()


# ============================================================================
# EventCluster Model Tests
# ============================================================================


class TestEventClusterModel:
    """Tests for the EventCluster model."""

    def test_create_cluster_with_location(self, db, warsaw_location: Point):
        """Cluster can be created with centroid location."""
        cluster = EventCluster.objects.create(
            centroid=warsaw_location,
            event_count=1,
        )

        assert cluster.id is not None
        assert isinstance(cluster.id, UUID)
        assert cluster.centroid == warsaw_location
        assert cluster.event_count == 1

    def test_cluster_default_severity(self, db, warsaw_location: Point):
        """Cluster defaults to LOW severity."""
        cluster = EventCluster.objects.create(centroid=warsaw_location)

        assert cluster.computed_severity == SeverityChoices.LOW

    def test_cluster_event_count_updates(
        self, db, warsaw_location: Point, warsaw_nearby_location: Point
    ):
        """Cluster event_count reflects actual events."""
        cluster = EventCluster.objects.create(
            centroid=warsaw_location,
            event_count=0,
        )

        Event.objects.create(location=warsaw_location, cluster=cluster)
        Event.objects.create(location=warsaw_nearby_location, cluster=cluster)

        assert cluster.events.count() == 2

    def test_cluster_timestamps(self, db, warsaw_location: Point):
        """Cluster has first_event_at and last_event_at timestamps."""
        cluster = EventCluster.objects.create(centroid=warsaw_location)

        assert cluster.first_event_at is not None
        assert cluster.last_event_at is not None

    def test_cluster_severity_escalation(self, db, warsaw_location: Point):
        """Cluster severity can be escalated based on event count."""
        cluster = EventCluster.objects.create(
            centroid=warsaw_location,
            event_count=5,
            computed_severity=SeverityChoices.CRITICAL,
        )

        assert cluster.computed_severity == SeverityChoices.CRITICAL

    def test_cluster_str_representation(self, event_cluster: EventCluster):
        """Cluster string representation is meaningful."""
        cluster_str = str(event_cluster)
        assert "Cluster" in cluster_str or str(event_cluster.id) in cluster_str

    def test_cluster_ordering_by_severity_desc(self, db, warsaw_location: Point):
        """Clusters are ordered by computed_severity descending."""
        cluster_low = EventCluster.objects.create(
            centroid=warsaw_location,
            computed_severity=SeverityChoices.LOW,
        )
        cluster_critical = EventCluster.objects.create(
            centroid=warsaw_location,
            computed_severity=SeverityChoices.CRITICAL,
        )
        cluster_medium = EventCluster.objects.create(
            centroid=warsaw_location,
            computed_severity=SeverityChoices.MEDIUM,
        )

        clusters = list(EventCluster.objects.all())
        assert clusters[0] == cluster_critical
        assert clusters[1] == cluster_medium
        assert clusters[2] == cluster_low


# ============================================================================
# UserProfile Model Tests
# ============================================================================


class TestUserProfileModel:
    """Tests for the UserProfile model."""

    def test_create_user_profile(self, db, user: User):
        """UserProfile can be created for a user."""
        profile = UserProfile.objects.create(user=user)

        assert profile.user == user
        assert profile.reports_submitted == 0
        assert profile.badges == []

    def test_profile_one_to_one_relationship(self, db, user: User):
        """UserProfile has one-to-one relationship with User."""
        UserProfile.objects.create(user=user)

        # Cannot create second profile for same user
        with pytest.raises(IntegrityError):
            UserProfile.objects.create(user=user)

    def test_profile_badges_as_json(self, db, user: User):
        """Badges are stored as JSON array."""
        profile = UserProfile.objects.create(
            user=user,
            badges=["first_report", "night_owl", "consistent_contributor"],
        )

        profile.refresh_from_db()
        assert len(profile.badges) == 3
        assert "first_report" in profile.badges

    def test_profile_reports_submitted_increment(self, db, user: User):
        """Reports submitted count can be incremented."""
        profile = UserProfile.objects.create(user=user, reports_submitted=0)

        profile.reports_submitted += 1
        profile.save()
        profile.refresh_from_db()

        assert profile.reports_submitted == 1

    def test_profile_str_representation(self, user_profile: UserProfile):
        """Profile string representation includes username."""
        assert user_profile.user.username in str(user_profile)

    def test_profile_deleted_with_user(self, db, user: User):
        """Profile is deleted when user is deleted (CASCADE)."""
        profile = UserProfile.objects.create(user=user)
        profile_id = profile.id

        user.delete()

        assert not UserProfile.objects.filter(id=profile_id).exists()


# ============================================================================
# Choice Enum Tests
# ============================================================================


class TestChoiceEnums:
    """Tests for model choice enumerations."""

    def test_category_choices_values(self):
        """CategoryChoices has expected values."""
        assert CategoryChoices.EMERGENCY == "emergency"
        assert CategoryChoices.SECURITY == "security"
        assert CategoryChoices.TRAFFIC == "traffic"
        assert CategoryChoices.PROTEST == "protest"
        assert CategoryChoices.INFRASTRUCTURE == "infrastructure"
        assert CategoryChoices.ENVIRONMENTAL == "environmental"
        assert CategoryChoices.INFORMATIONAL == "informational"

    def test_severity_choices_values(self):
        """SeverityChoices has expected integer values."""
        assert SeverityChoices.LOW == 1
        assert SeverityChoices.MEDIUM == 2
        assert SeverityChoices.HIGH == 3
        assert SeverityChoices.CRITICAL == 4

    def test_status_choices_values(self):
        """StatusChoices has expected values."""
        assert StatusChoices.NEW == "new"
        assert StatusChoices.REVIEWING == "reviewing"
        assert StatusChoices.VERIFIED == "verified"
        assert StatusChoices.RESOLVED == "resolved"
        assert StatusChoices.FALSE_ALARM == "false_alarm"

    def test_media_type_choices_values(self):
        """MediaTypeChoices has expected values."""
        assert MediaTypeChoices.IMAGE == "image"
        assert MediaTypeChoices.VIDEO == "video"


# ============================================================================
# Spatial Query Tests
# ============================================================================


class TestSpatialQueries:
    """Tests for PostGIS spatial queries."""

    def test_filter_events_within_distance(
        self,
        db,
        warsaw_location: Point,
        warsaw_nearby_location: Point,
        london_location: Point,
    ):
        """Events can be filtered by distance from a point."""
        from django.contrib.gis.measure import D

        Event.objects.create(location=warsaw_location, description="Warsaw center")
        Event.objects.create(
            location=warsaw_nearby_location, description="Warsaw nearby"
        )
        Event.objects.create(location=london_location, description="London")

        # Find events within 200m of Warsaw center
        nearby = Event.objects.filter(
            location__distance_lte=(warsaw_location, D(m=200))
        )

        assert nearby.count() == 2  # Warsaw center and nearby
        descriptions = [e.description for e in nearby]
        assert "London" not in descriptions

    def test_events_within_bounding_box(
        self,
        db,
        warsaw_location: Point,
        london_location: Point,
    ):
        """Events can be filtered by bounding box (bbox)."""
        from django.contrib.gis.geos import Polygon

        Event.objects.create(location=warsaw_location, description="Warsaw")
        Event.objects.create(location=london_location, description="London")

        # Bounding box around Warsaw (roughly)
        bbox = Polygon.from_bbox((20.5, 52.0, 21.5, 52.5))

        events_in_bbox = Event.objects.filter(location__within=bbox)

        assert events_in_bbox.count() == 1
        assert events_in_bbox.first().description == "Warsaw"
