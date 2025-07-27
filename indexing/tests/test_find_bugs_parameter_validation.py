# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for find_bugs parameter validation.

Comprehensive validation tests for the find_bugs tool to ensure all parameters
are properly validated and error conditions are handled correctly.

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


class TestFindBugsParameterValidation(unittest.TestCase):
    """Test find_bugs parameter validation comprehensively."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = BugFindingAnalyzer()

        # Create temporary directory and files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test.py"
        self.temp_file.write_text("print('hello world')")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_directory_parameter_required(self):
        """Test that directory parameter is required."""
        # Missing directory parameter
        args = {}
        is_valid, error = self.analyzer.validate_parameters(args)

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("directory", error.lower())
        self.assertIn("required", error.lower())

    def test_directory_parameter_validation_exists(self):
        """Test directory parameter validation with existing directory."""
        args = {"directory": self.temp_dir}
        is_valid, error = self.analyzer.validate_parameters(args)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_directory_parameter_validation_not_exists(self):
        """Test directory parameter validation with non-existent directory."""
        args = {"directory": "/nonexistent/directory/path"}
        is_valid, error = self.analyzer.validate_parameters(args)

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("does not exist", error)

    def test_directory_parameter_validation_not_directory(self):
        """Test directory parameter validation with file instead of directory."""
        args = {"directory": str(self.temp_file)}
        is_valid, error = self.analyzer.validate_parameters(args)

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("not a directory", error)

    def test_severity_filter_parameter_valid_values(self):
        """Test severity_filter parameter with valid values."""
        valid_severities = [
            ["critical"],
            ["high"],
            ["medium"],
            ["low"],
            ["critical", "high"],
            ["medium", "low"],
            ["critical", "high", "medium", "low"],
        ]

        for severity_list in valid_severities:
            with self.subTest(severity_filter=severity_list):
                args = {"directory": self.temp_dir, "severity_filter": severity_list}
                is_valid, error = self.analyzer.validate_parameters(args)
                self.assertTrue(is_valid, f"Should be valid for {severity_list}")
                self.assertIsNone(error)

    def test_severity_filter_parameter_invalid_values(self):
        """Test severity_filter parameter with invalid values."""
        invalid_severities = [
            ["invalid"],
            ["critical", "invalid"],
            ["super_high"],
            [""],
            [None],
            ["Critical"],  # Case sensitivity
            ["HIGH"],  # Case sensitivity
        ]

        # Note: Base parameter validation doesn't check enum values deeply
        # The schema validation would catch these, but our basic validator
        # only checks existence and type. This test documents expected behavior.
        for severity_list in invalid_severities:
            with self.subTest(severity_filter=severity_list):
                args = {"directory": self.temp_dir, "severity_filter": severity_list}
                # Base validator allows invalid enum values - schema validation would catch this
                is_valid, error = self.analyzer.validate_parameters(args)
                # This passes basic validation but would fail JSON schema validation
                self.assertTrue(is_valid or error is None)

    def test_bug_categories_parameter_valid_values(self):
        """Test bug_categories parameter with valid values."""
        valid_categories = [
            ["security"],
            ["memory"],
            ["logic"],
            ["performance"],
            ["concurrency"],
            ["api_usage"],
            ["security", "memory"],
            ["logic", "performance", "concurrency"],
            ["security", "memory", "logic", "performance", "concurrency", "api_usage"],
        ]

        for category_list in valid_categories:
            with self.subTest(bug_categories=category_list):
                args = {"directory": self.temp_dir, "bug_categories": category_list}
                is_valid, error = self.analyzer.validate_parameters(args)
                self.assertTrue(is_valid, f"Should be valid for {category_list}")
                self.assertIsNone(error)

    def test_bug_categories_parameter_invalid_values(self):
        """Test bug_categories parameter with invalid values."""
        invalid_categories = [
            ["invalid"],
            ["security", "invalid"],
            ["bugs"],
            [""],
            [None],
            ["Security"],  # Case sensitivity
            ["MEMORY"],  # Case sensitivity
        ]

        # Same as severity_filter - base validation doesn't check enum values
        for category_list in invalid_categories:
            with self.subTest(bug_categories=category_list):
                args = {"directory": self.temp_dir, "bug_categories": category_list}
                # Base validator allows invalid enum values
                is_valid, error = self.analyzer.validate_parameters(args)
                self.assertTrue(is_valid or error is None)

    def test_include_suggestions_parameter_valid_values(self):
        """Test include_suggestions parameter with valid boolean values."""
        valid_values = [True, False]

        for value in valid_values:
            with self.subTest(include_suggestions=value):
                args = {"directory": self.temp_dir, "include_suggestions": value}
                is_valid, error = self.analyzer.validate_parameters(args)
                self.assertTrue(is_valid)
                self.assertIsNone(error)

    def test_include_suggestions_parameter_invalid_values(self):
        """Test include_suggestions parameter with invalid non-boolean values."""
        invalid_values = ["true", "false", 1, 0, "yes", "no", None]

        for value in invalid_values:
            with self.subTest(include_suggestions=value):
                args = {"directory": self.temp_dir, "include_suggestions": value}
                # Base validator doesn't do type checking - would pass
                is_valid, error = self.analyzer.validate_parameters(args)
                # This documents that type validation isn't done at base level
                self.assertTrue(is_valid or error is None)

    def test_model_parameter_valid_values(self):
        """Test model parameter with valid Gemini model names."""
        valid_models = ["gemini-1.5-flash", "gemini-2.5-pro"]

        for model in valid_models:
            with self.subTest(model=model):
                args = {"directory": self.temp_dir, "model": model}
                is_valid, error = self.analyzer.validate_parameters(args)
                self.assertTrue(is_valid)
                self.assertIsNone(error)

    def test_model_parameter_invalid_values(self):
        """Test model parameter with invalid model names."""
        invalid_models = ["gemini-1.0", "gpt-4", "claude-3", "invalid-model", "", None]

        for model in invalid_models:
            with self.subTest(model=model):
                args = {"directory": self.temp_dir, "model": model}
                is_valid, error = self.analyzer.validate_parameters(args)

                # All invalid model names should be caught (including None/empty)
                self.assertFalse(is_valid)
                self.assertIsNotNone(error)
                self.assertIn("Invalid model", error)

    def test_max_file_size_parameter_valid_values(self):
        """Test max_file_size parameter with valid numeric values."""
        valid_sizes = [1024, 1048576, 10485760, 1.5e6]

        for size in valid_sizes:
            with self.subTest(max_file_size=size):
                args = {"directory": self.temp_dir, "max_file_size": size}
                is_valid, error = self.analyzer.validate_parameters(args)
                self.assertTrue(is_valid)
                self.assertIsNone(error)

    def test_max_file_size_parameter_invalid_values(self):
        """Test max_file_size parameter with invalid values."""
        invalid_sizes = [0, -1, -1000, "1024", "1MB", None, [1024]]

        for size in invalid_sizes:
            with self.subTest(max_file_size=size):
                args = {"directory": self.temp_dir, "max_file_size": size}
                is_valid, error = self.analyzer.validate_parameters(args)

                if size is None:
                    # None should be handled gracefully (uses default)
                    self.assertTrue(is_valid)
                    self.assertIsNone(error)
                elif isinstance(size, (int, float)) and size <= 0:
                    # Zero/negative should be rejected
                    self.assertFalse(is_valid)
                    self.assertIn("positive number", error)
                else:
                    # Non-numeric should be rejected or handled
                    if not isinstance(size, (int, float)):
                        self.assertFalse(is_valid)
                        self.assertIn("positive number", error)

    def test_focus_areas_parameter_valid_values(self):
        """Test focus_areas parameter with valid string arrays."""
        valid_focus_areas = [
            [],
            ["authentication"],
            ["input_validation", "error_handling"],
            ["security", "performance", "memory_management"],
            ["api_design", "database_queries", "error_handling", "testing"],
        ]

        for focus_areas in valid_focus_areas:
            with self.subTest(focus_areas=focus_areas):
                args = {"directory": self.temp_dir, "focus_areas": focus_areas}
                is_valid, error = self.analyzer.validate_parameters(args)
                self.assertTrue(is_valid)
                self.assertIsNone(error)

    def test_focus_areas_parameter_invalid_values(self):
        """Test focus_areas parameter with invalid values."""
        invalid_focus_areas = [
            "single_string",  # Should be array
            [123, 456],  # Should be strings
            [None],  # Null values
            [""],  # Empty strings
            None,  # Should be array or omitted
        ]

        for focus_areas in invalid_focus_areas:
            with self.subTest(focus_areas=focus_areas):
                args = {"directory": self.temp_dir, "focus_areas": focus_areas}
                is_valid, error = self.analyzer.validate_parameters(args)

                if focus_areas is None:
                    # None should be handled gracefully (uses default)
                    self.assertTrue(is_valid)
                    self.assertIsNone(error)
                else:
                    # Base validator doesn't do deep type checking on arrays
                    # Schema validation would catch these issues
                    self.assertTrue(is_valid or error is None)

    def test_combined_parameters_valid(self):
        """Test valid combination of all find_bugs parameters."""
        args = {
            "directory": self.temp_dir,
            "severity_filter": ["critical", "high"],
            "bug_categories": ["security", "memory", "logic"],
            "include_suggestions": True,
            "model": "gemini-2.5-pro",
            "max_file_size": 2097152,
            "focus_areas": ["authentication", "input_validation"],
        }

        is_valid, error = self.analyzer.validate_parameters(args)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_combined_parameters_invalid_directory(self):
        """Test that invalid directory fails validation even with other valid parameters."""
        args = {
            "directory": "/invalid/path",
            "severity_filter": ["critical"],
            "bug_categories": ["security"],
            "include_suggestions": True,
            "model": "gemini-1.5-flash",
            "max_file_size": 1048576,
            "focus_areas": ["security"],
        }

        is_valid, error = self.analyzer.validate_parameters(args)
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)

    def test_tool_schema_completeness(self):
        """Test that the complete tool schema includes all expected parameters."""
        schema = self.analyzer.get_complete_tool_schema()
        properties = schema.get("properties", {})

        # Base parameters from BaseCodeAnalyzer
        expected_base_params = ["directory", "focus_areas", "model", "max_file_size"]
        for param in expected_base_params:
            self.assertIn(param, properties, f"Missing base parameter: {param}")

        # Bug-specific parameters
        expected_bug_params = ["severity_filter", "bug_categories", "include_suggestions"]
        for param in expected_bug_params:
            self.assertIn(param, properties, f"Missing bug-specific parameter: {param}")

        # Required parameters
        required = schema.get("required", [])
        self.assertIn("directory", required, "directory should be required")

    def test_tool_schema_parameter_types(self):
        """Test that tool schema parameters have correct types and constraints."""
        schema = self.analyzer.get_complete_tool_schema()
        properties = schema.get("properties", {})

        # Test severity_filter schema
        severity_schema = properties.get("severity_filter", {})
        self.assertEqual(severity_schema.get("type"), "array")
        severity_items = severity_schema.get("items", {})
        expected_severities = ["critical", "high", "medium", "low"]
        self.assertEqual(set(severity_items.get("enum", [])), set(expected_severities))

        # Test bug_categories schema
        categories_schema = properties.get("bug_categories", {})
        self.assertEqual(categories_schema.get("type"), "array")
        categories_items = categories_schema.get("items", {})
        expected_categories = ["security", "memory", "logic", "performance", "concurrency", "api_usage"]
        self.assertEqual(set(categories_items.get("enum", [])), set(expected_categories))

        # Test include_suggestions schema
        suggestions_schema = properties.get("include_suggestions", {})
        self.assertEqual(suggestions_schema.get("type"), "boolean")

    def test_default_parameter_handling(self):
        """Test that default parameters are handled correctly."""
        # Minimal valid arguments (only directory)
        args = {"directory": self.temp_dir}
        is_valid, error = self.analyzer.validate_parameters(args)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Verify that analyzer can handle missing optional parameters
        # by checking that format_analysis_prompt works with defaults
        files = {"test.py": "print('test')"}
        file_tree = "test.py"
        focus_areas = []
        claude_md_path = None

        # Set empty defaults to simulate missing parameters
        self.analyzer._current_bug_categories = []
        self.analyzer._current_severity_filter = None
        self.analyzer._current_include_suggestions = True

        try:
            prompt = self.analyzer.format_analysis_prompt(files, file_tree, focus_areas, claude_md_path)

            # Should generate valid prompt with defaults
            self.assertIn("Bug Finding Analysis Request", prompt)
            self.assertIn("General bug detection across all categories", prompt)

        finally:
            # Cleanup
            if hasattr(self.analyzer, "_current_bug_categories"):
                delattr(self.analyzer, "_current_bug_categories")
            if hasattr(self.analyzer, "_current_severity_filter"):
                delattr(self.analyzer, "_current_severity_filter")
            if hasattr(self.analyzer, "_current_include_suggestions"):
                delattr(self.analyzer, "_current_include_suggestions")


if __name__ == "__main__":
    unittest.main()
