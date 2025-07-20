# MCP Server Development Guide

This guide documents how to create MCP (Model Context Protocol) servers based on the working implementation in this project.

## Table of Contents
1. [Overview](#overview)
2. [MCP Server Architecture](#mcp-server-architecture)
3. [Installation and Configuration](#installation-and-configuration)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Debugging MCP Servers](#debugging)
6. [Template for New Servers](#template)

## Overview

MCP servers allow Claude Desktop and Claude Code CLI to access external tools and services. This project includes two working MCP servers:
- `code-search`: Search code symbols, content, and files using indexed database
- `code-review`: AI-powered code review using Google Gemini

## MCP Server Architecture

### Centralized Installation Structure
```
~/.claude/mcp/central/
├── venv/                       # Shared Python environment
│   ├── bin/python             # Python executable
│   └── lib/python3.x/site-packages/
├── code-search/
│   ├── server.py              # MCP search server
│   └── logs/                  # Server logs
│       └── server_YYYYMMDD.log
└── code-review/
    ├── server.py              # MCP review server
    └── logs/                  # Server logs
        └── server_YYYYMMDD.log
```

### Configuration Files
- **Claude Desktop**: `~/.config/claude/claude_desktop_config.json`
- **Claude Code CLI**: Manual registration with `claude mcp add`
- **Project-specific**: `.mcp.json` (takes precedence over global config)

## Installation and Configuration

### Automated Installation
```bash
# Install servers for Claude Desktop (uses .mcp.json)
./install-mcp-servers.sh

# Install servers for Claude Code CLI
./install-mcp-central.sh
claude mcp add code-search ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-search/server.py
claude mcp add code-review ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-review/server.py
```

### Configuration Differences

#### Claude Desktop
- Automatically loads `.mcp.json` from project root
- No manual server registration required
- Uses STDIO transport

#### Claude Code CLI
- Requires manual server registration with `claude mcp add`
- Project `.mcp.json` not automatically loaded
- Must use absolute paths in configuration

### Example Configuration (.mcp.json)
```json
{
  "mcpServers": {
    "code-search": {
      "command": "/home/user/.claude/mcp/central/venv/bin/python",
      "args": ["/home/user/.claude/mcp/central/code-search/server.py"]
    },
    "code-review": {
      "command": "/home/user/.claude/mcp/central/venv/bin/python",
      "args": ["/home/user/.claude/mcp/central/code-review/server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Step-by-Step Implementation

### 1. Server Implementation Pattern

```python
#!/usr/bin/env python3
"""MCP server for [functionality]."""

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

# Set up logging to file only (never stdout/stderr)
LOG_DIR = Path.home() / ".claude" / "mcp" / "central" / "{server-name}" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        # NEVER log to stdout/stderr - breaks MCP protocol
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
        return [
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

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "tool_name":
                result = "Tool result"
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Run server with proper initialization
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="{server-name}",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Installation Script Pattern

```bash
#!/bin/bash
set -euo pipefail

echo "Installing MCP {Server Name} Server..."

# Central installation directory
CENTRAL_DIR="$HOME/.claude/mcp/central"
SERVER_DIR="$CENTRAL_DIR/{server-name}"
VENV_DIR="$CENTRAL_DIR/venv"

# Create directories
mkdir -p "$SERVER_DIR/logs"

# Create shared venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
fi

# Install dependencies
"$VENV_DIR/bin/pip" install mcp

# Copy server file
cp "mcp_{name}_server.py" "$SERVER_DIR/server.py"
chmod +x "$SERVER_DIR/server.py"

echo "Installation complete!"
echo "Server: $SERVER_DIR/server.py"
echo "Python: $VENV_DIR/bin/python"
```

### 3. Key Requirements

1. **Protocol Version**: Must use `2024-11-05`
2. **Transport**: STDIO only (no HTTP for Claude Desktop)
3. **Logging**: File-based only, never stdout/stderr during operation
4. **Paths**: Absolute paths required in configuration
5. **Dependencies**: Shared venv for all servers
6. **Registration**: Manual registration required for Claude Code CLI

## Debugging MCP Servers

### 1. Check Logs
```bash
tail -f ~/.claude/mcp/central/{server-name}/logs/server_*.log
```

### 2. Test Server Manually
```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05"},"id":1}' | \
  ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/{server-name}/server.py
```

### 3. Test with Claude Code
```bash
# Enable debug mode
claude --debug --dangerously-skip-permissions -p 'test'

# Look for MCP messages in output
# ✅ "MCP server 'name': Connected successfully"
# ❌ No MCP messages = servers not loaded
```

### 4. Verify Configuration
```bash
# For Claude Code CLI
claude mcp list

# Check if servers are registered
# If not, add them manually
```

## Template for New Servers

### Minimal Working Server
```python
#!/usr/bin/env python3
"""Minimal MCP server template."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Set up file logging only
LOG_DIR = Path.home() / ".claude" / "mcp" / "central" / "my-server" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE)]
)

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

1. **Wrong Protocol Version**: Must use `2024-11-05` (as of 2025)
2. **STDIO Corruption**: Never write to stdout/stderr during operation
3. **Path Issues**: Always use absolute paths in configuration
4. **CLI vs Desktop**: Different registration methods required
5. **Import Errors**: Ensure dependencies are in the correct venv
6. **Permission Issues**: Use `--dangerously-skip-permissions` only for testing

## Summary

Key principles for working MCP servers:
1. Use centralized installation with shared venv
2. File-based logging only (never stdout/stderr)
3. Proper protocol version and initialization
4. Absolute paths in all configurations
5. Different setup for Claude Desktop vs CLI
6. Comprehensive testing and debugging procedures

For complete examples, see the working `code-search` and `code-review` servers in this project.
