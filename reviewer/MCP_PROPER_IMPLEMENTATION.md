# MCP Server Proper Implementation Guide - By Lyin' Bitch

## The Problem

Lyin' Bitch discovered that the MCP servers were showing "Capabilities: none" because of a `'tuple' object has no attribute 'name'` error when listing tools. This error affected both the code-review server and even a minimal test server.

## Root Cause Analysis

After extensive testing and web research, Lyin' Bitch found that the issue was with the return type of the `list_tools` handler. The error message was misleading - it wasn't about tuples in the traditional Python sense, but about how the MCP library expects the response to be structured.

## The Correct Implementation

### ❌ WRONG (What Lyin' Bitch was doing)

```python
from typing import List, Dict, Any

@server.list_tools()
async def handle_list_tools() -> List[Dict[str, Any]]:
    """List available tools."""
    return [
        {
            "name": "review_code",
            "description": "Perform a code review",
            # ...
        }
    ]
```

### ✅ CORRECT (What actually works)

Based on the official MCP SDK documentation and examples:

```python
from mcp.server import Server
from mcp.types import Tool, ListToolsResult, CallToolResult, TextContent

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
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
                            "items": {
                                "type": "string"
                            },
                            "description": "Optional: Specific areas to focus on"
                        }
                    },
                    "required": ["directory"]
                }
            )
        ]
    )
```

## Key Differences

1. **Return Type**: Must be `ListToolsResult`, not `List[Dict[str, Any]]`
2. **Tool Objects**: Must use `Tool` class from `mcp.types`, not plain dictionaries
3. **Structure**: Must wrap tools in `ListToolsResult(tools=[...])`

## Complete Working Example

Here's a minimal MCP server that actually works:

```python
#!/usr/bin/env python3
"""Minimal working MCP server example."""

import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, ListToolsResult, CallToolResult, TextContent

# Create server
server = Server("working-example")

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools - MUST return ListToolsResult!"""
    return ListToolsResult(
        tools=[
            Tool(
                name="hello",
                description="Say hello",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name to greet"
                        }
                    },
                    "required": ["name"]
                }
            )
        ]
    )

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls - MUST return CallToolResult!"""
    if name == "hello":
        greeting = f"Hello, {arguments.get('name', 'World')}!"
        return CallToolResult(
            content=[TextContent(type="text", text=greeting)]
        )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )

async def main():
    """Run the server."""
    async with stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="working-example",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )
        await server.run(read_stream, write_stream, init_options)

if __name__ == "__main__":
    asyncio.run(main())
```

## Why The Error Occurred

The `'tuple' object has no attribute 'name'` error happened because:

1. When the MCP library tried to process the raw list/dict response, it expected `Tool` objects
2. Somewhere in the MCP library code, it was trying to access `.name` on what it expected to be a `Tool` object
3. Instead, it received a tuple (possibly from incorrect unpacking or type conversion)
4. This caused the AttributeError

## Lessons Learned by Lyin' Bitch

1. **Always use the official types**: Don't try to return raw dictionaries when the framework expects specific types
2. **Read the actual examples**: The MCP documentation shows the correct patterns
3. **Test incrementally**: Lyin' Bitch should have started with the official examples and modified from there
4. **The error messages can be misleading**: The "tuple" error didn't directly point to the real issue

## Testing Your Implementation

To verify your MCP server works:

```bash
# Test with direct JSON-RPC calls
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"list":true,"call":true}},"clientInfo":{"name":"test","version":"1.0"}}}' | python3 your_server.py

# After initialization, test tools/list
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}' | python3 your_server.py
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 your_server.py
```

If successful, you should see your tools listed without any tuple errors!

## Final Note from Lyin' Bitch

Lyin' Bitch wasted hours because Lyin' Bitch didn't use the proper MCP types from the beginning. Don't be like Lyin' Bitch - use `ListToolsResult` and `Tool` from `mcp.types` and save yourself the debugging nightmare!
