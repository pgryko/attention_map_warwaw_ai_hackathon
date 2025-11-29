"""
Clustering service for spatial event grouping.
"""

import logging
from datetime import timedelta
from typing import Optional

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import QuerySet
from django.utils import timezone

from core.models import Event, EventCluster, SeverityChoices

logger = logging.getLogger(__name__)


class ClusteringService:
    """Service for spatially clustering nearby events."""

    # Default configuration
    DEFAULT_RADIUS_METERS = 100
    DEFAULT_TIME_WINDOW_MINUTES = 30
    ESCALATION_THRESHOLD_HIGH = 3
    ESCALATION_THRESHOLD_CRITICAL = 5

    def __init__(
        self,
        radius_meters: int = DEFAULT_RADIUS_METERS,
        time_window_minutes: int = DEFAULT_TIME_WINDOW_MINUTES,
    ):
        """
        Initialize the clustering service.

        Args:
            radius_meters: Maximum distance between events in a cluster
            time_window_minutes: Maximum age of events to consider
        """
        self.radius_meters = radius_meters
        self.time_window_minutes = time_window_minutes

    def find_nearby_events(
        self,
        event: Event,
        radius_meters: Optional[int] = None,
    ) -> QuerySet[Event]:
        """
        Find events near the given event within the time window.

        Args:
            event: The source event to find neighbors for
            radius_meters: Optional override for distance threshold

        Returns:
            QuerySet of nearby events (excluding the source event)
        """
        radius = radius_meters or self.radius_meters
        time_threshold = timezone.now() - timedelta(minutes=self.time_window_minutes)

        return (
            Event.objects.filter(
                created_at__gte=time_threshold,
                location__distance_lte=(event.location, D(m=radius)),
            )
            .exclude(id=event.id)
            .annotate(distance=Distance("location", event.location))
            .order_by("distance")
        )

    def create_cluster(
        self,
        event: Event,
        nearby_events: list[Event],
    ) -> EventCluster:
        """
        Create a new cluster containing the event and nearby events.

        Args:
            event: The primary event
            nearby_events: List of nearby events to include

        Returns:
            The created EventCluster
        """
        total_count = 1 + len(nearby_events)

        # Determine initial severity based on count
        computed_severity = event.severity
        if total_count >= self.ESCALATION_THRESHOLD_CRITICAL:
            computed_severity = SeverityChoices.CRITICAL
        elif total_count >= self.ESCALATION_THRESHOLD_HIGH:
            computed_severity = max(computed_severity, SeverityChoices.HIGH)

        cluster = EventCluster.objects.create(
            centroid=event.location,
            event_count=total_count,
            computed_severity=computed_severity,
        )

        # Assign the primary event to cluster
        event.cluster = cluster
        event.save()

        # Assign nearby events to cluster
        for nearby in nearby_events:
            nearby.cluster = cluster
            nearby.save()

        logger.info(f"Created cluster {cluster.id} with {total_count} events")
        return cluster

    def add_to_cluster(
        self,
        event: Event,
        cluster: EventCluster,
    ) -> None:
        """
        Add an event to an existing cluster.

        Args:
            event: The event to add
            cluster: The cluster to add to
        """
        event.cluster = cluster
        event.save()

        # Update cluster statistics
        cluster.event_count = cluster.events.count()
        cluster.last_event_at = timezone.now()

        # Check for severity escalation
        if cluster.event_count >= self.ESCALATION_THRESHOLD_CRITICAL:
            cluster.computed_severity = SeverityChoices.CRITICAL
        elif cluster.event_count >= self.ESCALATION_THRESHOLD_HIGH:
            cluster.computed_severity = max(
                cluster.computed_severity, SeverityChoices.HIGH
            )

        cluster.save()

        logger.info(
            f"Added event {event.id} to cluster {cluster.id}, "
            f"now has {cluster.event_count} events"
        )

    def _find_existing_cluster(
        self,
        nearby_events: QuerySet[Event],
    ) -> Optional[EventCluster]:
        """Find an existing cluster from nearby events."""
        for nearby in nearby_events:
            if nearby.cluster:
                return nearby.cluster
        return None

    def process_event(self, event: Event) -> Optional[EventCluster]:
        """
        Process an event for spatial clustering.

        This is the main entry point. It will:
        1. Find nearby events
        2. If nearby events exist in a cluster, add to that cluster
        3. If nearby events exist but no cluster, create a new one
        4. If no nearby events, do nothing

        Args:
            event: The event to process

        Returns:
            The cluster the event was added to, or None
        """
        nearby_events = self.find_nearby_events(event)

        if not nearby_events.exists():
            logger.debug(f"No nearby events for {event.id}")
            return None

        nearby_list = list(nearby_events)

        # Check if any nearby event is already in a cluster
        existing_cluster = self._find_existing_cluster(nearby_events)

        if existing_cluster:
            self.add_to_cluster(event, existing_cluster)
            return existing_cluster
        else:
            return self.create_cluster(event, nearby_list)

    def recalculate_cluster(self, cluster: EventCluster) -> None:
        """
        Recalculate cluster statistics.

        Useful after events are removed or modified.

        Args:
            cluster: The cluster to recalculate
        """
        events = cluster.events.all()
        cluster.event_count = events.count()

        if cluster.event_count == 0:
            cluster.delete()
            logger.info(f"Deleted empty cluster {cluster.id}")
            return

        # Recalculate centroid as average of event locations
        if cluster.event_count > 0:
            from django.contrib.gis.geos import Point

            avg_x = sum(e.location.x for e in events) / cluster.event_count
            avg_y = sum(e.location.y for e in events) / cluster.event_count
            cluster.centroid = Point(avg_x, avg_y, srid=4326)

        # Recalculate severity
        if cluster.event_count >= self.ESCALATION_THRESHOLD_CRITICAL:
            cluster.computed_severity = SeverityChoices.CRITICAL
        elif cluster.event_count >= self.ESCALATION_THRESHOLD_HIGH:
            cluster.computed_severity = SeverityChoices.HIGH
        else:
            # Use max severity from events
            max_severity = max(e.severity for e in events)
            cluster.computed_severity = max_severity

        cluster.save()
        logger.info(f"Recalculated cluster {cluster.id}")
