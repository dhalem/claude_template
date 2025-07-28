# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Tests for BaseFormatter class."""

import os
import sys
import unittest

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), "src")
sys.path.insert(0, src_dir)

from base_formatter import BaseFormatter


class TestBaseFormatter(unittest.TestCase):
    """Test cases for BaseFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = BaseFormatter()
        self.sample_files = {
            "test.py": "def hello():\n    print('Hello, world!')\n",
            "config.json": '{"key": "value"}\n',
            "README.md": "# Test Project\n\nThis is a test.\n",
            "CLAUDE.md": "# Project Rules\n\nTest project guidelines.\n",
        }

    def test_format_file_tree(self):
        """Test file tree formatting."""
        file_tree = "test.py\nconfig.json\nREADME.md"
        result = self.formatter._format_file_tree(file_tree)

        self.assertIn("```", result)
        self.assertIn("test.py", result)
        self.assertIn("config.json", result)
        self.assertIn("README.md", result)

    def test_get_language_from_extension(self):
        """Test language identification from file extensions."""
        test_cases = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".sh": "bash",
            ".bash": "bash",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".md": "markdown",
            ".rst": "rst",
            ".txt": "text",
            ".unknown": "text",  # Default case
        }

        for extension, expected_language in test_cases.items():
            with self.subTest(extension=extension):
                result = self.formatter._get_language_from_extension(extension)
                self.assertEqual(result, expected_language)

    def test_format_code_files(self):
        """Test code files formatting."""
        result = self.formatter._format_code_files(self.sample_files)

        # Check that all files are included
        for file_path in self.sample_files.keys():
            self.assertIn(f"## File: {file_path}", result)

        # Check that content is included
        self.assertIn("def hello():", result)
        self.assertIn('{"key": "value"}', result)
        self.assertIn("# Test Project", result)

        # Check that appropriate language tags are used
        self.assertIn("```python", result)
        self.assertIn("```json", result)
        self.assertIn("```markdown", result)

    def test_generate_file_tree_from_files(self):
        """Test file tree generation from files dictionary."""
        result = self.formatter._generate_file_tree_from_files(self.sample_files)

        # All files should be listed
        for file_path in self.sample_files.keys():
            self.assertIn(file_path, result)

        # Should be sorted
        lines = result.split("\n")
        file_names = [line.strip() for line in lines if line.strip()]
        self.assertEqual(file_names, sorted(file_names))

    def test_generate_file_tree_empty_files(self):
        """Test file tree generation with empty files dictionary."""
        result = self.formatter._generate_file_tree_from_files({})
        self.assertEqual(result, "No files provided")

    def test_load_claude_md_from_files(self):
        """Test loading CLAUDE.md content from files."""
        # Test with CLAUDE.md present
        result = self.formatter._load_claude_md_from_files(self.sample_files)
        self.assertEqual(result, "# Project Rules\n\nTest project guidelines.\n")

        # Test with different case
        files_with_different_case = {"claude.md": "# Lower case rules\n", "other.py": "print('test')"}
        result = self.formatter._load_claude_md_from_files(files_with_different_case)
        self.assertEqual(result, "# Lower case rules\n")

        # Test without CLAUDE.md
        files_without_claude = {"test.py": "print('test')", "config.json": '{"test": true}'}
        result = self.formatter._load_claude_md_from_files(files_without_claude)
        self.assertEqual(result, "No CLAUDE.md file found in the provided files.")

    def test_format_base_context(self):
        """Test formatting of base context components."""
        result = self.formatter.format_base_context(self.sample_files)

        # Check that all expected keys are present
        expected_keys = ["claude_md", "file_tree", "code_files"]
        for key in expected_keys:
            self.assertIn(key, result)

        # Check CLAUDE.md content
        self.assertEqual(result["claude_md"], "# Project Rules\n\nTest project guidelines.\n")

        # Check file tree formatting
        self.assertIn("```", result["file_tree"])

        # Check code files formatting
        self.assertIn("## File:", result["code_files"])
        self.assertIn("```python", result["code_files"])

    def test_format_base_context_with_custom_file_tree(self):
        """Test format_base_context with custom file tree."""
        custom_tree = "custom/\n  file1.py\n  file2.js"
        result = self.formatter.format_base_context(self.sample_files, file_tree=custom_tree)

        # Should use provided file tree
        self.assertIn("custom/", result["file_tree"])
        self.assertIn("file1.py", result["file_tree"])
        self.assertIn("file2.js", result["file_tree"])

    def test_format_base_context_empty_files(self):
        """Test format_base_context with empty files."""
        result = self.formatter.format_base_context({})

        # Should handle empty files gracefully
        self.assertIn("claude_md", result)
        self.assertIn("file_tree", result)
        self.assertIn("code_files", result)

        # CLAUDE.md should have default message
        self.assertEqual(result["claude_md"], "No CLAUDE.md file found in the provided files.")

        # File tree should indicate no files
        self.assertIn("No files provided", result["file_tree"])


if __name__ == "__main__":
    unittest.main()
