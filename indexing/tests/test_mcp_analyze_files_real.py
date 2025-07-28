# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Real integration tests for analyze_files tool in MCP server."""

import asyncio
import os
import sys
import tempfile
import unittest

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, "src")
sys.path.insert(0, src_dir)
sys.path.insert(0, parent_dir)


class TestAnalyzeFilesRealIntegration(unittest.TestCase):
    """Real integration tests for analyze_files MCP tool without mocks."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test files for analysis
        self.test_files = {}

        # Python file with various code patterns
        self.python_file = os.path.join(self.temp_dir, "sample.py")
        python_content = '''#!/usr/bin/env python3
"""Sample Python module for testing."""

import os
import sys
from typing import List, Dict, Optional

class DataProcessor:
    """Process data with various methods."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.data = []

    def load_data(self, file_path: str) -> List[Dict]:
        """Load data from file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Simple data loading simulation
        return [{"id": 1, "name": "test"}]

    def process_batch(self, items: List[Dict]) -> List[Dict]:
        """Process a batch of items."""
        results = []
        for item in items:
            processed_item = {
                "id": item.get("id"),
                "name": item.get("name", "").upper(),
                "processed": True
            }
            results.append(processed_item)
        return results

    def save_results(self, results: List[Dict], output_path: str) -> None:
        """Save results to file."""
        with open(output_path, 'w') as f:
            for result in results:
                f.write(f"{result}\\n")

def main():
    """Main function."""
    processor = DataProcessor("config.json")
    data = processor.load_data("input.txt")
    results = processor.process_batch(data)
    processor.save_results(results, "output.txt")
    print("Processing complete")

if __name__ == "__main__":
    main()
'''
        with open(self.python_file, "w") as f:
            f.write(python_content)
        self.test_files[self.python_file] = python_content

        # JavaScript file
        self.js_file = os.path.join(self.temp_dir, "utils.js")
        js_content = """/**
 * Utility functions for data processing
 */

