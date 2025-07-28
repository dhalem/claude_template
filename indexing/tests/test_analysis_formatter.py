# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Tests for AnalysisFormatter class."""

import os
import sys
import unittest

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), "src")
sys.path.insert(0, src_dir)

from analysis_formatter import AnalysisFormatter


class TestAnalysisFormatter(unittest.TestCase):
    """Test cases for AnalysisFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = AnalysisFormatter()
        self.sample_files = {
            "test.py": "def calculate(a, b):\n    return a + b\n",
            "utils.js": "function formatDate(date) {\n    return date.toISOString();\n}",
            "CLAUDE.md": "# Test Project\n\nThis is a test project for analysis.\n",
        }
        self.custom_prompt = "Analyze these files for code quality and suggest improvements."

    def test_format_analysis_request(self):
        """Test formatting of analysis request with custom prompt."""
        result = self.formatter.format_analysis_request(files=self.sample_files, custom_prompt=self.custom_prompt)

        # Check that the result contains all expected sections
        self.assertIn("You are an expert code analyst", result)
        self.assertIn("**Project Context:**", result)
        self.assertIn("**Codebase Structure:**", result)
        self.assertIn("**Code Files:**", result)
        self.assertIn("**Custom Analysis Instructions:**", result)

        # Check that custom prompt is included
        self.assertIn(self.custom_prompt, result)

        # Check that CLAUDE.md content is included
        self.assertIn("This is a test project for analysis", result)

        # Check that file contents are included
        self.assertIn("def calculate(a, b):", result)
        self.assertIn("function formatDate(date)", result)

        # Check that appropriate language tags are used
        self.assertIn("```python", result)
        self.assertIn("```javascript", result)

    def test_format_analysis_request_with_custom_file_tree(self):
        """Test analysis formatting with custom file tree."""
        custom_tree = "src/\n  test.py\n  utils.js"
        result = self.formatter.format_analysis_request(
            files=self.sample_files, custom_prompt=self.custom_prompt, file_tree=custom_tree
        )

        # Should use provided file tree
        self.assertIn("src/", result)
        self.assertIn("test.py", result)
        self.assertIn("utils.js", result)

    def test_format_analysis_request_without_claude_md(self):
        """Test analysis formatting when CLAUDE.md is not present."""
        files_without_claude = {"test.py": "def hello():\n    print('Hello')\n", "config.json": '{"debug": true}\n'}

        result = self.formatter.format_analysis_request(files=files_without_claude, custom_prompt=self.custom_prompt)

        # Should include default CLAUDE.md message
        self.assertIn("No CLAUDE.md file found in the provided files", result)

        # Should still include files and custom prompt
        self.assertIn(self.custom_prompt, result)
        self.assertIn("def hello():", result)

    def test_format_analysis_request_empty_files(self):
        """Test analysis formatting with empty files dictionary."""
        result = self.formatter.format_analysis_request(files={}, custom_prompt=self.custom_prompt)

        # Should handle empty files gracefully
        self.assertIn("You are an expert code analyst", result)
        self.assertIn(self.custom_prompt, result)
        self.assertIn("No files provided", result)

    def test_build_analysis_prompt(self):
        """Test building of analysis prompt with all components."""
        claude_md = "# Test Project\n\nProject guidelines here."
        file_tree = "```\ntest.py\nutils.js\n```"
        code_files = "## File: test.py\n\n```python\nprint('test')\n```"
        custom_prompt = "Find security vulnerabilities"

        result = self.formatter._build_analysis_prompt(
            claude_md=claude_md, file_tree=file_tree, code_files=code_files, custom_prompt=custom_prompt
        )

        # Check all components are included
        self.assertIn("You are an expert code analyst", result)
        self.assertIn(claude_md, result)
        self.assertIn(file_tree, result)
        self.assertIn(code_files, result)
        self.assertIn(custom_prompt, result)

        # Check structure
        self.assertIn("**Project Context:**", result)
        self.assertIn("**Codebase Structure:**", result)
        self.assertIn("**Code Files:**", result)
        self.assertIn("**Custom Analysis Instructions:**", result)

    def test_format_simple_analysis(self):
        """Test simple analysis formatting for single content."""
        content = "def vulnerable_function(user_input):\n    eval(user_input)  # Dangerous!"
        prompt = "Check for security vulnerabilities"

        result = self.formatter.format_simple_analysis(content, prompt)

        # Check structure
        self.assertIn("You are an expert code analyst", result)
        self.assertIn("**Code to Analyze:**", result)
        self.assertIn("**Analysis Instructions:**", result)

        # Check content
        self.assertIn(content, result)
        self.assertIn(prompt, result)
        self.assertIn("def vulnerable_function", result)

    def test_format_simple_analysis_multiline_prompt(self):
        """Test simple analysis with multiline prompt."""
        content = "class Calculator:\n    def add(self, a, b):\n        return a + b"
        prompt = """Analyze this code for:
1. Code quality
2. Performance issues
3. Best practices
4. Documentation needs"""

        result = self.formatter.format_simple_analysis(content, prompt)

        # Multi-line prompt should be preserved
        self.assertIn("1. Code quality", result)
        self.assertIn("2. Performance issues", result)
        self.assertIn("3. Best practices", result)
        self.assertIn("4. Documentation needs", result)

    def test_inheritance_from_base_formatter(self):
        """Test that AnalysisFormatter properly inherits from BaseFormatter."""
        # Should have access to base formatter methods
        self.assertTrue(hasattr(self.formatter, "_format_file_tree"))
        self.assertTrue(hasattr(self.formatter, "_format_code_files"))
        self.assertTrue(hasattr(self.formatter, "_get_language_from_extension"))
        self.assertTrue(hasattr(self.formatter, "format_base_context"))

        # Test that inherited methods work
        file_tree = "test.py\nutils.js"
        result = self.formatter._format_file_tree(file_tree)
        self.assertIn("```", result)
        self.assertIn("test.py", result)

    def test_integration_with_base_context(self):
        """Test that AnalysisFormatter integrates properly with base context."""
        # This tests the integration between AnalysisFormatter and BaseFormatter
        result = self.formatter.format_analysis_request(files=self.sample_files, custom_prompt=self.custom_prompt)

        # The analysis request should use base formatter's context generation
        # and include properly formatted components
        self.assertIn("## File: test.py", result)
        self.assertIn("```python", result)
        self.assertIn("```javascript", result)

        # Should include the auto-generated file tree
        self.assertIn("CLAUDE.md", result)  # File should be in tree
        self.assertIn("test.py", result)  # File should be in tree
        self.assertIn("utils.js", result)  # File should be in tree


if __name__ == "__main__":
    unittest.main()
