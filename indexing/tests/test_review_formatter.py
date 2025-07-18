# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for ReviewFormatter class."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from review_formatter import ReviewFormatter


class TestReviewFormatter(unittest.TestCase):
    """Test ReviewFormatter functionality."""

    def setUp(self):
        """Set up test environment."""
        self.formatter = ReviewFormatter()
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_formatter_initialization(self):
        """Test that formatter initializes correctly."""
        self.assertEqual(self.formatter.claude_md_content, "")
        self.assertEqual(self.formatter.file_tree, "")
        self.assertEqual(self.formatter.code_files, "")

    def test_format_file_tree_simple(self):
        """Test formatting a simple file tree."""
        file_tree = """project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
└── README.md"""

        formatted = self.formatter._format_file_tree(file_tree)

        # Should contain the original structure
        self.assertIn("project/", formatted)
        self.assertIn("src/", formatted)
        self.assertIn("main.py", formatted)
        self.assertIn("README.md", formatted)

    def test_format_files_basic(self):
        """Test formatting basic file collection."""
        files = {
            "/project/src/main.py": "def main():\n    print('hello')",
            "/project/README.md": "# Project\n\nThis is a test project.",
            "/project/config.json": '{"name": "test", "version": "1.0"}'
        }

        formatted = self.formatter._format_code_files(files)

        # Should contain file paths and contents
        self.assertIn("main.py", formatted)
        self.assertIn("def main():", formatted)
        self.assertIn("README.md", formatted)
        self.assertIn("# Project", formatted)
        self.assertIn("config.json", formatted)
        self.assertIn('"name": "test"', formatted)

    def test_format_files_empty(self):
        """Test formatting empty file collection."""
        formatted = self.formatter._format_code_files({})
        self.assertEqual(formatted, "")

    def test_load_claude_md_from_path(self):
        """Test loading CLAUDE.md from provided path."""
        claude_content = """# CLAUDE.md - Project Rules

## Rule 1: Always test
## Rule 2: Write clean code
"""

        claude_file = self.test_dir / "CLAUDE.md"
        claude_file.write_text(claude_content)

        self.formatter._load_claude_md(str(claude_file), {})

        self.assertIn("Project Rules", self.formatter.claude_md_content)
        self.assertIn("Always test", self.formatter.claude_md_content)

    def test_load_claude_md_from_files(self):
        """Test loading CLAUDE.md from files dictionary."""
        claude_content = """# CLAUDE.md - From Files

## Important Guidelines
- Follow coding standards
- Write documentation
"""

        files = {
            "/project/src/main.py": "def main(): pass",
            "/project/CLAUDE.md": claude_content,
            "/project/README.md": "# README"
        }

        self.formatter._load_claude_md(None, files)

        self.assertIn("From Files", self.formatter.claude_md_content)
        self.assertIn("Important Guidelines", self.formatter.claude_md_content)

    def test_load_claude_md_not_found(self):
        """Test handling when CLAUDE.md is not found."""
        files = {
            "/project/src/main.py": "def main(): pass",
            "/project/README.md": "# README"
        }

        self.formatter._load_claude_md(None, files)

        # Should contain default message
        self.assertEqual(self.formatter.claude_md_content, "No CLAUDE.md file found in the project.")

    def test_format_focus_areas_single(self):
        """Test formatting single focus area."""
        focus_areas = ["security"]
        formatted = self.formatter._build_focus_areas_prompt(focus_areas)

        self.assertIn("security", formatted.lower())
        self.assertIn("focus", formatted.lower())

    def test_format_focus_areas_multiple(self):
        """Test formatting multiple focus areas."""
        focus_areas = ["performance", "security", "maintainability"]
        formatted = self.formatter._build_focus_areas_prompt(focus_areas)

        for area in focus_areas:
            self.assertIn(area, formatted.lower())

    def test_format_focus_areas_none(self):
        """Test formatting when no focus areas provided."""
        formatted = self.formatter._build_focus_areas_prompt(None)
        self.assertEqual(formatted, "")

        formatted_empty = self.formatter._build_focus_areas_prompt([])
        self.assertEqual(formatted_empty, "")

    def test_format_review_request_complete(self):
        """Test complete review request formatting."""
        files = {
            "/project/src/main.py": """def main():
    '''Main function.'''
    print('Hello, World!')
    return 0""",
            "/project/tests/test_main.py": """import unittest
from main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        self.assertEqual(main(), 0)""",
            "/project/CLAUDE.md": """# Project Guidelines
- Write tests for everything
- Follow PEP 8"""
        }

        file_tree = """project/
├── src/
│   └── main.py
└── tests/
    └── test_main.py"""

        focus_areas = ["testing", "code quality"]

        prompt = self.formatter.format_review_request(
            files=files,
            file_tree=file_tree,
            focus_areas=focus_areas
        )

        # Should contain all major sections
        self.assertIn("code review", prompt.lower())
        self.assertIn("main.py", prompt)
        self.assertIn("test_main.py", prompt)
        self.assertIn("testing", prompt.lower())
        self.assertIn("code quality", prompt.lower())
        self.assertIn("Project Guidelines", prompt)
        self.assertIn("def main():", prompt)

    def test_format_review_request_minimal(self):
        """Test review request with minimal inputs."""
        files = {
            "/simple.py": "print('hello')"
        }

        file_tree = "simple.py"

        prompt = self.formatter.format_review_request(
            files=files,
            file_tree=file_tree
        )

        # Should still generate a valid prompt
        self.assertIn("code review", prompt.lower())
        self.assertIn("simple.py", prompt)
        self.assertIn("print('hello')", prompt)

    def test_format_review_request_no_files(self):
        """Test review request with no files."""
        prompt = self.formatter.format_review_request(
            files={},
            file_tree="empty/"
        )

        # Should handle gracefully
        self.assertIn("review", prompt.lower())
        # The prompt should still be generated even with no files
        self.assertIn("code files:", prompt.lower())

    def test_format_review_request_large_files(self):
        """Test review request handles large file collections."""
        # Create a large number of files
        files = {}
        for i in range(50):
            files[f"/project/file_{i}.py"] = f"def function_{i}():\n    return {i}"

        file_tree = "\n".join([f"file_{i}.py" for i in range(50)])

        prompt = self.formatter.format_review_request(
            files=files,
            file_tree=file_tree
        )

        # Should contain references to the files
        self.assertIn("file_0.py", prompt)
        self.assertIn("function_0", prompt)
        self.assertGreater(len(prompt), 1000)  # Should be substantial

    def test_format_review_request_special_characters(self):
        """Test handling of special characters in files."""
        files = {
            "/project/unicode_test.py": """# -*- coding: utf-8 -*-
def greet(name):
    '''Greet with emojis 🎉'''
    return f"Hello {name}! 👋"

# Test with various Unicode: αβγ, 中文, العربية""",
            "/project/symbols.py": """def calculate():
    # Math symbols: ∑, ∆, π, ∞
    result = 3.14159 * 2
    return result"""
        }

        file_tree = """project/
├── unicode_test.py
└── symbols.py"""

        prompt = self.formatter.format_review_request(
            files=files,
            file_tree=file_tree
        )

        # Should preserve Unicode characters
        self.assertIn("🎉", prompt)
        self.assertIn("👋", prompt)
        self.assertIn("∑", prompt)
        self.assertIn("中文", prompt)

    def test_claude_md_case_insensitive_search(self):
        """Test that CLAUDE.md search is case insensitive."""
        files = {
            "/project/claude.md": "# lowercase claude.md",
            "/project/CLAUDE.MD": "# uppercase CLAUDE.MD",
            "/project/Claude.md": "# mixed case Claude.md"
        }

        # Should find the first matching file
        self.formatter._load_claude_md(None, files)

        # Should have found one of them
        self.assertNotEqual(self.formatter.claude_md_content, "")
        self.assertIn("claude.md", self.formatter.claude_md_content.lower())

    def test_format_files_preserves_indentation(self):
        """Test that file formatting preserves code indentation."""
        files = {
            "/project/indented.py": """class Example:
    def __init__(self):
        self.value = 0

    def method(self):
        if self.value > 0:
            return True
        else:
            return False"""
        }

        formatted = self.formatter._format_code_files(files)

        # Should preserve indentation structure
        lines = formatted.split('\n')
        indented_lines = [line for line in lines if line.startswith('    ')]
        self.assertGreater(len(indented_lines), 0)

        # Check specific indentation levels
        self.assertIn("    def __init__(self):", formatted)
        self.assertIn("        self.value = 0", formatted)
        self.assertIn("            return True", formatted)


if __name__ == '__main__':
    unittest.main()
