#!/usr/bin/env python3
"""
Real MCP server implementation using official MCP Python SDK.
This server provides code search functionality through proper MCP protocol.
"""

import asyncio
import json
from typing import Any, Dict

# Import our existing search functionality
from claude_code_search import ClaudeCodeSearcher
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)


class CodeSearchMCPServer:
    """MCP server for code search functionality using official MCP SDK"""

    def __init__(self):
        self.searcher = ClaudeCodeSearcher()
        self.server = Server("code-search-server")
        self._setup_tools()

    def _setup_tools(self):
        """Setup MCP tools"""

        @self.server.list_tools()
        async def list_tools():
            """List available tools"""
            return [
                Tool(
                    name="search_code",
                    description="Search for functions, classes, and symbols in the codebase",
                    inputSchema={
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
                ),
                Tool(
                    name="explore_file",
                    description="Get all symbols in a specific file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to explore"
                            }
                        },
                        "required": ["file_path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list:
            """Handle tool calls"""
            try:
                if name == "search_code":
                    result = await self._handle_search_code(arguments or {})
                elif name == "list_symbols":
                    result = await self._handle_list_symbols(arguments or {})
                elif name == "explore_file":
                    result = await self._handle_explore_file(arguments or {})
                else:
                    return [TextContent(type="text", text=json.dumps({
                        "success": False,
                        "error": f"Unknown tool: {name}"
                    }, indent=2))]

                # Convert CallToolResult to list of content
                return result.content
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": f"Tool execution failed: {str(e)}"
                }, indent=2))]

    async def _handle_search_code(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle search_code tool call"""
        # Extract and validate arguments
        query = arguments.get("query")
        if not query:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": "Missing required argument: query"
                }, indent=2))]
            )

        search_type = arguments.get("search_type", "name")
        symbol_type = arguments.get("symbol_type")
        limit = arguments.get("limit", 20)

        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            limit = 20

        # Perform search
        result = self.searcher.search(
            query=query,
            search_type=search_type,
            symbol_type=symbol_type,
            limit=limit
        )

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

    async def _handle_list_symbols(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle list_symbols tool call"""
        symbol_type = arguments.get("symbol_type")
        if not symbol_type:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": "Missing required argument: symbol_type"
                }, indent=2))]
            )

        limit = arguments.get("limit", 50)

        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            limit = 50

        # List symbols by type
        result = self.searcher.search(
            query=symbol_type,
            search_type="type",
            limit=limit
        )

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

    async def _handle_explore_file(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle explore_file tool call"""
        file_path = arguments.get("file_path")
        if not file_path:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": "Missing required argument: file_path"
                }, indent=2))]
            )

        # Explore file
        result = self.searcher.search(
            query=file_path,
            search_type="file_symbols"
        )

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point"""
    server = CodeSearchMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
