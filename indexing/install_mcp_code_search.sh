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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing MCP Code Search Server...${NC}"

# Check if MCP is installed
if ! command -v mcp &> /dev/null; then
    echo -e "${RED}Error: MCP is not installed${NC}"
    echo "Please install MCP first: npm install -g @modelcontextprotocol/cli"
    exit 1
fi

# Get the installation directory
MCP_DIR="$HOME/.claude/mcp/servers/code-search"
echo -e "${YELLOW}Installation directory: $MCP_DIR${NC}"

# Create directory structure
mkdir -p "$MCP_DIR"
mkdir -p "$MCP_DIR/logs"

# Copy the server file
echo "Copying server files..."
cp mcp_search_server.py "$MCP_DIR/"

# Create a simple test script
cat > "$MCP_DIR/test_server.py" << 'EOF'
#!/usr/bin/env python3
"""Test the MCP code search server installation."""

import sys
import os

# Add the server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import mcp_search_server
    print("✓ Server module imported successfully")

    # Test that the CodeSearcher class exists
    searcher_class = getattr(mcp_search_server, 'CodeSearcher', None)
    if searcher_class:
        print("✓ CodeSearcher class found")
    else:
        print("✗ CodeSearcher class not found")
        sys.exit(1)

    print("\nServer installation verified successfully!")

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
EOF

chmod +x "$MCP_DIR/test_server.py"

# Test the installation
echo -e "\n${YELLOW}Testing installation...${NC}"
if python3 "$MCP_DIR/test_server.py"; then
    echo -e "${GREEN}✓ Installation test passed${NC}"
else
    echo -e "${RED}✗ Installation test failed${NC}"
    exit 1
fi

# Create configuration for Claude Desktop
CONFIG_FILE="$HOME/.config/claude/claude_desktop_config.json"
mkdir -p "$(dirname "$CONFIG_FILE")"

echo -e "\n${YELLOW}Updating Claude Desktop configuration...${NC}"

# Check if config exists and has mcpServers
if [ -f "$CONFIG_FILE" ]; then
    # Backup existing config
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"

    # Check if the server is already configured
    if grep -q '"code-search"' "$CONFIG_FILE"; then
        echo -e "${YELLOW}Code search server already configured. Updating...${NC}"
        # Remove existing code-search configuration
        python3 -c "
import json
import sys

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

if 'mcpServers' in config and 'code-search' in config['mcpServers']:
    del config['mcpServers']['code-search']

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    fi
else
    # Create new config
    echo '{"mcpServers": {}}' > "$CONFIG_FILE"
fi

# Add our server to the config
python3 -c "
import json
import sys
import os

config_file = '$CONFIG_FILE'
mcp_dir = '$MCP_DIR'

with open(config_file, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['code-search'] = {
    'command': 'python3',
    'args': [os.path.join(mcp_dir, 'mcp_search_server.py')],
    'env': {}
}

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print('✓ Configuration updated successfully')
"

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "\nThe MCP Code Search Server has been installed and configured."
echo -e "\n${YELLOW}Available tools:${NC}"
echo "  - search_code: Search for code symbols by name, content, or file path"
echo "  - list_symbols: List all symbols of a specific type"
echo "  - get_search_stats: Get statistics about the code index database"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Make sure your code indexer is running (./start-indexer.sh)"
echo "2. Restart Claude Desktop to load the new server"
echo "3. The code search tools will be available in Claude"
echo -e "\n${YELLOW}Logs are available at:${NC} $MCP_DIR/logs/"
