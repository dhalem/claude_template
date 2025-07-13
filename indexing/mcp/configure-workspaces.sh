#!/bin/bash
# Auto-detect and configure workspaces for MCP code search
# This script will be copied to ~/.claude/mcp/ during installation

MCP_DIR="$HOME/.claude/mcp"
CONFIG_FILE="$MCP_DIR/config.json"

# Ensure config directory exists
mkdir -p "$MCP_DIR/logs"

# Create default configuration if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
{
  "workspaces": {},
  "cache_ttl": 300
}
EOF
    echo "Created default configuration at $CONFIG_FILE"
else
    echo "Configuration already exists at $CONFIG_FILE"
fi

echo "Workspace configuration complete."
echo "To add a workspace manually, edit $CONFIG_FILE and add:"
echo '{
  "workspaces": {
    "/path/to/your/repo": {
      "docker_context": "your-context",
      "container_name": "your-container",
      "indexing_path": "/app/indexing"
    }
  }
}'
