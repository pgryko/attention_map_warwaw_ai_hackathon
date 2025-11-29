"""
Audio transcription service using Groq's Whisper API.

Extracts and transcribes audio from video files or processes audio files directly.
"""

import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Service for transcribing audio content using Groq's Whisper API.

    Supports:
    - Direct audio file transcription
    - Audio extraction from video files (via FFmpeg)
    - Multiple audio formats (mp3, wav, m4a, webm, mp4)
    """

    # Supported audio formats for Groq Whisper
    SUPPORTED_FORMATS = {"mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"}

    def __init__(self):
        """Initialize the transcription service."""
        self.api_key = getattr(settings, "GROQ_API_KEY", "")
        self.ffmpeg_path = getattr(settings, "FFMPEG_PATH", "ffmpeg")
        self.model = getattr(settings, "GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
        self.client = None

        if self.api_key:
            try:
                from groq import Groq

                self.client = Groq(api_key=self.api_key)
            except ImportError:
                logger.warning("Groq package not installed")

    def is_available(self) -> bool:
        """Check if the transcription service is available."""
        return self.client is not None

    def _is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available for audio extraction."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def extract_audio(self, video_data: bytes) -> Optional[bytes]:
        """
        Extract audio track from video file.

        Args:
            video_data: Video file as bytes

        Returns:
            Audio data as bytes (MP3 format), or None if extraction failed
        """
        if not self._is_ffmpeg_available():
            logger.warning("FFmpeg not available for audio extraction")
            return None

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.mp4"
            output_path = Path(tmpdir) / "output.mp3"

            input_path.write_bytes(video_data)

            try:
                result = subprocess.run(
                    [
                        self.ffmpeg_path,
                        "-y",  # Overwrite output
                        "-i",
                        str(input_path),
                        "-vn",  # No video
                        "-acodec",
                        "libmp3lame",
                        "-ar",
                        "16000",  # 16kHz for Whisper
                        "-ac",
                        "1",  # Mono
                        "-b:a",
                        "64k",  # Bitrate
                        str(output_path),
                    ],
                    capture_output=True,
                    timeout=120,
                )

                if result.returncode != 0:
                    stderr = result.stderr.decode("utf-8", errors="ignore")
                    logger.error(f"FFmpeg audio extraction failed: {stderr}")
                    return None

                if output_path.exists() and output_path.stat().st_size > 0:
                    return output_path.read_bytes()

            except subprocess.TimeoutExpired:
                logger.error("FFmpeg timed out during audio extraction")
            except subprocess.SubprocessError as e:
                logger.error(f"FFmpeg subprocess error: {e}")

        return None

    def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        filename: str = "audio.mp3",
    ) -> Optional[str]:
        """
        Transcribe audio content using Groq's Whisper API.

        Args:
            audio_data: Audio file as bytes
            language: Optional language code (e.g., 'en', 'pl')
            filename: Filename hint for the audio format

        Returns:
            Transcribed text, or None if transcription failed
        """
        if not self.is_available():
            logger.warning("Transcription service not configured (no API key)")
            return None

        if not audio_data:
            logger.warning("No audio data provided for transcription")
            return None

        try:
            # Create file-like object for API
            audio_file = io.BytesIO(audio_data)
            audio_file.name = filename

            # Call Groq Whisper API
            transcription = self.client.audio.transcriptions.create(
                file=(filename, audio_file),
                model=self.model,
                language=language,
                response_format="text",
            )

            # Clean up the transcription
            text = str(transcription).strip()

            if text:
                logger.info(f"Successfully transcribed {len(audio_data)} bytes")
                return text

        except Exception as e:
            logger.error(f"Transcription failed: {e}")

        return None

    def transcribe_video(
        self,
        video_data: bytes,
        language: Optional[str] = None,
    ) -> Optional[str]:
        """
        Extract audio from video and transcribe it.

        Args:
            video_data: Video file as bytes
            language: Optional language code

        Returns:
            Transcribed text, or None if extraction/transcription failed
        """
        # Extract audio from video
        audio_data = self.extract_audio(video_data)
        if not audio_data:
            logger.warning("Could not extract audio from video")
            return None

        # Transcribe the extracted audio
        return self.transcribe(audio_data, language=language, filename="audio.mp3")

    def transcribe_media(
        self,
        media_data: bytes,
        media_type: str,
        language: Optional[str] = None,
    ) -> Optional[str]:
        """
        Transcribe media content (audio or video).

        This is the main entry point for the processing pipeline.

        Args:
            media_data: Media file as bytes
            media_type: Either 'video' or 'audio'
            language: Optional language code

        Returns:
            Transcribed text, or None if transcription failed
        """
        if media_type == "video":
            return self.transcribe_video(media_data, language=language)
        elif media_type == "audio":
            return self.transcribe(media_data, language=language)
        else:
            logger.warning(f"Unsupported media type for transcription: {media_type}")
            return None
