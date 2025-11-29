"""
Storage service for MinIO media management.
"""

import io
import logging

from django.conf import settings
from minio import Minio

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storing media files in MinIO."""

    def __init__(self):
        """Initialize MinIO client from settings."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket = settings.MINIO_BUCKET
        self.endpoint = settings.MINIO_ENDPOINT
        self.use_ssl = settings.MINIO_USE_SSL

    def ensure_bucket(self) -> None:
        """Ensure the storage bucket exists, create if not."""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Created bucket: {self.bucket}")

    def _get_base_url(self) -> str:
        """Get the base URL for media files."""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.endpoint}/{self.bucket}"

    def upload_media(
        self,
        event_id: str,
        data: bytes,
        content_type: str,
        suffix: str = "",
    ) -> str:
        """
        Upload media file to MinIO.

        Args:
            event_id: The event ID for organizing files
            data: The file data as bytes
            content_type: MIME type of the file
            suffix: Optional suffix for the object name

        Returns:
            URL of the uploaded file
        """
        self.ensure_bucket()

        object_name = f"events/{event_id}/media{suffix}"

        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(data),
            len(data),
            content_type=content_type,
        )

        logger.info(f"Uploaded media for event {event_id}: {object_name}")
        return f"{self._get_base_url()}/{object_name}"

    def upload_thumbnail(
        self,
        event_id: str,
        data: bytes,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload thumbnail image to MinIO.

        Args:
            event_id: The event ID for organizing files
            data: The thumbnail data as bytes
            content_type: MIME type (defaults to image/jpeg)

        Returns:
            URL of the uploaded thumbnail
        """
        return self.upload_media(
            event_id,
            data,
            content_type,
            suffix="_thumb.jpg",
        )

    def delete_media(self, event_id: str) -> None:
        """
        Delete all media files for an event.

        Args:
            event_id: The event ID to delete files for
        """
        prefix = f"events/{event_id}/"
        objects = self.client.list_objects(self.bucket, prefix=prefix)

        for obj in objects:
            self.client.remove_object(self.bucket, obj.object_name)
            logger.info(f"Deleted: {obj.object_name}")
