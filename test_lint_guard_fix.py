#!/usr/bin/env python3
"""Test the fixed lint-guard.sh tool name extraction."""

import json
import subprocess
import tempfile

print("Testing lint-guard.sh tool name extraction fix...")

# Create test JSON input that mimics a Write operation
test_json = {
    "tool_name": "Write",
    "tool_input": {
        "file_path": "/home/dhalem/github/claude_template/test_demo.py",
        "content": '''def add_numbers(data):
    """Add all numbers in the data list."""
    result = 0
    for num in data:
        result += num
    return result''',
    },
}

print(f"✓ Test JSON created with tool_name: {test_json['tool_name']}")

# Test the JSON extraction logic
json_str = json.dumps(test_json)
print(f"✓ JSON string: {json_str}")
extract_cmd = f"echo {json.dumps(json_str)} | jq -r '.tool_name // \"lint\"'"

try:
    result = subprocess.run(extract_cmd, shell=True, capture_output=True, text=True)
    extracted_tool_name = result.stdout.strip()
    print(f"✓ Extracted tool name: '{extracted_tool_name}'")

    if extracted_tool_name == "Write":
        print("✅ Tool name extraction working correctly!")
    else:
        print(f"❌ Tool name extraction failed - got '{extracted_tool_name}' instead of 'Write'")

except Exception as e:
    print(f"❌ Tool name extraction test failed: {e}")

# Test the complete flow with the fixed script
print("\n--- Testing complete lint-guard.sh flow ---")

try:
    # Use the fixed script from repository
    script_path = "hooks/lint-guard.sh"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_json, f)
        temp_file = f.name

    cmd = f"cat {temp_file} | {script_path}"
    print(f"Running: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")

except Exception as e:
    print(f"Complete flow test failed: {e}")

print("Lint-guard test complete.")