class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.timeout = 5000;
    }

    async fetchData(endpoint) {
        const url = `${this.baseUrl}/${endpoint}`;

        try {
            const response = await fetch(url, {
                timeout: this.timeout
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Failed to fetch data from ${url}:`, error);
            throw error;
        }
    }

    processUserData(userData) {
        // Data transformation logic
        return {
            id: userData.id,
            name: userData.full_name || userData.name,
            email: userData.email.toLowerCase(),
            isActive: userData.status === 'active'
        };
    }
}

module.exports = ApiClient;
"""
        with open(self.js_file, "w") as f:
            f.write(js_content)
        self.test_files[self.js_file] = js_content

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mcp_server_has_analyze_files_tool(self):
        """Test that the MCP server properly registers analyze_files tool."""
        # Import server module to verify it loads without errors
        import mcp_review_server

        # Verify the server has the required components
        self.assertTrue(hasattr(mcp_review_server, "main"))
        self.assertTrue(hasattr(mcp_review_server, "FileCollector"))
        self.assertTrue(hasattr(mcp_review_server, "AnalysisFormatter"))
        self.assertTrue(hasattr(mcp_review_server, "GeminiClient"))
        self.assertTrue(hasattr(mcp_review_server, "ReviewFormatter"))

    def test_analysis_formatter_with_real_files(self):
        """Test AnalysisFormatter with real files."""
        from analysis_formatter import AnalysisFormatter

        formatter = AnalysisFormatter()

        # Test with real file content
        files = {self.python_file: self.test_files[self.python_file], self.js_file: self.test_files[self.js_file]}

        custom_prompt = (
            "Analyze these files for code quality, identify potential improvements, and check for best practices."
        )

        result = formatter.format_analysis_request(files, custom_prompt)

        # Verify the analysis request structure
        self.assertIn("You are an expert code analyst", result)
        self.assertIn(custom_prompt, result)
        self.assertIn("**Project Context:**", result)
        self.assertIn("**Codebase Structure:**", result)
        self.assertIn("**Code Files:**", result)
        self.assertIn("**Custom Analysis Instructions:**", result)

        # Verify file content is included
        self.assertIn("sample.py", result)
        self.assertIn("utils.js", result)
        self.assertIn("class DataProcessor", result)
        self.assertIn("class ApiClient", result)
        self.assertIn("```python", result)
        self.assertIn("```javascript", result)

    def test_file_collector_specific_files_real(self):
        """Test FileCollector.collect_specific_files with real files."""
        from file_collector import FileCollector

        collector = FileCollector()

        # Test collecting specific files
        file_paths = [self.python_file, self.js_file]
        collected = collector.collect_specific_files(file_paths)

        # Verify collection results
        self.assertEqual(len(collected), 2)
        self.assertIn(self.python_file, collected)
        self.assertIn(self.js_file, collected)

        # Verify content matches
        self.assertEqual(collected[self.python_file], self.test_files[self.python_file])
        self.assertEqual(collected[self.js_file], self.test_files[self.js_file])

        # Check collection summary
        summary = collector.get_collection_summary()
        self.assertEqual(summary["files_collected"], 2)
        self.assertEqual(summary["files_skipped"], 0)
        self.assertGreater(summary["total_size"], 0)

    def test_file_collector_with_nonexistent_files(self):
        """Test FileCollector handles non-existent files properly."""
        from file_collector import FileCollector

        collector = FileCollector()

        # Mix of existing and non-existent files
        nonexistent_file = os.path.join(self.temp_dir, "does_not_exist.py")
        file_paths = [self.python_file, nonexistent_file, self.js_file]

        collected = collector.collect_specific_files(file_paths)

        # Should only collect existing files
        self.assertEqual(len(collected), 2)
        self.assertIn(self.python_file, collected)
        self.assertIn(self.js_file, collected)
        self.assertNotIn(nonexistent_file, collected)

        # Check that skipped file is tracked
        summary = collector.get_collection_summary()
        self.assertEqual(summary["files_collected"], 2)
        self.assertEqual(summary["files_skipped"], 1)
        self.assertTrue(any("does not exist" in skipped for skipped in summary["skipped_files"]))

    def test_file_collector_with_size_limits(self):
        """Test FileCollector respects file size limits."""
        from file_collector import FileCollector

        # Create a small test file that fits within the limit
        small_file = os.path.join(self.temp_dir, "small.py")
        small_content = "# Small\nprint('ok')\n"  # About 19 bytes
        with open(small_file, "w") as f:
            f.write(small_content)

        # Create a large file
        large_file = os.path.join(self.temp_dir, "large.py")
        large_content = "# Large file\n" + "print('line')\n" * 1000
        with open(large_file, "w") as f:
            f.write(large_content)

        # Set small size limit
        collector = FileCollector(max_file_size=100)  # 100 bytes

        file_paths = [small_file, large_file]
        collected = collector.collect_specific_files(file_paths)

        # Should only collect the small file
        self.assertEqual(len(collected), 1)
        self.assertIn(small_file, collected)
        self.assertNotIn(large_file, collected)

        summary = collector.get_collection_summary()
        self.assertEqual(summary["files_collected"], 1)
        self.assertEqual(summary["files_skipped"], 1)

    def test_integration_file_collection_and_formatting(self):
        """Test integration between FileCollector and AnalysisFormatter."""
        from analysis_formatter import AnalysisFormatter
        from file_collector import FileCollector

        # Collect files
        collector = FileCollector()
        files = collector.collect_specific_files([self.python_file, self.js_file])

        # Format for analysis
        formatter = AnalysisFormatter()
        prompt = "Find potential bugs and suggest improvements"
        analysis_request = formatter.format_analysis_request(files, prompt)

        # Verify integration works
        self.assertIn("Find potential bugs and suggest improvements", analysis_request)
        self.assertIn("DataProcessor", analysis_request)  # From Python file
        self.assertIn("ApiClient", analysis_request)  # From JS file

        # Verify file tree is generated
        self.assertIn("sample.py", analysis_request)
        self.assertIn("utils.js", analysis_request)

    def test_mcp_server_tool_structure_real(self):
        """Test MCP server tool structure with real async execution."""
        import mcp_review_server

        async def test_tool_registration():
            """Test that tools are properly registered."""
            # This tests the actual server setup without mocking
            try:
                # Import should work without errors
                server_module = mcp_review_server

                # Check that all required imports are available
                self.assertTrue(hasattr(server_module, "FileCollector"))
                self.assertTrue(hasattr(server_module, "AnalysisFormatter"))
                self.assertTrue(hasattr(server_module, "ReviewFormatter"))

                # Create instances to verify they work
                file_collector = server_module.FileCollector()
                analysis_formatter = server_module.AnalysisFormatter()
                review_formatter = server_module.ReviewFormatter()

                # Verify instances are created successfully
                self.assertIsNotNone(file_collector)
                self.assertIsNotNone(analysis_formatter)
                self.assertIsNotNone(review_formatter)

                return True

            except Exception as e:
                self.fail(f"Tool registration test failed: {e}")
                return False

        # Run the async test
        result = asyncio.run(test_tool_registration())
        self.assertTrue(result)

    def test_end_to_end_analyze_files_workflow(self):
        """Test the complete analyze_files workflow end-to-end."""
        from analysis_formatter import AnalysisFormatter
        from file_collector import FileCollector

        # Step 1: Collect files (simulates MCP server file collection)
        collector = FileCollector()
        files = collector.collect_specific_files([self.python_file, self.js_file])

        self.assertEqual(len(files), 2)

        # Step 2: Format analysis request (simulates MCP server formatting)
        formatter = AnalysisFormatter()
        custom_prompt = """
        Analyze these code files and provide:
        1. Code quality assessment
        2. Potential bugs or issues
        3. Performance considerations
        4. Best practice recommendations
        5. Security considerations

        Focus on practical, actionable feedback.
        """

        analysis_request = formatter.format_analysis_request(files, custom_prompt)

        # Step 3: Verify the complete workflow produces correct output
        self.assertIn("You are an expert code analyst", analysis_request)
        self.assertIn("Code quality assessment", analysis_request)
        self.assertIn("## File: " + self.python_file, analysis_request)
        self.assertIn("## File: " + self.js_file, analysis_request)
        self.assertIn("```python", analysis_request)
        self.assertIn("```javascript", analysis_request)

        # Verify file content is properly included
        self.assertIn("class DataProcessor", analysis_request)
        self.assertIn("def load_data", analysis_request)
        self.assertIn("class ApiClient", analysis_request)
        self.assertIn("async fetchData", analysis_request)

        # Step 4: Get collection summary (simulates MCP server response formatting)
        summary = collector.get_collection_summary()

        # Verify summary is accurate
        self.assertEqual(summary["files_collected"], 2)
        self.assertEqual(summary["files_skipped"], 0)
        self.assertGreater(summary["total_size"], 0)

        # Total size should match sum of file contents
        expected_size = len(files[self.python_file]) + len(files[self.js_file])
        self.assertEqual(summary["total_size"], expected_size)

    def test_analyze_files_with_different_file_types(self):
        """Test analyze_files workflow with various file types."""
        # Create additional test files
        config_file = os.path.join(self.temp_dir, "config.json")
        config_content = """{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "testdb"
    },
    "api": {
        "timeout": 30000,
        "retries": 3
    },
    "features": {
        "caching": true,
        "logging": "debug"
    }
}"""
        with open(config_file, "w") as f:
            f.write(config_content)

        readme_file = os.path.join(self.temp_dir, "README.md")
        readme_content = """# Test Project

## Overview
This is a test project for analyzing different file types.

## Features
- Data processing capabilities
- API client functionality
- Configuration management

## Usage
```python
processor = DataProcessor("config.json")
data = processor.load_data("input.txt")
```

## Dependencies
- Python 3.8+
- Node.js 14+
"""
        with open(readme_file, "w") as f:
            f.write(readme_content)

        # Test collection of mixed file types
        from analysis_formatter import AnalysisFormatter
        from file_collector import FileCollector

        collector = FileCollector()
        all_files = [self.python_file, self.js_file, config_file, readme_file]
        collected = collector.collect_specific_files(all_files)

        # Should collect all supported file types
        self.assertEqual(len(collected), 4)

        # Test formatting with mixed file types
        formatter = AnalysisFormatter()
        prompt = "Analyze the project structure and configuration"
        result = formatter.format_analysis_request(collected, prompt)

        # Should include all file types with appropriate syntax highlighting
        self.assertIn("```python", result)
        self.assertIn("```javascript", result)
        self.assertIn("```json", result)
        self.assertIn("```markdown", result)

        # Should include content from all files
        self.assertIn("DataProcessor", result)
        self.assertIn("ApiClient", result)
        self.assertIn("database", result)
        self.assertIn("Test Project", result)


if __name__ == "__main__":
    unittest.main()
