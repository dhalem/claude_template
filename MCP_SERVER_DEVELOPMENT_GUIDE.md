# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# MCP Server Development Guide

This guide provides everything needed to quickly create new MCP servers based on our proven patterns and avoid the pitfalls we've discovered.

## 🚀 Quick Start Checklist

For building a new MCP server, follow this exact sequence:

1. **Copy existing server template** ✅
2. **Modify server functionality** ✅
3. **Test locally** ✅
4. **Add to central installation** ✅
5. **Register with user scope** ✅
6. **Test cross-workspace** ✅
7. **Update documentation** ✅

## 📋 Server Creation Template

### 1. Copy from Existing Server

```bash
# Start from a working server
cp indexing/mcp_search_server.py indexing/mcp_myserver_server.py

# Update the key identifiers
sed -i 's/Code Search MCP Server/My Server MCP Server/g' indexing/mcp_myserver_server.py
sed -i 's/code-search/my-server/g' indexing/mcp_myserver_server.py
```

### 2. Server Code Template

```python
#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.

"""
My Server MCP Server - Brief description of functionality

Key features:
- Feature 1
- Feature 2
- Feature 3
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging to file only (NEVER stdout - breaks MCP protocol)
log_dir = Path.home() / ".claude" / "mcp" / "central" / "my-server" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger(__name__)

# MCP imports (CRITICAL: Use exact versions)
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

# Initialize server
server = Server("my-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools - MUST return list[Tool] not ListToolsResult"""
    logger.info("Listing available tools")

    return [
        Tool(
            name="my_tool_function",
            description="Description of what this tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of parameter"
                    },
                    "param2": {
                        "type": "string",
                        "description": "Optional parameter",
                        "default": "default_value"
                    }
                },
                "required": ["param1"]
            }
        ),
        # Add more tools here
    ]

@server.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls"""
    logger.info(f"Tool called: {request.params.name}")

    try:
        if request.params.name == "my_tool_function":
            return await handle_my_tool(request)
        else:
            error_msg = f"Unknown tool: {request.params.name}"
            logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {error_msg}")]
            )

    except Exception as e:
        error_msg = f"Error in tool {request.params.name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {error_msg}")]
        )

async def handle_my_tool(request: CallToolRequest) -> CallToolResult:
    """Implementation of my_tool_function"""
    args = request.params.arguments or {}
    param1 = args.get("param1", "")
    param2 = args.get("param2", "default_value")

    logger.info(f"Processing tool with param1={param1}, param2={param2}")

    # Your tool logic here
    result = f"Processed {param1} with {param2}"

    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def main():
    """Main server function"""
    logger.info("My Server MCP Server starting")

    # CRITICAL: Use exact protocol version
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
```

## 🔧 Development Workflow

### Step 1: Local Development

```bash
# Activate environment
source venv/bin/activate

# Test server startup
python3 indexing/mcp_myserver_server.py

# Should log: "My Server MCP Server starting"
# Press Ctrl+C to stop
```

### Step 2: Add to Project Configuration

```bash
# Add to .mcp.json for local testing
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "my-server": {
      "command": "./venv/bin/python3",
      "args": ["indexing/mcp_myserver_server.py"]
    }
  }
}
EOF
```

### Step 3: Test Locally

```bash
# Test with Claude Code CLI
claude mcp add my-server -s local ./venv/bin/python3 indexing/mcp_myserver_server.py

# Verify registration
claude mcp list

# Test functionality
claude --debug --dangerously-skip-permissions -p 'Use my_tool_function to test'
```

### Step 4: Add to Central Installation

Edit `install-mcp-central.sh` to include your new server:

```bash
# Add to SERVER_CONFIGS array
declare -A SERVER_CONFIGS=(
    ["code-search"]="indexing/mcp_search_server.py"
    ["code-review"]="indexing/mcp_review_server.py"
    ["my-server"]="indexing/mcp_myserver_server.py"  # ADD THIS LINE
)
```

### Step 5: Install Centrally

```bash
# Reinstall with new server
./install-mcp-central.sh

# Verify central installation
ls ~/.claude/mcp/central/my-server/
```

### Step 6: Register for User Scope

Edit `register-mcp-global.sh` to include your server:

```bash
# Add after existing registrations
echo "Registering my-server..."
if claude mcp add my-server -s user "$CENTRAL_PYTHON" "$HOME/.claude/mcp/central/my-server/server.py"; then
    echo "✅ my-server registered for user (cross-workspace)"
else
    echo "❌ Failed to register my-server for user"
fi
```

### Step 7: Test Cross-Workspace

```bash
# Re-register all servers
./register-mcp-global.sh

# Test in different directory
./test_mcp_other_workspace.sh /tmp/test_myserver
```

## 📝 Required Files Checklist

