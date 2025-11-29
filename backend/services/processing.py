"""
Event processing service - orchestrates the full processing pipeline.
"""

import logging
from typing import Optional

from api.streaming import broadcast_new_event
from core.models import Event

from .classification import ClassificationService
from .clustering import ClusteringService
from .keyframe import KeyframeService
from .storage import StorageService
from .transcription import TranscriptionService

logger = logging.getLogger(__name__)


class EventProcessingService:
    """
    Orchestrator for the complete event processing pipeline.

    This service coordinates:
    1. Media storage
    2. Keyframe extraction (for videos)
    3. Audio transcription (for videos)
    4. AI classification (using description + transcription)
    5. Spatial clustering
    6. Real-time broadcast
    """

    def __init__(self):
        """Initialize all sub-services."""
        self.storage = StorageService()
        self.keyframe = KeyframeService()
        self.transcription = TranscriptionService()
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
        if event.media_type == "video" and media_data:
            try:
                thumbnail_url = self._extract_keyframe(event, media_data)
                if thumbnail_url:
                    event.thumbnail_url = thumbnail_url
                    event.save()
                    result["steps_completed"].append("extract_keyframe")
                    result["thumbnail_url"] = thumbnail_url
            except Exception as e:
                logger.error(f"Failed to extract keyframe for event {event.id}: {e}")
                result["errors"].append(f"extract_keyframe: {e}")

        # Step 3: Transcribe audio (if video)
        if event.media_type == "video" and media_data:
            try:
                transcription = self._transcribe_media(event, media_data)
                if transcription:
                    event.transcription = transcription
                    event.save()
                    result["steps_completed"].append("transcribe")
                    result["transcription"] = transcription
            except Exception as e:
                logger.error(f"Failed to transcribe event {event.id}: {e}")
                result["errors"].append(f"transcribe: {e}")

        # Step 4: AI Classification (using description + transcription)
        try:
            # Combine description and transcription for better classification
            classification_text = self._build_classification_text(event)
            classification = self.classification.classify(classification_text)
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

        # Step 5: Spatial clustering
        try:
            cluster = self.clustering.process_event(event)
            if cluster:
                result["steps_completed"].append("cluster")
                result["cluster_id"] = str(cluster.id)
        except Exception as e:
            logger.error(f"Failed to cluster event {event.id}: {e}")
            result["errors"].append(f"cluster: {e}")

        # Step 6: Broadcast to SSE clients
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

    def _extract_keyframe(self, event: Event, video_data: bytes) -> Optional[str]:
        """
        Extract a keyframe from video and upload as thumbnail.

        Args:
            event: The Event model instance
            video_data: Video file bytes

        Returns:
            URL of the uploaded thumbnail, or None if extraction failed
        """
        # Extract keyframe using FFmpeg
        thumbnail_data = self.keyframe.extract_keyframe(video_data)
        if not thumbnail_data:
            logger.warning(f"Could not extract keyframe for event {event.id}")
            return None

        # Upload thumbnail to storage
        thumbnail_url = self.storage.upload_thumbnail(
            str(event.id),
            thumbnail_data,
            content_type="image/jpeg",
        )

        logger.info(f"Extracted and uploaded keyframe for event {event.id}")
        return thumbnail_url

    def _transcribe_media(self, event: Event, media_data: bytes) -> Optional[str]:
        """
        Transcribe audio from media file.

        Args:
            event: The Event model instance
            media_data: Media file bytes

        Returns:
            Transcription text, or None if transcription failed
        """
        transcription = self.transcription.transcribe_media(
            media_data,
            media_type=event.media_type,
        )
        if transcription:
            logger.info(f"Transcribed media for event {event.id}")
        else:
            logger.warning(f"Could not transcribe media for event {event.id}")
        return transcription

    def _build_classification_text(self, event: Event) -> str:
        """
        Build the text input for classification.

        Combines user description with transcription for richer context.

        Args:
            event: The Event model instance

        Returns:
            Combined text for classification
        """
        parts = []

        if event.description:
            parts.append(f"User description: {event.description}")

        if event.transcription:
            parts.append(f"Audio transcription: {event.transcription}")

        if not parts:
            return ""

        return "\n\n".join(parts)

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
