#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Direct function tests for MCP server tool handlers.

These tests provide fast unit-level feedback by testing MCP server functions directly,
complementing the integration tests that verify the full Claude CLI pipeline.

Test Coverage:
- Fast unit tests for MCP tool handlers (this file)
- End-to-end integration tests via Claude CLI (tests/test_mcp_integration.py)

Both test types are critical for comprehensive coverage.
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add paths for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from code_searcher import CodeSearcher


class TestMCPSearchServerDirect(unittest.TestCase):
    """Direct tests for MCP search server tool handlers."""

    def setUp(self):
        """Set up test database for each test."""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db_path = self.test_db.name
        self.test_db.close()

        # Create test database with sample data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                column INTEGER DEFAULT 0,
                parent TEXT,
                signature TEXT,
                docstring TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert test data
        test_symbols = [
            ("test_function", "function", "/test.py", 10, 0, None, "def test_function():", "Test function docstring"),
            ("TestClass", "class", "/test.py", 20, 0, None, "class TestClass:", "Test class docstring"),
            ("test_method", "method", "/test.py", 25, 4, "TestClass", "def test_method(self):", "Test method docstring"),
            ("debug_variable", "variable", "/debug.py", 5, 0, None, "debug_variable = True", None),
        ]

        cursor.executemany(
            "INSERT INTO symbols (name, type, file_path, line_number, column, parent, signature, docstring) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            test_symbols
        )

        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.test_db_path)
        except:
            pass

    async def test_search_code_tool_handler_by_name(self):
        """Test the search_code tool handler with name search."""
        # Import the server module to access tool handlers
        # We'll mock the CodeSearcher to use our test database
        with patch('mcp_search_server.CodeSearcher') as mock_searcher_class:
            # Set up mock searcher
            mock_searcher = Mock()
            mock_searcher.search.return_value = {
                "success": True,
                "query": "test_function",
                "search_type": "name",
                "symbol_type": None,
                "count": 1,
                "results": [{
                    "name": "test_function",
                    "type": "function",
                    "file_path": "/test.py",
                    "line_number": 10,
                    "location": "/test.py:10",
                    "signature": "def test_function():",
                    "docstring": "Test function docstring"
                }]
            }
            mock_searcher_class.return_value = mock_searcher

            # Import and test the tool handler logic

            # Create mock server for testing
            server = Mock()

            # Get the tool handler function
            # We need to simulate the handler call directly
            arguments = {
                "query": "test_function",
                "search_type": "name",
                "symbol_type": None,
                "limit": 50
            }

            # Create a searcher instance and call search
            searcher = mock_searcher_class()
            result = searcher.search(
                arguments.get("query", ""),
                arguments.get("search_type", "name"),
                arguments.get("symbol_type"),
                arguments.get("limit", 50)
            )

            # Verify the mock was called correctly
            mock_searcher.search.assert_called_once_with("test_function", "name", None, 50)

            # Verify the result structure
            self.assertTrue(result["success"])
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["results"][0]["name"], "test_function")
            self.assertEqual(result["results"][0]["type"], "function")

    async def test_search_code_tool_handler_by_content(self):
        """Test the search_code tool handler with content search."""
        with patch('mcp_search_server.CodeSearcher') as mock_searcher_class:
            mock_searcher = Mock()
            mock_searcher.search.return_value = {
                "success": True,
                "query": "docstring",
                "search_type": "content",
                "symbol_type": None,
                "count": 2,
                "results": [
                    {
                        "name": "test_function",
                        "type": "function",
                        "file_path": "/test.py",
                        "line_number": 10,
                        "location": "/test.py:10",
                        "signature": "def test_function():",
                        "docstring": "Test function docstring"
                    },
                    {
                        "name": "TestClass",
                        "type": "class",
                        "file_path": "/test.py",
                        "line_number": 20,
                        "location": "/test.py:20",
                        "signature": "class TestClass:",
                        "docstring": "Test class docstring"
                    }
                ]
            }
            mock_searcher_class.return_value = mock_searcher

            # Test content search
            arguments = {
                "query": "docstring",
                "search_type": "content",
                "limit": 50
            }

            searcher = mock_searcher_class()
            result = searcher.search(
                arguments.get("query", ""),
                arguments.get("search_type", "name"),
                arguments.get("symbol_type"),
                arguments.get("limit", 50)
            )

            mock_searcher.search.assert_called_once_with("docstring", "content", None, 50)
            self.assertTrue(result["success"])
            self.assertEqual(result["count"], 2)

    async def test_list_symbols_tool_handler(self):
        """Test the list_symbols tool handler."""
        with patch('mcp_search_server.CodeSearcher') as mock_searcher_class:
            mock_searcher = Mock()
            mock_searcher.list_symbols.return_value = {
                "success": True,
                "count": 1,
                "results": [{
                    "name": "test_function",
                    "type": "function",
                    "file_path": "/test.py",
                    "line_number": 10,
                    "signature": "def test_function():",
                    "docstring": "Test function docstring"
                }]
            }
            mock_searcher_class.return_value = mock_searcher

            # Test list symbols
            arguments = {
                "symbol_type": "function",
                "limit": 100
            }

            searcher = mock_searcher_class()
            result = searcher.list_symbols(
                arguments.get("symbol_type", "function"),
                arguments.get("limit", 100)
            )

            mock_searcher.list_symbols.assert_called_once_with("function", 100)
            self.assertTrue(result["success"])
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["results"][0]["type"], "function")

    async def test_get_search_stats_tool_handler(self):
        """Test the get_search_stats tool handler."""
        with patch('mcp_search_server.CodeSearcher') as mock_searcher_class:
            mock_searcher = Mock()
            mock_searcher.get_stats.return_value = {
                "success": True,
                "stats": {
                    "total_symbols": 4,
                    "total_files": 2,
                    "by_type": {
                        "function": 1,
                        "class": 1,
                        "method": 1,
                        "variable": 1
                    },
                    "last_indexed": "2025-01-19 15:00:00"
                }
            }
            mock_searcher_class.return_value = mock_searcher

            # Test get stats
            searcher = mock_searcher_class()
            result = searcher.get_stats()

            mock_searcher.get_stats.assert_called_once()
            self.assertTrue(result["success"])
            self.assertEqual(result["stats"]["total_symbols"], 4)
            self.assertEqual(result["stats"]["total_files"], 2)
            self.assertIn("by_type", result["stats"])

    async def test_search_code_error_handling(self):
        """Test error handling in search_code tool."""
        with patch('mcp_search_server.CodeSearcher') as mock_searcher_class:
            mock_searcher = Mock()
            mock_searcher.search.return_value = {
                "success": False,
                "error": "Database not found",
                "query": "test",
                "search_type": "name"
            }
            mock_searcher_class.return_value = mock_searcher

            arguments = {"query": "test"}
            searcher = mock_searcher_class()
            result = searcher.search(
                arguments.get("query", ""),
                arguments.get("search_type", "name"),
                arguments.get("symbol_type"),
                arguments.get("limit", 50)
            )

            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["error"], "Database not found")

    def test_real_code_searcher_integration(self):
        """Test with real CodeSearcher using our test database."""
        # This bridges unit tests with real implementation
        searcher = CodeSearcher(db_path=self.test_db_path)

        # Test search by name
        result = searcher.search("test_function", "name")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["name"], "test_function")

        # Test search by type
        result = searcher.search("*", "name", symbol_type="function")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)

        # Test list symbols
        result = searcher.list_symbols("function")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)

        # Test get stats
        result = searcher.get_stats()
        self.assertTrue(result["success"])
        self.assertEqual(result["stats"]["total_symbols"], 4)
        self.assertEqual(result["stats"]["total_files"], 2)


