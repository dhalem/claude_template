#!/usr/bin/env python3
"""
Real MCP server test suite - NO MOCKS, NO FALLBACKS, NO CHEATING

These tests are designed to FAIL if the MCP server implementation is wrong.
They test the actual MCP protocol as Claude Code would use it.
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict


class MCPServerTester:
    """Test MCP server with real protocol interactions"""

    def __init__(self, server_cmd):
        self.server_cmd = server_cmd
        self.server_process = None

    def start_server(self) -> subprocess.Popen:
        """Start the MCP server process"""
        print(f"Starting MCP server: {self.server_cmd}")

        # Start server with proper stdio handling
        process = subprocess.Popen(
            self.server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )

        # Give server time to initialize
        time.sleep(0.1)

        if process.poll() is not None:
            stderr_output = process.stderr.read()
            raise Exception(f"Server failed to start: {stderr_output}")

        self.server_process = process
        return process

    def stop_server(self):
        """Stop the MCP server"""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            self.server_process = None

    def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server and get response"""
        if not self.server_process:
            raise Exception("Server not started")

        # Send request
        request_line = json.dumps(request) + "\n"
        print(f"→ Sending: {request_line.strip()}")

        self.server_process.stdin.write(request_line)
        self.server_process.stdin.flush()

        # Read response with timeout
        try:
            response_line = self.server_process.stdout.readline()
            if not response_line:
                # Check if process died
                if self.server_process.poll() is not None:
                    stderr_output = self.server_process.stderr.read()
                    raise Exception(f"Server died: {stderr_output}")
                raise Exception("No response from server")

            print(f"← Received: {response_line.strip()}")
            return json.loads(response_line.strip())

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {response_line.strip()}")

    def test_server_initialization(self):
        """Test MCP server initialization sequence"""
        print("\n=== Testing Server Initialization ===")

        # Test 1: Server should respond to initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        response = self.send_request(init_request)

        # Verify response structure
        assert "jsonrpc" in response, f"Missing jsonrpc in response: {response}"
        assert response["jsonrpc"] == "2.0", f"Wrong jsonrpc version: {response}"
        assert "id" in response, f"Missing id in response: {response}"
        assert response["id"] == 1, f"Wrong id in response: {response}"
        assert "result" in response, f"Missing result in response: {response}"

        result = response["result"]
        assert "protocolVersion" in result, f"Missing protocolVersion: {result}"
        assert "capabilities" in result, f"Missing capabilities: {result}"
        assert "serverInfo" in result, f"Missing serverInfo: {result}"

        print("✅ Initialization test passed")
        return response

    def test_tools_list(self):
        """Test tools/list method"""
        print("\n=== Testing Tools List ===")

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        response = self.send_request(request)

        # Verify response structure
        assert "result" in response, f"Missing result in response: {response}"
        assert "tools" in response["result"], f"Missing tools in result: {response['result']}"

        tools = response["result"]["tools"]
        assert isinstance(tools, list), f"Tools should be a list: {tools}"
        assert len(tools) > 0, f"Should have at least one tool: {tools}"

        # Verify each tool has required fields
        for tool in tools:
            assert "name" in tool, f"Tool missing name: {tool}"
            assert "description" in tool, f"Tool missing description: {tool}"
            assert "inputSchema" in tool, f"Tool missing inputSchema: {tool}"

        # Verify specific tools exist
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["search_code", "list_symbols", "explore_file"]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Missing expected tool: {expected_tool}"

        print(f"✅ Tools list test passed - found tools: {tool_names}")
        return tools

    def test_search_code_tool(self):
        """Test search_code tool execution"""
        print("\n=== Testing Search Code Tool ===")

        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {
                    "query": "get_metadata",
                    "limit": 5
                }
            }
        }

        response = self.send_request(request)

        # Verify response structure
        assert "result" in response, f"Missing result in response: {response}"
        result = response["result"]

        assert "content" in result, f"Missing content in result: {result}"
        content = result["content"]
        assert isinstance(content, list), f"Content should be a list: {content}"
        assert len(content) > 0, f"Should have content: {content}"

        # Verify content structure
        first_content = content[0]
        assert "type" in first_content, f"Missing type in content: {first_content}"
        assert first_content["type"] == "text", f"Wrong content type: {first_content}"
        assert "text" in first_content, f"Missing text in content: {first_content}"

        # Parse the text content as JSON (should be search results)
        search_results = json.loads(first_content["text"])
        assert "success" in search_results, f"Missing success in results: {search_results}"
        assert search_results["success"] is True, f"Search should succeed: {search_results}"
        assert "results" in search_results, f"Missing results: {search_results}"

        print(f"✅ Search code test passed - found {len(search_results['results'])} results")
        return search_results

    def test_invalid_method(self):
        """Test handling of invalid method"""
        print("\n=== Testing Invalid Method Handling ===")

        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "invalid/method",
            "params": {}
        }

        response = self.send_request(request)

        # Should return an error
        assert "error" in response, f"Should return error for invalid method: {response}"
        error = response["error"]
        assert "code" in error, f"Missing error code: {error}"
        assert "message" in error, f"Missing error message: {error}"

        print("✅ Invalid method test passed")
        return response

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        print("\n=== Testing Malformed JSON Handling ===")

        # Send malformed JSON
        malformed_json = '{"invalid": json,}\n'
        print(f"→ Sending malformed: {malformed_json.strip()}")

        self.server_process.stdin.write(malformed_json)
        self.server_process.stdin.flush()

        # Should get error response
        response_line = self.server_process.stdout.readline()
        print(f"← Received: {response_line.strip()}")

        response = json.loads(response_line.strip())
        assert "error" in response, f"Should return error for malformed JSON: {response}"
        assert response["error"]["code"] == -32700, f"Should be parse error: {response}"

        print("✅ Malformed JSON test passed")
        return response

    def test_concurrent_requests(self):
        """Test multiple requests in sequence"""
        print("\n=== Testing Concurrent Requests ===")

        # Send multiple requests
        requests = [
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "search_code",
                    "arguments": {
                        "query": f"test{i}",
                        "limit": 1
                    }
                }
            }
            for i in range(5, 8)
        ]

        responses = []
        for request in requests:
            response = self.send_request(request)
            responses.append(response)

            # Verify we get responses in order
            assert response["id"] == request["id"], f"Response ID mismatch: {response}"

        print("✅ Concurrent requests test passed")
        return responses


