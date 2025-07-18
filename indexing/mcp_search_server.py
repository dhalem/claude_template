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

"""MCP server for code search using the official MCP library."""

import asyncio
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

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


class CodeSearcher:
    """Handles code search operations using the existing .code_index.db"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the code searcher.

        Args:
            db_path: Path to the database file. If None, searches for .code_index.db
        """
        self.db_path = self._find_database(db_path)
        logger.info(f"Using database at: {self.db_path}")

    def _find_database(self, db_path: Optional[str] = None) -> str:
        """Find the code index database."""
        if db_path and os.path.exists(db_path):
            return db_path

        # Search for .code_index.db in common locations
        search_paths = [
            Path.cwd() / ".code_index.db",
            Path.home() / ".code_index.db",
            Path("/app/.code_index.db"),  # Docker container path
        ]

        # Also check parent directories up to 3 levels
        current = Path.cwd()
        for _ in range(3):
            search_paths.append(current / ".code_index.db")
            current = current.parent

        for path in search_paths:
            if path.exists():
                return str(path)

        raise FileNotFoundError(
            "No .code_index.db found. Please run the code indexer first.\n"
            "You can start it with: ./start-indexer.sh"
        )

    def search(self, query: str, search_type: str = "name",
               symbol_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Search for code symbols.

        Args:
            query: Search query (supports * and ? wildcards)
            search_type: Type of search - 'name', 'content', or 'file'
            symbol_type: Filter by symbol type - 'function', 'class', 'method', or 'variable'
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Convert wildcards to SQL LIKE pattern
            pattern = query.replace('*', '%').replace('?', '_')

            # Build SQL query based on search type
            if search_type == "file":
                sql = """
                    SELECT DISTINCT file_path, COUNT(*) as symbol_count
                    FROM symbols
                    WHERE file_path LIKE ?
                    GROUP BY file_path
                    ORDER BY file_path
                    LIMIT ?
                """
                params = [f"%{pattern}%", limit]

            else:
                sql = """
                    SELECT name, type, file_path, line_number, column,
                           parent, signature, docstring
                    FROM symbols
                    WHERE 1=1
                """
                params = []

                if search_type == "name":
                    sql += " AND name LIKE ?"
                    params.append(pattern)
                elif search_type == "content":
                    sql += " AND (name LIKE ? OR docstring LIKE ? OR signature LIKE ?)"
                    params.extend([f"%{pattern}%", f"%{pattern}%", f"%{pattern}%"])

                if symbol_type:
                    sql += " AND type = ?"
                    params.append(symbol_type)

                sql += " ORDER BY name, file_path LIMIT ?"
                params.append(limit)

            cursor = conn.execute(sql, params)
            results = []

            if search_type == "file":
                for row in cursor:
                    results.append({
                        "file_path": row["file_path"],
                        "symbol_count": row["symbol_count"]
                    })
            else:
                for row in cursor:
                    results.append({
                        "name": row["name"],
                        "type": row["type"],
                        "file_path": row["file_path"],
                        "line_number": row["line_number"],
                        "column": row["column"],
                        "parent": row["parent"],
                        "signature": row["signature"],
                        "docstring": row["docstring"],
                        "location": f"{row['file_path']}:{row['line_number']}"
                    })

            conn.close()

            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "symbol_type": symbol_type,
                "count": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "search_type": search_type
            }

    def list_symbols(self, symbol_type: str, limit: int = 100) -> Dict[str, Any]:
        """List all symbols of a specific type.

        Args:
            symbol_type: Type of symbol - 'function', 'class', 'method', or 'variable'
            limit: Maximum number of results

        Returns:
            Dictionary with symbol list
        """
        return self.search("*", search_type="name", symbol_type=symbol_type, limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database stats
        """
        try:
            conn = sqlite3.connect(self.db_path)

            stats = {}

            # Total symbols
            cursor = conn.execute("SELECT COUNT(*) FROM symbols")
            stats["total_symbols"] = cursor.fetchone()[0]

            # Symbols by type
            cursor = conn.execute("""
                SELECT type, COUNT(*) as count
                FROM symbols
                GROUP BY type
            """)
            stats["by_type"] = {row[0]: row[1] for row in cursor}

            # Total files
            cursor = conn.execute("SELECT COUNT(DISTINCT file_path) FROM symbols")
            stats["total_files"] = cursor.fetchone()[0]

            # Database info
            cursor = conn.execute("SELECT indexed_at FROM metadata ORDER BY indexed_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                stats["last_indexed"] = row[0]

            conn.close()

            return {
                "success": True,
                "stats": stats
            }

        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """Main MCP server function."""
    server = Server("code-search")

    # Initialize code searcher (will be created per request to ensure fresh DB)
    logger.info("Code Search MCP Server starting")

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
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="code-search",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
