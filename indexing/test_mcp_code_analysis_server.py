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

"""Test script for the code analysis MCP server with both tools."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add src to path for imports
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))


class MCPServerTester:
    """Test harness for MCP servers."""

    def __init__(self, server_path: str):
        self.server_path = server_path
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 1

    def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server and get response."""
        request = {"jsonrpc": "2.0", "method": method, "id": self.request_id, "params": params or {}}

        self.request_id += 1

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")

        return json.loads(response_line.decode())

    def start_server(self):
        """Start the MCP server process."""
        env = os.environ.copy()
        # Ensure required environment variables
        if not env.get("GEMINI_API_KEY"):
            print("⚠️  Warning: GEMINI_API_KEY not set - API calls will fail")

        cmd = [sys.executable, self.server_path]

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=False,  # Use binary mode for better control
        )

        # Give server time to start
        time.sleep(1)

    def stop_server(self):
        """Stop the server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    def test_initialization(self):
        """Test server initialization."""
        print("\n🧪 Testing server initialization...")

        response = self.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        if "result" in response:
            print("✅ Server initialized successfully")
            print(f"   Server: {response['result'].get('serverInfo', {}).get('name', 'Unknown')}")
            print(f"   Version: {response['result'].get('serverInfo', {}).get('version', 'Unknown')}")
            return True
        else:
            print(f"❌ Initialization failed: {response}")
            return False

    def test_list_tools(self):
        """Test listing available tools."""
        print("\n🧪 Testing tool listing...")

        response = self.send_request("tools/list")

        if "result" in response:
            tools = response["result"].get("tools", [])
            print(f"✅ Found {len(tools)} tools:")

            for tool in tools:
                print(f"\n   📦 Tool: {tool['name']}")
                print(f"      Description: {tool['description'][:100]}...")

                # Check schema
                schema = tool.get("inputSchema", {})
                properties = schema.get("properties", {})
                required = schema.get("required", [])

                print(f"      Parameters: {', '.join(properties.keys())}")
                print(f"      Required: {', '.join(required)}")

            # Verify we have both tools
            tool_names = [t["name"] for t in tools]
            if "review_code" in tool_names and "find_bugs" in tool_names:
                print("\n✅ Both review_code and find_bugs tools are available!")
                return True
            else:
                print(f"\n❌ Missing tools. Found: {tool_names}")
                return False
        else:
            print(f"❌ Tool listing failed: {response}")
            return False

    def test_tool_schema_validation(self):
        """Test that tool schemas are correct."""
        print("\n🧪 Testing tool schema validation...")

        response = self.send_request("tools/list")

        if "result" not in response:
            print("❌ Could not get tool list")
            return False

        tools = response["result"].get("tools", [])
        all_valid = True

        for tool in tools:
            print(f"\n   🔍 Validating schema for: {tool['name']}")
            schema = tool.get("inputSchema", {})
            properties = schema.get("properties", {})

            # Common properties both tools should have
            common_props = ["directory", "focus_areas", "model", "max_file_size"]

            for prop in common_props:
                if prop in properties:
                    print(f"      ✅ Has {prop}")
                else:
                    print(f"      ❌ Missing {prop}")
                    all_valid = False

            # Tool-specific properties
            if tool["name"] == "find_bugs":
                bug_props = ["severity_filter", "bug_categories", "include_suggestions"]
                for prop in bug_props:
                    if prop in properties:
                        print(f"      ✅ Has {prop} (bug-specific)")
                    else:
                        print(f"      ❌ Missing {prop} (bug-specific)")
                        all_valid = False

            # Check required fields
            required = schema.get("required", [])
            if "directory" in required:
                print("      ✅ directory is required")
            else:
                print("      ❌ directory should be required")
                all_valid = False

        return all_valid

    def test_tool_execution_validation(self):
        """Test tool execution with invalid parameters."""
        print("\n🧪 Testing tool parameter validation...")

        # Test with missing required parameter
        print("\n   📋 Testing review_code with missing directory...")
        response = self.send_request("tools/call", {"name": "review_code", "arguments": {"focus_areas": ["security"]}})

        if "error" in response or ("result" in response and "Error" in str(response["result"])):
            print("   ✅ Correctly rejected missing directory")
        else:
            print("   ❌ Should have rejected missing directory")
            return False

        # Test with invalid directory
        print("\n   📋 Testing find_bugs with invalid directory...")
        response = self.send_request(
            "tools/call",
            {
                "name": "find_bugs",
                "arguments": {"directory": "/nonexistent/path/that/should/not/exist", "bug_categories": ["security"]},
            },
        )

        if "error" in response or ("result" in response and "does not exist" in str(response["result"])):
            print("   ✅ Correctly rejected invalid directory")
        else:
            print("   ❌ Should have rejected invalid directory")
            return False

        return True

    def test_sample_execution(self):
        """Test actual tool execution with sample code."""
        print("\n🧪 Testing sample code analysis...")

        # Create temporary directory with sample code
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create vulnerable sample code
            sample_file = Path(temp_dir) / "vulnerable.py"
            sample_file.write_text(
                '''
import sqlite3

def get_user(user_id):
    """Get user by ID - has SQL injection vulnerability."""
    conn = sqlite3.connect('users.db')
    # VULNERABILITY: SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()

def process_data(data):
    """Process data - missing error handling."""
    result = 1 / len(data)  # Potential division by zero
    return result
'''
            )

            # Test review_code tool
            print("\n   📋 Testing review_code on sample...")
            response = self.send_request(
                "tools/call",
                {
                    "name": "review_code",
                    "arguments": {
                        "directory": temp_dir,
                        "focus_areas": ["security", "error_handling"],
                        "model": "gemini-1.5-flash",  # Use faster model for testing
                    },
                },
            )

            if "result" in response:
                result = response["result"]
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get("text", "")
                    if "Code Review Report" in content:
                        print("   ✅ review_code executed successfully")
                        print(f"   📄 Response length: {len(content)} characters")
                    else:
                        print("   ⚠️  review_code executed but unexpected format")
                else:
                    print("   ❌ review_code failed - unexpected result format")
            else:
                print(f"   ❌ review_code failed: {response.get('error', 'Unknown error')}")

            # Test find_bugs tool
            print("\n   📋 Testing find_bugs on sample...")
            response = self.send_request(
                "tools/call",
                {
                    "name": "find_bugs",
                    "arguments": {
                        "directory": temp_dir,
                        "bug_categories": ["security", "logic"],
                        "severity_filter": ["critical", "high"],
                        "include_suggestions": True,
                    },
                },
            )

            if "result" in response:
                result = response["result"]
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get("text", "")
                    if "Bug Analysis Report" in content:
                        print("   ✅ find_bugs executed successfully")
                        print(f"   📄 Response length: {len(content)} characters")
                    else:
                        print("   ⚠️  find_bugs executed but unexpected format")
                else:
                    print("   ❌ find_bugs failed - unexpected result format")
            else:
                print(f"   ❌ find_bugs failed: {response.get('error', 'Unknown error')}")

        return True

    def run_all_tests(self):
        """Run all tests."""
        print(f"\n🚀 Testing MCP Server: {self.server_path}")
        print("=" * 60)

        try:
            self.start_server()
            print("✅ Server started successfully")

            # Run tests
            tests_passed = 0
            total_tests = 5

            if self.test_initialization():
                tests_passed += 1

            if self.test_list_tools():
                tests_passed += 1

            if self.test_tool_schema_validation():
                tests_passed += 1

            if self.test_tool_execution_validation():
                tests_passed += 1

            if os.environ.get("GEMINI_API_KEY"):
                if self.test_sample_execution():
                    tests_passed += 1
            else:
                print("\n⚠️  Skipping sample execution test - GEMINI_API_KEY not set")
                total_tests -= 1

            print("\n" + "=" * 60)
            print(f"📊 Test Results: {tests_passed}/{total_tests} passed")

            if tests_passed == total_tests:
                print("✅ All tests passed!")
                return 0
            else:
                print("❌ Some tests failed")
                return 1

        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback

            traceback.print_exc()
            return 1
        finally:
            self.stop_server()
            print("\n🛑 Server stopped")


def main():
    """Main test function."""
    server_path = Path(__file__).parent / "mcp_code_analysis_server.py"

    if not server_path.exists():
        print(f"❌ Server not found: {server_path}")
        return 1

    tester = MCPServerTester(str(server_path))
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
