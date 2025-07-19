#!/usr/bin/env python3
"""Test MCP server stdin/stdout communication."""

import json
import os
import subprocess
import time


def test_mcp_server_communication():
    """Test if MCP servers can handle stdin/stdout properly."""

    servers = [
        "/home/dhalem/.claude/mcp/central/code-search/server.py",
        "/home/dhalem/.claude/mcp/central/code-review/server.py"
    ]

    for server_path in servers:
        print(f"\n🔍 Testing {server_path}")

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(os.path.dirname(server_path))

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

            # Send MCP initialize message
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }

            message_str = json.dumps(init_message) + "\n"
            print(f"Sending: {message_str.strip()}")

            # Send message
            proc.stdin.write(message_str)
            proc.stdin.flush()

            # Try to read response with timeout
            start_time = time.time()
            response = None

            while time.time() - start_time < 5:  # 5 second timeout
                if proc.poll() is not None:
                    # Process has exited
                    stdout, stderr = proc.communicate()
                    print(f"❌ Process exited with code {proc.returncode}")
                    print(f"STDOUT: {stdout}")
                    print(f"STDERR: {stderr}")
                    break

                try:
                    # Try to read a line with short timeout
                    proc.stdout.settimeout(0.1)
                    line = proc.stdout.readline()
                    if line:
                        response = line.strip()
                        print(f"✅ Received: {response}")
                        break
                except:
                    pass

                time.sleep(0.1)

            if response is None and proc.poll() is None:
                print("❌ No response received, killing process")
                proc.terminate()
                proc.wait()
            elif response:
                print("✅ Server responded correctly")
                proc.terminate()
                proc.wait()

        except Exception as e:
            print(f"❌ Exception: {e}")


if __name__ == "__main__":
    test_mcp_server_communication()
