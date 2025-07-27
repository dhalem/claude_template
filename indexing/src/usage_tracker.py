# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Centralized usage tracking and cost estimation for all analysis types.

This module provides comprehensive usage intelligence, cost management,
and analytics across all code analysis tools, enabling unified monitoring
and optimization of AI analysis usage.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TaskUsage:
    """Usage statistics for a specific analysis task type."""

    def __init__(self, task_type: str):
        self.task_type = task_type
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.call_count = 0
        self.first_call = None
        self.last_call = None

    def update(self, input_tokens: int, output_tokens: int, total_tokens: int):
        """Update usage statistics for this task type."""
        now = datetime.now()

        if self.first_call is None:
            self.first_call = now
        self.last_call = now

        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens
        self.call_count += 1

    def get_stats(self) -> Dict:
        """Get usage statistics for this task type."""
        return {
            "task_type": self.task_type,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "call_count": self.call_count,
            "first_call": self.first_call.isoformat() if self.first_call else None,
            "last_call": self.last_call.isoformat() if self.last_call else None,
        }


class UsageTracker:
    """Centralized usage tracking and cost estimation system.

    Tracks AI analysis usage across all tools and task types, providing
    comprehensive cost management, analytics, and optimization insights.
    """

    # Default pricing per 1K tokens (as of January 2025)
    # WARNING: These prices may become outdated - check Google's current pricing
    DEFAULT_PRICING = {
        "flash": 0.000125,  # $0.125 per 1M tokens
        "pro": 0.0025,  # $2.50 per 1M tokens
    }

    def __init__(self, custom_pricing: Optional[Dict[str, float]] = None):
        """Initialize the usage tracker.

        Args:
            custom_pricing: Optional custom pricing per 1K tokens for different models
        """
        self.pricing = custom_pricing or self.DEFAULT_PRICING.copy()
        self.task_usage: Dict[str, TaskUsage] = {}
        self.session_start = datetime.now()

        logger.info("UsageTracker initialized with pricing: %s", self.pricing)

    def update_usage(self, task_type: str, model: str, input_tokens: int, output_tokens: int, total_tokens: int):
        """Update usage statistics for a specific task and model.

        Args:
            task_type: Type of analysis task (e.g., 'review', 'bug_finding')
            model: Model used (e.g., 'gemini-1.5-flash', 'gemini-2.5-pro')
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            total_tokens: Total tokens used
        """
        # Create task usage tracker if it doesn't exist
        if task_type not in self.task_usage:
            self.task_usage[task_type] = TaskUsage(task_type)

        # Update task-specific usage
        self.task_usage[task_type].update(input_tokens, output_tokens, total_tokens)

        logger.info(
            "Usage updated - Task: %s, Model: %s, Input: %d, Output: %d, Total: %d",
            task_type,
            model,
            input_tokens,
            output_tokens,
            total_tokens,
        )

    def get_task_usage(self, task_type: str) -> Dict:
        """Get usage statistics for a specific task type.

        Args:
            task_type: Task type to get usage for

        Returns:
            Dictionary with task usage statistics
        """
        if task_type not in self.task_usage:
            return {
                "task_type": task_type,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "call_count": 0,
                "estimated_cost": 0.0,
                "first_call": None,
                "last_call": None,
            }

        usage = self.task_usage[task_type]
        estimated_cost = self._calculate_cost(usage.total_tokens)

        stats = usage.get_stats()
        stats["estimated_cost"] = estimated_cost

        return stats

    def get_total_usage(self) -> Dict:
        """Get combined usage statistics across all task types.

        Returns:
            Dictionary with total usage statistics
        """
        total_tokens = sum(usage.total_tokens for usage in self.task_usage.values())
        total_input = sum(usage.input_tokens for usage in self.task_usage.values())
        total_output = sum(usage.output_tokens for usage in self.task_usage.values())
        total_calls = sum(usage.call_count for usage in self.task_usage.values())

        estimated_cost = self._calculate_cost(total_tokens)

        # Find earliest and latest calls
        first_call = None
        last_call = None
        for usage in self.task_usage.values():
            if usage.first_call:
                if first_call is None or usage.first_call < first_call:
                    first_call = usage.first_call
            if usage.last_call:
                if last_call is None or usage.last_call > last_call:
                    last_call = usage.last_call

        return {
            "total_tokens": total_tokens,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "call_count": total_calls,
            "estimated_cost": estimated_cost,
            "session_start": self.session_start.isoformat(),
            "first_call": first_call.isoformat() if first_call else None,
            "last_call": last_call.isoformat() if last_call else None,
            "task_count": len(self.task_usage),
            "task_types": list(self.task_usage.keys()),
        }

    def get_detailed_report(self) -> Dict:
        """Get comprehensive usage report with per-task breakdown.

        Returns:
            Dictionary with detailed usage analytics
        """
        total_usage = self.get_total_usage()
        task_breakdown = {}

        for task_type in self.task_usage.keys():
            task_breakdown[task_type] = self.get_task_usage(task_type)

        return {"summary": total_usage, "by_task": task_breakdown, "pricing": self.pricing}

    def estimate_cost(self, tokens: int, model_hint: Optional[str] = None) -> float:
        """Estimate cost for a given number of tokens.

        Args:
            tokens: Number of tokens to estimate cost for
            model_hint: Optional hint about model type for pricing

        Returns:
            Estimated cost in dollars
        """
        return self._calculate_cost(tokens, model_hint)

    def _calculate_cost(self, tokens: int, model_hint: Optional[str] = None) -> float:
        """Internal method to calculate cost based on tokens.

        Args:
            tokens: Number of tokens
            model_hint: Optional model hint for pricing tier

        Returns:
            Cost in dollars
        """
        if tokens <= 0:
            return 0.0

        # Determine pricing tier
        if model_hint and "flash" in model_hint.lower():
            cost_per_1k_tokens = self.pricing.get("flash", self.DEFAULT_PRICING["flash"])
        elif model_hint and "pro" in model_hint.lower():
            cost_per_1k_tokens = self.pricing.get("pro", self.DEFAULT_PRICING["pro"])
        else:
            # Default to pro pricing if unsure
            cost_per_1k_tokens = self.pricing.get("pro", self.DEFAULT_PRICING["pro"])

        # Calculate cost (pricing is per 1K tokens)
        cost = (tokens / 1000) * cost_per_1k_tokens

        return round(cost, 6)

    def reset_usage(self, task_type: Optional[str] = None):
        """Reset usage statistics.

        Args:
            task_type: Optional specific task type to reset, or None for all
        """
        if task_type:
            if task_type in self.task_usage:
                del self.task_usage[task_type]
                logger.info("Reset usage for task type: %s", task_type)
        else:
            self.task_usage.clear()
            self.session_start = datetime.now()
            logger.info("Reset all usage statistics")

    def get_cost_optimization_insights(self) -> Dict:
        """Get insights for cost optimization.

        Returns:
            Dictionary with optimization recommendations
        """
        total_usage = self.get_total_usage()
        insights = {"total_cost": total_usage["estimated_cost"], "recommendations": []}

        # Analyze usage patterns for optimization opportunities
        if total_usage["call_count"] > 0:
            avg_tokens_per_call = total_usage["total_tokens"] / total_usage["call_count"]

            if avg_tokens_per_call > 10000:
                insights["recommendations"].append(
                    {
                        "type": "high_token_usage",
                        "message": f"Average {avg_tokens_per_call:.0f} tokens per call. Consider using gemini-1.5-flash for simpler tasks.",
                        "potential_savings": self._calculate_cost(total_usage["total_tokens"], "flash")
                        - total_usage["estimated_cost"],
                    }
                )

            if total_usage["call_count"] > 100:
                insights["recommendations"].append(
                    {
                        "type": "high_volume",
                        "message": f"{total_usage['call_count']} API calls made. Consider batch processing for similar analyses.",
                        "potential_savings": "Batch processing could reduce API overhead costs.",
                    }
                )

        return insights

    def export_usage_data(self) -> Dict:
        """Export usage data for external analysis or backup.

        Returns:
            Complete usage data in exportable format
        """
        return {
            "export_timestamp": datetime.now().isoformat(),
            "session_start": self.session_start.isoformat(),
            "usage_data": self.get_detailed_report(),
            "optimization_insights": self.get_cost_optimization_insights(),
        }
