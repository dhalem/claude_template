#!/usr/bin/env python3
"""Simple working MCP server with minimal logging."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup logging to file
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler(LOG_FILE, mode='w')]
)

logger = logging.getLogger(__name__)

logger.info("="*80)
logger.info("SIMPLE MCP SERVER STARTING")
logger.info("="*80)
logger.info(f"Python: {sys.executable}")
logger.info(f"PID: {os.getpid()}")
logger.info(f"Parent PID: {os.getppid()}")

# Check if started by Claude
try:
    if os.path.exists(f"/proc/{os.getppid()}/cmdline"):
        with open(f"/proc/{os.getppid()}/cmdline", 'r') as f:
            parent_cmd = f.read().replace('\0', ' ').strip()
            if 'claude' in parent_cmd.lower():
                logger.info(">>> STARTED BY CLAUDE CODE!")
except:
    pass

# Setup import paths for auto-discovery structure
try:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    if sys.argv and sys.argv[0]:
        current_file_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        current_file_dir = os.path.abspath(".")

# Add src path for imports
src_path = os.path.join(current_file_dir, '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    logger.info(f"Added to sys.path: {src_path}")

try:
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    logger.info("✓ MCP imports successful")
except Exception as e:
    logger.error(f"Failed to import MCP: {e}")
    sys.exit(1)

# Import our modules
try:
    logger.info("✓ Local imports successful")
except Exception as e:
    logger.error(f"Failed to import local modules: {e}")
    logger.error(f"sys.path: {sys.path}")
    # Continue anyway for debugging


async def main():
    logger.info(">>> main() started")

    server = Server("code-review")
    logger.info("Server created")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        logger.info(">>> handle_list_tools called")
        return [
            Tool(
                name="test_tool",
                description="Test tool",
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
        return [TextContent(type="text", text="Test response")]

    logger.info("Starting stdio_server...")
    async with stdio_server() as (read_stream, write_stream):
        logger.info("stdio_server started")

        init_options = InitializationOptions(
            server_name="code-review",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )

        logger.info("Starting server.run()...")
        await server.run(read_stream, write_stream, init_options)
        logger.info("server.run() completed")


if __name__ == "__main__":
    logger.info(">>> Starting event loop")
    try:
        asyncio.run(main())
        logger.info("Event loop completed")
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
