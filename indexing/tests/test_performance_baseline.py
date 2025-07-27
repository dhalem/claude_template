# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Performance baseline tests for review_code tool - Phase 1.7.

These tests establish performance baselines before refactoring to ensure
no performance regression occurs during the shared component extraction.

Measurements include:
- File collection performance
- Gemini API response times
- Memory usage patterns
- Component-level timing
- Overall end-to-end performance

NO MOCKS - Real performance measurements only, following claude_template rules.
"""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict

import psutil

# Import the components to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from file_collector import FileCollector
from review_formatter import ReviewFormatter


class PerformanceMetrics:
    """Helper class to collect and report performance metrics."""

    def __init__(self):
        self.metrics = {}
        self.process = psutil.Process()

    def start_measurement(self, name: str):
        """Start timing a measurement."""
        self.metrics[name] = {
            "start_time": time.time(),
            "start_memory": self.process.memory_info().rss / 1024 / 1024,  # MB
            "start_cpu": self.process.cpu_percent(),
        }

    def end_measurement(self, name: str):
        """End timing a measurement."""
        if name not in self.metrics:
            raise ValueError(f"No measurement started for {name}")

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.process.cpu_percent()

        self.metrics[name].update(
            {
                "end_time": end_time,
                "end_memory": end_memory,
                "end_cpu": end_cpu,
                "duration": end_time - self.metrics[name]["start_time"],
                "memory_delta": end_memory - self.metrics[name]["start_memory"],
                "cpu_usage": end_cpu,
            }
        )

    def get_summary(self) -> Dict:
        """Get performance summary."""
        summary = {}
        for name, data in self.metrics.items():
            if "duration" in data:
                summary[name] = {
                    "duration_seconds": round(data["duration"], 3),
                    "memory_delta_mb": round(data["memory_delta"], 2),
                    "cpu_usage_percent": round(data["cpu_usage"], 1),
                }
        return summary


class TestFileCollectorPerformance(unittest.TestCase):
    """Performance tests for FileCollector component."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.metrics = PerformanceMetrics()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.collector = FileCollector()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def _create_test_files(self, num_files: int, avg_size: int = 1000):
        """Create test files for performance testing."""
        for i in range(num_files):
            subdir = self.temp_path / f"dir_{i // 10}"
            subdir.mkdir(exist_ok=True)

            file_path = subdir / f"file_{i}.py"
            content = f"# Test file {i}\n" + "x" * (avg_size - 20)
            file_path.write_text(content)

    def test_small_project_performance(self):
        """Test file collection performance on small project (10 files)."""
        self._create_test_files(10, 1000)  # 10 files, 1KB each

        self.metrics.start_measurement("small_project_collection")
        files = self.collector.collect_files(str(self.temp_path))
        self.metrics.end_measurement("small_project_collection")

        # Verify collection worked
        self.assertEqual(len(files), 10)

        # Performance assertions (generous limits for baseline)
        summary = self.metrics.get_summary()
        duration = summary["small_project_collection"]["duration_seconds"]
        memory = summary["small_project_collection"]["memory_delta_mb"]

        self.assertLess(duration, 1.0, "Small project collection should take <1 second")
        self.assertLess(memory, 10.0, "Small project should use <10MB additional memory")

        print(f"Small project (10 files): {duration}s, {memory}MB")

    def test_medium_project_performance(self):
        """Test file collection performance on medium project (100 files)."""
        self._create_test_files(100, 2000)  # 100 files, 2KB each

        self.metrics.start_measurement("medium_project_collection")
        files = self.collector.collect_files(str(self.temp_path))
        self.metrics.end_measurement("medium_project_collection")

        # Verify collection worked
        self.assertEqual(len(files), 100)

        # Performance assertions
        summary = self.metrics.get_summary()
        duration = summary["medium_project_collection"]["duration_seconds"]
        memory = summary["medium_project_collection"]["memory_delta_mb"]

        self.assertLess(duration, 5.0, "Medium project collection should take <5 seconds")
        self.assertLess(memory, 50.0, "Medium project should use <50MB additional memory")

        print(f"Medium project (100 files): {duration}s, {memory}MB")

    def test_large_project_performance(self):
        """Test file collection performance on large project (500 files)."""
        self._create_test_files(500, 3000)  # 500 files, 3KB each

        self.metrics.start_measurement("large_project_collection")
        files = self.collector.collect_files(str(self.temp_path))
        self.metrics.end_measurement("large_project_collection")

        # Verify collection worked
        self.assertEqual(len(files), 500)

        # Performance assertions (more generous for large projects)
        summary = self.metrics.get_summary()
        duration = summary["large_project_collection"]["duration_seconds"]
        memory = summary["large_project_collection"]["memory_delta_mb"]

        self.assertLess(duration, 15.0, "Large project collection should take <15 seconds")
        self.assertLess(memory, 100.0, "Large project should use <100MB additional memory")

        print(f"Large project (500 files): {duration}s, {memory}MB")

    def test_file_tree_generation_performance(self):
        """Test file tree generation performance."""
        self._create_test_files(100, 1000)
        self.collector.collect_files(str(self.temp_path))

        self.metrics.start_measurement("file_tree_generation")
        tree = self.collector.get_file_tree()
        self.metrics.end_measurement("file_tree_generation")

        # Verify tree was generated
        self.assertGreater(len(tree), 100)

        # Performance assertion
        summary = self.metrics.get_summary()
        duration = summary["file_tree_generation"]["duration_seconds"]

        self.assertLess(duration, 0.1, "File tree generation should take <100ms")
        print(f"File tree generation (100 files): {duration}s")


