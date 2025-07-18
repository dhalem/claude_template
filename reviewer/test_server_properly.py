#!/usr/bin/env python3
"""Actually test the server to see what's wrong - Lyin' Bitch edition."""

import json
import subprocess

# Test the actual server script directly
venv_python = "/home/dhalem/.claude/mcp/code-review/venv/bin/python3"
server_script = "/home/dhalem/.claude/mcp/code-review/bin/server.py"

print("=== Testing server with actual MCP protocol ===")

# Test with a proper MCP initialize request
mcp_init = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {"list": True, "call": True}},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
}

try:
    result = subprocess.run(
        [venv_python, server_script],
        input=json.dumps(mcp_init) + "\n",
        capture_output=True,
        text=True,
        timeout=5
    )

    print("Return code:", result.returncode)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)

    # Try to parse the response
    if result.stdout:
        try:
            response = json.loads(result.stdout.strip())
            print("Parsed response:", json.dumps(response, indent=2))
        except json.JSONDecodeError as e:
            print(f"Could not parse JSON response: {e}")

except subprocess.TimeoutExpired:
    print("Server timed out - might be hanging")
except Exception as e:
    print(f"Error: {e}")
