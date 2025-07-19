#!/usr/bin/env python3
"""Minimal MCP server for debugging connection issues."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Extreme debug logging
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"minimal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Log to file only - stderr interferes with stdio
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler(LOG_FILE, mode='w')]
)

logger = logging.getLogger(__name__)

logger.info("="*80)
logger.info("MINIMAL MCP DEBUG SERVER STARTING")
logger.info("="*80)
logger.info(f"Python: {sys.executable}")
logger.info(f"Version: {sys.version}")
logger.info(f"PID: {os.getpid()}")
logger.info(f"Parent PID: {os.getppid()}")
logger.info(f"Working Dir: {os.getcwd()}")
logger.info(f"Script: {__file__ if '__file__' in globals() else 'Unknown'}")
logger.info(f"Args: {sys.argv}")
logger.info("="*80)

# Try to determine who started us
try:
    if os.path.exists(f"/proc/{os.getppid()}/cmdline"):
        with open(f"/proc/{os.getppid()}/cmdline", 'r') as f:
            parent_cmd = f.read().replace('\0', ' ').strip()
            logger.info(f"Parent command: {parent_cmd}")
            if 'claude' in parent_cmd.lower():
                logger.info(">>> STARTED BY CLAUDE CODE!")
except:
    pass

try:
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    logger.info("✓ MCP imports successful")
except Exception as e:
    logger.error(f"Failed to import MCP: {e}")
    sys.exit(1)


class DebugStdio:
    """Log all stdio communication."""
    def __init__(self, name, stream):
        self.name = name
        self.stream = stream
        self.logger = logger

    async def read(self, n=-1):
        data = await self.stream.read(n)
        self.logger.debug(f"STDIO {self.name} READ: {len(data)} bytes")
        if len(data) < 1000:
            try:
                text = data.decode('utf-8', errors='replace')
                self.logger.debug(f"STDIO {self.name} DATA: {text}")
            except:
                pass
        return data

    async def readline(self):
        line = await self.stream.readline()
        try:
            text = line.decode('utf-8', errors='replace').strip()
            self.logger.debug(f"STDIO {self.name} LINE: {text}")
        except:
            pass
        return line

    def write(self, data):
        if isinstance(data, str):
            self.logger.debug(f"STDIO {self.name} WRITE STRING: {data}")
        else:
            self.logger.debug(f"STDIO {self.name} WRITE: {len(data)} bytes")
            if len(data) < 1000:
                try:
                    text = data.decode('utf-8', errors='replace')
                    self.logger.debug(f"STDIO {self.name} DATA: {text}")
                except:
                    pass
        return self.stream.write(data)

    async def drain(self):
        await self.stream.drain()

    def __getattr__(self, name):
        return getattr(self.stream, name)


async def main():
    logger.info(">>> main() started")

    try:
        # Create minimal server
        server = Server("code-review")
        logger.info("Server created")

        @server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            logger.info(">>> handle_list_tools called")
            return [
                Tool(
                    name="test_tool",
                    description="Test tool for debugging",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            logger.info(f">>> handle_call_tool: {name}")
            return [TextContent(type="text", text="Debug response")]

        # Start stdio server
        logger.info("Starting stdio_server...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("stdio_server started")

            # Wrap for debugging
            debug_read = DebugStdio("READ", read_stream)
            debug_write = DebugStdio("WRITE", write_stream)

            # Run server
            logger.info("Starting server.run()...")
            await server.run(
                debug_read,
                debug_write,
                InitializationOptions(
                    server_name="code-review",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
            logger.info("server.run() completed")

    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        raise

    logger.info(">>> main() completed")


if __name__ == "__main__":
    logger.info(">>> Starting event loop")
    try:
        asyncio.run(main())
        logger.info("Event loop completed normally")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info(">>> Server shutdown complete")
