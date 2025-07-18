#!/bin/bash
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Install script for Code Review MCP Server (FastMCP version)

set -e

echo "Installing Code Review MCP Server (FastMCP)..."

# Define installation directory
MCP_DIR="$HOME/.claude/mcp/code-review"
mkdir -p "$MCP_DIR"

# Create bin and src directories
mkdir -p "$MCP_DIR/bin"
mkdir -p "$MCP_DIR/src"

# Create virtual environment
echo "Creating virtual environment..."
cd "$MCP_DIR"
python3 -m venv venv

# Activate venv and install dependencies
echo "Installing dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install mcp google-generativeai pathspec

# Copy the FastMCP server script
echo "Copying server files..."
cp "$(dirname "$0")/mcp_code_review_server_fastmcp.py" "$MCP_DIR/bin/server.py"

# Copy src files
echo "Copying source files..."
cp "$(dirname "$0")/src/file_collector.py" "$MCP_DIR/src/"
cp "$(dirname "$0")/src/gemini_client.py" "$MCP_DIR/src/"
cp "$(dirname "$0")/src/review_formatter.py" "$MCP_DIR/src/"
cp "$(dirname "$0")/src/__init__.py" "$MCP_DIR/src/" 2>/dev/null || touch "$MCP_DIR/src/__init__.py"

# Create start script
cat > "$MCP_DIR/start-server.sh" << 'EOF'
#!/bin/bash
# Startup script for MCP code review server

# Get the current working directory (where Claude Code is running)
export MCP_CWD="$PWD"

# Run the server with its own venv
exec "$HOME/.claude/mcp/code-review/venv/bin/python3" "$HOME/.claude/mcp/code-review/bin/server.py"
EOF

chmod +x "$MCP_DIR/start-server.sh"

# Create or update Claude MCP settings (global)
CONFIG_FILE="$HOME/Library/Application Support/Claude/mcp_settings.json"
CONFIG_DIR="$(dirname "$CONFIG_FILE")"
mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_FILE" ]; then
    echo "Updating existing MCP settings..."
    # Backup existing config
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"

    # Update config using Python to handle JSON properly
    ./venv/bin/python3 << 'PYTHON_EOF'
import json
import os

config_file = os.path.expanduser("~/Library/Application Support/Claude/mcp_settings.json")

# Read existing config
with open(config_file, 'r') as f:
    config = json.load(f)

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add or update code-review server
config['mcpServers']['code-review'] = {
    "command": os.path.expanduser("~/.claude/mcp/code-review/start-server.sh"),
    "restart": True
}

# Write updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("MCP settings updated successfully!")
PYTHON_EOF
else
    echo "Creating new MCP settings..."
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "code-review": {
      "command": "$MCP_DIR/start-server.sh",
      "restart": true
    }
  }
}
EOF
fi

echo "Installation complete!"
echo ""
echo "The Code Review MCP Server (FastMCP) has been installed."
echo "Please restart Claude for the changes to take effect."
echo ""
echo "To use the server, you can use the tool: mcp__code-review__review_code"
echo "Example: Review the code in /path/to/project directory"
