#!/usr/bin/env python3
"""MCP server for code search using the official MCP library."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Use local imports - all required modules are copied to src/
# Always use direct imports since this runs as a standalone script
try:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # If __file__ is not defined, try sys.argv[0] or current directory
    if sys.argv and sys.argv[0]:
        current_file_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        current_file_dir = os.path.abspath(".")

src_path = os.path.join(current_file_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from code_searcher import CodeSearcher

# Set up logging
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-search" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        # Don't log to stderr to avoid interfering with MCP protocol
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main MCP server function."""
    logger.info("=== Code Search MCP Server MAIN() called ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Script path: {__file__}")
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    logger.info(f"Command line args: {sys.argv}")

    try:
        server = Server("code-search")
        logger.info("✅ Server object created successfully")

        # Initialize code searcher (will be created per request to ensure fresh DB)
        logger.info("Code Search MCP Server starting tools setup")

        @server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            tools = [
                Tool(
                    name="search_code",
                    description="Search for code symbols by name, content, or file path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (supports * and ? wildcards)"
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["name", "content", "file"],
                                "description": "Type of search - 'name' (default), 'content', or 'file'"
                            },
                            "symbol_type": {
                                "type": "string",
                                "enum": ["function", "class", "method", "variable"],
                                "description": "Optional: Filter by symbol type"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results (default: 50)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="list_symbols",
                    description="List all symbols of a specific type",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol_type": {
                                "type": "string",
                                "enum": ["function", "class", "method", "variable"],
                                "description": "Type of symbol to list"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results (default: 100)"
                            }
                        },
                        "required": ["symbol_type"]
                    }
                ),
                Tool(
                    name="get_search_stats",
                    description="Get statistics about the code index database",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

            logger.info(f"Listing {len(tools)} tools")
            return tools

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")

            try:
                # Create searcher for each request to ensure fresh DB
                searcher = CodeSearcher()

                if name == "search_code":
                    query = arguments.get("query", "")
                    search_type = arguments.get("search_type", "name")
                    symbol_type = arguments.get("symbol_type")
                    limit = arguments.get("limit", 50)

                    result = searcher.search(query, search_type, symbol_type, limit)

                    # Format results for display
                    if result["success"]:
                        output = "# Code Search Results\n\n"
                        output += f"Query: `{query}`\n"
                        output += f"Type: {search_type}\n"
                        if symbol_type:
                            output += f"Symbol Type: {symbol_type}\n"
                        output += f"Found: {result['count']} results\n\n"

                        if search_type == "file":
                            for item in result["results"]:
                                output += f"- {item['file_path']} ({item['symbol_count']} symbols)\n"
                        else:
                            for item in result["results"]:
                                output += f"## {item['name']} ({item['type']})\n"
                                output += f"Location: `{item['location']}`\n"
                                if item.get('signature'):
                                    output += f"Signature: `{item['signature']}`\n"
                                if item.get('docstring'):
                                    output += f"Docstring: {item['docstring'][:100]}...\n"
                                output += "\n"
                    else:
                        output = f"Error: {result['error']}"

                    return [TextContent(type="text", text=output)]

                elif name == "list_symbols":
                    symbol_type = arguments.get("symbol_type", "function")
                    limit = arguments.get("limit", 100)

                    result = searcher.list_symbols(symbol_type, limit)

                    if result["success"]:
                        output = f"# {symbol_type.title()} List\n\n"
                        output += f"Found: {result['count']} {symbol_type}s\n\n"

                        for item in result["results"]:
                            output += f"- **{item['name']}** in `{item['file_path']}:{item['line_number']}`\n"
                            if item.get('signature'):
                                output += f"  Signature: `{item['signature']}`\n"
                    else:
                        output = f"Error: {result['error']}"

                    return [TextContent(type="text", text=output)]

                elif name == "get_search_stats":
                    result = searcher.get_stats()

                    if result["success"]:
                        stats = result["stats"]
                        output = "# Code Index Statistics\n\n"
                        output += f"Total Symbols: {stats['total_symbols']}\n"
                        output += f"Total Files: {stats['total_files']}\n"
                        if 'last_indexed' in stats:
                            output += f"Last Indexed: {stats['last_indexed']}\n"
                        output += "\n## Symbols by Type\n"
                        for sym_type, count in stats.get('by_type', {}).items():
                            output += f"- {sym_type}: {count}\n"
                    else:
                        output = f"Error: {result['error']}"

                    return [TextContent(type="text", text=output)]

                else:
                    error_msg = f"Unknown tool: {name}"
                    logger.error(error_msg)
                    return [TextContent(type="text", text=error_msg)]

            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=error_msg)]

        # Run the server
        logger.info("🚀 About to start stdio_server context manager")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("✅ stdio_server context manager entered successfully")
            logger.info("📡 Server running with stdio transport")

            init_options = InitializationOptions(
                server_name="code-search",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
            logger.info(f"📋 Initialization options created: {init_options}")

            logger.info("🏃 About to call server.run()")
            await server.run(read_stream, write_stream, init_options)
            logger.info("🏁 server.run() completed")

    except Exception as e:
        logger.error(f"💥 FATAL ERROR in main(): {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("🎬 SCRIPT STARTING - __main__ block executing")
    logger.info(f"📄 Script: {__file__}")
    logger.info(f"🐍 Python: {sys.executable}")
    logger.info(f"📂 CWD: {os.getcwd()}")

    try:
        logger.info("▶️  Calling asyncio.run(main())")
        asyncio.run(main())
        logger.info("✅ asyncio.run(main()) completed normally")
    except KeyboardInterrupt:
        logger.info("⏹️  Server stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"💥 FATAL ERROR in __main__: {e}", exc_info=True)
        sys.exit(1)

    logger.info("🏁 SCRIPT ENDING - __main__ block complete")
