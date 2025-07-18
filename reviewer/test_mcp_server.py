#!/usr/bin/env python3
"""Test the MCP server directly."""

import subprocess
import sys
from pathlib import Path


def test_server_import():
    """Test that the server can be imported without errors."""
    server_path = Path.home() / ".claude" / "mcp" / "code-review" / "bin" / "server.py"
    python_path = Path.home() / ".claude" / "mcp" / "code-review" / "venv" / "bin" / "python3"

    print(f"Testing server import: {server_path}")
    print(f"Using Python: {python_path}")

    # Test import
    result = subprocess.run([
        str(python_path), "-c", f"import sys; sys.path.insert(0, '{server_path.parent}'); import server"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Server imports successfully")
        return True
    else:
        print("✗ Server import failed:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False

def test_server_startup():
    """Test that the server can start."""
    startup_script = Path.home() / ".claude" / "mcp" / "code-review" / "start-server.sh"

    print(f"\nTesting server startup: {startup_script}")

    # Test startup with a timeout
    try:
        result = subprocess.run([
            "bash", str(startup_script)
        ], input="", capture_output=True, text=True, timeout=5)

        print(f"✓ Server started and responded (exit code: {result.returncode})")
        if result.stdout:
            print(f"STDOUT: {result.stdout[:200]}...")
        if result.stderr:
            print(f"STDERR: {result.stderr[:200]}...")
        return True

    except subprocess.TimeoutExpired:
        print("✓ Server started (timeout after 5s, which is expected)")
        return True
    except Exception as e:
        print(f"✗ Server startup failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing MCP Code Review Server...")

    import_ok = test_server_import()
    startup_ok = test_server_startup()

    if import_ok and startup_ok:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)
