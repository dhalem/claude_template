#!/bin/bash
# Register MCP servers globally (available in all Claude instances)

set -e

echo "Registering MCP servers globally..."

# Remove any existing registrations (local or global)
claude mcp remove code-search 2>/dev/null || true
claude mcp remove code-review 2>/dev/null || true
claude mcp remove code-search --global 2>/dev/null || true
claude mcp remove code-review --global 2>/dev/null || true

# Add servers to global configuration
echo "Adding code-search server globally..."
claude mcp add code-search bash "/home/dhalem/.claude/mcp/code-search/start-server.sh" --global

echo "Adding code-review server globally..."
claude mcp add code-review bash "/home/dhalem/.claude/mcp/code-review/start-server.sh" --global

echo ""
echo "Registration complete. Listing global MCP servers:"
claude mcp list --global
echo ""
echo "These servers are now available in ALL Claude Code instances!"
