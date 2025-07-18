"""Gemini client for code review MCP server using official SDK.

Refactored to use the google-generativeai SDK instead of requests.
"""

import logging
import os
from typing import Dict

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini API client for code review."""

    def __init__(self, model: str = "gemini-1.5-flash"):
        """Initialize the Gemini client.

        Args:
            model: The Gemini model to use (default: gemini-1.5-flash)
        """
        self.model_name = model

        # Get API key
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")

        # Configure the SDK
        genai.configure(api_key=api_key)

        # Initialize the model
        self.model = genai.GenerativeModel(model)

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
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent reviews
                top_k=40,
                top_p=0.95,
                max_output_tokens=8192,
            )

            logger.debug(f"Sending request to Gemini API ({self.model_name}) with prompt length: {len(content)}")

            # Generate content using the SDK
            response = self.model.generate_content(
                content,
                generation_config=generation_config
            )

            # Update usage tracking
            self._update_usage(response)

            # Extract text from response
            review_text = self._extract_text_from_response(response)

            return review_text

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise

    def _extract_text_from_response(self, response: genai.types.GenerateContentResponse) -> str:
        """Extract text content from Gemini API SDK response.

        Args:
            response: The SDK response object

        Returns:
            The extracted text content
        """
        try:
            # The SDK provides a simple text property
            return response.text
        except ValueError as e:
            # Handle cases where the response was blocked or has no text
            logger.error(f"Response blocked or has no text: {e}")
            if response.prompt_feedback:
                logger.error(f"Prompt feedback: {response.prompt_feedback}")
            if response.candidates:
                logger.error(f"Candidates: {response.candidates}")
            raise ValueError("No text content in Gemini response, it may have been blocked.") from e

    def _update_usage(self, response: genai.types.GenerateContentResponse) -> None:
        """Update token usage statistics from response.

        Args:
            response: The SDK response object
        """
        self.call_count += 1

        # The SDK provides usage metadata
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata

            # Extract token counts
            prompt_tokens = getattr(usage, 'prompt_token_count', 0)
            completion_tokens = getattr(usage, 'candidates_token_count', 0)
            total_tokens = getattr(usage, 'total_token_count', 0)

            # Update running totals
            self.input_tokens += prompt_tokens
            self.output_tokens += completion_tokens
            self.total_tokens += total_tokens

            logger.debug(
                f"Usage - Input: {prompt_tokens}, Output: {completion_tokens}, Total: {total_tokens}"
            )
        else:
            logger.warning("No usage metadata in response")

    def get_usage_report(self) -> Dict:
        """Get token usage statistics.

        Returns:
            Dictionary with usage statistics
        """
        # Pricing per 1K tokens (as of 2024)
        pricing = {
            "flash": 0.000125,  # $0.125 per 1M tokens
            "pro": 0.0025,      # $2.50 per 1M tokens
        }

        # Determine pricing tier
        if "flash" in self.model_name.lower():
            cost_per_1k_tokens = pricing["flash"]
        else:
            cost_per_1k_tokens = pricing["pro"]

        estimated_cost = (self.total_tokens / 1000) * cost_per_1k_tokens

        return {
            "model": self.model_name,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "call_count": self.call_count,
            "estimated_cost": round(estimated_cost, 6)
        }
