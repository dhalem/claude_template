#!/bin/bash
# Update the installed MCP server with the fixed version

set -e

echo "Updating MCP server..."
cp mcp_server_proper.py ~/.claude/mcp/code-search/bin/server.py
echo "Server updated successfully!"
