#!/bin/bash
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing MCP Code Search Server with actual MCP protocol...${NC}"

# Create a temporary test script
TEST_SCRIPT=$(mktemp /tmp/test_mcp_search_XXXXXX.py)
trap 'rm -f $TEST_SCRIPT' EXIT

cat > "$TEST_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""Test the MCP code search server with actual MCP protocol."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_server():
    """Test the server using MCP protocol over stdio."""

    # Find the server
    server_paths = [
        Path("mcp_search_server.py"),
        Path(__file__).parent / "mcp_search_server.py",
        Path.home() / ".claude/mcp/servers/code-search/mcp_search_server.py"
    ]

    server_path = None
    for path in server_paths:
        if path.exists():
            server_path = path
            break

    if not server_path:
        print("❌ Could not find mcp_search_server.py")
        return False

    print(f"✓ Found server at: {server_path}")

    # Start the server process
    process = await asyncio.create_subprocess_exec(
        sys.executable, str(server_path),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        await send_message(process, init_request)
        response = await read_message(process)

        if response and "result" in response:
            print("✓ Server initialized successfully")
            server_info = response["result"].get("serverInfo", {})
            print(f"  Server: {server_info.get('name', 'unknown')} v{server_info.get('version', 'unknown')}")
        else:
            print("❌ Failed to initialize server")
            return False

        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await send_message(process, initialized)

        # List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        await send_message(process, list_tools_request)
        response = await read_message(process)

        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"✓ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print("❌ Failed to list tools")
            return False

        # Test search_code tool
        search_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {
                    "query": "CodeIndexer",
                    "search_type": "name"
                }
            }
        }

        await send_message(process, search_request)
        response = await read_message(process)

        if response and "result" in response:
            print("✓ Search tool executed successfully")
            content = response["result"].get("content", [])
            if content:
                print(f"  Response preview: {content[0].get('text', '')[:100]}...")
        else:
            print("❌ Search tool failed")
            return False

        # Test get_search_stats tool
        stats_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_search_stats",
                "arguments": {}
            }
        }

        await send_message(process, stats_request)
        response = await read_message(process)

        if response and "result" in response:
            print("✓ Stats tool executed successfully")
        else:
            print("❌ Stats tool failed")
            return False

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    finally:
        # Terminate the server
        process.terminate()
        await process.wait()


async def send_message(process, message):
    """Send a JSON-RPC message to the server."""
    json_str = json.dumps(message)
    message_bytes = json_str.encode('utf-8')
    header = f"Content-Length: {len(message_bytes)}\r\n\r\n"

    process.stdin.write(header.encode('utf-8'))
    process.stdin.write(message_bytes)
    await process.stdin.drain()


async def read_message(process):
    """Read a JSON-RPC message from the server."""
    # Read headers
    headers = {}
    while True:
        line = await process.stdout.readline()
        if not line:
            return None
        line = line.decode('utf-8').strip()
        if not line:
            break
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()

    # Read content
    content_length = int(headers.get('Content-Length', '0'))
    if content_length > 0:
        content = await process.stdout.read(content_length)
        return json.loads(content.decode('utf-8'))

    return None


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
EOF

# Make the test script executable
chmod +x "$TEST_SCRIPT"

# Run the test
echo -e "\n${YELLOW}Running MCP protocol tests...${NC}\n"
if python3 "$TEST_SCRIPT"; then
    echo -e "\n${GREEN}✅ MCP server is working correctly!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ MCP server tests failed${NC}"
    exit 1
fi
