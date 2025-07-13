"""Tests for LintGuard.

REMINDER: Update HOOKS.md when adding new tests!
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardContext  # noqa: E402
from guards.lint_guards import LintGuard  # noqa: E402


class TestLintGuard(unittest.TestCase):
    """Test cases for LintGuard."""

    def setUp(self):
        """Set up test fixtures."""
        self.guard = LintGuard()
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_context(self, tool_name="Edit", file_path=None):
        """Helper to create GuardContext."""
        tool_input = {}
        if file_path:
            tool_input["file_path"] = file_path

        return GuardContext(tool_name=tool_name, tool_input=tool_input, file_path=file_path)

    def create_temp_file(self, filename, content):
        """Create a temporary file with given content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def test_should_trigger_on_edit_operations(self):
        """Should trigger on Edit, Write, and MultiEdit operations."""
        # Create a test file
        file_path = self.create_temp_file("test.py", "print('hello')")

        # Test Edit
        context = self.create_context("Edit", file_path)
        self.assertTrue(self.guard.should_trigger(context))

        # Test Write
        context = self.create_context("Write", file_path)
        self.assertTrue(self.guard.should_trigger(context))

        # Test MultiEdit
        context = self.create_context("MultiEdit", file_path)
        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_other_operations(self):
        """Should not trigger on non-file-editing operations."""
        file_path = self.create_temp_file("test.py", "print('hello')")

        # Test other tools
        for tool in ["Bash", "Read", "Task", "Search"]:
            context = self.create_context(tool, file_path)
            self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_nonexistent_files(self):
        """Should not trigger if file doesn't exist."""
        context = self.create_context("Edit", "/nonexistent/file.py")
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_excluded_directories(self):
        """Should not trigger for excluded directories."""
        excluded_paths = ["archive/test.py", "temp/script.py", "test-screenshots/capture.png", ".git/config"]

        for path in excluded_paths:
            # Create the file in temp dir but with excluded path prefix
            full_path = os.path.join(self.temp_dir, "test.py")
            with open(full_path, "w") as f:
                f.write("content")

            # Mock the file path to appear as excluded
            context = self.create_context("Edit", path)
            with patch("os.path.isfile", return_value=True):
                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_without_file_path(self):
        """Should not trigger without a file path."""
        context = self.create_context("Edit", None)
        self.assertFalse(self.guard.should_trigger(context))

    def test_generic_fixes_trailing_whitespace(self):
        """Should fix trailing whitespace."""
        file_path = self.create_temp_file("test.txt", "line1   \nline2\t\nline3")

        messages = self.guard._apply_generic_fixes(file_path)

        # Check file was fixed
        with open(file_path) as f:
            content = f.read()

        self.assertEqual(content, "line1\nline2\nline3\n")
        self.assertIn("Fixed trailing whitespace", messages[0])

    def test_generic_fixes_missing_newline(self):
        """Should add missing final newline."""
        file_path = self.create_temp_file("test.txt", "line1\nline2")

        messages = self.guard._apply_generic_fixes(file_path)

        # Check file was fixed
        with open(file_path) as f:
            content = f.read()

        self.assertTrue(content.endswith("\n"))
        self.assertIn("Added missing final newline", messages[0])

    def test_generic_fixes_handles_empty_file(self):
        """Should handle empty files gracefully."""
        file_path = self.create_temp_file("empty.txt", "")

        messages = self.guard._apply_generic_fixes(file_path)

        self.assertEqual(messages, [])

    def test_generic_fixes_handles_io_error(self):
        """Should handle IO errors gracefully."""
        # Use a path that will cause an error
        messages = self.guard._apply_generic_fixes("/nonexistent/file.txt")

        self.assertEqual(len(messages), 1)
        self.assertIn("Could not apply generic fixes", messages[0])

    def test_json_linting_fixes_formatting(self):
        """Should auto-format JSON files."""
        # Create unformatted JSON
        json_content = '{"key1":"value1","key2":[1,2,3],"key3":{"nested":"value"}}'
        file_path = self.create_temp_file("test.json", json_content)

        messages = self.guard._run_json_linters(file_path)

        # Check file was formatted
        with open(file_path) as f:
            content = f.read()

        # Should be pretty-printed
        parsed = json.loads(content)
        self.assertEqual(parsed["key1"], "value1")
        self.assertIn("Auto-formatted JSON", messages[0])
        self.assertIn("\n", content)  # Should have newlines

    def test_json_linting_detects_syntax_errors(self):
        """Should detect JSON syntax errors."""
        # Create invalid JSON
        file_path = self.create_temp_file("bad.json", '{"key": "value",}')  # Trailing comma

        messages = self.guard._run_json_linters(file_path)

        self.assertIn("JSON syntax error", messages[0])

    def test_json_linting_handles_unicode(self):
        """Should handle Unicode in JSON files."""
        json_content = '{"emoji":"🎵","chinese":"你好"}'
        file_path = self.create_temp_file("unicode.json", json_content)

        messages = self.guard._run_json_linters(file_path)

        # Check Unicode preserved
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        self.assertIn("🎵", content)
        self.assertIn("你好", content)

    @patch("subprocess.run")
    def test_python_linting_with_tools(self, mock_run):
        """Should run Python linting tools when available."""
        file_path = self.create_temp_file("test.py", "import os\nprint('hello')")

        # Mock tool availability
        with patch.object(self.guard, "_command_exists") as mock_exists:
            mock_exists.return_value = True
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            messages = self.guard._run_python_linters(file_path)

            # Should have tried to run tools
            self.assertTrue(mock_run.called)
            # Should report success
            self.assertTrue(any("Auto-fixed" in msg for msg in messages))

    @patch("subprocess.run")
    def test_python_linting_reports_remaining_issues(self, mock_run):
        """Should report when issues remain after auto-fix."""
        file_path = self.create_temp_file("test.py", "import os\nprint('hello')")

        with patch.object(self.guard, "_command_exists") as mock_exists:
            mock_exists.return_value = True
            # Need to provide enough mock returns for all subprocess calls
            mock_run.side_effect = [
                MagicMock(returncode=0),  # ruff fix
                MagicMock(returncode=1),  # ruff check
                MagicMock(returncode=0),  # black
                MagicMock(returncode=0),  # isort
                MagicMock(returncode=1),  # flake8
            ]

            messages = self.guard._run_python_linters(file_path)

            self.assertTrue(
                any("issues remain" in msg for msg in messages) or any("issues found" in msg for msg in messages)
            )

    def test_python_linting_without_tools(self):
        """Should handle missing linting tools gracefully."""
        file_path = self.create_temp_file("test.py", "print('hello')")

        with patch.object(self.guard, "_command_exists", return_value=False):
            messages = self.guard._run_python_linters(file_path)

            # Should not crash, might have no messages or generic message
            self.assertIsInstance(messages, list)

    def test_yaml_linting_with_pyyaml(self):
        """Should format YAML files when PyYAML is available."""
        yaml_content = "key1: value1\nkey2:\n  - item1\n  - item2\nkey3:   value3"
        file_path = self.create_temp_file("test.yaml", yaml_content)

        messages = self.guard._run_yaml_linters(file_path)

        # Should report formatting
        if messages:  # PyYAML might not be available in test env
            self.assertTrue(any("YAML" in msg for msg in messages))

    def test_yaml_linting_syntax_error(self):
        """Should detect YAML syntax errors."""
        # Invalid YAML (bad indentation)
        yaml_content = "key1: value1\n  key2: value2\n    key3: value3"
        file_path = self.create_temp_file("bad.yaml", yaml_content)

        messages = self.guard._run_yaml_linters(file_path)

        # Should detect error if PyYAML available
        self.assertIsInstance(messages, list)

    @patch("subprocess.run")
    def test_shell_linting_with_shellcheck(self, mock_run):
        """Should run shellcheck when available."""
        shell_content = "#!/bin/bash\necho $UNQUOTED_VAR"
        file_path = self.create_temp_file("test.sh", shell_content)

        with patch.object(self.guard, "_command_exists", return_value=True):
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

            messages = self.guard._run_shell_linters(file_path)

            self.assertTrue(any("Shell script issues" in msg for msg in messages))
            self.assertTrue(any("Quote variables" in msg for msg in messages))

    def test_shell_linting_without_shellcheck(self):
        """Should inform when shellcheck is not available."""
        file_path = self.create_temp_file("test.sh", "#!/bin/bash\necho hello")

        with patch.object(self.guard, "_command_exists", return_value=False):
            messages = self.guard._run_shell_linters(file_path)

            self.assertTrue(any("shellcheck not available" in msg for msg in messages))

    @patch("subprocess.run")
    def test_javascript_linting_with_tools(self, mock_run):
        """Should run JS/TS linting tools when available."""
        js_content = "const x = 'hello';\nconsole.log(x);"
        file_path = self.create_temp_file("test.js", js_content)

        with patch.object(self.guard, "_command_exists", return_value=True):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            messages = self.guard._run_javascript_linters(file_path)

            self.assertTrue(mock_run.called)

    @patch("subprocess.run")
    def test_css_linting_with_tools(self, mock_run):
        """Should run CSS linting tools when available."""
        css_content = ".class { color: red; margin: 0 }"
        file_path = self.create_temp_file("test.css", css_content)

        with patch.object(self.guard, "_command_exists", return_value=True):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            messages = self.guard._run_css_linters(file_path)

            self.assertTrue(mock_run.called)

    def test_get_default_action_is_allow(self):
        """Should always have ALLOW as default action."""
        self.assertEqual(self.guard.get_default_action().value, "allow")

    def test_check_never_blocks(self):
        """Should never block operations."""
        file_path = self.create_temp_file("test.py", "bad code!!!")
        context = self.create_context("Edit", file_path)

        # Even with "errors", should not block
        result = self.guard.check(context)
        self.assertFalse(result.should_block)

    def test_check_returns_message(self):
        """Should return helpful messages."""
        file_path = self.create_temp_file("test.txt", "content   ")
        context = self.create_context("Edit", file_path)

        result = self.guard.check(context)
        self.assertFalse(result.should_block)
        self.assertIsNotNone(result.message)

    def test_command_exists_check(self):
        """Should correctly check if commands exist."""
        # 'which' should exist on most systems
        self.assertTrue(self.guard._command_exists("which"))

        # Random command shouldn't exist
        self.assertFalse(self.guard._command_exists("nonexistent_command_xyz"))

    def test_get_message_comprehensive(self):
        """Should run appropriate linters based on file type."""
        # Test different file types
        test_files = [
            ("test.py", "print('hello')"),
            ("test.json", '{"key": "value"}'),
            ("test.yaml", "key: value"),
            ("test.sh", "echo hello"),
            ("test.js", "console.log('hello');"),
            ("test.css", ".class { color: red; }"),
            ("test.txt", "plain text"),
        ]

        for filename, content in test_files:
            file_path = self.create_temp_file(filename, content)
            context = self.create_context("Edit", file_path)

            message = self.guard.get_message(context)
            self.assertIsNotNone(message)
            self.assertIn(filename, message)

    def test_guard_metadata(self):
        """Should have correct metadata."""
        self.assertEqual(self.guard.name, "Code Linting and Auto-fix")
        self.assertIn("real-time linting", self.guard.description)


if __name__ == "__main__":
    unittest.main()
