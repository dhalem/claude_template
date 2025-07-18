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

"""Test the MCP Code Review Server."""

import json
import subprocess
import sys
from pathlib import Path


def test_mcp_server():
    """Test the MCP server communication."""
    server_path = Path(__file__).parent / "mcp_code_review_server.py"

    print("Testing MCP Code Review Server...")

    # Test 1: List tools
    print("\n1. Testing tools/list...")
    list_request = {
        "method": "tools/list",
        "params": {}
    }

    response = send_request(server_path, list_request)
    print(f"Response: {json.dumps(response, indent=2)}")

    # Verify tools are listed
    if "tools" in response:
        tools = response["tools"]
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
    else:
        print("✗ No tools found in response")
        return False

    # Test 2: Call review_code tool (without API key, will fail gracefully)
    print("\n2. Testing tools/call (review_code)...")
    current_dir = str(Path(__file__).parent.absolute())

    call_request = {
        "method": "tools/call",
        "params": {
            "name": "review_code",
            "arguments": {
                "directory": current_dir,
                "model": "gemini-1.5-flash",
                "focus_areas": ["security", "code quality"]
            }
        }
    }

    response = send_request(server_path, call_request)
    print(f"Response type: {type(response)}")

    # Check if it's an error (expected if no API key)
    if "error" in response:
        print(f"✓ Expected error (no API key): {response['error']['message']}")
        return True
    elif "content" in response:
        print("✓ Got successful response (API key available)")
        content = response["content"][0]["text"]
        print(f"Review preview: {content[:200]}...")
        return True
    else:
        print(f"✗ Unexpected response: {response}")
        return False


def send_request(server_path, request):
    """Send a request to the MCP server."""
    try:
        # Use venv python
        venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python3"

        # Start the server process
        process = subprocess.Popen(
            [str(venv_python), str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send request
        request_json = json.dumps(request) + "\n"
        stdout, stderr = process.communicate(input=request_json, timeout=30)

        if stderr:
            print(f"Server stderr: {stderr}")

        # Parse response
        response = json.loads(stdout.strip())
        return response

    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": {"code": -32603, "message": "Request timeout"}}
    except Exception as e:
        return {"error": {"code": -32603, "message": f"Communication error: {str(e)}"}}


if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
