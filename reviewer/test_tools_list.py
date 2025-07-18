#!/usr/bin/env python3
"""Test the tools/list method - Lyin' Bitch edition."""

import json
import subprocess

venv_python = "/home/dhalem/.claude/mcp/code-review/venv/bin/python3"
server_script = "/home/dhalem/.claude/mcp/code-review/bin/server.py"

print("=== Testing tools/list method ===")

# First initialize
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {"list": True, "call": True}},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
}

# Then request tools list
tools_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}

# Send both requests
input_data = json.dumps(init_request) + "\n" + json.dumps(tools_request) + "\n"

try:
    result = subprocess.run(
        [venv_python, server_script],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=5
    )

    print("Return code:", result.returncode)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)

    # Try to parse each line of response
    if result.stdout:
        for line_num, line in enumerate(result.stdout.strip().split('\n'), 1):
            if line.strip():
                try:
                    response = json.loads(line)
                    print(f"Response {line_num}:", json.dumps(response, indent=2))
                except json.JSONDecodeError as e:
                    print(f"Could not parse line {line_num}: {e}")
                    print(f"Raw line: {line}")

except Exception as e:
    print(f"Error: {e}")
