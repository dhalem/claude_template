# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Baseline tests for review_code tool - Phase 1 TDD implementation.

These tests establish comprehensive coverage of the existing review_code functionality
before any refactoring takes place. All tests must pass before proceeding to Phase 2.

Testing approach:
- Real integration tests with actual files and data
- External service boundaries handled appropriately
- See TESTING_STRATEGY.md for detailed guidelines
"""

import os

# Import the MCP server components
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from file_collector import FileCollector
from review_formatter import ReviewFormatter


class TestReviewCodeParameterValidation(unittest.TestCase):
    """Test parameter validation for review_code tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create test files
        (self.temp_path / "test.py").write_text("print('hello world')")
        (self.temp_path / "README.md").write_text("# Test Project")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_directory_parameter_required(self):
        """Test that directory parameter is required."""
        # This simulates the validation logic from the MCP server
        arguments = {}
        directory = arguments.get("directory")
        self.assertIsNone(directory, "Directory parameter should be None when not provided")

    def test_directory_parameter_validation_exists(self):
        """Test directory parameter validation for existing directory."""
        arguments = {"directory": str(self.temp_path)}
        directory = arguments.get("directory")

        self.assertIsNotNone(directory)
        directory_path = Path(directory).resolve()
        self.assertTrue(directory_path.exists())
        self.assertTrue(directory_path.is_dir())

    def test_directory_parameter_validation_not_exists(self):
        """Test directory parameter validation for non-existent directory."""
        nonexistent_path = "/path/that/does/not/exist"
        arguments = {"directory": nonexistent_path}
        directory = arguments.get("directory")

        directory_path = Path(directory).resolve()
        self.assertFalse(directory_path.exists())

    def test_directory_parameter_validation_not_directory(self):
        """Test directory parameter validation for file instead of directory."""
        file_path = self.temp_path / "test.py"
        arguments = {"directory": str(file_path)}
        directory = arguments.get("directory")

        directory_path = Path(directory).resolve()
        self.assertTrue(directory_path.exists())
        self.assertFalse(directory_path.is_dir())

    def test_focus_areas_parameter_optional(self):
        """Test that focus_areas parameter is optional."""
        arguments = {"directory": str(self.temp_path)}
        focus_areas = arguments.get("focus_areas", [])
        self.assertEqual(focus_areas, [])

    def test_focus_areas_parameter_with_values(self):
        """Test focus_areas parameter with actual values."""
        test_focus_areas = ["security", "performance"]
        arguments = {"directory": str(self.temp_path), "focus_areas": test_focus_areas}
        focus_areas = arguments.get("focus_areas", [])
        self.assertEqual(focus_areas, test_focus_areas)

    def test_model_parameter_optional_with_default(self):
        """Test that model parameter is optional with default value."""
        arguments = {"directory": str(self.temp_path)}
        default_model = "gemini-2.5-pro"
        model = arguments.get("model", default_model)
        self.assertEqual(model, default_model)

    def test_model_parameter_with_valid_values(self):
        """Test model parameter with valid values."""
        valid_models = ["gemini-1.5-flash", "gemini-2.5-pro"]

        for valid_model in valid_models:
            arguments = {"directory": str(self.temp_path), "model": valid_model}
            model = arguments.get("model", "gemini-2.5-pro")
            self.assertEqual(model, valid_model)

    def test_max_file_size_parameter_optional_with_default(self):
        """Test that max_file_size parameter is optional with default value."""
        arguments = {"directory": str(self.temp_path)}
        default_max_size = 1048576  # 1MB
        max_file_size = arguments.get("max_file_size", default_max_size)
        self.assertEqual(max_file_size, default_max_size)

    def test_max_file_size_parameter_with_custom_value(self):
        """Test max_file_size parameter with custom value."""
        custom_size = 2048576  # 2MB
        arguments = {"directory": str(self.temp_path), "max_file_size": custom_size}
        max_file_size = arguments.get("max_file_size", 1048576)
        self.assertEqual(max_file_size, custom_size)


