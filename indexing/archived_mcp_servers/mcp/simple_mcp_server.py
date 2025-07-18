#!/usr/bin/env python3
"""Simple MCP code search server - uses local filesystem search directly.

NO DOCKER. NO CONTAINERS. NO ROUTING.
Just wraps the existing ClaudeCodeSearcher in MCP protocol.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

# Import the existing search functionality
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_code_search import ClaudeCodeSearcher


class SimpleMCPServer:
    """Simple MCP server that uses local search directly."""

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
            raise ValueError(f"Method not found: {method}")

    def _list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "search_code",
                    "description": "Search for functions, classes, and symbols by name",
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
                },
                {
                    "name": "search_in_files",
                    "description": "Search for symbols in specific files matching a pattern",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_pattern": {
                                "type": "string",
                                "description": "File pattern to search in"
                            },
                            "name_pattern": {
                                "type": "string",
                                "description": "Symbol name pattern to find (optional)"
                            }
                        },
                        "required": ["file_pattern"]
                    }
                }
            ]
        }

    def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Check for valid tool first
        valid_tools = ["search_code", "list_symbols", "explore_file", "search_in_files"]
        if tool_name not in valid_tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            # Route to the appropriate search method
            if tool_name == "search_code":
                result = self.searcher.search(
                    arguments["query"],
                    "name",
                    symbol_type=arguments.get("symbol_type"),
                    limit=arguments.get("limit", 20)
                )
            elif tool_name == "list_symbols":
                result = self.searcher.search(
                    arguments["symbol_type"],
                    "type",
                    limit=arguments.get("limit", 50)
                )
            elif tool_name == "explore_file":
                result = self.searcher.search(
                    arguments["file_path"],
                    "file_symbols"
                )
            elif tool_name == "search_in_files":
                result = self.searcher.search(
                    arguments["file_pattern"],
                    "file",
                    name_pattern=arguments.get("name_pattern")
                )

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        except Exception:
            # Let exceptions propagate - no fallbacks
            raise


def main():
    """Main MCP server loop."""
    server = SimpleMCPServer()

    # Read from stdin in a loop
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            # Return error response but let exceptions propagate for debugging
            error_response = {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
            # Re-raise for debugging
            raise


if __name__ == "__main__":
    main()