class TestGeminiClientPerformance(unittest.TestCase):
    """Performance tests for GeminiClient component."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.metrics = PerformanceMetrics()
        # Only test if API key is available
        self.has_api_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        "Skipping real API performance tests - No API key available",
    )
    def test_small_prompt_performance(self):
        """Test Gemini API performance with small prompt."""
        from gemini_client import GeminiClient

        client = GeminiClient(model="gemini-1.5-flash")  # Use flash for faster responses

        small_prompt = "Review this simple code:\n\ndef hello():\n    print('Hello')\n    return True"

        self.metrics.start_measurement("small_prompt_api_call")
        response = client.review_code(small_prompt)
        self.metrics.end_measurement("small_prompt_api_call")

        # Verify response
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 10)

        # Performance assertions
        summary = self.metrics.get_summary()
        duration = summary["small_prompt_api_call"]["duration_seconds"]

        self.assertLess(duration, 10.0, "Small prompt should get response in <10 seconds")
        print(f"Small prompt API call: {duration}s")

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        "Skipping real API performance tests - No API key available",
    )
    def test_medium_prompt_performance(self):
        """Test Gemini API performance with medium prompt."""
        from gemini_client import GeminiClient

        client = GeminiClient(model="gemini-1.5-flash")

        # Create a medium-sized prompt (about 2KB)
        code_sample = (
            "def process_data(items):\n    results = []\n    for item in items:\n        if validate_item(item):\n            processed = transform_item(item)\n            results.append(processed)\n    return results\n\n"
            * 10
        )
        medium_prompt = f"Review this code for best practices:\n\n{code_sample}"

        self.metrics.start_measurement("medium_prompt_api_call")
        response = client.review_code(medium_prompt)
        self.metrics.end_measurement("medium_prompt_api_call")

        # Verify response
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 50)

        # Performance assertions
        summary = self.metrics.get_summary()
        duration = summary["medium_prompt_api_call"]["duration_seconds"]

        self.assertLess(duration, 20.0, "Medium prompt should get response in <20 seconds")
        print(f"Medium prompt API call: {duration}s")

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        "Skipping real API performance tests - No API key available",
    )
    def test_usage_tracking_performance(self):
        """Test usage tracking performance overhead."""
        from gemini_client import GeminiClient

        client = GeminiClient(model="gemini-1.5-flash")

        # Make a small API call to generate usage data
        client.review_code("def test(): pass")

        # Test usage report generation performance
        self.metrics.start_measurement("usage_report_generation")
        for _ in range(100):  # Generate 100 reports
            usage = client.get_usage_report()
        self.metrics.end_measurement("usage_report_generation")

        # Verify usage report
        self.assertIsInstance(usage, dict)
        self.assertIn("total_tokens", usage)

        # Performance assertion
        summary = self.metrics.get_summary()
        duration = summary["usage_report_generation"]["duration_seconds"]

        self.assertLess(duration, 0.1, "100 usage reports should generate in <100ms")
        print(f"Usage tracking (100 reports): {duration}s")


class TestReviewFormatterPerformance(unittest.TestCase):
    """Performance tests for ReviewFormatter component."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.metrics = PerformanceMetrics()
        self.formatter = ReviewFormatter()

    def _create_sample_files(self, num_files: int, avg_size: int) -> Dict[str, str]:
        """Create sample files dictionary for testing."""
        files = {}
        for i in range(num_files):
            file_path = f"src/module_{i}.py"
            content = f"# Module {i}\n" + "x" * (avg_size - 20)
            files[file_path] = content
        return files

    def test_small_format_performance(self):
        """Test review formatting performance with small input."""
        files = self._create_sample_files(5, 500)  # 5 files, 500 bytes each
        file_tree = "src/\n├── module_0.py\n├── module_1.py\n└── ..."

        self.metrics.start_measurement("small_format_request")
        result = self.formatter.format_review_request(files, file_tree)
        self.metrics.end_measurement("small_format_request")

        # Verify formatting worked
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 100)

        # Performance assertion
        summary = self.metrics.get_summary()
        duration = summary["small_format_request"]["duration_seconds"]

        self.assertLess(duration, 0.1, "Small format should take <100ms")
        print(f"Small formatting (5 files): {duration}s")

    def test_medium_format_performance(self):
        """Test review formatting performance with medium input."""
        files = self._create_sample_files(25, 2000)  # 25 files, 2KB each
        file_tree = "src/\n" + "\n".join([f"├── module_{i}.py" for i in range(25)])

        self.metrics.start_measurement("medium_format_request")
        result = self.formatter.format_review_request(files, file_tree)
        self.metrics.end_measurement("medium_format_request")

        # Verify formatting worked
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 1000)

        # Performance assertion
        summary = self.metrics.get_summary()
        duration = summary["medium_format_request"]["duration_seconds"]

        self.assertLess(duration, 0.5, "Medium format should take <500ms")
        print(f"Medium formatting (25 files): {duration}s")

    def test_large_format_performance(self):
        """Test review formatting performance with large input."""
        files = self._create_sample_files(100, 5000)  # 100 files, 5KB each
        file_tree = "src/\n" + "\n".join([f"├── module_{i}.py" for i in range(100)])

        self.metrics.start_measurement("large_format_request")
        result = self.formatter.format_review_request(files, file_tree)
        self.metrics.end_measurement("large_format_request")

        # Verify formatting worked
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 10000)

        # Performance assertion
        summary = self.metrics.get_summary()
        duration = summary["large_format_request"]["duration_seconds"]

        self.assertLess(duration, 2.0, "Large format should take <2 seconds")
        print(f"Large formatting (100 files): {duration}s")


