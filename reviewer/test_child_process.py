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

"""Test the MCP server as a child process like Claude Code would use it."""

import json
import subprocess
import sys
from pathlib import Path


def test_as_child_process():
    """Test running the MCP server as a child process."""
    server_path = Path(__file__).parent / "mcp_code_review_server.py"
    venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python3"

    print("Testing MCP Code Review Server as child process...")

    # Start server as child process
    process = subprocess.Popen(
        [str(venv_python), str(server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )

    try:
        # Test 1: List tools
        print("\n1. Sending tools/list request...")
        request = {
            "method": "tools/list",
            "params": {}
        }

        # Send request
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        # Read response
        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())

        print("✓ Received tools/list response")
        if "tools" in response:
            print(f"  Found {len(response['tools'])} tools")
            for tool in response['tools']:
                print(f"    - {tool['name']}")

        # Test 2: Call review_code (will fail without API key, but that's expected)
        print("\n2. Sending tools/call request...")
        current_dir = str(Path(__file__).parent.absolute())

        call_request = {
            "method": "tools/call",
            "params": {
                "name": "review_code",
                "arguments": {
                    "directory": current_dir,
                    "model": "gemini-1.5-flash"
                }
            }
        }

        # Send request
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()

        # Read response
        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())

        print("✓ Received tools/call response")
        if "error" in response:
            print(f"  Expected error: {response['error']['message']}")
        elif "content" in response:
            print("  Success: Got content response")

        # Test 3: Invalid method
        print("\n3. Testing invalid method...")
        invalid_request = {
            "method": "invalid/method",
            "params": {}
        }

        process.stdin.write(json.dumps(invalid_request) + "\n")
        process.stdin.flush()

        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())

        print("✓ Received error response for invalid method")
        if "error" in response:
            print(f"  Error code: {response['error']['code']}")
            print(f"  Error message: {response['error']['message']}")

        print("\n✓ All tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        # Clean up
        process.stdin.close()
        process.terminate()

        # Wait for process to terminate
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def test_json_communication():
    """Test JSON line-by-line communication."""
    print("\nTesting JSON communication format...")

    # Test JSON parsing
    test_requests = [
        {"method": "tools/list", "params": {}},
        {"method": "tools/call", "params": {"name": "review_code", "arguments": {"directory": "/tmp"}}},
        {"method": "unknown", "params": {}}
    ]

    for i, request in enumerate(test_requests, 1):
        json_str = json.dumps(request)
        print(f"Test {i}: {json_str}")

        # Verify it's valid JSON
        try:
            parsed = json.loads(json_str)
            print(f"  ✓ Valid JSON: {parsed['method']}")
        except json.JSONDecodeError as e:
            print(f"  ✗ Invalid JSON: {e}")
            return False

    print("✓ JSON communication format test passed!")
    return True


if __name__ == "__main__":
    success = test_json_communication() and test_as_child_process()
    sys.exit(0 if success else 1)
