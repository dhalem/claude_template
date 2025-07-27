#!/usr/bin/env python3
"""Simple test of jq tool name extraction."""

import json
import subprocess

test_json = {
    "tool_name": "Write",
    "tool_input": {"file_path": "/home/dhalem/github/claude_template/test.py", "content": "def test(): pass"},
}

json_str = json.dumps(test_json)
print(f"JSON: {json_str}")

# Test jq extraction properly
try:
    # Use subprocess with input instead of shell command
    jq_process = subprocess.run(["jq", "-r", '.tool_name // "lint"'], input=json_str, text=True, capture_output=True)

    tool_name = jq_process.stdout.strip()
    print(f"Extracted tool name: '{tool_name}'")

    if tool_name == "Write":
        print("✅ jq extraction working!")
    else:
        print(f"❌ jq extraction failed: got '{tool_name}'")

except Exception as e:
    print(f"Error: {e}")

print("Simple test complete.")