class TestEndToEndPerformance(unittest.TestCase):
    """End-to-end performance tests simulating full review_code workflow."""

    def setUp(self):
        """Set up end-to-end test fixtures."""
        self.metrics = PerformanceMetrics()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create realistic test project
        self._create_realistic_project()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def _create_realistic_project(self):
        """Create a realistic small Python project for testing."""
        # Main module
        (self.temp_path / "main.py").write_text(
            """
#!/usr/bin/env python3
'''Main application entry point.'''

import sys
from utils import helper_function
from models import DataModel

def main():
    '''Main function.'''
    print("Starting application...")

    model = DataModel()
    result = helper_function(model.get_data())

    print(f"Result: {result}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
        )

        # Utils module
        (self.temp_path / "utils.py").write_text(
            """
'''Utility functions for the application.'''

import json
import logging

logger = logging.getLogger(__name__)

def helper_function(data):
    '''Process data using helper logic.'''
    try:
        if not data:
            return None

        processed = [item.upper() for item in data if isinstance(item, str)]
        logger.info(f"Processed {len(processed)} items")

        return processed
    except Exception as e:
        logger.error(f"Error in helper_function: {e}")
        return None

def load_config(config_path):
    '''Load configuration from JSON file.'''
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}")
        return {}
"""
        )

        # Models module
        (self.temp_path / "models.py").write_text(
            """
