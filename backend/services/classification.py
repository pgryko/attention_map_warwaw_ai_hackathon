"""
Classification service for AI-powered event categorization.
"""

import json
import logging
from typing import Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for classifying events using OpenRouter API."""

    # Category definitions for the AI prompt
    CATEGORIES = {
        "emergency": "Fire, explosion, collapse",
        "security": "Drone activity, suspicious activity",
        "traffic": "Accident, road blockage",
        "protest": "March, demonstration, gathering",
        "infrastructure": "Pothole, broken streetlight, damage",
        "environmental": "Pollution, fallen tree, flooding",
        "informational": "General observation",
    }

    # Severity definitions
    SEVERITY_LEVELS = {
        1: "Low - Informational only",
        2: "Medium - Needs attention, not urgent",
        3: "High - Urgent, requires response",
        4: "Critical - Life-threatening emergency",
    }

    def __init__(self):
        """Initialize OpenRouter client if API key is configured."""
        self.client = None
        self.model = getattr(
            settings, "OPENROUTER_MODEL", "google/gemini-2.5-flash-lite"
        )

        api_key = getattr(settings, "OPENROUTER_API_KEY", "")
        if api_key:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=api_key,
                base_url=settings.OPENROUTER_BASE_URL,
            )

    def _build_prompt(self, description: str) -> str:
        """Build the classification prompt."""
        categories_text = "\n".join(
            f"- {name}: {desc}" for name, desc in self.CATEGORIES.items()
        )
        severity_text = "\n".join(
            f"- {level}: {desc}" for level, desc in self.SEVERITY_LEVELS.items()
        )

        return f"""Analyze this incident report and classify it.

Description: {description or "No description provided"}

Classify into one of these categories:
{categories_text}

Also assign severity (1-4):
{severity_text}

Respond in JSON format only:
{{"category": "...", "subcategory": "...", "severity": N, "confidence": 0.0-1.0,
"reasoning": "..."}}
"""

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse the API response, handling markdown-wrapped JSON."""
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        return json.loads(content)

    def _default_classification(self, reason: str) -> dict[str, Any]:
        """Return default classification for error cases."""
        return {
            "category": "informational",
            "subcategory": "",
            "severity": 1,
            "confidence": None,
            "reasoning": reason,
        }

    def classify(self, description: str) -> dict[str, Any]:
        """
        Classify an event description using AI.

        Args:
            description: The event description to classify

        Returns:
            Dictionary with classification results:
            - category: One of the predefined categories
            - subcategory: More specific classification
            - severity: 1-4 severity level
            - confidence: 0.0-1.0 confidence score
            - reasoning: Explanation of the classification
        """
        if not self.client:
            logger.warning("OpenRouter API not configured, skipping classification")
            return self._default_classification(
                "Classification skipped - API not configured"
            )

        try:
            prompt = self._build_prompt(description)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                extra_headers={
                    "HTTP-Referer": "https://attention-map.app",
                    "X-Title": "Attention Map",
                },
            )

            content = response.choices[0].message.content
            result = self._parse_response(content)

            logger.info(
                f"Classified event as {result.get('category')} "
                f"with severity {result.get('severity')}"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
            return self._default_classification(
                "Classification failed: Invalid JSON response"
            )
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return self._default_classification(f"Classification failed: {e}")

    def classify_with_media(
        self,
        description: str,
        media_url: Optional[str] = None,
        transcription: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Classify an event with optional media context.

        Args:
            description: The event description
            media_url: URL of associated media (for vision models)
            transcription: Audio transcription if available

        Returns:
            Classification results dictionary
        """
        # Enhance description with transcription if available
        full_description = description
        if transcription:
            full_description = f"{description}\n\nAudio transcription: {transcription}"

        # TODO: Add vision model support for image analysis
        return self.classify(full_description)
