#!/bin/bash
# Test the installed MCP server using proper client

set -e

echo "Testing installed MCP server..."

# Use the proper test client
../venv/bin/python3 test_mcp_client.py \
    ~/.claude/mcp/code-search/bin/server.py \
    ~/.claude/mcp/code-search/venv/bin/python3
