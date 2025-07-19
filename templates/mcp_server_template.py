#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Template MCP Server - Copy this file to create new MCP servers

This template provides:
- Proper MCP protocol implementation
- File-based logging (never stdout)
- Error handling patterns
- Cross-workspace compatibility
- User scope registration support

To use this template:
1. Copy to indexing/mcp_yourserver_server.py
2. Replace TEMPLATE_SERVER with your-server-name
3. Replace TEMPLATE_TOOL with your-tool-name
4. Implement your tool logic
5. Update installation scripts
6. Test and deploy
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configure logging to file only (NEVER stdout - breaks MCP protocol)
log_dir = Path.home() / ".claude" / "mcp" / "central" / "TEMPLATE_SERVER" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger(__name__)

# MCP imports (CRITICAL: Use exact versions that work)
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    TextContent,
    Tool,
)

# Initialize server
server = Server("TEMPLATE_SERVER")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools

    CRITICAL: Must return list[Tool] not ListToolsResult
    This is the most common MCP implementation mistake
    """
    logger.info("Listing available tools")

    return [
        Tool(
            name="TEMPLATE_TOOL",
            description="Template tool - replace with your implementation",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter for the tool"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Processing mode",
                        "enum": ["basic", "advanced"],
                        "default": "basic"
                    },
                    "options": {
                        "type": "object",
                        "description": "Additional options",
                        "properties": {
                            "verbose": {
                                "type": "boolean",
                                "description": "Enable verbose output",
                                "default": False
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Limit number of results",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100
                            }
                        },
                        "additionalProperties": False
                    }
                },
                "required": ["input"],
                "additionalProperties": False
            }
        ),
        # Add more tools here following the same pattern
        Tool(
            name="TEMPLATE_STATUS",
            description="Get server status and health information",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
    ]

@server.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """
    Handle tool calls

    This is the main entry point for all tool requests.
    Always include proper error handling and logging.
    """
    tool_name = request.params.name
    logger.info(f"Tool called: {tool_name}")

    try:
        if tool_name == "TEMPLATE_TOOL":
            return await handle_template_tool(request)
        elif tool_name == "TEMPLATE_STATUS":
            return await handle_status_tool(request)
        else:
            error_msg = f"Unknown tool: {tool_name}"
            logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {error_msg}")]
            )

    except Exception as e:
        error_msg = f"Error in tool {tool_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {error_msg}")]
        )

async def handle_template_tool(request: CallToolRequest) -> CallToolResult:
    """
    Implementation of TEMPLATE_TOOL

    Replace this with your actual tool logic.
    Always validate inputs and handle errors gracefully.
    """
    args = request.params.arguments or {}

    # Extract and validate parameters
    input_data = args.get("input", "")
    mode = args.get("mode", "basic")
    options = args.get("options", {})

    verbose = options.get("verbose", False)
    limit = options.get("limit", 10)

    logger.info(f"Processing tool with input='{input_data}', mode='{mode}', verbose={verbose}, limit={limit}")

    # Validate inputs
    if not input_data:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: input parameter is required")]
        )

    if mode not in ["basic", "advanced"]:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: mode must be 'basic' or 'advanced'")]
        )

    # TODO: Implement your tool logic here
    # This is where you'd add your actual functionality

    if mode == "basic":
        result = f"Basic processing of: {input_data}"
    else:
        result = f"Advanced processing of: {input_data} with limit {limit}"

    if verbose:
        result += f"\nProcessed at: {datetime.now().isoformat()}"
        result += f"\nOptions: {options}"

    logger.info(f"Tool completed successfully, result length: {len(result)}")

    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def handle_status_tool(request: CallToolRequest) -> CallToolResult:
    """
    Get server status and health information

    This is a useful tool to include in every server for debugging.
    """
    logger.info("Status tool called")

    status = {
        "server": "TEMPLATE_SERVER",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "log_file": str(log_file),
        "tools_available": ["TEMPLATE_TOOL", "TEMPLATE_STATUS"]
    }

    result = json.dumps(status, indent=2)

    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def main():
    """
    Main server function

    CRITICAL:
    - Use exact protocol version that works
    - Use stdio_server() for Claude Desktop/CLI compatibility
    - Never write to stdout during operation
    """
    logger.info("Template MCP Server starting")

    try:
        # CRITICAL: Use exact protocol version
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="TEMPLATE_SERVER",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Server startup error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
