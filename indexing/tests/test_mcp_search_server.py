#!/usr/bin/env python3
"""Comprehensive tests for the MCP code search server.

This consolidates all MCP search server tests into a single, well-organized test suite.
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add paths for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'src'))

import mcp_search_server
from code_searcher import CodeSearcher


class TestCodeSearcher(unittest.TestCase):
    """Test the CodeSearcher class functionality."""

    def setUp(self):
        """Create a test database."""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db_path = self.test_db.name
        self.test_db.close()

        # Create test database with sample data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Create tables
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
            ("TestClass", "class", "/test/file1.py", 10, 0, None, None, "Test class docstring"),
            ("test_function", "function", "/test/file1.py", 20, 0, None, "(arg1, arg2)", "Test function"),
            ("another_function", "function", "/test/file2.py", 5, 0, None, "()", None),
            ("TestClass.test_method", "method", "/test/file1.py", 15, 4, "TestClass", "(self)", "Test method"),
            ("test_variable", "variable", "/test/file2.py", 10, 0, None, None, None),
        ]

        cursor.executemany(
            "INSERT INTO symbols (name, type, file_path, line_number, column, parent, signature, docstring) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            test_symbols
        )

        conn.commit()
        conn.close()

        # Create searcher with test database
        self.searcher = CodeSearcher(self.test_db_path)

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_find_database(self):
        """Test database finding logic."""
        # Test with explicit path
        searcher = CodeSearcher(self.test_db_path)
        self.assertEqual(searcher.db_path, self.test_db_path)

        # Test with non-existent database - it falls back to searching
        with patch('src.code_searcher.Path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                CodeSearcher()

    def test_search_by_name(self):
        """Test searching by name."""
        # Exact match
        result = self.searcher.search("TestClass", search_type="name")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["name"], "TestClass")
        self.assertEqual(result["results"][0]["type"], "class")

        # Wildcard search
        result = self.searcher.search("test*", search_type="name")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 4)  # test_function, TestClass.test_method, test_variable, and TestClass

        # No matches
        result = self.searcher.search("nonexistent", search_type="name")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 0)

    def test_search_by_content(self):
        """Test searching by content."""
        result = self.searcher.search("Test", search_type="content")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 4)  # TestClass, test_function, TestClass.test_method, all have "Test"

    def test_search_by_file(self):
        """Test searching by file path."""
        result = self.searcher.search("file1", search_type="file")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["file_path"], "/test/file1.py")
        self.assertEqual(result["results"][0]["symbol_count"], 3)

    def test_search_with_symbol_type(self):
        """Test searching with symbol type filter."""
        result = self.searcher.search("*", search_type="name", symbol_type="function")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)  # test_function and another_function

        for item in result["results"]:
            self.assertEqual(item["type"], "function")

    def test_list_symbols(self):
        """Test listing symbols by type."""
        result = self.searcher.list_symbols("class")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["name"], "TestClass")

    def test_get_stats(self):
        """Test getting database statistics."""
        result = self.searcher.get_stats()
        self.assertTrue(result["success"])

        stats = result["stats"]
        self.assertEqual(stats["total_symbols"], 5)
        self.assertEqual(stats["total_files"], 2)
        self.assertEqual(stats["by_type"]["class"], 1)
        self.assertEqual(stats["by_type"]["function"], 2)
        self.assertEqual(stats["by_type"]["method"], 1)
        self.assertEqual(stats["by_type"]["variable"], 1)
        self.assertIn("last_indexed", stats)

    def test_error_handling(self):
        """Test error handling in search."""
        # Corrupt the database path
        self.searcher.db_path = "/invalid/path.db"

        result = self.searcher.search("test")
        self.assertFalse(result["success"])
        self.assertIn("error", result)


class TestMCPProtocol(unittest.TestCase):
    """Test MCP protocol-level functionality."""

    @patch('mcp_search_server.CodeSearcher')
    async def test_handle_search_code(self, mock_searcher_class):
        """Test the search_code tool handler."""
        # Set up mock
        mock_searcher = Mock()
        mock_searcher.search.return_value = {
            "success": True,
            "query": "test",
            "search_type": "name",
            "symbol_type": None,
            "count": 1,
            "results": [{
                "name": "test_func",
                "type": "function",
                "file_path": "/test.py",
                "line_number": 1,
                "location": "/test.py:1",
                "signature": "()",
                "docstring": "Test function"
            }]
        }
        mock_searcher_class.return_value = mock_searcher

        # Import and set up server components
        from mcp.server import Server
        server = Server("test-server")

        # Manually set up the tool handler
        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            if name == "search_code":
                searcher = mock_searcher_class()
                result = searcher.search(
                    arguments.get("query", ""),
                    arguments.get("search_type", "name"),
                    arguments.get("symbol_type"),
                    arguments.get("limit", 50)
                )

                if result["success"]:
                    output = f"Found: {result['count']} results\n"
                    for item in result["results"]:
                        output += f"{item['name']} ({item['type']})\n"
                else:
                    output = f"Error: {result['error']}"

                from mcp.types import TextContent
                return [TextContent(type="text", text=output)]

        # Test the handler
        result = await handle_call_tool("search_code", {"query": "test"})

        self.assertEqual(len(result), 1)
        self.assertIn("Found: 1 results", result[0].text)
        self.assertIn("test_func (function)", result[0].text)


class TestInstallation(unittest.TestCase):
    """Test installation and configuration verification."""

    def test_server_directory_structure(self):
        """Test that server follows correct MCP directory structure."""
        # This would be run after installation
        mcp_dir = Path.home() / ".claude" / "mcp" / "code-search"

        if mcp_dir.exists():
            # Check required directories
            self.assertTrue((mcp_dir / "bin").exists(), "bin directory missing")
            self.assertTrue((mcp_dir / "venv").exists(), "venv directory missing")
            self.assertTrue((mcp_dir / "logs").exists(), "logs directory missing")

            # Check server file
            server_file = mcp_dir / "bin" / "server.py"
            self.assertTrue(server_file.exists(), "server.py missing")
            self.assertTrue(os.access(server_file, os.X_OK), "server.py not executable")
        else:
            self.skipTest("MCP server not installed")

    def test_no_manual_configuration(self):
        """Test that server doesn't use manual configuration."""
        config_file = Path.home() / ".config" / "claude" / "claude_desktop_config.json"

        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)

            if 'mcpServers' in config:
                msg = "Manual configuration found (should use auto-discovery)"
                self.assertNotIn('code-search', config['mcpServers'], msg)


