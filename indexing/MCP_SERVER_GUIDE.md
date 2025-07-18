# MCP Server Development Guide

This guide documents how to create MCP (Model Context Protocol) servers based on the working `code-review` server implementation.

## Table of Contents
1. [Overview](#overview)
2. [Key Differences Between Servers](#key-differences)
3. [MCP Server Architecture](#mcp-server-architecture)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Installation Requirements](#installation-requirements)
6. [Configuration in Claude Desktop](#configuration)
7. [Debugging MCP Servers](#debugging)
8. [Template for New Servers](#template)

## Overview

MCP servers allow Claude Desktop to access external tools and services. The `code-review` server works because it follows a specific structure and installation pattern that differs from what we attempted with `code-search`.

## Key Differences Between Servers

### Working Code-Review Server
- **Installation Path**: `~/.claude/mcp/code-review/bin/server.py`
- **Dependencies**: Installed in `~/.claude/mcp/code-review/venv/`
- **Source Files**: Copied to `~/.claude/mcp/code-review/src/`
- **Configuration**: Not explicitly in claude_desktop_config.json (loaded automatically)

### Non-Working Code-Search Server
- **Installation Path**: `~/.claude/mcp/servers/code-search/mcp_search_server.py`
- **Dependencies**: Using external venv
- **Source Files**: None (all in main file)
- **Configuration**: Explicitly added to claude_desktop_config.json

## MCP Server Architecture

### 1. Directory Structure
```
~/.claude/mcp/{server-name}/
├── bin/
│   └── server.py          # Main server executable
├── src/                   # Supporting modules
│   ├── module1.py
│   └── module2.py
├── venv/                  # Isolated Python environment
│   └── ...
└── logs/                  # Server logs
    └── server_YYYYMMDD.log
```

### 2. Server Implementation Pattern

```python
#!/usr/bin/env python3
"""MCP server for [functionality] using the official MCP library."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Handle imports with fallback for MCP environment
try:
    from .src.module1 import Module1
    from .src.module2 import Module2
except ImportError:
    # Fallback for direct execution
    try:
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        if sys.argv and sys.argv[0]:
            current_file_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            current_file_dir = os.path.abspath(".")

    src_path = os.path.join(current_file_dir, '..', 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from module1 import Module1
    from module2 import Module2

# Set up logging
LOG_DIR = Path.home() / ".claude" / "mcp" / "{server-name}" / "logs"
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
    server = Server("{server-name}")

    logger.info("{Server Name} MCP Server starting")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List available tools."""
        tools = [
            Tool(
                name="tool_name",
                description="Tool description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Parameter description"
                        }
                    },
                    "required": ["param1"]
                }
            )
        ]
        return tools

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
        """Handle tool calls - returns list of TextContent."""
        try:
            if name == "tool_name":
                # Tool implementation
                result = "Tool result"
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        init_options = InitializationOptions(
            server_name="{server-name}",
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

## Step-by-Step Implementation

### 1. Create Server File
Create your main server file following the pattern above.

### 2. Create Installation Script
```bash
#!/bin/bash
set -euo pipefail

echo "Installing MCP {Server Name} Server..."
echo "====================================="

# Check if running from correct directory
if [ ! -f "mcp_{name}_server.py" ]; then
    echo "Error: mcp_{name}_server.py not found in current directory"
    exit 1
fi

# Target directory structure (CRITICAL!)
TARGET_DIR="$HOME/.claude/mcp/{server-name}"
TARGET_BIN="$TARGET_DIR/bin"
TARGET_SRC="$TARGET_DIR/src"

# Create directory structure
mkdir -p "$TARGET_BIN" "$TARGET_SRC" "$TARGET_DIR/logs"

# Install server (MUST be named server.py in bin/)
cp mcp_{name}_server.py "$TARGET_BIN/server.py"
chmod +x "$TARGET_BIN/server.py"

# Copy source files if any
if [ -d "src" ]; then
    cp src/*.py "$TARGET_SRC/"
fi

# Create isolated venv
if [ ! -d "$TARGET_DIR/venv" ]; then
    python3 -m venv "$TARGET_DIR/venv"
fi

# Install dependencies
"$TARGET_DIR/venv/bin/pip" install --upgrade pip
"$TARGET_DIR/venv/bin/pip" install mcp

# Additional dependencies
if [ -f "requirements.txt" ]; then
    "$TARGET_DIR/venv/bin/pip" install -r requirements.txt
fi

echo "Installation complete!"
echo "Server installed at: $TARGET_BIN/server.py"
echo "Restart Claude Desktop to load the server"
```

### 3. Key Installation Requirements

1. **MUST use specific directory structure**: `~/.claude/mcp/{server-name}/bin/server.py`
2. **MUST be named `server.py`** in the bin directory
3. **MUST have its own venv** in `~/.claude/mcp/{server-name}/venv/`
4. **MUST NOT add to claude_desktop_config.json** - Claude auto-discovers servers in the correct location

## Configuration in Claude Desktop

Claude Desktop automatically discovers MCP servers in:
- `~/.claude/mcp/*/bin/server.py`

The server name comes from the directory name, not the config file. Tools are accessed as:
- `mcp__{server-name}__{tool_name}`

## Debugging MCP Servers

### 1. Check Logs
```bash
tail -f ~/.claude/mcp/{server-name}/logs/server_*.log
```

### 2. Test Server Directly
```python
# Test imports and basic functionality
cd ~/.claude/mcp/{server-name}/bin
../venv/bin/python3 -c "import server; print('Server imports OK')"
```

### 3. Verify Installation
```bash
# Check directory structure
ls -la ~/.claude/mcp/{server-name}/
# Should show: bin/ src/ venv/ logs/

# Check server file
ls -la ~/.claude/mcp/{server-name}/bin/server.py
# Should be executable

# Check venv
~/.claude/mcp/{server-name}/venv/bin/python3 --version
# Should show Python version
```

## Template for New Servers

### Minimal Working Server
```python
#!/usr/bin/env python3
"""Minimal MCP server template."""

import asyncio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

async def main():
    server = Server("my-server")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return [
            Tool(
                name="hello",
                description="Say hello",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"}
                    },
                    "required": ["name"]
                }
            )
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "hello":
            return [TextContent(type="text", text=f"Hello, {arguments.get('name', 'World')}!")]
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities()
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Pitfalls

1. **Wrong installation path**: Must be in `~/.claude/mcp/{name}/bin/server.py`
2. **Wrong file name**: Must be named `server.py`, not `mcp_whatever_server.py`
3. **External dependencies**: Must use the server's own venv, not system or project venv
4. **Manual configuration**: Don't add to claude_desktop_config.json
5. **Import paths**: Must handle both package imports and direct execution

## Summary

The key insight is that Claude Desktop has a specific auto-discovery mechanism for MCP servers:
1. Looks in `~/.claude/mcp/*/bin/server.py`
2. Uses the directory name as the server name
3. Expects each server to have its own isolated environment
4. Does NOT use claude_desktop_config.json for these auto-discovered servers

This is why the code-review server works (follows this pattern) while code-search doesn't (uses different structure).
