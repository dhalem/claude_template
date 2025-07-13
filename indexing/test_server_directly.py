#!/usr/bin/env python3
"""Test the MCP server directly to see what's happening"""

import json
import subprocess
import time

print("Testing MCP server...")

# Start the server
proc = subprocess.Popen(
    ["bash", "/home/dhalem/.claude/mcp/start-code-search.sh"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give it a moment to start
time.sleep(0.5)

# Send a test request
request = {"method": "tools/list", "params": {}}
print(f"Sending: {json.dumps(request)}")

try:
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Wait for response with timeout
    import select
    ready, _, _ = select.select([proc.stdout], [], [], 5.0)

    if ready:
        response = proc.stdout.readline()
        print(f"Response: {response}")
    else:
        print("TIMEOUT: No response from server")

    # Check stderr
    ready, _, _ = select.select([proc.stderr], [], [], 0.1)
    if ready:
        errors = proc.stderr.read()
        if errors:
            print(f"STDERR: {errors}")

except Exception as e:
    print(f"Error: {e}")
finally:
    proc.terminate()
    proc.wait(timeout=2)
    print("Test complete")
