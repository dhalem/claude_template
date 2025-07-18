#!/usr/bin/env python3
"""MCP server wrapper that uses the live index from the current workspace."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add the MCP directory to path so we can import the search modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_code_search import ClaudeCodeSearcher


class WorkspaceAwareMCPServer:
    """MCP server that uses the live index from the current workspace."""

    def __init__(self):
        # Don't initialize searcher yet - we'll do it per request with the right DB
        pass

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

    def get_searcher(self, cwd: str) -> ClaudeCodeSearcher:
        """Get a searcher instance for the current workspace."""
        db_path = self.find_workspace_db(cwd)

        # Temporarily change to the directory containing the DB
        # so the search modules can find it
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(db_path))

        try:
            searcher = ClaudeCodeSearcher()
            return searcher
        finally:
            # Always restore the original directory
            os.chdir(old_cwd)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})

        # Get current working directory from environment
        cwd = os.environ.get("MCP_CWD", os.getcwd())

        if method == "tools/list":
            return self._list_tools()
        elif method == "tools/call":
            return self._call_tool(params, cwd)
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
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
                    "message": str(e)
                }
            }

    def _search_code(self, searcher: ClaudeCodeSearcher, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for code symbols."""
        query = args.get("query")
        search_type = args.get("search_type", "name")
        symbol_type = args.get("symbol_type")
        limit = args.get("limit", 20)

        return searcher.search(
            query,
            search_type,
            symbol_type=symbol_type,
            limit=limit
        )

    def _list_symbols(self, searcher: ClaudeCodeSearcher, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all symbols of a type."""
        symbol_type = args.get("symbol_type")
        limit = args.get("limit", 50)

        return searcher.search(symbol_type, "type", limit=limit)

    def _explore_file(self, searcher: ClaudeCodeSearcher, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all symbols in a file."""
        file_path = args.get("file_path")
        return searcher.search(file_path, "file_symbols")


def main():
    """Main MCP server loop."""
    server = WorkspaceAwareMCPServer()

    # Read from stdin in a loop
    for line in sys.stdin:
        try:
            # Set the current working directory in environment
            # MCP might pass this in the future
            if "MCP_CWD" not in os.environ:
                os.environ["MCP_CWD"] = os.getcwd()

            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
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


if __name__ == "__main__":
    main()