def test_startup_script():
    """Test the actual startup script"""
    print("\n=== Testing Startup Script ===")

    startup_script = os.path.expanduser("~/.claude/mcp/start-search-server.sh")
    if not os.path.exists(startup_script):
        raise Exception(f"Startup script not found: {startup_script}")

    # Test that startup script can be executed
    result = subprocess.run(
        ["bash", "-c", f"timeout 5s bash {startup_script}"],
        input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
        capture_output=True,
        text=True
    )

    # Should not exit with error code
    if result.returncode == 124:  # timeout
        print("✅ Startup script runs (timed out as expected)")
    elif result.returncode != 0:
        raise Exception(f"Startup script failed: {result.stderr}")
    else:
        print("✅ Startup script test passed")


def main():
    """Run all MCP server tests"""
    print("🧪 MCP Server Test Suite - NO MOCKS, NO FALLBACKS")
    print("=" * 60)

    # Test 1: Check if server file exists
    server_script = os.path.expanduser("~/.claude/mcp/code-search-server.py")
    venv_python = os.path.expanduser("~/.claude/mcp/venv/bin/python3")

    if not os.path.exists(server_script):
        print(f"❌ Server script not found: {server_script}")
        sys.exit(1)

    if not os.path.exists(venv_python):
        print(f"❌ Venv python not found: {venv_python}")
        sys.exit(1)

    # Test 2: Test startup script
    try:
        test_startup_script()
    except Exception as e:
        print(f"❌ Startup script test failed: {e}")
        sys.exit(1)

    # Test 3: Test MCP server protocol
    server_cmd = [venv_python, server_script]
    tester = MCPServerTester(server_cmd)

    try:
        # Start server
        tester.start_server()

        # Run protocol tests
        tester.test_server_initialization()
        tester.test_tools_list()
        tester.test_search_code_tool()
        tester.test_invalid_method()
        tester.test_malformed_json()
        tester.test_concurrent_requests()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - MCP server implementation is correct!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 60)
        print("💥 MCP server implementation is BROKEN")
        sys.exit(1)

    finally:
        tester.stop_server()


if __name__ == "__main__":
    main()
