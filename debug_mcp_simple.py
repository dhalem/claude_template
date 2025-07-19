#!/usr/bin/env python3
"""Simple MCP server debug test."""

import json
import os
import select
import subprocess
import time


def test_server_basic():
    """Test basic server startup and response."""

    server_path = "/home/dhalem/.claude/mcp/central/code-search/server.py"

    print("🔍 Testing basic server communication")

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(server_path)

        # Start server
        proc = subprocess.Popen([
            "/home/dhalem/.claude/mcp/central/venv/bin/python",
            server_path
        ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        print("Server started, waiting for initialization...")
        time.sleep(1)

        # Check if process is still running
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            print(f"❌ Server exited immediately with code {proc.returncode}")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return

        # Send a simple initialize message
        init_msg = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }) + "\n"

        print("Sending initialize message...")
        proc.stdin.write(init_msg)
        proc.stdin.flush()

        # Wait for response with timeout
        print("Waiting for response...")

        # Use select to wait for data with timeout
        ready, _, _ = select.select([proc.stdout], [], [], 5.0)

        if ready:
            response = proc.stdout.readline()
            print(f"✅ Received response: {response.strip()}")

            # Try to parse JSON
            try:
                resp_data = json.loads(response)
                print(f"✅ Valid JSON response: {resp_data}")
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}")

        else:
            print("❌ No response within timeout")

        # Check if server is still running
        if proc.poll() is None:
            print("✅ Server still running, terminating...")
            proc.terminate()
            proc.wait()
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ Server exited during test with code {proc.returncode}")
            if stderr:
                print(f"STDERR: {stderr}")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server_basic()
