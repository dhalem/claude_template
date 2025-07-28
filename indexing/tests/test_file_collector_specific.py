# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Tests for FileCollector.collect_specific_files method."""

import os
import sys
import tempfile
import unittest

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), "src")
sys.path.insert(0, src_dir)

from file_collector import FileCollector


class TestFileCollectorSpecific(unittest.TestCase):
    """Test cases for FileCollector.collect_specific_files method."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = FileCollector()
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        self.test_files = {}

        # Python file
        self.python_file = os.path.join(self.temp_dir, "test.py")
        python_content = "def hello():\n    print('Hello, world!')\n"
        with open(self.python_file, "w") as f:
            f.write(python_content)
        self.test_files[self.python_file] = python_content

        # JavaScript file
        self.js_file = os.path.join(self.temp_dir, "utils.js")
        js_content = "function greet(name) {\n    return `Hello, ${name}!`;\n}"
        with open(self.js_file, "w") as f:
            f.write(js_content)
        self.test_files[self.js_file] = js_content

        # JSON file
        self.json_file = os.path.join(self.temp_dir, "config.json")
        json_content = '{\n    "debug": true,\n    "port": 3000\n}'
        with open(self.json_file, "w") as f:
            f.write(json_content)
        self.test_files[self.json_file] = json_content

        # Markdown file
        self.md_file = os.path.join(self.temp_dir, "README.md")
        md_content = "# Test Project\n\nThis is a test.\n"
        with open(self.md_file, "w") as f:
            f.write(md_content)
        self.test_files[self.md_file] = md_content

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_collect_specific_files_success(self):
        """Test successful collection of specific files."""
        file_paths = [self.python_file, self.js_file, self.json_file]
        result = self.collector.collect_specific_files(file_paths)

        # Should collect all requested files
        self.assertEqual(len(result), 3)

        # Check that all files are included with correct content
        self.assertIn(self.python_file, result)
        self.assertIn(self.js_file, result)
        self.assertIn(self.json_file, result)

        # Check content matches
        self.assertEqual(result[self.python_file], self.test_files[self.python_file])
        self.assertEqual(result[self.js_file], self.test_files[self.js_file])
        self.assertEqual(result[self.json_file], self.test_files[self.json_file])

    def test_collect_specific_files_nonexistent(self):
        """Test handling of non-existent files."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.py")
        file_paths = [self.python_file, nonexistent_file, self.js_file]

        result = self.collector.collect_specific_files(file_paths)

        # Should only collect existing files
        self.assertEqual(len(result), 2)
        self.assertIn(self.python_file, result)
        self.assertIn(self.js_file, result)
        self.assertNotIn(nonexistent_file, result)

        # Should track skipped file
        summary = self.collector.get_collection_summary()
        self.assertEqual(summary["files_skipped"], 1)
        self.assertTrue(any("does not exist" in skipped for skipped in summary["skipped_files"]))

    def test_collect_specific_files_directory_path(self):
        """Test handling when a directory path is provided instead of file."""
        file_paths = [self.python_file, self.temp_dir, self.js_file]

        result = self.collector.collect_specific_files(file_paths)

        # Should only collect files, not directories
        self.assertEqual(len(result), 2)
        self.assertIn(self.python_file, result)
        self.assertIn(self.js_file, result)

        # Should track skipped directory
        summary = self.collector.get_collection_summary()
        self.assertEqual(summary["files_skipped"], 1)
        self.assertTrue(any("not a file" in skipped for skipped in summary["skipped_files"]))

    def test_collect_specific_files_unsupported_extension(self):
        """Test handling of files with unsupported extensions."""
        # Create a file with unsupported extension
        unsupported_file = os.path.join(self.temp_dir, "data.bin")
        with open(unsupported_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03")  # Binary content

        file_paths = [self.python_file, unsupported_file, self.js_file]

        result = self.collector.collect_specific_files(file_paths)

        # Should only collect supported files
        self.assertEqual(len(result), 2)
        self.assertIn(self.python_file, result)
        self.assertIn(self.js_file, result)
        self.assertNotIn(unsupported_file, result)

        # Should track skipped file
        summary = self.collector.get_collection_summary()
        self.assertEqual(summary["files_skipped"], 1)
        self.assertTrue(any("unsupported file type" in skipped for skipped in summary["skipped_files"]))

    def test_collect_specific_files_size_limit(self):
        """Test file size limit handling."""
        # Create a large file
        large_file = os.path.join(self.temp_dir, "large.py")
        large_content = "# Large file\n" + "print('x')\n" * 1000  # Should be > 1KB
        with open(large_file, "w") as f:
            f.write(large_content)

        # Set a small size limit
        self.collector.max_file_size = 100  # 100 bytes

        file_paths = [self.python_file, large_file, self.js_file]

        result = self.collector.collect_specific_files(file_paths)

        # Should skip the large file
        self.assertIn(self.python_file, result)
        self.assertIn(self.js_file, result)
        self.assertNotIn(large_file, result)

        # Should track skipped file
        summary = self.collector.get_collection_summary()
        self.assertTrue(any("too large" in skipped for skipped in summary["skipped_files"]))

    def test_collect_specific_files_empty_list(self):
        """Test handling of empty file paths list."""
        result = self.collector.collect_specific_files([])

        self.assertEqual(len(result), 0)
        self.assertEqual(result, {})

        summary = self.collector.get_collection_summary()
        self.assertEqual(summary["files_collected"], 0)
        self.assertEqual(summary["files_skipped"], 0)

    def test_collect_specific_files_relative_paths(self):
        """Test handling of relative paths (should be resolved to absolute)."""
        # Create a file in current directory for relative path testing
        current_dir = os.getcwd()
        try:
            # Change to temp directory
            os.chdir(self.temp_dir)

            # Use relative paths
            file_paths = ["test.py", "utils.js"]

            result = self.collector.collect_specific_files(file_paths)

            # Should collect files and use absolute paths as keys
            self.assertEqual(len(result), 2)

            # Keys should be absolute paths
            for key in result.keys():
                self.assertTrue(os.path.isabs(key))

        finally:
            # Restore original directory
            os.chdir(current_dir)

    def test_collect_specific_files_duplicate_paths(self):
        """Test handling of duplicate file paths."""
        file_paths = [self.python_file, self.python_file, self.js_file, self.python_file]

        result = self.collector.collect_specific_files(file_paths)

        # Should only collect each unique file once
        self.assertEqual(len(result), 2)
        self.assertIn(self.python_file, result)
        self.assertIn(self.js_file, result)

        # Content should be correct
        self.assertEqual(result[self.python_file], self.test_files[self.python_file])

    def test_collect_specific_files_mixed_scenarios(self):
        """Test mixed scenario with various edge cases."""
        # Create an unreadable file (if possible)
        unreadable_file = os.path.join(self.temp_dir, "unreadable.py")
        with open(unreadable_file, "w") as f:
            f.write("print('test')")

        nonexistent_file = os.path.join(self.temp_dir, "missing.py")

        file_paths = [
            self.python_file,  # Valid file
            nonexistent_file,  # Non-existent
            self.temp_dir,  # Directory
            self.js_file,  # Valid file
            unreadable_file,  # File that might have read issues
        ]

        result = self.collector.collect_specific_files(file_paths)

        # Should collect valid files
        self.assertIn(self.python_file, result)
        self.assertIn(self.js_file, result)

        # Get summary to check tracking
        summary = self.collector.get_collection_summary()
        self.assertGreaterEqual(summary["files_skipped"], 2)  # At least directory and non-existent

    def test_collect_specific_files_collection_summary(self):
        """Test that collection summary is properly updated."""
        file_paths = [self.python_file, self.js_file, self.md_file]

        result = self.collector.collect_specific_files(file_paths)
        summary = self.collector.get_collection_summary()

        # Check summary accuracy
        self.assertEqual(summary["files_collected"], 3)
        self.assertEqual(summary["files_skipped"], 0)
        self.assertGreater(summary["total_size"], 0)
        self.assertEqual(len(summary["skipped_files"]), 0)

        # Total size should be sum of file contents
        expected_size = sum(len(content) for content in result.values())
        self.assertEqual(summary["total_size"], expected_size)

    def test_collect_specific_files_state_reset(self):
        """Test that collector state is properly reset between calls."""
        # First collection
        result1 = self.collector.collect_specific_files([self.python_file])
        summary1 = self.collector.get_collection_summary()

        # Second collection with different files
        result2 = self.collector.collect_specific_files([self.js_file, self.json_file])
        summary2 = self.collector.get_collection_summary()

        # Second result should not include first file
        self.assertNotIn(self.python_file, result2)
        self.assertIn(self.js_file, result2)
        self.assertIn(self.json_file, result2)

        # Summary should reflect only second collection
        self.assertEqual(summary2["files_collected"], 2)
        self.assertEqual(len(result2), 2)


if __name__ == "__main__":
    unittest.main()
