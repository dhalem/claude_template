#!/usr/bin/env python3
"""Truly global MCP server that works with any workspace's code index."""

import json
import logging
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up logging to file
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-search" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    name: str
    type: str
    file_path: str
    line_number: int
    column: int
    parent: Optional[str]
    signature: Optional[str]
    docstring: Optional[str]
    score: float = 1.0


class GlobalCodeSearcher:
    """Direct database search without external dependencies."""

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

    def search_by_type(self, symbol_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List all symbols of a specific type."""
        sql = "SELECT * FROM symbols WHERE type = ? ORDER BY name LIMIT ?"
        cursor = self.conn.execute(sql, (symbol_type, limit))
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

    def get_file_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all symbols in a specific file."""
        sql = "SELECT * FROM symbols WHERE file_path = ? ORDER BY line_number"
        cursor = self.conn.execute(sql, (file_path,))
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

    def close(self):
        """Close database connection."""
        self.conn.close()


class GlobalMCPServer:
    """MCP server that works with any workspace's code index."""

    def __init__(self):
        # We'll create searchers on demand for each workspace
        self.searchers = {}

    def find_workspace_db(self, cwd: str) -> str:
        """Find the code index database for the current workspace."""
        current = Path(cwd).resolve()

        # Walk up the directory tree looking for .code_index.db
        while current != current.parent:
            db_path = current / '.code_index.db'
            if db_path.exists():
                return str(db_path)

            # Also check for .git to know when to stop
            if (current / '.git').exists() and not db_path.exists():
                # We're at a git root but no index
                raise FileNotFoundError(f"No .code_index.db found in repository at {current}")

            current = current.parent

        raise FileNotFoundError(f"No .code_index.db found in any parent directory of {cwd}")

    def get_searcher(self, cwd: str) -> GlobalCodeSearcher:
        """Get or create a searcher instance for the current workspace."""
        db_path = self.find_workspace_db(cwd)

        # Reuse existing searcher if we have one for this database
        if db_path not in self.searchers:
            self.searchers[db_path] = GlobalCodeSearcher(db_path)

        return self.searchers[db_path]

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})

        # Get current working directory from environment
        cwd = os.environ.get("MCP_CWD", os.getcwd())

        if method == "initialize":
            return self._handle_initialize(request)
        elif method == "tools/list":
            return self._list_tools()
        elif method == "tools/call":
            return self._call_tool(params, cwd)
        else:
            logger.warning(f"Unknown method: {method}")
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    def _handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization handshake."""
        logger.info("Handling initialize request")
        return {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "code-search",
                "version": "1.0.0"
            }
        }

    def _list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
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
                            "search_type": {
                                "type": "string",
                                "enum": ["name", "file", "type", "file_symbols"],
                                "description": "Type of search to perform",
                                "default": "name"
                            },
                            "symbol_type": {
                                "type": "string",
                                "enum": ["function", "class", "method", "variable"],
                                "description": "Filter by symbol type (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "list_symbols",
                    "description": "List all symbols of a specific type in the current workspace",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol_type": {
                                "type": "string",
                                "enum": ["function", "class", "method", "variable"],
                                "description": "Type of symbols to list"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 100
                            }
                        },
                        "required": ["symbol_type"]
                    }
                },
                {
                    "name": "explore_file",
                    "description": "Get all symbols in a specific file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to explore"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            ]
        }

    def _call_tool(self, params: Dict[str, Any], cwd: str) -> Dict[str, Any]:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            # Get searcher for the current workspace
            searcher = self.get_searcher(cwd)

            if tool_name == "search_code":
                result = self._search_code(searcher, arguments)
            elif tool_name == "list_symbols":
                result = self._list_symbols(searcher, arguments)
            elif tool_name == "explore_file":
                result = self._explore_file(searcher, arguments)
            else:
                return {
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        except FileNotFoundError as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Workspace index not found: {str(e)}"
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error: {str(e)}"
                }
            }

    def _search_code(self, searcher: GlobalCodeSearcher, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for code symbols."""
        query = args.get("query")
        search_type = args.get("search_type", "name")
        symbol_type = args.get("symbol_type")
        limit = args.get("limit", 20)

        if search_type == "name":
            results = searcher.search_by_name(query, symbol_type, limit)
        elif search_type == "type":
            results = searcher.search_by_type(query, limit)
        elif search_type == "file_symbols":
            results = searcher.get_file_symbols(query)
        else:
            results = searcher.search_by_name(query, symbol_type, limit)

        return {
            "success": True,
            "query": query,
            "search_type": search_type,
            "count": len(results),
            "results": results
        }

    def _list_symbols(self, searcher: GlobalCodeSearcher, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all symbols of a type."""
        symbol_type = args.get("symbol_type")
        limit = args.get("limit", 50)

        results = searcher.search_by_type(symbol_type, limit)

        return {
            "success": True,
            "query": symbol_type,
            "search_type": "type",
            "count": len(results),
            "results": results
        }

    def _explore_file(self, searcher: GlobalCodeSearcher, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all symbols in a file."""
        file_path = args.get("file_path")
        results = searcher.get_file_symbols(file_path)

        return {
            "success": True,
            "query": file_path,
            "search_type": "file_symbols",
            "count": len(results),
            "results": results
        }

    def cleanup(self):
        """Close all database connections."""
        for searcher in self.searchers.values():
            searcher.close()


def main():
    """Main MCP server loop."""
    logger.info(f"MCP Server starting - Log file: {LOG_FILE}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python version: {sys.version}")

    server = GlobalMCPServer()
    logger.info("Server instance created")

    try:
        logger.info("Starting main loop - waiting for stdin...")
        # Read from stdin in a loop
        for line in sys.stdin:
            logger.debug(f"Received line: {line.strip()}")
            try:
                # Set the current working directory in environment
                # MCP might pass this in the future
                if "MCP_CWD" not in os.environ:
                    os.environ["MCP_CWD"] = os.getcwd()

                request = json.loads(line.strip())
                logger.debug(f"Parsed request: {request}")

                response = server.handle_request(request)
                logger.debug(f"Generated response: {response}")

                response_json = json.dumps(response)
                print(response_json)
                sys.stdout.flush()
                logger.debug(f"Sent response: {response_json}")
            except json.JSONDecodeError:
                error_response = {
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    finally:
        server.cleanup()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