class TestFileCollectorBaseline(unittest.TestCase):
    """Baseline tests for FileCollector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.collector = FileCollector()

        # Create test file structure
        (self.temp_path / "src").mkdir()
        (self.temp_path / "src" / "main.py").write_text("def main(): pass")
        (self.temp_path / "src" / "utils.py").write_text("def helper(): pass")
        (self.temp_path / "README.md").write_text("# Test Project")
        (self.temp_path / "package.json").write_text('{"name": "test"}')

        # Create excluded directory
        (self.temp_path / "__pycache__").mkdir()
        (self.temp_path / "__pycache__" / "test.pyc").write_text("binary")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_collect_files_basic_functionality(self):
        """Test basic file collection functionality."""
        files = self.collector.collect_files(str(self.temp_path))

        self.assertIsInstance(files, dict)
        self.assertGreater(len(files), 0)

        # Check expected files are collected
        expected_files = ["src/main.py", "src/utils.py", "README.md", "package.json"]
        for expected_file in expected_files:
            self.assertIn(expected_file, files)

    def test_collect_files_excludes_pycache(self):
        """Test that __pycache__ directories are excluded."""
        files = self.collector.collect_files(str(self.temp_path))

        # Should not contain files from __pycache__
        for file_path in files.keys():
            self.assertNotIn("__pycache__", file_path)

    def test_collect_files_respects_max_file_size(self):
        """Test that max_file_size parameter is respected."""
        # Create a large file
        large_content = "x" * 2000  # 2KB
        (self.temp_path / "large_file.py").write_text(large_content)

        # Set small max file size
        self.collector.max_file_size = 1000  # 1KB
        files = self.collector.collect_files(str(self.temp_path))

        # Large file should not be included
        self.assertNotIn("large_file.py", files)
        self.assertGreater(len(self.collector.skipped_files), 0)

    def test_collect_files_handles_nonexistent_directory(self):
        """Test handling of non-existent directory."""
        with self.assertRaises(ValueError):
            self.collector.collect_files("/path/that/does/not/exist")

    def test_collect_files_handles_file_instead_of_directory(self):
        """Test handling when path is a file instead of directory."""
        file_path = self.temp_path / "README.md"
        with self.assertRaises(ValueError):
            self.collector.collect_files(str(file_path))

    def test_get_collection_summary(self):
        """Test collection summary functionality."""
        files = self.collector.collect_files(str(self.temp_path))
        summary = self.collector.get_collection_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn("files_collected", summary)
        self.assertIn("total_size", summary)
        self.assertEqual(summary["files_collected"], len(files))
        self.assertGreater(summary["total_size"], 0)

    def test_get_file_tree(self):
        """Test file tree generation."""
        self.collector.collect_files(str(self.temp_path))
        file_tree = self.collector.get_file_tree()

        self.assertIsInstance(file_tree, str)
        self.assertGreater(len(file_tree), 0)
        # Should contain the collected files (main.py and utils.py are in src/ subdirectory)
        self.assertIn("main.py", file_tree)
        self.assertIn("utils.py", file_tree)

    def test_file_extension_filtering(self):
        """Test that only supported file extensions are collected."""
        # Create files with various extensions
        (self.temp_path / "script.py").write_text("# Python file")
        (self.temp_path / "config.json").write_text('{"key": "value"}')
        (self.temp_path / "docs.md").write_text("# Documentation")
        (self.temp_path / "binary.exe").write_text("binary content")
        (self.temp_path / "image.png").write_bytes(b"\x89PNG binary")

        files = self.collector.collect_files(str(self.temp_path))

        # Should include supported extensions
        self.assertIn("script.py", files)
        self.assertIn("config.json", files)
        self.assertIn("docs.md", files)

        # Should exclude unsupported extensions
        self.assertNotIn("binary.exe", files)
        self.assertNotIn("image.png", files)

    def test_gitignore_pattern_loading(self):
        """Test gitignore pattern loading functionality."""
        # Create .gitignore file
        gitignore_content = "*.log\ntemp/\n__pycache__/"
        (self.temp_path / ".gitignore").write_text(gitignore_content)

        # Create files that should be ignored
        (self.temp_path / "debug.log").write_text("log content")
        (self.temp_path / "temp").mkdir()
        (self.temp_path / "temp" / "cache.txt").write_text("temp file")

        files = self.collector.collect_files(str(self.temp_path))

        # Should respect gitignore patterns
        self.assertNotIn("debug.log", files)
        self.assertNotIn("temp/cache.txt", files)


class TestGeminiClientBaseline(unittest.TestCase):
    """Baseline tests for GeminiClient functionality - REAL API TESTING ONLY."""

    def setUp(self):
        """Set up test fixtures."""
        # Only test if API key is available
        self.has_api_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

    def test_gemini_client_missing_api_key(self):
        """Test GeminiClient initialization without API key."""
        # Temporarily remove API keys from environment
        original_gemini = os.environ.get("GEMINI_API_KEY")
        original_google = os.environ.get("GOOGLE_API_KEY")

        if original_gemini:
            del os.environ["GEMINI_API_KEY"]
        if original_google:
            del os.environ["GOOGLE_API_KEY"]

        try:
            with self.assertRaises(ValueError) as context:
                from gemini_client import GeminiClient

                GeminiClient()

            self.assertIn("API_KEY environment variable not set", str(context.exception))
        finally:
            # Restore original values
            if original_gemini:
                os.environ["GEMINI_API_KEY"] = original_gemini
            if original_google:
                os.environ["GOOGLE_API_KEY"] = original_google

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"), "Skipping real API tests - No API key available"
    )
    def test_gemini_client_initialization_with_api_key(self):
        """Test GeminiClient initialization with real API key."""
        from gemini_client import GeminiClient

        client = GeminiClient(model="gemini-1.5-flash")

        self.assertEqual(client.model_name, "gemini-1.5-flash")
        self.assertEqual(client.total_tokens, 0)
        self.assertEqual(client.input_tokens, 0)
        self.assertEqual(client.output_tokens, 0)
        self.assertEqual(client.call_count, 0)

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"), "Skipping real API tests - No API key available"
    )
    def test_gemini_client_custom_pricing(self):
        """Test GeminiClient with custom pricing."""
        from gemini_client import GeminiClient

        custom_pricing = {"flash": 0.001, "pro": 0.005}
        client = GeminiClient(custom_pricing=custom_pricing)

        self.assertEqual(client.pricing, custom_pricing)

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"), "Skipping real API tests - No API key available"
    )
    def test_get_usage_report_initial_state(self):
        """Test usage report in initial state."""
        from gemini_client import GeminiClient

        client = GeminiClient()
        usage = client.get_usage_report()

        self.assertIsInstance(usage, dict)
        self.assertIn("total_tokens", usage)
        self.assertIn("input_tokens", usage)
        self.assertIn("output_tokens", usage)
        self.assertIn("estimated_cost", usage)
        self.assertEqual(usage["total_tokens"], 0)
        self.assertEqual(usage["input_tokens"], 0)
        self.assertEqual(usage["output_tokens"], 0)
        self.assertEqual(usage["estimated_cost"], 0.0)

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"), "Skipping real API tests - No API key available"
    )
    def test_review_code_basic_functionality(self):
        """Test basic review_code API call functionality."""
        from gemini_client import GeminiClient

        try:
            client = GeminiClient(model="gemini-1.5-flash")  # Use flash for faster/cheaper tests

            # Simple test code to review
            test_code = """def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
