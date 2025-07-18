# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for FileCollector class.

Tests are now automatically run by pre-commit hooks.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_collector import FileCollector


class TestFileCollector(unittest.TestCase):
    """Test FileCollector functionality."""

    def setUp(self):
        """Set up test environment."""
        self.collector = FileCollector()
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_should_include_file_source_extensions(self):
        """Test that source files are included."""
        source_files = [
            "main.py", "app.js", "component.tsx", "server.go",
            "utils.rs", "config.json", "README.md"
        ]

        for filename in source_files:
            with self.subTest(filename=filename):
                file_path = self.test_dir / filename
                self.assertTrue(
                    self.collector._should_include_file(file_path),
                    f"Should include {filename}"
                )

    def test_should_exclude_file_binary_extensions(self):
        """Test that binary files are excluded."""
        binary_files = [
            "image.png", "data.db", "archive.zip", "binary.exe",
            "document.pdf", "audio.mp3"
        ]

        for filename in binary_files:
            with self.subTest(filename=filename):
                file_path = self.test_dir / filename
                self.assertFalse(
                    self.collector._should_include_file(file_path),
                    f"Should exclude {filename}"
                )

    def test_always_include_files(self):
        """Test that special files are always included."""
        # Based on actual ALWAYS_INCLUDE constant
        always_include = ['claude.md', 'readme.md', 'pyproject.toml', 'package.json', 'cargo.toml']

        for filename in always_include:
            with self.subTest(filename=filename):
                file_path = self.test_dir / filename
                self.assertTrue(
                    self.collector._should_include_file(file_path),
                    f"Should always include {filename}"
                )

    def test_excluded_directories_constants(self):
        """Test the EXCLUDED_DIRS constant."""
        expected_excluded = {
            '.git', 'node_modules', 'venv', '.venv', '__pycache__',
            'dist', 'build', 'target', '.pytest_cache', '.mypy_cache'
        }

        self.assertEqual(self.collector.EXCLUDED_DIRS, expected_excluded)

    def test_gitignore_pattern_matching(self):
        """Test gitignore pattern matching."""
        test_cases = [
            ("app.log", ["*.log"], True),
            ("debug.log", ["*.log"], True),
            ("app.py", ["*.log"], False),
            ("temp", ["temp/"], True),  # Directory patterns
            ("temp/file.txt", ["temp/"], True),
            ("other/file.txt", ["temp/"], False),
            ("build/output.txt", ["build/*"], True),
            ("src/build.py", ["build/*"], False),
        ]

        for file_path, test_patterns, expected in test_cases:
            with self.subTest(file_path=file_path):
                path_obj = Path(file_path)
                result = self.collector._matches_gitignore(path_obj, test_patterns)
                self.assertEqual(
                    result, expected,
                    f"Pattern matching failed for {file_path} with {test_patterns}"
                )

    def test_load_gitignore_file_exists(self):
        """Test loading gitignore when file exists."""
        gitignore_content = """# Comments should be ignored
*.log
temp/
!important.log

# Empty lines should be ignored

build/*
*.pyc
"""

        with patch('builtins.open', mock_open(read_data=gitignore_content)):
            with patch('pathlib.Path.exists', return_value=True):
                patterns = self.collector._load_gitignore(self.test_dir)

                expected_patterns = ['*.log', 'temp/', '!important.log', 'build/*', '*.pyc']
                self.assertEqual(patterns, expected_patterns)

    def test_load_gitignore_file_not_exists(self):
        """Test loading gitignore when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            patterns = self.collector._load_gitignore(self.test_dir)
            self.assertEqual(patterns, [])

    def test_binary_content_detection(self):
        """Test binary content detection."""
        # Text content
        text_content = "Hello world\nThis is text"
        self.assertFalse(self.collector._is_binary_content(text_content))

        # Binary content (contains null bytes)
        binary_content = "Hello\x00world"
        self.assertTrue(self.collector._is_binary_content(binary_content))

    def test_collect_files_integration(self):
        """Test the main collect_files method with a real directory structure."""
        # Create a temporary directory structure
        test_structure = {
            "src/main.py": "print('hello')",
            "src/utils.py": "def helper(): pass",
            "tests/test_main.py": "import unittest",
            "README.md": "# Project",
            "pyproject.toml": "[tool.poetry]",
            ".gitignore": "*.log\ntemp/",
            "temp/cache.txt": "cached data",
            "debug.log": "log content",
        }

        # Create the structure
        for rel_path, content in test_structure.items():
            file_path = self.test_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Collect files
        collected = self.collector.collect_files(str(self.test_dir))

        # Get just the filenames for easier checking
        collected_names = {Path(path).name for path in collected.keys()}

        # Should include these
        expected_included = {"main.py", "utils.py", "test_main.py", "README.md", "pyproject.toml"}
        for expected in expected_included:
            self.assertIn(expected, collected_names, f"Should include {expected}")

        # Should exclude these (gitignore patterns)
        expected_excluded = {"cache.txt", "debug.log"}
        for excluded in expected_excluded:
            self.assertNotIn(excluded, collected_names, f"Should exclude {excluded}")

    def test_collect_files_handles_large_files(self):
        """Test handling of large files."""
        # Create a file larger than default max size
        large_content = "x" * (self.collector.max_file_size + 1000)
        large_file = self.test_dir / "large.py"
        large_file.write_text(large_content)

        # Create a normal file
        normal_file = self.test_dir / "normal.py"
        normal_file.write_text("print('hello')")

        collected = self.collector.collect_files(str(self.test_dir))

        # Large file should be skipped
        collected_names = {Path(path).name for path in collected.keys()}
        self.assertNotIn("large.py", collected_names)

        # Normal file should be included
        self.assertIn("normal.py", collected_names)

        # Large file should be in skipped list
        skipped_names = {Path(f.split(' ')[0]).name for f in self.collector.skipped_files}
        self.assertIn("large.py", skipped_names)

    def test_read_file_safely_text_file(self):
        """Test reading normal text files."""
        test_content = "Hello\nWorld\nPython"
        test_file = self.test_dir / "test.py"
        test_file.write_text(test_content)

        result = self.collector._read_file_safely(test_file)
        self.assertEqual(result, test_content)

    def test_read_file_safely_binary_file(self):
        """Test reading binary files returns None."""
        binary_content = b'\x00\x01\x02\x03binary data\x00'
        test_file = self.test_dir / "binary.dat"
        test_file.write_bytes(binary_content)

        result = self.collector._read_file_safely(test_file)
        self.assertIsNone(result)

    def test_pattern_matching_edge_cases(self):
        """Test edge cases in pattern matching."""
        test_cases = [
            # Simple wildcards
            ("file.txt", "*", True),
            ("file.txt", "*.txt", True),
            ("file.py", "*.txt", False),

            # Directory patterns
            ("dir/", "dir/", True),
            ("dir/subdir/", "dir/", True),  # Should match subdirectories
            ("other/", "dir/", False),

            # Complex patterns
            ("build/output", "build/*", True),
            ("src/build.py", "build/*", False),
        ]

        for path_str, pattern, expected in test_cases:
            with self.subTest(path=path_str, pattern=pattern):
                result = self.collector._match_pattern(path_str, pattern)
                self.assertEqual(result, expected,
                                 f"Pattern '{pattern}' should {'match' if expected else 'not match'} '{path_str}'")

    def test_collect_files_empty_directory(self):
        """Test collecting from empty directory."""
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()

        collected = self.collector.collect_files(str(empty_dir))
        self.assertEqual(len(collected), 0)

    def test_collect_files_permission_error(self):
        """Test handling permission errors gracefully."""
        # Create a directory and file
        test_file = self.test_dir / "test.py"
        test_file.write_text("print('hello')")

        # Mock permission error during iteration
        with patch('pathlib.Path.iterdir', side_effect=PermissionError("Access denied")):
            # Should not crash
            collected = self.collector.collect_files(str(self.test_dir))
            # May return empty results due to permission error
            self.assertIsInstance(collected, dict)

    def test_file_extensions_constants(self):
        """Test that file extension constants are properly defined."""
        # Source extensions
        expected_source = {'.py', '.js', '.jsx', '.ts', '.tsx', '.rs', '.go', '.java', '.c', '.cpp', '.h', '.hpp', '.sh', '.bash'}
        self.assertEqual(self.collector.SOURCE_EXTENSIONS, expected_source)

        # Config extensions
        expected_config = {'.json', '.yaml', '.yml', '.toml', '.ini'}
        self.assertEqual(self.collector.CONFIG_EXTENSIONS, expected_config)

        # Doc extensions
        expected_doc = {'.md', '.rst', '.txt'}
        self.assertEqual(self.collector.DOC_EXTENSIONS, expected_doc)


if __name__ == '__main__':
    unittest.main()
