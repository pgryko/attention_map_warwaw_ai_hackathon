"""
Keyframe extraction service for video processing.

Uses FFmpeg to extract representative frames from video files.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class KeyframeService:
    """
    Service for extracting keyframes from video files.

    Uses FFmpeg to extract frames at specified timestamps or
    automatically detect scene changes.
    """

    def __init__(self):
        """Initialize the keyframe service."""
        self.ffmpeg_path = getattr(settings, "FFMPEG_PATH", "ffmpeg")
        self.ffprobe_path = getattr(settings, "FFPROBE_PATH", "ffprobe")
        self.thumbnail_width = getattr(settings, "THUMBNAIL_WIDTH", 640)
        self.thumbnail_quality = getattr(settings, "THUMBNAIL_QUALITY", 85)

    def is_available(self) -> bool:
        """Check if FFmpeg is available on the system."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_video_duration(self, video_data: bytes) -> Optional[float]:
        """
        Get the duration of a video in seconds.

        Args:
            video_data: Video file as bytes

        Returns:
            Duration in seconds, or None if unable to determine
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
            tmp.write(video_data)
            tmp.flush()

            try:
                result = subprocess.run(
                    [
                        self.ffprobe_path,
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        tmp.name,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())
            except (subprocess.SubprocessError, ValueError) as e:
                logger.warning(f"Failed to get video duration: {e}")

        return None

    def extract_keyframe(
        self,
        video_data: bytes,
        timestamp: Optional[float] = None,
    ) -> Optional[bytes]:
        """
        Extract a keyframe from video data.

        Args:
            video_data: Video file as bytes
            timestamp: Time in seconds to extract frame (default: 1 second or 10%)

        Returns:
            JPEG image data as bytes, or None if extraction failed
        """
        if not self.is_available():
            logger.warning("FFmpeg not available, skipping keyframe extraction")
            return None

        # Determine extraction timestamp
        if timestamp is None:
            duration = self.get_video_duration(video_data)
            if duration:
                # Use 10% of duration or 1 second, whichever is less
                timestamp = min(duration * 0.1, 1.0)
            else:
                timestamp = 1.0

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.mp4"
            output_path = Path(tmpdir) / "output.jpg"

            # Write video to temp file
            input_path.write_bytes(video_data)

            try:
                # Extract frame using FFmpeg
                result = subprocess.run(
                    [
                        self.ffmpeg_path,
                        "-y",  # Overwrite output
                        "-ss",
                        str(timestamp),  # Seek to timestamp
                        "-i",
                        str(input_path),  # Input file
                        "-vframes",
                        "1",  # Extract 1 frame
                        "-vf",
                        f"scale={self.thumbnail_width}:-1",  # Scale width
                        "-q:v",
                        str(int((100 - self.thumbnail_quality) / 10 + 1)),
                        str(output_path),
                    ],
                    capture_output=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    stderr = result.stderr.decode("utf-8", errors="ignore")
                    logger.error(f"FFmpeg failed: {stderr}")
                    return None

                if output_path.exists():
                    return output_path.read_bytes()

            except subprocess.TimeoutExpired:
                logger.error("FFmpeg timed out during keyframe extraction")
            except subprocess.SubprocessError as e:
                logger.error(f"FFmpeg subprocess error: {e}")

        return None

    def extract_multiple_keyframes(
        self,
        video_data: bytes,
        count: int = 3,
    ) -> list[bytes]:
        """
        Extract multiple keyframes evenly distributed throughout the video.

        Args:
            video_data: Video file as bytes
            count: Number of keyframes to extract

        Returns:
            List of JPEG image data as bytes
        """
        duration = self.get_video_duration(video_data)
        if not duration:
            # Try extracting just one frame at the beginning
            frame = self.extract_keyframe(video_data, timestamp=1.0)
            return [frame] if frame else []

        frames = []
        for i in range(count):
            # Distribute timestamps evenly (avoiding very start and end)
            timestamp = duration * (i + 1) / (count + 1)
            frame = self.extract_keyframe(video_data, timestamp=timestamp)
            if frame:
                frames.append(frame)

        return frames
