# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Integration tests for review_code and find_bugs tools working together.

This test suite validates that both tools can work together seamlessly,
sharing components correctly and tracking usage across different analysis types.
Tests the complete integration without requiring actual API calls.

Testing approach:
- Real integration tests with actual files and data
- External service boundaries handled appropriately
- See TESTING_STRATEGY.md for detailed guidelines
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Import the components to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bug_finding_analyzer import BugFindingAnalyzer
from review_code_analyzer import ReviewCodeAnalyzer
from usage_tracker import UsageTracker


class TestIntegrationReviewAndBugs(unittest.TestCase):
    """Test integration between review_code and find_bugs tools."""

    def setUp(self):
        """Set up test fixtures."""
        # Shared usage tracker for both tools
        self.usage_tracker = UsageTracker()

        # Initialize both analyzers with shared tracker
        self.bug_analyzer = BugFindingAnalyzer(usage_tracker=self.usage_tracker)
        self.review_analyzer = ReviewCodeAnalyzer(usage_tracker=self.usage_tracker)

        # Create temporary directory with sample code
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = self._create_sample_codebase()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_sample_codebase(self):
        """Create a realistic sample codebase for testing both tools."""
        # Main application file with various issues
        app_py = Path(self.temp_dir) / "app.py"
        app_py.write_text(
            '''
"""Main application module with some issues."""

import sqlite3
import subprocess
import logging

# Global configuration
DATABASE_URL = "sqlite:///app.db"
DEBUG_MODE = True

class UserManager:
    """Manages user operations with some security issues."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_pool = []

    def authenticate_user(self, username, password):
        """Authenticate user - has SQL injection vulnerability."""
        conn = sqlite3.connect('users.db')

        # SECURITY ISSUE: SQL injection vulnerability
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

        try:
            result = conn.execute(query).fetchone()
            return result is not None
        except Exception as e:
            # ISSUE: Poor error handling - logs sensitive data
            self.logger.error(f"Auth failed for {username}:{password} - {e}")
            return False
        finally:
            # MEMORY ISSUE: Connection not always closed
            if conn:
                conn.close()

    def execute_admin_command(self, command):
        """Execute admin command - has command injection."""
        if not self._is_admin():
            return "Access denied"

        # SECURITY ISSUE: Command injection vulnerability
        result = subprocess.run(f"admin_tool {command}",
                              shell=True, capture_output=True, text=True)
        return result.stdout

    def _is_admin(self):
        """Check admin status - placeholder implementation."""
        return True  # LOGIC ISSUE: Always returns True

    def get_user_data(self, user_ids):
        """Get user data - has performance issues."""
        results = []

        # PERFORMANCE ISSUE: N+1 query problem
        for user_id in user_ids:
            conn = sqlite3.connect('users.db')
            query = "SELECT * FROM users WHERE id = ?"
            result = conn.execute(query, (user_id,)).fetchone()
            results.append(result)
            # MEMORY ISSUE: Connection not closed in loop

        return results

    def process_user_files(self, file_paths):
        """Process user files - resource leak."""
        processed_files = []

        for path in file_paths:
            try:
                # API USAGE ISSUE: File not closed in exception path
                file_handle = open(path, 'r')
                content = file_handle.read()
                processed_files.append(content)
                file_handle.close()
            except IOError:
                # File remains open if exception occurs
                continue

        return processed_files
'''
        )

        # Utility module with concurrency issues
        utils_py = Path(self.temp_dir) / "utils.py"
        utils_py.write_text(
            '''
"""Utility functions with concurrency and logic issues."""

import threading
import time

# Global shared state
counter = 0
user_cache = {}

def increment_counter():
    """Increment global counter - race condition."""
    global counter

    # CONCURRENCY ISSUE: Race condition - not thread safe
    temp = counter
    time.sleep(0.001)  # Simulate work
    counter = temp + 1

def find_maximum(numbers):
    """Find maximum in list - off-by-one error."""
    if not numbers:
        return None

    max_val = numbers[0]
    # LOGIC ISSUE: Off-by-one error - misses last element
    for i in range(0, len(numbers) - 1):
        if numbers[i] > max_val:
            max_val = numbers[i]

    return max_val

def cache_user_data(user_id, data):
    """Cache user data - memory leak."""
    # MEMORY ISSUE: Unbounded cache growth
    user_cache[user_id] = data
    # No cache cleanup or size limits

def binary_search(arr, target):
    """Binary search with infinite loop potential."""
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            # LOGIC ISSUE: Should be mid + 1, can cause infinite loop
            left = mid
        else:
            right = mid - 1

    return -1

class ThreadUnsafeCounter:
    """Counter class with thread safety issues."""

    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        """Increment counter - missing synchronization."""
        # CONCURRENCY ISSUE: Should use lock but doesn't
        self.value += 1

    def decrement(self):
        """Decrement counter - partial synchronization."""
        with self.lock:
            self.value -= 1
        # Inconsistent lock usage between increment/decrement
'''
        )

        # Configuration file
        config_py = Path(self.temp_dir) / "config.py"
        config_py.write_text(
            '''
"""Configuration settings with security issues."""

import os

# SECURITY ISSUE: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_SECRET_KEY = "super_secret_key_123"

# SECURITY ISSUE: Debug mode in production
DEBUG = True
TESTING = False

# SECURITY ISSUE: Overly permissive settings
CORS_ORIGINS = ["*"]  # Allows all origins
SSL_VERIFY = False    # Disables SSL verification

def get_database_url():
    """Get database URL - insecure defaults."""
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    # SECURITY ISSUE: Default to root user
    password = os.getenv("DB_PASSWORD", DATABASE_PASSWORD)

    return f"mysql://{user}:{password}@{host}/app"

def setup_logging():
    """Setup logging - information disclosure."""
    import logging

    # SECURITY ISSUE: Debug logging includes sensitive data
    logging.basicConfig(
        level=logging.DEBUG if DEBUG else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # SECURITY ISSUE: Log to file without rotation
    handler = logging.FileHandler('/tmp/app.log')
    logging.getLogger().addHandler(handler)
'''
        )

        # Project documentation
        readme_md = Path(self.temp_dir) / "README.md"
        readme_md.write_text(
            """
# Sample Application

This is a sample application for testing code review and bug detection tools.

## Features

- User authentication and management
- Admin command execution
- File processing capabilities
- Caching and utilities

## Security Notes

This application intentionally contains various security vulnerabilities,
performance issues, and logic errors for testing purposes.

## Usage

```python
from app import UserManager

manager = UserManager()
user_authenticated = manager.authenticate_user("admin", "password")
```

## Known Issues

- SQL injection vulnerabilities in authentication
- Command injection in admin functions
- Memory leaks in caching
- Race conditions in threading code
- Performance issues with database queries
"""
        )

        # CLAUDE.md project context
        claude_md = Path(self.temp_dir) / "CLAUDE.md"
        claude_md.write_text(
            """
# Project Rules

## Security Requirements
- Use parameterized queries for all database operations
- Validate and sanitize all user inputs
- Never log sensitive information like passwords
- Use proper authentication and authorization

## Performance Guidelines
- Avoid N+1 query problems
- Implement proper connection pooling
- Use appropriate data structures and algorithms
- Cache frequently accessed data with size limits

## Code Quality Standards
- Handle all exceptions appropriately
- Close all resources (files, connections, etc.)
- Use thread-safe operations in concurrent code
- Validate all inputs and handle edge cases

## Testing Requirements
- Write comprehensive unit tests
- Test error conditions and edge cases
- Verify security controls work correctly
- Performance test with realistic data volumes
"""
        )

        return {
            str(app_py): app_py.read_text(),
            str(utils_py): utils_py.read_text(),
            str(config_py): config_py.read_text(),
            str(readme_md): readme_md.read_text(),
            str(claude_md): claude_md.read_text(),
        }

    def test_shared_usage_tracker_integration(self):
        """Test that both tools share usage tracking correctly."""
        # Verify both analyzers share the same tracker
        self.assertIs(self.bug_analyzer.usage_tracker, self.usage_tracker)
        self.assertIs(self.review_analyzer.usage_tracker, self.usage_tracker)

        # Verify initial state
        initial_usage = self.usage_tracker.get_total_usage()
        self.assertEqual(initial_usage["total_tokens"], 0)
        self.assertEqual(initial_usage["call_count"], 0)

        # Simulate usage by both tools
        self.usage_tracker.update_usage(
            "find_bugs", "gemini-2.5-pro", input_tokens=1000, output_tokens=500, total_tokens=1500
        )

        self.usage_tracker.update_usage(
            "review_code", "gemini-1.5-flash", input_tokens=800, output_tokens=300, total_tokens=1100
        )

        # Verify combined tracking
        total_usage = self.usage_tracker.get_total_usage()
        self.assertEqual(total_usage["total_tokens"], 2600)
        self.assertEqual(total_usage["call_count"], 2)

        # Verify detailed reporting includes both tools
        detailed_report = self.usage_tracker.get_detailed_report()
        self.assertIn("find_bugs", detailed_report["by_task"])
        self.assertIn("review_code", detailed_report["by_task"])

        # Verify cost optimization insights
        insights = self.usage_tracker.get_cost_optimization_insights()
        self.assertIn("total_cost", insights)
        self.assertIn("recommendations", insights)

    def test_both_tools_parameter_validation(self):
        """Test parameter validation works for both tools."""
        # Test find_bugs parameter validation
        bug_args = {
            "directory": self.temp_dir,
            "bug_categories": ["security", "memory"],
            "severity_filter": ["critical", "high"],
            "include_suggestions": True,
        }

        is_valid, error = self.bug_analyzer.validate_parameters(bug_args)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Test review_code parameter validation
        review_args = {
            "directory": self.temp_dir,
            "focus_areas": ["security", "performance"],
            "model": "gemini-1.5-flash",
            "max_file_size": 1048576,
        }

        is_valid, error = self.review_analyzer.validate_parameters(review_args)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Test invalid parameters for both tools
        invalid_args = {"directory": "/nonexistent/path"}

        is_valid, error = self.bug_analyzer.validate_parameters(invalid_args)
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)

        is_valid, error = self.review_analyzer.validate_parameters(invalid_args)
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)

    def test_shared_file_collection_consistency(self):
        """Test that both tools collect files consistently."""
        max_file_size = 1048576

        # Collect files using bug analyzer
        bug_files, bug_tree = self.bug_analyzer.collect_files(self.temp_dir, max_file_size)

        # Collect files using review analyzer
        review_files, review_tree = self.review_analyzer.collect_files(self.temp_dir, max_file_size)

        # Files should be identical
        self.assertEqual(set(bug_files.keys()), set(review_files.keys()))
        self.assertEqual(bug_tree, review_tree)

        # Content should be identical
        for file_path in bug_files:
            self.assertEqual(bug_files[file_path], review_files[file_path])

        # Should collect expected files
        expected_files = ["app.py", "utils.py", "config.py", "README.md", "CLAUDE.md"]
        for expected in expected_files:
            found = any(file_path.endswith(expected) for file_path in bug_files)
            self.assertTrue(found, f"Expected file {expected} not found")

    def test_tool_schema_differences(self):
        """Test that tools have correct distinct schemas while sharing base."""
        # Get complete schemas for both tools
        bug_schema = self.bug_analyzer.get_complete_tool_schema()
        review_schema = self.review_analyzer.get_complete_tool_schema()

        # Both should have base parameters
        base_params = ["directory", "focus_areas", "model", "max_file_size"]
        for param in base_params:
            self.assertIn(param, bug_schema["properties"])
            self.assertIn(param, review_schema["properties"])

        # Bug tool should have bug-specific parameters
        bug_specific = ["severity_filter", "bug_categories", "include_suggestions"]
        for param in bug_specific:
            self.assertIn(param, bug_schema["properties"])
            self.assertNotIn(param, review_schema["properties"])

        # Review tool should NOT have bug-specific parameters
        for param in bug_specific:
            self.assertNotIn(param, review_schema["properties"])

        # Both should require directory
        self.assertIn("directory", bug_schema["required"])
        self.assertIn("directory", review_schema["required"])

    def test_prompt_generation_differences(self):
        """Test that tools generate different prompts for same codebase."""
        files = {
            "test.py": "def vulnerable_function(): pass",
            "CLAUDE.md": "# Security rules\n- Use secure coding practices",
        }
        file_tree = "test.py\nCLAUDE.md"
        focus_areas = ["security"]
        claude_md_path = "CLAUDE.md"

        # Generate bug finding prompt
        self.bug_analyzer._current_bug_categories = ["security"]
        self.bug_analyzer._current_severity_filter = ["critical"]
        self.bug_analyzer._current_include_suggestions = True

        try:
            bug_prompt = self.bug_analyzer.format_analysis_prompt(files, file_tree, focus_areas, claude_md_path)
        finally:
            self._cleanup_analyzer_attributes(self.bug_analyzer)

        # Generate review prompt
        review_prompt = self.review_analyzer.format_analysis_prompt(files, file_tree, focus_areas, claude_md_path)

        # Prompts should be different
        self.assertNotEqual(bug_prompt, review_prompt)

        # Bug prompt should contain bug-specific content
        self.assertIn("Bug Finding Analysis Request", bug_prompt)
        self.assertIn("security engineer and code auditor", bug_prompt)
        self.assertIn("SQL injection", bug_prompt)
        self.assertIn("BUG-001", bug_prompt)

        # Review prompt should contain review-specific content
        self.assertIn("You are an expert code reviewer", review_prompt)
        self.assertIn("Architecture & Design", review_prompt)
        self.assertIn("code quality", review_prompt)

        # Both should include project context
        self.assertIn("Security rules", bug_prompt)
        self.assertIn("Security rules", review_prompt)

    def test_response_formatting_differences(self):
        """Test that tools format responses differently."""
        from base_code_analyzer import AnalysisResult

        # Create test result
        test_result = AnalysisResult(
            content="Sample analysis content",
            usage_stats={"total_tokens": 1500, "input_tokens": 1000, "output_tokens": 500, "estimated_cost": 0.003},
            collection_stats={"files_collected": 3, "total_size": 1024},
            directory=self.temp_dir,
            model="gemini-2.5-pro",
            focus_areas=["security", "performance"],
        )

        # Format responses with both tools
        bug_response = self.bug_analyzer.format_analysis_response(test_result)
        review_response = self.review_analyzer.format_analysis_response(test_result)

        # Responses should be different
        self.assertNotEqual(bug_response, review_response)

        # Bug response should have bug-specific formatting
        self.assertIn("# Bug Analysis Report", bug_response)
        self.assertIn("## Bug Findings Summary", bug_response)
        self.assertIn("Total Bugs Found", bug_response)

        # Review response should have review-specific formatting
        self.assertIn("# Code Review Report", review_response)
        self.assertIn("## Summary", review_response)

        # Both should include usage statistics
        self.assertIn("## Usage Statistics", bug_response)
        self.assertIn("## Usage Statistics", review_response)
        self.assertIn("Total Tokens**: 1,500", bug_response)
        self.assertIn("Total Tokens**: 1,500", review_response)

    def test_gemini_client_task_awareness(self):
        """Test that GeminiClient is task-aware for both tools."""
        # Test that GeminiClient can differentiate between tasks
        from gemini_client import GeminiClient

        gemini_client = GeminiClient(usage_tracker=self.usage_tracker)

        # Verify task type detection works
        bug_tool_name, _, _ = self.bug_analyzer.get_tool_info()
        review_tool_name, _, _ = self.review_analyzer.get_tool_info()

        self.assertEqual(bug_tool_name, "find_bugs")
        self.assertEqual(review_tool_name, "review_code")

        # Test that client would track different task types
        # (We can't actually make API calls, but we can test the interface)
        self.assertTrue(hasattr(gemini_client, "analyze_code"))
        self.assertTrue(hasattr(gemini_client, "usage_tracker"))

    def test_concurrent_usage_scenario(self):
        """Test scenario where both tools might be used concurrently."""
        # Simulate concurrent usage patterns

        # Tool 1: Bug analysis session
        bug_args = {
            "directory": self.temp_dir,
            "bug_categories": ["security", "memory"],
            "severity_filter": ["critical", "high"],
        }

        is_valid, error = self.bug_analyzer.validate_parameters(bug_args)
        self.assertTrue(is_valid)

        # Tool 2: Review analysis session
        review_args = {
            "directory": self.temp_dir,
            "focus_areas": ["performance", "maintainability"],
            "model": "gemini-1.5-flash",
        }

        is_valid, error = self.review_analyzer.validate_parameters(review_args)
        self.assertTrue(is_valid)

        # Both tools should collect files independently
        bug_files, _ = self.bug_analyzer.collect_files(self.temp_dir, 1048576)
        review_files, _ = self.review_analyzer.collect_files(self.temp_dir, 1048576)

        # Results should be consistent
        self.assertEqual(bug_files, review_files)

        # Simulate usage tracking from both tools
        self.usage_tracker.update_usage("find_bugs", "gemini-2.5-pro", 1200, 600, 1800)
        self.usage_tracker.update_usage("review_code", "gemini-1.5-flash", 900, 400, 1300)

        # Verify combined tracking
        total = self.usage_tracker.get_total_usage()
        self.assertEqual(total["total_tokens"], 3100)
        self.assertEqual(total["call_count"], 2)

    def test_error_handling_consistency(self):
        """Test that both tools handle errors consistently."""
        # Test with invalid directory
        invalid_args = {"directory": "/definitely/nonexistent/path"}

        # Both tools should fail validation consistently
        bug_valid, bug_error = self.bug_analyzer.validate_parameters(invalid_args)
        review_valid, review_error = self.review_analyzer.validate_parameters(invalid_args)

        self.assertFalse(bug_valid)
        self.assertFalse(review_valid)
        self.assertIn("does not exist", bug_error)
        self.assertIn("does not exist", review_error)

        # Test with file instead of directory
        test_file = Path(self.temp_dir) / "not_a_directory.txt"
        test_file.write_text("test content")

        file_args = {"directory": str(test_file)}

        bug_valid, bug_error = self.bug_analyzer.validate_parameters(file_args)
        review_valid, review_error = self.review_analyzer.validate_parameters(file_args)

        self.assertFalse(bug_valid)
        self.assertFalse(review_valid)
        self.assertIn("not a directory", bug_error)
        self.assertIn("not a directory", review_error)

    def test_performance_baseline_comparison(self):
        """Test that both tools have similar performance characteristics."""
        import time

        # Measure file collection performance for both tools
        start_time = time.time()
        bug_files, bug_tree = self.bug_analyzer.collect_files(self.temp_dir, 1048576)
        bug_time = time.time() - start_time

        start_time = time.time()
        review_files, review_tree = self.review_analyzer.collect_files(self.temp_dir, 1048576)
        review_time = time.time() - start_time

        # Performance should be similar (within reasonable bounds)
        self.assertLess(abs(bug_time - review_time), 0.1)  # Within 100ms

        # Results should be identical
        self.assertEqual(bug_files, review_files)
        self.assertEqual(bug_tree, review_tree)

        # Measure parameter validation performance
        valid_args = {"directory": self.temp_dir}

        start_time = time.time()
        self.bug_analyzer.validate_parameters(valid_args)
        bug_validation_time = time.time() - start_time

        start_time = time.time()
        self.review_analyzer.validate_parameters(valid_args)
        review_validation_time = time.time() - start_time

        # Validation should be fast for both
        self.assertLess(bug_validation_time, 0.01)  # Less than 10ms
        self.assertLess(review_validation_time, 0.01)  # Less than 10ms

    def _cleanup_analyzer_attributes(self, analyzer):
        """Helper method to clean up temporary analyzer attributes."""
        attrs_to_clean = ["_current_bug_categories", "_current_severity_filter", "_current_include_suggestions"]

        for attr in attrs_to_clean:
            if hasattr(analyzer, attr):
                delattr(analyzer, attr)


if __name__ == "__main__":
    unittest.main()
