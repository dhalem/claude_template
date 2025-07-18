#!/usr/bin/env python3
"""MCP server using the official MCP library."""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Set up logging
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-search" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
    ]
)

logger = logging.getLogger(__name__)


class CodeSearcher:
    """Direct database search."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def search_by_name(self, query: str, symbol_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search symbols by name pattern."""
        sql = "SELECT * FROM symbols WHERE name LIKE ? OR name GLOB ?"
        params = [f"%{query}%", query]

        if symbol_type:
            sql += " AND type = ?"
            params.append(symbol_type)

        sql += " ORDER BY name LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(sql, params)
        results = []

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

        return results


def find_workspace_db(cwd: str) -> Optional[str]:
    """Find the code index database for the current workspace."""
    current = Path(cwd).resolve()

    # Walk up the directory tree looking for .code_index.db
    while current != current.parent:
        db_path = current / '.code_index.db'
        if db_path.exists():
            return str(db_path)

        # Stop at git root if no database found
        if (current / '.git').exists():
            return None

        current = current.parent

    return None


async def main():
    """Main entry point for the MCP server."""
    logger.info(f"Starting MCP server - Log: {LOG_FILE}")

    # Create server instance
    server = Server("code-search")

    # Cache for searchers
    searchers: Dict[str, CodeSearcher] = {}

    @server.list_tools()
    async def list_tools() -> List[Dict[str, Any]]:
        """List available tools."""
        # Check if we have a database in current directory
        cwd = os.getcwd()
        db_path = find_workspace_db(cwd)

        if not db_path:
            logger.warning(f"No .code_index.db found in {cwd}")
            return []

        return [
            {
                "name": "search_code",
                "description": "Search for functions, classes, and symbols in the current workspace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (supports wildcards like 'get_*')"
                        },
                        "symbol_type": {
                            "type": "string",
                            "enum": ["function", "class", "method", "variable"],
                            "description": "Filter by symbol type (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 20
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool."""
        logger.debug(f"Tool called: {name} with args: {arguments}")

        cwd = os.getcwd()
        db_path = find_workspace_db(cwd)

        if not db_path:
            raise Exception(f"No .code_index.db found in workspace at {cwd}")

        # Get or create searcher for this database
        if db_path not in searchers:
            searchers[db_path] = CodeSearcher(db_path)

        searcher = searchers[db_path]

        if name == "search_code":
            query = arguments.get("query")
            symbol_type = arguments.get("symbol_type")
            limit = arguments.get("limit", 20)

            results = searcher.search_by_name(query, symbol_type, limit)

            return [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "query": query,
                    "count": len(results),
                    "results": results
                }, indent=2)
            }]
        else:
            raise ValueError(f"Unknown tool: {name}")

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        init_options = InitializationOptions(
            server_name="code-search",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