For each new server, ensure these files exist:

- [ ] `indexing/mcp_myserver_server.py` - Main server implementation
- [ ] Updated `install-mcp-central.sh` - Includes new server
- [ ] Updated `register-mcp-global.sh` - Registers new server
- [ ] Updated central installation test
- [ ] Documentation for the new server's tools

## 🚨 Critical Requirements (DON'T SKIP)

### Protocol Requirements
- ✅ **Protocol Version**: Must use `2024-11-05`
- ✅ **Return Types**: `list[Tool]` not `ListToolsResult`
- ✅ **No stdout/stderr**: Only file logging during operation
- ✅ **Proper imports**: Use exact MCP library versions

### Path Requirements
- ✅ **User scope**: Always register with `-s user` for cross-workspace
- ✅ **Central paths**: Use `~/.claude/mcp/central/` installation
- ✅ **No hardcoded paths**: Use `$HOME` variables
- ✅ **Absolute paths**: All configuration paths must be absolute

### Testing Requirements
- ✅ **Local testing**: Verify server starts without errors
- ✅ **CLI registration**: Test with `claude mcp add`
- ✅ **Cross-workspace**: Test from different directories
- ✅ **Tool functionality**: Verify each tool works correctly

## 🔄 Update Scripts for New Servers

### Update `install-mcp-central.sh`

Add to SERVER_CONFIGS array:
```bash
declare -A SERVER_CONFIGS=(
    ["code-search"]="indexing/mcp_search_server.py"
    ["code-review"]="indexing/mcp_review_server.py"
    ["my-server"]="indexing/mcp_myserver_server.py"
    ["other-server"]="indexing/mcp_other_server.py"
    # Add new servers here
)
```

### Update `register-mcp-global.sh`

Add registration block:
```bash
echo "Registering my-server..."
if claude mcp add my-server -s user "$CENTRAL_PYTHON" "$HOME/.claude/mcp/central/my-server/server.py"; then
    echo "✅ my-server registered for user (cross-workspace)"
else
    echo "❌ Failed to register my-server for user"
    echo "   You may need to request an override code"
fi
```

### Update Test Scripts

Add to `test_mcp_cross_workspace_prevention.py` in the test_user_scope_registration function:
```python
# Check for expected servers
expected_servers = ["code-search", "code-review", "my-server"]
for server in expected_servers:
    if server not in stdout:
        print(f"❌ Expected server {server} not found")
        return False
```

## 📖 Server Examples by Use Case

### File System Server
```python
# Tools: list_files, read_file, write_file
# Use cases: File management, content analysis
```

### API Integration Server
```python
# Tools: api_call, parse_response, format_data
# Use cases: External service integration
```

### Data Processing Server
```python
# Tools: process_data, analyze_data, generate_report
# Use cases: Data transformation, analysis
```

### Development Tools Server
```python
# Tools: run_command, parse_logs, check_status
# Use cases: Development workflow automation
```

## 🐛 Common Pitfalls to Avoid

### 1. Protocol Issues
- ❌ Wrong return types (`ListToolsResult` instead of `list[Tool]`)
- ❌ Using stdout/stderr during operation
- ❌ Wrong protocol version

### 2. Path Issues
- ❌ Hardcoded user paths (`/home/username/`)
- ❌ Project-specific paths (`/project/claude_template/`)
- ❌ Relative paths in configuration

### 3. Scope Issues
- ❌ Using local scope (workspace-specific)
- ❌ Forgetting to register with user scope
- ❌ Not testing cross-workspace functionality

### 4. Installation Issues
- ❌ Not updating installation scripts
- ❌ Missing dependencies in central environment
- ❌ Forgetting to run central installation

## ✅ Pre-Deployment Checklist

Before considering a server "done":

- [ ] Server starts without errors locally
- [ ] All tools return proper responses
- [ ] Logging works (file-based, no stdout)
- [ ] Added to installation scripts
- [ ] Central installation successful
- [ ] User scope registration works
- [ ] Cross-workspace testing passes
- [ ] Documentation updated
- [ ] Prevention tests updated

## 🔧 Environment Variables

Document any required environment variables:

```bash
# Example for servers requiring API keys
export OPENAI_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"
export CUSTOM_API_KEY="your-key-here"
```

Add to installation scripts and documentation.

## 📚 Further Reading

- `MCP_KEY_LEARNINGS.md` - Critical discoveries and patterns
- `MCP_SERVER_TROUBLESHOOTING.md` - Debugging guide
- `MCP_CROSS_WORKSPACE_SETUP.md` - Cross-workspace configuration
- `indexing/mcp_search_server.py` - Reference implementation
- `indexing/mcp_review_server.py` - API integration example

This guide ensures you can rapidly create new MCP servers that work correctly across all workspaces from day one.