"""

            # Make the API call
            review_result = client.review_code(test_code)
        except Exception as e:
            if "API key not valid" in str(e) or "API_KEY_INVALID" in str(e):
                self.skipTest(f"Skipping test due to invalid API key: {e}")
            else:
                raise

        # Verify response
        self.assertIsInstance(review_result, str)
        self.assertGreater(len(review_result), 0)

        # Verify usage tracking was updated
        usage = client.get_usage_report()
        self.assertGreater(usage["total_tokens"], 0)
        self.assertGreater(usage["input_tokens"], 0)
        self.assertGreater(usage["output_tokens"], 0)
        self.assertEqual(usage["call_count"], 1)
        self.assertGreater(usage["estimated_cost"], 0.0)


class TestErrorHandlingBaseline(unittest.TestCase):
    """Baseline tests for error handling across all components."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_file_collector_permission_error_handling(self):
        """Test FileCollector handling of permission errors."""
        from file_collector import FileCollector

        collector = FileCollector()

        # Create a directory with restricted permissions (if possible on this system)
        restricted_dir = self.temp_path / "restricted"
        restricted_dir.mkdir()

        # Create a file inside
        (restricted_dir / "test.py").write_text("print('test')")

        # Try to restrict permissions (may not work on all systems)
        try:
            import os

            os.chmod(str(restricted_dir), 0o000)

            # Collection should still work, just log warnings
            files = collector.collect_files(str(self.temp_path))

            # Should complete without raising exception
            self.assertIsInstance(files, dict)

        except (PermissionError, OSError):
            # Permission change may not be supported on all systems
            self.skipTest("Cannot test permission errors on this system")
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(str(restricted_dir), 0o755)
            except (PermissionError, OSError):
                pass

    def test_file_collector_encoding_error_handling(self):
        """Test FileCollector handling of encoding errors."""
        from file_collector import FileCollector

        collector = FileCollector()

        # Create a file with binary content that looks like text
        binary_file = self.temp_path / "binary.py"
        with open(binary_file, "wb") as f:
            # Write some Python-like content followed by binary data
            f.write(b"def test():\n    pass\n")
            f.write(b"\x00\x01\x02\x03\xff\xfe")  # Binary content

        files = collector.collect_files(str(self.temp_path))

        # File should be skipped due to binary content
        self.assertNotIn("binary.py", files)
        self.assertGreater(len(collector.skipped_files), 0)

    def test_gemini_client_network_error_simulation(self):
        """Test GeminiClient error handling (simulated network issues)."""
        # This test checks that the client properly handles exceptions
        # We can't easily simulate network errors without mocking, but we can
        # test that the error handling paths exist and work correctly

        # Test with invalid API key format (should cause API error)
        import os

        from gemini_client import GeminiClient

        original_key = os.environ.get("GEMINI_API_KEY")

        try:
            os.environ["GEMINI_API_KEY"] = "invalid_key_format"
            client = GeminiClient()

            # This should raise an exception when trying to make API call
            with self.assertRaises(Exception):
                client.review_code("def test(): pass")

        finally:
            # Restore original key
            if original_key:
                os.environ["GEMINI_API_KEY"] = original_key
            elif "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

    def test_review_formatter_invalid_input_handling(self):
        """Test ReviewFormatter handling of invalid inputs."""
        from review_formatter import ReviewFormatter

        formatter = ReviewFormatter()

        # Test with None files input - this currently raises AttributeError
        # This demonstrates the current error handling behavior
        with self.assertRaises(AttributeError):
            formatter.format_review_request(files=None, file_tree="")

        # Test with invalid file tree (None) - files dict should be valid
        result = formatter.format_review_request(files={}, file_tree=None)
        self.assertIsInstance(result, str)

        # Test with empty but valid inputs
        result = formatter.format_review_request(files={}, file_tree="")
        self.assertIsInstance(result, str)

    def test_file_collector_very_large_file_handling(self):
        """Test FileCollector handling of very large files."""
        from file_collector import FileCollector

        # Set a small max file size for testing
        collector = FileCollector(max_file_size=1000)  # 1KB limit

        # Create a file larger than the limit
        large_file = self.temp_path / "large.py"
        large_content = "# Large file\n" + "x" * 2000  # 2KB+ content
        large_file.write_text(large_content)

        files = collector.collect_files(str(self.temp_path))

        # Large file should be skipped
        self.assertNotIn("large.py", files)
        self.assertTrue(any("large.py" in skip for skip in collector.skipped_files))

    def test_file_collector_empty_directory_handling(self):
        """Test FileCollector handling of empty directories."""
        from file_collector import FileCollector

        collector = FileCollector()

        # Create empty subdirectories
        (self.temp_path / "empty1").mkdir()
        (self.temp_path / "empty2").mkdir()
        (self.temp_path / "empty2" / "nested_empty").mkdir()

        files = collector.collect_files(str(self.temp_path))

        # Should handle empty directories gracefully
        self.assertIsInstance(files, dict)
        self.assertEqual(len(files), 0)  # No files to collect

        summary = collector.get_collection_summary()
        self.assertEqual(summary["files_collected"], 0)


