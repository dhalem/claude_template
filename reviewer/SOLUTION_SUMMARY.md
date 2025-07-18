# MCP Server Fix Summary

## The Problem
Both the code-review and code-search MCP servers were showing "Capabilities: none" after installation. The error was:
```
'tuple' object has no attribute 'name'
```

## Root Cause
The issue was with the return type of the `@server.list_tools()` handler. The MCP library expects the handler to return `List[Tool]`, not `ListToolsResult`.

## The Solution

### ❌ WRONG (What caused the error)
```python
from mcp.types import ListToolsResult, Tool

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    tool = Tool(
        name="review_code",
        description="...",
        inputSchema={...}
    )
    return ListToolsResult(tools=[tool])
```

### ✅ CORRECT (What works)
```python
from mcp.types import Tool

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    tool = Tool(
        name="review_code",
        description="...",
        inputSchema={...}
    )
    return [tool]
```

## Key Differences
1. Return type should be `list[Tool]` not `ListToolsResult`
2. Don't import `ListToolsResult`
3. Return a plain list `[tool]` not `ListToolsResult(tools=[tool])`

## Testing the Fix
The fixed server successfully responds to the MCP protocol handshake:
- Initialize: ✅
- tools/list: ✅ Returns tools without tuple error
- Server shows capabilities properly in Claude

## Lesson Learned
The MCP Python SDK handles the conversion from `list[Tool]` to the proper JSON-RPC response format internally. Trying to return `ListToolsResult` directly causes the tuple error because the framework expects a different return type from the handler.
