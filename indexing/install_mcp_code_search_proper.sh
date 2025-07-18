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

set -euo pipefail

echo "Installing MCP Code Search Server (Proper Structure)..."
echo "===================================================="

# Check if running from correct directory
if [ ! -f "mcp_search_server.py" ]; then
    echo "Error: mcp_search_server.py not found in current directory"
    echo "Please run this script from the indexing directory"
    exit 1
fi

# Target directory - MUST follow this structure for auto-discovery
TARGET_DIR="$HOME/.claude/mcp/code-search"
TARGET_BIN="$TARGET_DIR/bin"
TARGET_SRC="$TARGET_DIR/src"

# Check if MCP directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating MCP code-search directory structure..."
    mkdir -p "$TARGET_BIN" "$TARGET_SRC" "$TARGET_DIR/logs"
fi

# Backup existing server if it exists
if [ -f "$TARGET_BIN/server.py" ]; then
    BACKUP_NAME="server.py.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backing up existing server to: $BACKUP_NAME"
    cp "$TARGET_BIN/server.py" "$TARGET_BIN/$BACKUP_NAME"
fi

# Copy the server - MUST be named server.py in bin/
echo "Installing server to correct location..."
cp mcp_search_server.py "$TARGET_BIN/server.py"
chmod +x "$TARGET_BIN/server.py"

# Since code-search doesn't have separate src files, create empty __init__.py
touch "$TARGET_SRC/__init__.py"

# Create or update the MCP venv - MUST use server's own venv
echo "Setting up MCP virtual environment..."
if [ ! -d "$TARGET_DIR/venv" ]; then
    python3 -m venv "$TARGET_DIR/venv"
fi

# Always update dependencies
echo "Installing dependencies..."
"$TARGET_DIR/venv/bin/pip" install --upgrade pip >/dev/null 2>&1

# Install MCP and other dependencies
"$TARGET_DIR/venv/bin/pip" install mcp >/dev/null 2>&1 || {
    echo "Warning: Failed to install mcp package"
}

# Remove any manual configuration from claude_desktop_config.json
CONFIG_FILE="$HOME/.config/claude/claude_desktop_config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "Cleaning up manual configuration..."
    python3 -c "
import json
import os

config_file = '$CONFIG_FILE'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)

    if 'mcpServers' in config and 'code-search' in config['mcpServers']:
        del config['mcpServers']['code-search']
        print('Removed manual code-search configuration')

        # If mcpServers is now empty, remove it
        if not config['mcpServers']:
            del config['mcpServers']

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
"
fi

# Kill existing server processes to force reload
echo "Stopping any existing code-search servers..."
pkill -f "mcp/servers/code-search" 2>/dev/null || true
pkill -f "mcp/code-search/bin/server.py" 2>/dev/null || true

echo ""
echo "Installation complete!"
echo "====================="
echo ""
echo "The MCP code-search server has been installed with the correct structure:"
echo "  Server: $TARGET_BIN/server.py"
echo "  Venv: $TARGET_DIR/venv/"
echo "  Logs: $TARGET_DIR/logs/"
echo ""
echo "Claude Desktop will auto-discover the server at startup."
echo ""
echo "To use the server:"
echo "1. Restart Claude Desktop (completely exit and restart)"
echo "2. The server will load automatically"
echo "3. Tools will be available as:"
echo "   - mcp__code-search__search_code"
echo "   - mcp__code-search__list_symbols"
echo "   - mcp__code-search__get_search_stats"
echo ""
echo "To verify installation:"
echo "  ls -la $TARGET_DIR/"
echo ""
echo "To check logs:"
echo "  tail -f $TARGET_DIR/logs/server_*.log"
echo ""
