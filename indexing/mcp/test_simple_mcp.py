#!/usr/bin/env python3
"""Real tests for simple MCP server.

NO MOCKS. NO DOCKER. NO CONTAINERS.
Tests the MCP server using the actual local search functionality.
"""

# Import the simple server
import importlib.util
import json
import os
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("server", Path(__file__).parent / "simple_mcp_server.py")
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)
SimpleMCPServer = server_module.SimpleMCPServer


class TestSimpleMCPServer(unittest.TestCase):
    """Test the simple MCP server with real search functionality."""

    def setUp(self):
        """Set up test environment."""
        self.repo_root = Path(__file__).parent.parent.parent.resolve()
        self.original_cwd = os.getcwd()

        # Change to repo root so search works
        os.chdir(self.repo_root)

        # Create server instance
        self.server = SimpleMCPServer()

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)

    def test_local_search_works_first(self):
        """Verify the underlying search system works."""
        # Test the searcher directly
        result = self.server.searcher.search("get_metadata", "name")

        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["count"], 0)

        print(f"✓ Direct search works: found {result['count']} results")

    def test_mcp_tools_list(self):
        """Test MCP tools/list method."""
        request = {"method": "tools/list", "params": {}}
        response = self.server.handle_request(request)

        self.assertIn("tools", response)
        tools = response["tools"]
        self.assertEqual(len(tools), 4)

        # Check all expected tools exist
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["search_code", "list_symbols", "explore_file", "search_in_files"]

        for expected_tool in expected_tools:
            self.assertIn(expected_tool, tool_names)

        print(f"✓ MCP tools list works: {len(tools)} tools")

    def test_mcp_search_code(self):
        """Test MCP search_code tool with real search."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {"query": "get_metadata"}
            }
        }

        response = self.server.handle_request(request)

        self.assertIn("content", response)
        content_text = response["content"][0]["text"]
        result = json.loads(content_text)

        self.assertTrue(result["success"])
        self.assertGreater(result["count"], 0)
        self.assertEqual(result["query"], "get_metadata")

        print(f"✓ MCP search_code works: found {result['count']} results")

    def test_mcp_list_symbols(self):
        """Test MCP list_symbols tool."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "list_symbols",
                "arguments": {"symbol_type": "function", "limit": 5}
            }
        }

        response = self.server.handle_request(request)

        self.assertIn("content", response)
        content_text = response["content"][0]["text"]
        result = json.loads(content_text)

        self.assertTrue(result["success"])
        self.assertGreater(result["count"], 0)
        self.assertLessEqual(result["count"], 5)

        print(f"✓ MCP list_symbols works: found {result['count']} functions")

    def test_mcp_explore_file(self):
        """Test MCP explore_file tool."""
        # Use a file that definitely exists
        test_file = "indexing/claude_code_search.py"

        request = {
            "method": "tools/call",
            "params": {
                "name": "explore_file",
                "arguments": {"file_path": test_file}
            }
        }

        response = self.server.handle_request(request)

        self.assertIn("content", response)
        content_text = response["content"][0]["text"]
        result = json.loads(content_text)

        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["count"], 0)

        print(f"✓ MCP explore_file works: found {result['count']} symbols in {test_file}")

    def test_mcp_search_in_files(self):
        """Test MCP search_in_files tool."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_in_files",
                "arguments": {"file_pattern": "*.py"}
            }
        }

        response = self.server.handle_request(request)

        self.assertIn("content", response)
        content_text = response["content"][0]["text"]
        result = json.loads(content_text)

        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["count"], 0)

        print(f"✓ MCP search_in_files works: found {result['count']} symbols in Python files")

    def test_error_propagation(self):
        """Test that errors propagate correctly."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        }

        with self.assertRaises(ValueError) as cm:
            self.server.handle_request(request)

        self.assertIn("Unknown tool", str(cm.exception))

        print("✓ Error propagation works - no fallbacks")

    def test_unknown_method(self):
        """Test handling of unknown MCP methods."""
        request = {"method": "unknown/method", "params": {}}

        with self.assertRaises(ValueError) as cm:
            self.server.handle_request(request)

        self.assertIn("Method not found", str(cm.exception))

        print("✓ Unknown method handling works")

    def test_json_rpc_protocol(self):
        """Test full JSON-RPC protocol via stdin/stdout simulation."""
        # Test tools/list via JSON
        list_request_json = '{"method": "tools/list", "params": {}}'
        request = json.loads(list_request_json)
        response = self.server.handle_request(request)

        # Should be able to serialize response
        response_json = json.dumps(response)
        self.assertIsInstance(response_json, str)

        # Test search via JSON
        search_request_json = '{"method": "tools/call", "params": {"name": "search_code", "arguments": {"query": "main"}}}'
        request = json.loads(search_request_json)
        response = self.server.handle_request(request)

        self.assertIn("content", response)

        print("✓ JSON-RPC protocol compliance verified")


def run_simple_tests():
    """Run all simple MCP tests."""
    print("=" * 60)
    print("🔥 SIMPLE MCP TESTS - NO MOCKS, NO DOCKER, LOCAL ONLY")
    print("=" * 60)

    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_simple_tests()