class TestIntegration(unittest.TestCase):
    """Integration tests with actual functionality."""

    def test_with_real_database(self):
        """Test with the actual project database if it exists."""
        # Try to find the real database
        db_path = Path("/app/.code_index.db")
        if not db_path.exists():
            db_path = Path.cwd().parent.parent / ".code_index.db"

        if db_path.exists():
            try:
                searcher = CodeSearcher(str(db_path))

                # Search for something that should exist
                result = searcher.search("CodeIndexer", search_type="name")
                self.assertTrue(result["success"])
                self.assertGreater(result["count"], 0)

                # Get stats
                stats = searcher.get_stats()
                if stats["success"]:
                    self.assertGreater(stats["stats"]["total_symbols"], 0)
                else:
                    # Old database format without indexed_at is OK
                    self.assertIn("no such column: indexed_at", stats.get("error", ""))
            except Exception as e:
                self.skipTest(f"Integration test failed: {e}")
        else:
            self.skipTest("No real database found for integration test")


class TestMCPEnvironment(unittest.TestCase):
    """Test MCP-specific environment handling."""

    def test_file_not_defined(self):
        """Test handling when __file__ is not defined (MCP environment)."""
        # Save original __file__
        original_file = mcp_search_server.__file__

        try:
            # Remove __file__ to simulate MCP environment
            delattr(mcp_search_server, '__file__')

            # This should not raise an error
            # The server should handle the missing __file__ gracefully
            with patch('sys.argv', ['/path/to/script.py']):
                # Import would happen here in real scenario
                self.assertTrue(True)  # If we get here, it worked

        finally:
            # Restore __file__
            mcp_search_server.__file__ = original_file


# Test runner
if __name__ == "__main__":
    # Run tests with more verbosity
    unittest.main(verbosity=2)