'''Data models for the application.'''

class DataModel:
    '''Simple data model class.'''

    def __init__(self):
        self.data = ['hello', 'world', 'test', 'data']

    def get_data(self):
        '''Return the stored data.'''
        return self.data

    def add_item(self, item):
        '''Add an item to the data.'''
        if item and isinstance(item, str):
            self.data.append(item)
            return True
        return False

    def clear_data(self):
        '''Clear all stored data.'''
        self.data.clear()
"""
        )

        # Config file
        (self.temp_path / "config.json").write_text(
            """
{
    "app_name": "Test Application",
    "version": "1.0.0",
    "debug": true,
    "log_level": "INFO"
}
"""
        )

        # README
        (self.temp_path / "README.md").write_text(
            """
# Test Application

A simple test application for performance testing.

## Features
- Data processing
- Configuration management
- Logging

## Usage
```bash
python main.py
```
"""
        )

    def test_end_to_end_performance_no_api(self):
        """Test end-to-end performance without API call."""
        # This tests everything except the actual Gemini API call

        self.metrics.start_measurement("e2e_no_api")

        # File collection
        collector = FileCollector()
        files = collector.collect_files(str(self.temp_path))

        # Format request
        formatter = ReviewFormatter()
        file_tree = collector.get_file_tree()
        prompt = formatter.format_review_request(files, file_tree)

        self.metrics.end_measurement("e2e_no_api")

        # Verify components worked
        self.assertGreater(len(files), 0)
        self.assertGreater(len(prompt), 100)

        # Performance assertion
        summary = self.metrics.get_summary()
        duration = summary["e2e_no_api"]["duration_seconds"]
        memory = summary["e2e_no_api"]["memory_delta_mb"]

        self.assertLess(duration, 1.0, "End-to-end (no API) should take <1 second")
        self.assertLess(memory, 20.0, "End-to-end should use <20MB additional memory")

        print(f"End-to-end (no API): {duration}s, {memory}MB")

    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        "Skipping full end-to-end test - No API key available",
    )
    def test_full_end_to_end_performance(self):
        """Test complete end-to-end performance including API call."""

        self.metrics.start_measurement("full_e2e")

        # Complete workflow
        collector = FileCollector()
        files = collector.collect_files(str(self.temp_path))

        formatter = ReviewFormatter()
        file_tree = collector.get_file_tree()
        prompt = formatter.format_review_request(files, file_tree)

        from gemini_client import GeminiClient

        client = GeminiClient(model="gemini-1.5-flash")
        review = client.review_code(prompt)

        usage = client.get_usage_report()

        self.metrics.end_measurement("full_e2e")

        # Verify complete workflow
        self.assertGreater(len(files), 0)
        self.assertGreater(len(review), 50)
        self.assertGreater(usage["total_tokens"], 0)

        # Performance assertion (generous limits for full workflow)
        summary = self.metrics.get_summary()
        duration = summary["full_e2e"]["duration_seconds"]
        memory = summary["full_e2e"]["memory_delta_mb"]

        self.assertLess(duration, 30.0, "Full end-to-end should take <30 seconds")
        self.assertLess(memory, 50.0, "Full end-to-end should use <50MB additional memory")

        print(f"Full end-to-end: {duration}s, {memory}MB, {usage['total_tokens']} tokens")


if __name__ == "__main__":
    # Run with verbose output for performance metrics
    unittest.main(verbosity=2)