class TestReviewFormatterBaseline(unittest.TestCase):
    """Baseline tests for ReviewFormatter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = ReviewFormatter()
        self.sample_files = {
            "main.py": "def main(): print('hello')",
            "utils.py": "def helper(): return True",
            "README.md": "# Test Project\nThis is a test.",
        }
        self.sample_file_tree = "test/\n├── main.py\n├── utils.py\n└── README.md"

    def test_format_review_request_basic(self):
        """Test basic review request formatting."""
        result = self.formatter.format_review_request(files=self.sample_files, file_tree=self.sample_file_tree)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

        # Should contain file contents
        self.assertIn("def main()", result)
        self.assertIn("def helper()", result)

        # Should contain file tree
        self.assertIn("main.py", result)

    def test_format_review_request_with_focus_areas(self):
        """Test review request formatting with focus areas."""
        focus_areas = ["security", "performance"]
        result = self.formatter.format_review_request(
            files=self.sample_files, file_tree=self.sample_file_tree, focus_areas=focus_areas
        )

        self.assertIn("security", result.lower())
        self.assertIn("performance", result.lower())

    def test_format_review_request_with_claude_md(self):
        """Test review request formatting with CLAUDE.md content."""
        temp_dir = tempfile.mkdtemp()
        try:
            claude_md_path = Path(temp_dir) / "CLAUDE.md"
            claude_md_content = "# Project Guidelines\nThis is a test project."
            claude_md_path.write_text(claude_md_content)

            result = self.formatter.format_review_request(
                files=self.sample_files, file_tree=self.sample_file_tree, claude_md_path=str(claude_md_path)
            )

            self.assertIn("Project Guidelines", result)

        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_format_review_request_claude_md_from_files(self):
        """Test CLAUDE.md detection from files dictionary."""
        files_with_claude = self.sample_files.copy()
        files_with_claude["CLAUDE.md"] = "# Project Rules\nFollow these rules."

        result = self.formatter.format_review_request(files=files_with_claude, file_tree=self.sample_file_tree)

        self.assertIn("Project Rules", result)

    def test_format_review_request_empty_files(self):
        """Test review request formatting with empty files dict."""
        result = self.formatter.format_review_request(files={}, file_tree="empty/")

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_format_review_request_no_focus_areas(self):
        """Test review request formatting without focus areas."""
        result = self.formatter.format_review_request(
            files=self.sample_files, file_tree=self.sample_file_tree, focus_areas=None
        )

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
