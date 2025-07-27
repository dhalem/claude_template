# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Tests for UsageTracker functionality.

Validates the extracted usage tracking and cost estimation functionality
to ensure it works correctly before integration with other components.

Testing approach:
- Real integration tests with actual files and data
- External service boundaries handled appropriately
- See TESTING_STRATEGY.md for detailed guidelines
"""

import os
import sys
import unittest

# Import the UsageTracker to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from usage_tracker import UsageTracker


class TestUsageTracker(unittest.TestCase):
    """Test UsageTracker functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = UsageTracker()

    def test_initial_state(self):
        """Test UsageTracker initial state."""
        total_usage = self.tracker.get_total_usage()

        self.assertEqual(total_usage["total_tokens"], 0)
        self.assertEqual(total_usage["input_tokens"], 0)
        self.assertEqual(total_usage["output_tokens"], 0)
        self.assertEqual(total_usage["call_count"], 0)
        self.assertEqual(total_usage["estimated_cost"], 0.0)
        self.assertEqual(total_usage["task_count"], 0)
        self.assertEqual(total_usage["task_types"], [])

    def test_single_task_usage_update(self):
        """Test updating usage for a single task."""
        # Update usage for review task
        self.tracker.update_usage("review", "gemini-1.5-flash", 100, 50, 150)

        # Check task-specific usage
        review_usage = self.tracker.get_task_usage("review")
        self.assertEqual(review_usage["task_type"], "review")
        self.assertEqual(review_usage["total_tokens"], 150)
        self.assertEqual(review_usage["input_tokens"], 100)
        self.assertEqual(review_usage["output_tokens"], 50)
        self.assertEqual(review_usage["call_count"], 1)
        self.assertGreater(review_usage["estimated_cost"], 0)

        # Check total usage
        total_usage = self.tracker.get_total_usage()
        self.assertEqual(total_usage["total_tokens"], 150)
        self.assertEqual(total_usage["call_count"], 1)
        self.assertEqual(total_usage["task_count"], 1)
        self.assertEqual(total_usage["task_types"], ["review"])

    def test_multiple_task_usage_tracking(self):
        """Test tracking usage across multiple task types."""
        # Add usage for review task
        self.tracker.update_usage("review", "gemini-2.5-pro", 1000, 500, 1500)

        # Add usage for bug finding task
        self.tracker.update_usage("bug_finding", "gemini-1.5-flash", 800, 400, 1200)

        # Check individual task usage
        review_usage = self.tracker.get_task_usage("review")
        self.assertEqual(review_usage["total_tokens"], 1500)
        self.assertEqual(review_usage["call_count"], 1)

        bug_usage = self.tracker.get_task_usage("bug_finding")
        self.assertEqual(bug_usage["total_tokens"], 1200)
        self.assertEqual(bug_usage["call_count"], 1)

        # Check total usage
        total_usage = self.tracker.get_total_usage()
        self.assertEqual(total_usage["total_tokens"], 2700)  # 1500 + 1200
        self.assertEqual(total_usage["input_tokens"], 1800)  # 1000 + 800
        self.assertEqual(total_usage["output_tokens"], 900)  # 500 + 400
        self.assertEqual(total_usage["call_count"], 2)
        self.assertEqual(total_usage["task_count"], 2)
        self.assertIn("review", total_usage["task_types"])
        self.assertIn("bug_finding", total_usage["task_types"])

    def test_multiple_calls_same_task(self):
        """Test multiple calls for the same task type."""
        # First call
        self.tracker.update_usage("review", "gemini-1.5-flash", 100, 50, 150)
        # Second call
        self.tracker.update_usage("review", "gemini-1.5-flash", 200, 100, 300)

        review_usage = self.tracker.get_task_usage("review")
        self.assertEqual(review_usage["total_tokens"], 450)  # 150 + 300
        self.assertEqual(review_usage["input_tokens"], 300)  # 100 + 200
        self.assertEqual(review_usage["output_tokens"], 150)  # 50 + 100
        self.assertEqual(review_usage["call_count"], 2)

    def test_cost_estimation(self):
        """Test cost estimation functionality."""
        # Test flash model cost estimation
        flash_cost = self.tracker.estimate_cost(1000, "gemini-1.5-flash")
        expected_flash = 1000 / 1000 * 0.000125  # 1K tokens * flash price
        self.assertAlmostEqual(flash_cost, expected_flash, places=6)

        # Test pro model cost estimation
        pro_cost = self.tracker.estimate_cost(1000, "gemini-2.5-pro")
        expected_pro = 1000 / 1000 * 0.0025  # 1K tokens * pro price
        self.assertAlmostEqual(pro_cost, expected_pro, places=6)

    def test_custom_pricing(self):
        """Test UsageTracker with custom pricing."""
        custom_pricing = {"flash": 0.0001, "pro": 0.002}
        tracker = UsageTracker(custom_pricing=custom_pricing)

        cost = tracker.estimate_cost(1000, "gemini-1.5-flash")
        expected = 1000 / 1000 * 0.0001
        self.assertAlmostEqual(cost, expected, places=6)

    def test_detailed_report(self):
        """Test comprehensive usage reporting."""
        # Add some usage data
        self.tracker.update_usage("review", "gemini-2.5-pro", 1000, 500, 1500)
        self.tracker.update_usage("bug_finding", "gemini-1.5-flash", 800, 400, 1200)

        report = self.tracker.get_detailed_report()

        # Check report structure
        self.assertIn("summary", report)
        self.assertIn("by_task", report)
        self.assertIn("pricing", report)

        # Check summary
        summary = report["summary"]
        self.assertEqual(summary["total_tokens"], 2700)
        self.assertEqual(summary["task_count"], 2)

        # Check task breakdown
        task_breakdown = report["by_task"]
        self.assertIn("review", task_breakdown)
        self.assertIn("bug_finding", task_breakdown)
        self.assertEqual(task_breakdown["review"]["total_tokens"], 1500)
        self.assertEqual(task_breakdown["bug_finding"]["total_tokens"], 1200)

    def test_reset_functionality(self):
        """Test usage reset functionality."""
        # Add some usage
        self.tracker.update_usage("review", "gemini-1.5-flash", 100, 50, 150)
        self.tracker.update_usage("bug_finding", "gemini-1.5-flash", 200, 100, 300)

        # Verify usage exists
        total_usage = self.tracker.get_total_usage()
        self.assertEqual(total_usage["total_tokens"], 450)
        self.assertEqual(total_usage["task_count"], 2)

        # Reset specific task
        self.tracker.reset_usage("review")
        total_usage = self.tracker.get_total_usage()
        self.assertEqual(total_usage["total_tokens"], 300)  # Only bug_finding remains
        self.assertEqual(total_usage["task_count"], 1)

        # Reset all usage
        self.tracker.reset_usage()
        total_usage = self.tracker.get_total_usage()
        self.assertEqual(total_usage["total_tokens"], 0)
        self.assertEqual(total_usage["task_count"], 0)

    def test_nonexistent_task_usage(self):
        """Test querying usage for non-existent task."""
        usage = self.tracker.get_task_usage("nonexistent_task")

        self.assertEqual(usage["task_type"], "nonexistent_task")
        self.assertEqual(usage["total_tokens"], 0)
        self.assertEqual(usage["call_count"], 0)
        self.assertEqual(usage["estimated_cost"], 0.0)

    def test_optimization_insights(self):
        """Test cost optimization insights functionality."""
        # Add high-token usage (>10,000 tokens per call to trigger recommendation)
        for i in range(5):
            self.tracker.update_usage("review", "gemini-2.5-pro", 7000, 5000, 12000)

        insights = self.tracker.get_cost_optimization_insights()

        self.assertIn("total_cost", insights)
        self.assertIn("recommendations", insights)
        self.assertGreater(insights["total_cost"], 0)

        # Should have high token usage recommendation
        recommendations = insights["recommendations"]
        self.assertTrue(any("high_token_usage" in rec.get("type", "") for rec in recommendations))

    def test_export_functionality(self):
        """Test usage data export functionality."""
        # Add some usage
        self.tracker.update_usage("review", "gemini-1.5-flash", 500, 250, 750)

        export_data = self.tracker.export_usage_data()

        self.assertIn("export_timestamp", export_data)
        self.assertIn("session_start", export_data)
        self.assertIn("usage_data", export_data)
        self.assertIn("optimization_insights", export_data)

        # Verify usage data is included
        usage_data = export_data["usage_data"]
        self.assertIn("summary", usage_data)
        self.assertIn("by_task", usage_data)
        self.assertEqual(usage_data["summary"]["total_tokens"], 750)


if __name__ == "__main__":
    unittest.main()
