#!/usr/bin/env python3
"""Test MCP server exactly as Claude Code would start it."""

import json
import os
import select
import subprocess
import time


def test_claude_like_startup():
    """Test server startup exactly like Claude Code configuration."""

    # Read the actual Claude configuration
    config_path = "/home/dhalem/.config/claude/claude_desktop_config.json"

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Can't read Claude config: {e}")
        return

    servers = config.get("mcpServers", {})

    for server_name, server_config in servers.items():
        print(f"\n🔍 Testing {server_name} with Claude configuration")

        command = server_config["command"]
        args = server_config["args"]
        env_vars = server_config.get("env", {})

        print(f"Command: {command}")
        print(f"Args: {args}")
        print(f"Env: {env_vars}")

        try:
            # Set up environment exactly like Claude would
            env = os.environ.copy()
            env.update(env_vars)

            # Add current environment variables that might be needed
            if "GEMINI_API_KEY" in os.environ:
                env["GEMINI_API_KEY"] = os.environ["GEMINI_API_KEY"]

            # Start server exactly like Claude Code would
            full_command = [command] + args
            proc = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            print("Server started, waiting...")
            time.sleep(1)

            # Check if process is still running
            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                print(f"❌ Server exited immediately with code {proc.returncode}")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                continue

            # Send initialize message
            init_msg = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "claude-test", "version": "1.0"}
                }
            }) + "\n"

            print("Sending initialize...")
            proc.stdin.write(init_msg)
            proc.stdin.flush()

            # Wait for response
            ready, _, _ = select.select([proc.stdout], [], [], 5.0)

            if ready:
                response = proc.stdout.readline()
                print(f"✅ Response: {response.strip()}")

                try:
                    resp_data = json.loads(response)
                    if "result" in resp_data:
                        print(f"✅ {server_name} initialized successfully!")
                    else:
                        print(f"❌ Unexpected response: {resp_data}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {e}")
            else:
                print("❌ No response received")

            # Terminate server
            if proc.poll() is None:
                proc.terminate()
                proc.wait()
            else:
                stdout, stderr = proc.communicate()
                print(f"Server exited with code {proc.returncode}")
                if stderr:
                    print(f"STDERR: {stderr}")

        except Exception as e:
            print(f"❌ Exception testing {server_name}: {e}")
            import traceback
            traceback.print_exc()

def check_file_permissions():
    """Check if all required files are accessible."""
    print("\n🔍 Checking file permissions")

    files_to_check = [
        "/home/dhalem/.claude/mcp/central/venv/bin/python",
        "/home/dhalem/.claude/mcp/central/code-search/server.py",
        "/home/dhalem/.claude/mcp/central/code-review/server.py",
        "/home/dhalem/.config/claude/claude_desktop_config.json"
    ]

    for file_path in files_to_check:
        try:
            if os.path.exists(file_path):
                if os.access(file_path, os.R_OK):
                    if file_path.endswith(".py") and os.access(file_path, os.X_OK):
                        print(f"✅ {file_path} - readable and executable")
                    elif file_path.endswith("python") and os.access(file_path, os.X_OK):
                        print(f"✅ {file_path} - executable")
                    else:
                        print(f"✅ {file_path} - readable")
                else:
                    print(f"❌ {file_path} - not readable")
            else:
                print(f"❌ {file_path} - does not exist")
        except Exception as e:
            print(f"❌ {file_path} - error: {e}")

if __name__ == "__main__":
    check_file_permissions()
    test_claude_like_startup()
