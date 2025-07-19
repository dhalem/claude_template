#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Minimal MCP test server to isolate connection issues"""

import asyncio
import os
import sys
from datetime import datetime


# Log to stderr to avoid stdout pollution
def log(msg):
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {msg}", file=sys.stderr)

log("MCP Minimal Test Server starting")
log(f"Python: {sys.executable}")
log(f"CWD: {os.getcwd()}")
log(f"Environment: {dict(os.environ)}")

try:
    from mcp.server import Server
    from mcp.types import Tool
    log("MCP imports successful")
except Exception as e:
    log(f"MCP import failed: {e}")
    sys.exit(1)

# Create minimal server
app = Server("minimal-test")
log("Server instance created")

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    log("list_tools called")
    return [
        Tool(
            name="echo",
            description="Echo back the input",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    log(f"call_tool called: {name} with {arguments}")
    if name == "echo":
        return [{"type": "text", "text": arguments.get("message", "No message")}]
    return [{"type": "text", "text": f"Unknown tool: {name}"}]

async def main():
    log("Starting main async function")

    # Import stdio_server here since we need it for main
    from mcp.server.stdio import stdio_server

    try:
        log("Starting stdio_server")
        async with stdio_server() as (read_stream, write_stream):
            log("stdio_server opened, initializing MCP server")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        log(f"Server error: {e}")
        raise

if __name__ == "__main__":
    log("Running asyncio main")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Server stopped by user")
    except Exception as e:
        log(f"Fatal error: {e}")
        sys.exit(1)
