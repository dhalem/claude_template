#!/bin/bash
# Start script for MCP code search server

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Start the MCP server
exec python3 mcp_code_search_server.py
