"""
Event processing service - orchestrates the full processing pipeline.
"""

import logging
from typing import Optional

from api.streaming import broadcast_new_event
from core.models import Event

from .classification import ClassificationService
from .clustering import ClusteringService
from .storage import StorageService

logger = logging.getLogger(__name__)


class EventProcessingService:
    """
    Orchestrator for the complete event processing pipeline.

    This service coordinates:
    1. Media storage
    2. AI classification
    3. Spatial clustering
    4. Real-time broadcast
    """

    def __init__(self):
        """Initialize all sub-services."""
        self.storage = StorageService()
        self.classification = ClassificationService()
        self.clustering = ClusteringService()

    def process_event(
        self,
        event: Event,
        media_data: Optional[bytes] = None,
        media_content_type: str = "application/octet-stream",
    ) -> dict:
        """
        Process an event through the full pipeline.

        Args:
            event: The Event model instance
            media_data: Optional media file bytes
            media_content_type: MIME type of the media

        Returns:
            Dictionary with processing results
        """
        result = {
            "event_id": str(event.id),
            "steps_completed": [],
            "errors": [],
        }

        # Step 1: Store media
        if media_data:
            try:
                media_url = self.storage.upload_media(
                    str(event.id),
                    media_data,
                    media_content_type,
                )
                event.media_url = media_url
                event.save()
                result["steps_completed"].append("store_media")
                result["media_url"] = media_url
            except Exception as e:
                logger.error(f"Failed to store media for event {event.id}: {e}")
                result["errors"].append(f"store_media: {e}")

        # Step 2: Extract keyframe (if video)
        if event.media_type == "video" and event.media_url:
            try:
                thumbnail_url = self._extract_keyframe(event)
                if thumbnail_url:
                    event.thumbnail_url = thumbnail_url
                    event.save()
                    result["steps_completed"].append("extract_keyframe")
            except Exception as e:
                logger.error(f"Failed to extract keyframe for event {event.id}: {e}")
                result["errors"].append(f"extract_keyframe: {e}")

        # Step 3: AI Classification
        try:
            classification = self.classification.classify(event.description or "")
            event.category = classification.get("category", "")
            event.subcategory = classification.get("subcategory", "")
            event.severity = classification.get("severity", 1)
            event.ai_confidence = classification.get("confidence")
            event.ai_reasoning = classification.get("reasoning", "")
            event.save()
            result["steps_completed"].append("classify")
            result["classification"] = classification
        except Exception as e:
            logger.error(f"Failed to classify event {event.id}: {e}")
            result["errors"].append(f"classify: {e}")

        # Step 4: Spatial clustering
        try:
            cluster = self.clustering.process_event(event)
            if cluster:
                result["steps_completed"].append("cluster")
                result["cluster_id"] = str(cluster.id)
        except Exception as e:
            logger.error(f"Failed to cluster event {event.id}: {e}")
            result["errors"].append(f"cluster: {e}")

        # Step 5: Broadcast to SSE clients
        try:
            broadcast_new_event(event)
            result["steps_completed"].append("broadcast")
        except Exception as e:
            logger.error(f"Failed to broadcast event {event.id}: {e}")
            result["errors"].append(f"broadcast: {e}")

        logger.info(
            f"Processed event {event.id}: "
            f"completed={result['steps_completed']}, "
            f"errors={result['errors']}"
        )

        return result

    def _extract_keyframe(self, event: Event) -> Optional[str]:
        """
        Extract a keyframe from video.

        TODO: Implement ffmpeg-based keyframe extraction.
        """
        logger.info(f"Keyframe extraction not yet implemented for {event.media_url}")
        return None

    def reprocess_event(self, event: Event) -> dict:
        """
        Reprocess an existing event (e.g., after manual edit).

        Args:
            event: The Event model instance

        Returns:
            Dictionary with processing results
        """
        # Skip media storage for reprocessing
        return self.process_event(event, media_data=None)
