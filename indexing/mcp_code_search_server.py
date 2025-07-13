#!/usr/bin/env python3
"""MCP server wrapper for code search functionality."""

import json
import sys
from typing import Any, Dict

from claude_code_search import ClaudeCodeSearcher


class MCPCodeSearchServer:
    """MCP server for code search functionality."""

    def __init__(self):
        self.searcher = ClaudeCodeSearcher()

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return self._list_tools()
        elif method == "tools/call":
            return self._call_tool(params)
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
                    "description": "Search for functions, classes, and symbols in the codebase",
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
                                "default": 20
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "list_symbols",
                    "description": "List all symbols of a specific type",
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
                                "default": 50
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

    def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "search_code":
                result = self._search_code(arguments)
            elif tool_name == "list_symbols":
                result = self._list_symbols(arguments)
            elif tool_name == "explore_file":
                result = self._explore_file(arguments)
            else:
                return {
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    def _search_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for code symbols."""
        query = args.get("query")
        search_type = args.get("search_type", "name")
        symbol_type = args.get("symbol_type")
        limit = args.get("limit", 20)

        return self.searcher.search(
            query,
            search_type,
            symbol_type=symbol_type,
            limit=limit
        )

    def _list_symbols(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all symbols of a type."""
        symbol_type = args.get("symbol_type")
        limit = args.get("limit", 50)

        return self.searcher.search(symbol_type, "type", limit=limit)

    def _explore_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all symbols in a file."""
        file_path = args.get("file_path")
        return self.searcher.search(file_path, "file_symbols")


def main():
    """Main MCP server loop."""
    server = MCPCodeSearchServer()

    # Read from stdin in a loop
    for line in sys.stdin:
        try:
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
