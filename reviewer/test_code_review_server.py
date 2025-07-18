#!/usr/bin/env python3
"""Test script to run code-review server and capture errors."""

import os
import subprocess
import sys

# Test 1: Run the server and capture stderr
print("=== Testing code-review server startup ===")
try:
    # Use the installed server's venv and script
    venv_python = "/home/dhalem/.claude/mcp/code-review/venv/bin/python3"
    server_script = "/home/dhalem/.claude/mcp/code-review/bin/server.py"

    # First check if files exist
    if not os.path.exists(venv_python):
        print(f"ERROR: Venv python not found at {venv_python}")
        sys.exit(1)

    if not os.path.exists(server_script):
        print(f"ERROR: Server script not found at {server_script}")
        sys.exit(1)

    print(f"Found venv python: {venv_python}")
    print(f"Found server script: {server_script}")

    # Try to import and run the server
    print("\n=== Testing server imports ===")
    result = subprocess.run(
        [venv_python, "-c", "import sys; sys.path.insert(0, '/home/dhalem/.claude/mcp/code-review/bin'); import server"],  # Test import instead of exec
        capture_output=True,
        text=True,
        timeout=2
    )

    if result.returncode != 0:
        print("STDERR:")
        print(result.stderr)
        print("\nSTDOUT:")
        print(result.stdout)
    else:
        print("Server started without immediate errors")
        print("STDOUT:", result.stdout[:200] if result.stdout else "(empty)")

except subprocess.TimeoutExpired:
    print("Server started but timed out (this might be normal)")
except Exception as e:
    print(f"Error testing server: {e}")

# Test 2: Check imports directly
print("\n=== Testing imports directly ===")
test_imports = """
import sys
sys.path.insert(0, '/home/dhalem/.claude/mcp/code-review/bin')
sys.path.insert(0, '/home/dhalem/.claude/mcp/code-review/src')

try:
    from mcp.server import Server
    print("✓ MCP imports successful")
except Exception as e:
    print(f"✗ MCP import failed: {e}")

try:
    from file_collector import FileCollector
    print("✓ file_collector import successful")
except Exception as e:
    print(f"✗ file_collector import failed: {e}")

try:
    from gemini_client import GeminiClient
    print("✓ gemini_client import successful")
except Exception as e:
    print(f"✗ gemini_client import failed: {e}")

try:
    from review_formatter import ReviewFormatter
    print("✓ review_formatter import successful")
except Exception as e:
    print(f"✗ review_formatter import failed: {e}")
"""

result = subprocess.run(
    [venv_python, "-c", test_imports],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
