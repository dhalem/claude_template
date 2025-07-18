# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Gemini client for code review MCP server.

Adapted from the meta_cognitive_guard.py implementation.
"""

import json
import logging
import os
from typing import Dict

import requests

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini API client for code review."""

    def __init__(self, model: str = "gemini-1.5-flash"):
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")

        # Gemini API endpoint
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        # Track usage
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.call_count = 0

    def review_code(self, content: str) -> str:
        """Send code content to Gemini for review.

        Args:
            content: The code content to review

        Returns:
            Review text from Gemini
        """
        try:
            response = self._call_gemini_api(content)
            review_text = self._extract_text_from_response(response)

            # Update usage tracking
            self._update_usage(response)

            return review_text

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise

    def _call_gemini_api(self, prompt: str) -> Dict:
        """Make API call to Gemini."""
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,  # Lower temperature for more consistent reviews
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        logger.debug(f"Sending request to Gemini API ({self.model}) with prompt length: {len(prompt)}")

        response = requests.post(
            f"{self.endpoint}?key={self.api_key}",
            headers=headers,
            json=payload,
            timeout=300  # 5 minutes timeout for large code reviews
        )

        logger.debug(f"Gemini API response status: {response.status_code}")

        if response.status_code != 200:
            error_msg = f"Gemini API error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        response_data = response.json()
        logger.debug(f"Gemini API response received with {len(str(response_data))} characters")

        return response_data

    def _extract_text_from_response(self, response: Dict) -> str:
        """Extract text content from Gemini API response."""
        try:
            candidates = response.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates in Gemini response")

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            if not parts:
                raise ValueError("No parts in Gemini response")

            # Combine all text parts
            text_parts = []
            for part in parts:
                if "text" in part:
                    text_parts.append(part["text"])

            if not text_parts:
                raise ValueError("No text content in Gemini response")

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting text from Gemini response: {e}")
            logger.debug(f"Response structure: {json.dumps(response, indent=2)}")
            raise

    def _update_usage(self, response: Dict) -> None:
        """Update usage tracking from response."""
        self.call_count += 1

        # Extract token usage if available
        usage_metadata = response.get("usageMetadata", {})
        if usage_metadata:
            prompt_tokens = usage_metadata.get("promptTokenCount", 0)
            completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
            total_tokens = usage_metadata.get("totalTokenCount", 0)

            self.input_tokens += prompt_tokens
            self.output_tokens += completion_tokens
            self.total_tokens += total_tokens

            logger.debug(f"Token usage - Prompt: {prompt_tokens}, "
                         f"Completion: {completion_tokens}, Total: {total_tokens}")

    def get_usage_report(self) -> Dict:
        """Get usage statistics."""
        # Estimate cost based on model
        if "flash" in self.model.lower():
            cost_per_1k_tokens = 0.00001  # Flash pricing
        else:
            cost_per_1k_tokens = 0.002  # Pro model pricing

        estimated_cost = (self.total_tokens / 1000) * cost_per_1k_tokens

        return {
            "model": self.model,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "call_count": self.call_count,
            "estimated_cost": estimated_cost
        }

    def reset_usage(self) -> None:
        """Reset usage tracking."""
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.call_count = 0
