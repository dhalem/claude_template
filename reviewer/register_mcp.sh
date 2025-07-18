#!/bin/bash
# Register both MCP servers with Claude

set -e

echo "Registering MCP servers..."

# Remove existing registrations if present
claude mcp remove code-search 2>/dev/null || true
claude mcp remove code-review 2>/dev/null || true

# Add the original working code search server
claude mcp add code-search bash "/home/dhalem/.claude/mcp/start-search-server.sh"

# Add the code review server
claude mcp add code-review bash "/home/dhalem/.claude/mcp/code-review/start-server.sh"

echo "Registration complete. Listing MCP servers:"
claude mcp list
