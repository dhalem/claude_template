# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Gemini client for code analysis MCP server using official SDK.

Enhanced to support multiple analysis types with centralized usage tracking
and task-aware communication for better cost management and monitoring.
"""

import logging
import os
from typing import Dict, Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini API client for code analysis with task-aware tracking."""

    # Default pricing per 1K tokens (as of January 2025)
    # WARNING: These prices may become outdated - check Google's current pricing
    DEFAULT_PRICING = {
        "flash": 0.000125,  # $0.125 per 1M tokens
        "pro": 0.0025,  # $2.50 per 1M tokens
    }

    def __init__(self, model: str = "gemini-1.5-flash", usage_tracker=None, custom_pricing: dict = None):
        """Initialize the Gemini client with task-aware tracking.

        Args:
            model: The Gemini model to use (default: gemini-1.5-flash)
            usage_tracker: Optional centralized usage tracker for multi-tool monitoring
            custom_pricing: Custom pricing dict to override defaults (for updated pricing)
        """
        self.model_name = model
        self.pricing = custom_pricing or self.DEFAULT_PRICING.copy()

        # Use provided tracker or create local tracking
        self.usage_tracker = usage_tracker

        # Local tracking for backward compatibility when no UsageTracker provided
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.call_count = 0

        # Get API key
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")

        # Configure the SDK
        genai.configure(api_key=api_key)

        # Initialize the model
        self.model = genai.GenerativeModel(model)

    def analyze_code(self, content: str, task_type: str = "review") -> str:
        """Send code content to Gemini for analysis.

        Args:
            content: The code content to analyze
            task_type: Type of analysis task (e.g., 'review', 'bug_finding')

        Returns:
            Analysis text from Gemini
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

            # Generate content using the SDK with timeout
            response = self.model.generate_content(
                content, generation_config=generation_config, request_options={"timeout": 120}  # 2 minute timeout
            )

            # Update usage tracking
            self._update_usage(response, task_type)

            # Extract text from response
            review_text = self._extract_text_from_response(response)

            return review_text

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise

    def review_code(self, content: str) -> str:
        """Send code content to Gemini for review (backward compatibility).

        Args:
            content: The code content to review

        Returns:
            Review text from Gemini
        """
        return self.analyze_code(content, task_type="review")

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

    def _update_usage(self, response: genai.types.GenerateContentResponse, task_type: str = "review") -> None:
        """Update token usage statistics from response.

        Args:
            response: The SDK response object
            task_type: Type of analysis task for centralized tracking
        """
        self.call_count += 1

        # The SDK provides usage metadata
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata

            # Extract token counts
            prompt_tokens = getattr(usage, "prompt_token_count", 0)
            completion_tokens = getattr(usage, "candidates_token_count", 0)
            total_tokens = getattr(usage, "total_token_count", 0)

            # Update local tracking for backward compatibility
            self.input_tokens += prompt_tokens
            self.output_tokens += completion_tokens
            self.total_tokens += total_tokens

            # Update centralized tracking if available
            if self.usage_tracker:
                self.usage_tracker.update_usage(
                    task_type=task_type,
                    model=self.model_name,
                    input_tokens=prompt_tokens,
                    output_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )

            logger.debug(
                f"Usage - Task: {task_type}, Input: {prompt_tokens}, Output: {completion_tokens}, Total: {total_tokens}"
            )
        else:
            logger.warning("No usage metadata in response")

    def get_usage_report(self) -> Dict:
        """Get token usage statistics.

        Returns:
            Dictionary with usage statistics (local tracking for backward compatibility)
        """
        # Determine pricing tier using configured pricing
        if "flash" in self.model_name.lower():
            cost_per_1k_tokens = self.pricing.get("flash", self.DEFAULT_PRICING["pro"])
        else:
            cost_per_1k_tokens = self.pricing.get("pro", self.DEFAULT_PRICING["pro"])

        estimated_cost = (self.total_tokens / 1000) * cost_per_1k_tokens

        return {
            "model": self.model_name,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "call_count": self.call_count,
            "estimated_cost": round(estimated_cost, 6),
        }

    def get_centralized_usage_report(self) -> Optional[Dict]:
        """Get comprehensive usage report from centralized tracker.

        Returns:
            Detailed usage report from UsageTracker if available, None otherwise
        """
        if self.usage_tracker:
            return self.usage_tracker.get_detailed_report()
        return None

    def get_cost_optimization_insights(self) -> Optional[Dict]:
        """Get cost optimization insights from centralized tracker.

        Returns:
            Cost optimization insights if centralized tracker available, None otherwise
        """
        if self.usage_tracker:
            return self.usage_tracker.get_cost_optimization_insights()
        return None
