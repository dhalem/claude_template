#!/usr/bin/env python3
"""Test complete MCP protocol handshake - Lyin' Bitch edition."""

import json
import subprocess

venv_python = "/home/dhalem/.claude/mcp/code-review/venv/bin/python3"
server_script = "/home/dhalem/.claude/mcp/code-review/bin/server.py"

print("=== Testing complete MCP protocol handshake ===")

# Complete MCP handshake sequence
requests = [
    # 1. Initialize
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"list": True, "call": True}},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    },
    # 2. Initialized notification
    {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    },
    # 3. List tools
    {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/list",
        "params": {}
    }
]

# Send all requests
input_data = "\n".join(json.dumps(req) for req in requests) + "\n"

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

    # Parse each response
    if result.stdout:
        responses = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    response = json.loads(line)
                    responses.append(response)
                except json.JSONDecodeError as e:
                    print(f"Could not parse line: {e}")
                    print(f"Raw line: {line}")

        for i, response in enumerate(responses, 1):
            print(f"\nResponse {i}:")
            print(json.dumps(response, indent=2))

            # Check if this is the tools/list response
            if response.get("id") == 3:
                if "result" in response and "tools" in response["result"]:
                    tools = response["result"]["tools"]
                    print(f"\n🎉 SUCCESS! Found {len(tools)} tool(s):")
                    for tool in tools:
                        print(f"  - {tool.get('name')}: {tool.get('description')}")
                else:
                    print(f"\n❌ FAILED: tools/list error: {response.get('error', 'Unknown error')}")

except Exception as e:
    print(f"Error: {e}")
