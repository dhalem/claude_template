#!/usr/bin/env python3
"""Absolutely minimal MCP server for connection testing."""

import asyncio
import os
import sys
from pathlib import Path

# First, log that we started
log_dir = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "test_minimal.log"

with open(log_file, "w") as f:
    f.write(f"STARTED: {sys.executable}\n")
    f.write(f"Args: {sys.argv}\n")
    f.write(f"Env PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}\n")
    f.write(f"Working dir: {os.getcwd()}\n")

try:
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    with open(log_file, "a") as f:
        f.write("SUCCESS: MCP imports worked\n")
except Exception as e:
    with open(log_file, "a") as f:
        f.write(f"ERROR importing MCP: {e}\n")
        f.write(f"sys.path: {sys.path}\n")
    sys.exit(1)


async def main():
    with open(log_file, "a") as f:
        f.write("main() started\n")

    server = Server("code-review")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return []

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        return [TextContent(type="text", text="Test")]

    async with stdio_server() as (read_stream, write_stream):
        with open(log_file, "a") as f:
            f.write("stdio_server started\n")

        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="code-review",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

    with open(log_file, "a") as f:
        f.write("main() completed\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"FATAL ERROR: {e}\n")
            import traceback
            f.write(traceback.format_exc())
