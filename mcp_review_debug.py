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

"""MCP server for code review with EXTREME DEBUG LOGGING."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# EXTREME DEBUG LOGGING SETUP
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure root logger for maximum verbosity
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d - [%(levelname)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        # Don't log to stderr - it interferes with stdio protocol
    ]
)

# Set all loggers to DEBUG
for logger_name in ['mcp', 'mcp.server', 'mcp.server.stdio', 'asyncio']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Log startup environment
logger.info("="*80)
logger.info("MCP CODE REVIEW SERVER - EXTREME DEBUG MODE")
logger.info("="*80)
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Python path: {sys.path}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Script location: {__file__ if '__file__' in globals() else 'Unknown'}")
logger.info(f"Process ID: {os.getpid()}")
logger.info("Environment variables:")
for key, value in os.environ.items():
    if 'API' in key or 'KEY' in key:
        logger.info(f"  {key}={'<redacted>' if value else '<not set>'}")
    else:
        logger.info(f"  {key}={value}")
logger.info("="*80)

# Handle imports
try:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    if sys.argv and sys.argv[0]:
        current_file_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        current_file_dir = os.path.abspath(".")

src_paths = [
    os.path.join(current_file_dir, '..', 'src'),
    os.path.join(current_file_dir, 'indexing', 'src'),
]

logger.info("Setting up import paths:")
for src_path in src_paths:
    logger.info(f"  Adding to sys.path: {src_path}")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

try:
    logger.info("Attempting imports...")
    from file_collector import FileCollector
    logger.info("  ✓ Imported FileCollector")
    from gemini_client import GeminiClient
    logger.info("  ✓ Imported GeminiClient")
    from review_formatter import ReviewFormatter
    logger.info("  ✓ Imported ReviewFormatter")
except ImportError as e:
    logger.error(f"Import failed: {e}")
    logger.error(f"sys.path: {sys.path}")
    logger.error("Traceback:", exc_info=True)
    sys.exit(1)


# Custom stdio handlers to log all communication
class DebugReadStream:
    """Wrapper to log all incoming data from stdio."""
    def __init__(self, stream):
        self.stream = stream
        self.logger = logging.getLogger("DEBUG.READ")

    async def read(self, n=-1):
        data = await self.stream.read(n)
        self.logger.debug(f"READ {len(data)} bytes: {data[:200]}...")
        return data

    async def readline(self):
        line = await self.stream.readline()
        self.logger.debug(f"READLINE: {line.decode('utf-8', errors='replace').strip()}")
        return line

    def __getattr__(self, name):
        return getattr(self.stream, name)


class DebugWriteStream:
    """Wrapper to log all outgoing data to stdio."""
    def __init__(self, stream):
        self.stream = stream
        self.logger = logging.getLogger("DEBUG.WRITE")

    def write(self, data):
        if isinstance(data, str):
            self.logger.debug(f"WRITE STRING: {data.strip()}")
        else:
            self.logger.debug(f"WRITE {len(data)} bytes: {data[:200]}...")
        return self.stream.write(data)

    async def drain(self):
        self.logger.debug("DRAIN called")
        return await self.stream.drain()

    def __getattr__(self, name):
        return getattr(self.stream, name)


async def main():
    """Main MCP server function with extreme debugging."""
    logger.info(">>> main() function started")

    try:
        logger.info("Creating Server instance...")
        server = Server("code-review")
        logger.info(f"Server created: {server}")

        # Initialize components
        logger.info("Initializing components...")
        file_collector = FileCollector()
        review_formatter = ReviewFormatter()
        default_model = "gemini-2.5-pro"
        logger.info("Components initialized successfully")

        @server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            logger.info(">>> handle_list_tools() called")
            try:
                tool = Tool(
                    name="review_code",
                    description="Perform a comprehensive code review of a directory using Gemini AI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Absolute path to the directory to review"
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional: Specific areas to focus on"
                            },
                            "model": {
                                "type": "string",
                                "description": "Optional: Gemini model to use",
                                "enum": ["gemini-1.5-flash", "gemini-2.5-pro"]
                            },
                            "max_file_size": {
                                "type": "number",
                                "description": "Optional: Maximum file size in bytes"
                            }
                        },
                        "required": ["directory"]
                    }
                )
                logger.info(f"Returning tool: {tool}")
                return [tool]
            except Exception as e:
                logger.error(f"Error in handle_list_tools: {e}", exc_info=True)
                raise

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            logger.info(f">>> handle_call_tool() called with name={name}, arguments={arguments}")

            try:
                if name != "review_code":
                    logger.warning(f"Unknown tool requested: {name}")
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

                # Tool implementation would go here
                logger.info("Processing review_code tool...")
                return [TextContent(type="text", text="Debug mode - tool execution placeholder")]

            except Exception as e:
                logger.error(f"Error in handle_call_tool: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        # Start stdio server with debug wrappers
        logger.info(">>> Starting stdio_server context manager...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("stdio_server context entered")
            logger.info(f"read_stream type: {type(read_stream)}")
            logger.info(f"write_stream type: {type(write_stream)}")

            # Wrap streams for debugging
            debug_read = DebugReadStream(read_stream)
            debug_write = DebugWriteStream(write_stream)

            logger.info("Creating InitializationOptions...")
            init_options = InitializationOptions(
                server_name="code-review",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
            logger.info(f"InitializationOptions: {init_options}")

            logger.info(">>> Calling server.run()...")
            logger.info("This is where MCP protocol communication begins")
            logger.info("Expecting initialize request from client...")

            try:
                await server.run(debug_read, debug_write, init_options)
                logger.info("server.run() completed normally")
            except Exception as e:
                logger.error(f"Error during server.run(): {e}", exc_info=True)
                raise

        logger.info("stdio_server context exited")

    except Exception as e:
        logger.error(f"FATAL ERROR in main(): {e}")
        logger.error("Full traceback:", exc_info=True)
        raise

    logger.info(">>> main() function completed")


if __name__ == "__main__":
    logger.info(">>> __main__ block starting")
    logger.info(f"Command line arguments: {sys.argv}")

    # Check if we're being run by Claude Code
    parent_pid = os.getppid()
    logger.info(f"Parent process ID: {parent_pid}")

    try:
        # Try to get parent process info (Linux)
        if os.path.exists(f"/proc/{parent_pid}/cmdline"):
            with open(f"/proc/{parent_pid}/cmdline", 'r') as f:
                parent_cmd = f.read().replace('\0', ' ')
                logger.info(f"Parent process command: {parent_cmd}")
    except:
        pass

    try:
        logger.info(">>> Starting asyncio event loop...")
        asyncio.run(main())
        logger.info("asyncio.run() completed successfully")
    except KeyboardInterrupt:
        logger.info("Server stopped by KeyboardInterrupt")
    except Exception as e:
        logger.error(f"FATAL ERROR in __main__: {e}", exc_info=True)
        sys.exit(1)

    logger.info(">>> __main__ block completed")
    logger.info("="*80)
    logger.info("SERVER SHUTDOWN COMPLETE")
    logger.info("="*80)
