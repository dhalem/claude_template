#!/bin/bash
# Startup script for MCP code search server
# This script will be copied to ~/.claude/mcp/ during installation

# Get the home directory MCP path
MCP_DIR="$HOME/.claude/mcp"

# Start the server from the home directory
cd "$MCP_DIR"
exec python3 code-search-server.py
