# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Tests for BugFormatter functionality.

Validates the bug-specific prompt generation functionality to ensure
proper security vulnerability detection and comprehensive bug analysis prompts.

Testing approach:
- Real integration tests with actual files and data
- External service boundaries handled appropriately
- See TESTING_STRATEGY.md for detailed guidelines
"""

import os
import sys
import unittest

# Import the component to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bug_formatter import BugFormatter


class TestBugFormatter(unittest.TestCase):
    """Test BugFormatter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = BugFormatter()

        # Sample test files
        self.test_files = {
            "app.py": """
import sqlite3
def get_user(user_id):
    conn = sqlite3.connect('db.sqlite')
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()
""",
            "api.py": """
def login(username, password):
    if username == "admin" and password == "password123":
        return {"token": "admin_token"}
    return None
""",
            "CLAUDE.md": """
# Project Rules
- Use parameterized queries
- Validate all user inputs
- Use secure authentication
""",
        }

        self.test_file_tree = """
project/
├── app.py
├── api.py
└── CLAUDE.md
"""

    def test_basic_security_prompt_generation(self):
        """Test basic security-focused prompt generation."""
        prompt = self.formatter.format_bug_finding_request(
            files=self.test_files,
            file_tree=self.test_file_tree,
            bug_categories=["security"],
            focus_areas=["authentication", "input_validation"],
            claude_md_path="CLAUDE.md",
        )

        # Verify key sections are present
        self.assertIn("Bug Finding Analysis Request", prompt)
        self.assertIn("security engineer and code auditor", prompt)
        self.assertIn("SQL injection", prompt)
        self.assertIn("authentication", prompt)
        self.assertIn("input_validation", prompt)

        # Verify project context is included
        self.assertIn("Project Context (from CLAUDE.md)", prompt)
        self.assertIn("Use parameterized queries", prompt)

        # Verify file contents are included
        self.assertIn("app.py", prompt)
        self.assertIn("SELECT * FROM users", prompt)
        self.assertIn("api.py", prompt)
        self.assertIn("admin_token", prompt)

    def test_multiple_bug_categories(self):
        """Test prompt generation with multiple bug categories."""
        prompt = self.formatter.format_bug_finding_request(
            files=self.test_files,
            file_tree=self.test_file_tree,
            bug_categories=["security", "memory", "logic"],
            focus_areas=[],
            claude_md_path=None,
        )

        # Verify all requested categories are included
        self.assertIn("Security Issues", prompt)
        self.assertIn("Memory Issues", prompt)
        self.assertIn("Logic Issues", prompt)

        # Verify specific instructions for each category
        self.assertIn("SQL injection", prompt)
        self.assertIn("**Memory Leaks:**", prompt)
        self.assertIn("Off-by-one errors", prompt)

    def test_severity_filtering(self):
        """Test severity filtering in prompt generation."""
        prompt = self.formatter.format_bug_finding_request(
            files=self.test_files,
            file_tree=self.test_file_tree,
            bug_categories=["security"],
            focus_areas=[],
            claude_md_path=None,
            severity_filter=["critical", "high"],
        )

        # Verify severity filtering instructions
        self.assertIn("ONLY report bugs with these severity levels: critical, high", prompt)
        self.assertIn("Critical**: Security vulnerabilities", prompt)
        self.assertIn("High**: Correctness issues", prompt)

    def test_suggestions_inclusion_control(self):
        """Test controlling fix suggestions inclusion."""
        # Test with suggestions enabled (default)
        prompt_with_suggestions = self.formatter.format_bug_finding_request(
            files=self.test_files,
            file_tree=self.test_file_tree,
            bug_categories=["security"],
            focus_areas=[],
            claude_md_path=None,
            include_suggestions=True,
        )

        self.assertIn("Fix Suggestion", prompt_with_suggestions)
        self.assertIn("Recommended fix", prompt_with_suggestions)

        # Test with suggestions disabled
        prompt_without_suggestions = self.formatter.format_bug_finding_request(
            files=self.test_files,
            file_tree=self.test_file_tree,
            bug_categories=["security"],
            focus_areas=[],
            claude_md_path=None,
            include_suggestions=False,
        )

        self.assertNotIn("Fix Suggestion", prompt_without_suggestions)
        self.assertNotIn("Recommended fix", prompt_without_suggestions)

    def test_security_instructions_comprehensive(self):
        """Test that security instructions are comprehensive."""
        formatter = BugFormatter()
        security_instructions = formatter._get_security_instructions()

        # Verify key security categories are covered
        self.assertIn("SQL injection", security_instructions)
        self.assertIn("XSS vulnerabilities", security_instructions)
        self.assertIn("Command injection", security_instructions)
        self.assertIn("Authentication", security_instructions)
        self.assertIn("Authorization", security_instructions)
        self.assertIn("Cryptographic", security_instructions)
        self.assertIn("hardcoded", security_instructions.lower())
        self.assertIn("eval()", security_instructions)
        self.assertIn("os.system()", security_instructions)

    def test_memory_instructions_comprehensive(self):
        """Test that memory instructions cover key issues."""
        formatter = BugFormatter()
        memory_instructions = formatter._get_memory_instructions()

        # Verify key memory categories are covered
        self.assertIn("**Memory Leaks:**", memory_instructions)
        self.assertIn("Buffer overflow", memory_instructions)
        self.assertIn("Null pointer", memory_instructions)
        self.assertIn("Use-after-free", memory_instructions)
        self.assertIn("Resource", memory_instructions)
        self.assertIn("not properly closed", memory_instructions)

    def test_logic_instructions_comprehensive(self):
        """Test that logic instructions cover key error types."""
        formatter = BugFormatter()
        logic_instructions = formatter._get_logic_instructions()

        # Verify key logic error categories are covered
        self.assertIn("Off-by-one", logic_instructions)
        self.assertIn("boolean logic", logic_instructions)
        self.assertIn("Infinite loops", logic_instructions)
        self.assertIn("Race conditions", logic_instructions)
        self.assertIn("Division by zero", logic_instructions)

    def test_performance_instructions_comprehensive(self):
        """Test that performance instructions cover key issues."""
        formatter = BugFormatter()
        performance_instructions = formatter._get_performance_instructions()

        # Verify key performance categories are covered
        self.assertIn("Algorithmic", performance_instructions)
        self.assertIn("O(n²)", performance_instructions)
        self.assertIn("Memory waste", performance_instructions)
        self.assertIn("I/O Performance", performance_instructions)
        self.assertIn("N+1 problems", performance_instructions)

    def test_concurrency_instructions_comprehensive(self):
        """Test that concurrency instructions cover key issues."""
        formatter = BugFormatter()
        concurrency_instructions = formatter._get_concurrency_instructions()

        # Verify key concurrency categories are covered
        self.assertIn("**Race Conditions:**", concurrency_instructions)
        self.assertIn("Deadlocks", concurrency_instructions)
        self.assertIn("**Thread Safety:**", concurrency_instructions)
        self.assertIn("synchronization", concurrency_instructions)
        self.assertIn("**Async/Await Issues:**", concurrency_instructions)

    def test_api_usage_instructions_comprehensive(self):
        """Test that API usage instructions cover key issues."""
        formatter = BugFormatter()
        api_instructions = formatter._get_api_usage_instructions()

        # Verify key API usage categories are covered
        self.assertIn("Deprecated", api_instructions)
        self.assertIn("Resource Management", api_instructions)
        self.assertIn("Error Handling", api_instructions)
        self.assertIn("not properly closed", api_instructions)
        self.assertIn("timeout handling", api_instructions)

    def test_file_language_detection(self):
        """Test programming language detection for different file types."""
        formatter = BugFormatter()

        # Test common programming languages
        self.assertEqual(formatter._get_file_language("app.py"), "python")
        self.assertEqual(formatter._get_file_language("script.js"), "javascript")
        self.assertEqual(formatter._get_file_language("main.java"), "java")
        self.assertEqual(formatter._get_file_language("program.c"), "c")
        self.assertEqual(formatter._get_file_language("program.cpp"), "cpp")
        self.assertEqual(formatter._get_file_language("service.go"), "go")
        self.assertEqual(formatter._get_file_language("app.rs"), "rust")

        # Test config and data files
        self.assertEqual(formatter._get_file_language("config.yaml"), "yaml")
        self.assertEqual(formatter._get_file_language("data.json"), "json")
        self.assertEqual(formatter._get_file_language("query.sql"), "sql")

        # Test unknown file type
        self.assertEqual(formatter._get_file_language("unknown.xyz"), "text")

    def test_output_format_instructions(self):
        """Test that output format instructions are clear and complete."""
        prompt = self.formatter.format_bug_finding_request(
            files=self.test_files,
            file_tree=self.test_file_tree,
            bug_categories=["security"],
            focus_areas=[],
            claude_md_path=None,
        )

        # Verify output format requirements
        self.assertIn("Output Format", prompt)
        self.assertIn("Bug ID", prompt)
        self.assertIn("Category", prompt)
        self.assertIn("Severity", prompt)
        self.assertIn("Confidence", prompt)
        self.assertIn("BUG-001", prompt)  # Example format

        # Verify example output is provided
        self.assertIn("Example Markdown Format", prompt)
        self.assertIn("SQL Injection Vulnerability", prompt)

    def test_empty_files_handling(self):
        """Test handling of empty file dictionary."""
        prompt = self.formatter.format_bug_finding_request(
            files={}, file_tree="empty/", bug_categories=["security"], focus_areas=[], claude_md_path=None
        )

        # Should still generate a valid prompt
        self.assertIn("Bug Finding Analysis Request", prompt)
        self.assertIn("security", prompt)
        self.assertIn("empty/", prompt)

    def test_all_categories_default(self):
        """Test that all categories are included when none specified."""
        prompt = self.formatter.format_bug_finding_request(
            files=self.test_files,
            file_tree=self.test_file_tree,
            bug_categories=[],  # Empty list should default to all
            focus_areas=[],
            claude_md_path=None,
        )

        # Verify all default categories are included
        self.assertIn("Security Issues", prompt)
        self.assertIn("Memory Issues", prompt)
        self.assertIn("Logic Issues", prompt)
        self.assertIn("Performance Issues", prompt)
        self.assertIn("Concurrency Issues", prompt)
        self.assertIn("Api_Usage Issues", prompt)


if __name__ == "__main__":
    unittest.main()