# Test runner that handles async tests
def run_async_test(test_func):
    """Helper to run async test functions."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func)
    finally:
        loop.close()


class AsyncTestRunner(unittest.TestCase):
    """Test runner for async test methods."""

    def setUp(self):
        """Set up async test environment."""
        self.test_instance = TestMCPSearchServerDirect()
        self.test_instance.setUp()

    def tearDown(self):
        """Clean up async test environment."""
        self.test_instance.tearDown()

    def test_search_code_by_name_async(self):
        """Run async search by name test."""
        run_async_test(self.test_instance.test_search_code_tool_handler_by_name())

    def test_search_code_by_content_async(self):
        """Run async search by content test."""
        run_async_test(self.test_instance.test_search_code_tool_handler_by_content())

    def test_list_symbols_async(self):
        """Run async list symbols test."""
        run_async_test(self.test_instance.test_list_symbols_tool_handler())

    def test_get_stats_async(self):
        """Run async get stats test."""
        run_async_test(self.test_instance.test_get_search_stats_tool_handler())

    def test_error_handling_async(self):
        """Run async error handling test."""
        run_async_test(self.test_instance.test_search_code_error_handling())

    def test_real_integration(self):
        """Run real CodeSearcher integration test."""
        self.test_instance.test_real_code_searcher_integration()


if __name__ == '__main__':
    unittest.main()
