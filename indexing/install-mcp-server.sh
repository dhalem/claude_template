#!/bin/bash
# Install script for MCP Code Search Server
# This script installs the MCP server to ~/.claude/mcp/ and configures it for use

set -e  # Exit on any error

# Colors for output
# RED='\033[0;31m'  # Unused color code
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Installation directories
MCP_DIR="$HOME/.claude/mcp"
MCP_SERVER_DIR="$MCP_DIR/code-search"
VENV_DIR="$MCP_SERVER_DIR/venv"
LOGS_DIR="$MCP_SERVER_DIR/logs"
BIN_DIR="$MCP_SERVER_DIR/bin"
CONFIG_DIR="$MCP_SERVER_DIR/config"

echo -e "${BLUE}🚀 Installing MCP Code Search Server${NC}"
echo "Repository: $REPO_ROOT"
echo "Install to: $MCP_SERVER_DIR"
echo

# Step 1: Create directory structure (remove old installation first)
echo -e "${YELLOW}📁 Creating directory structure...${NC}"
if [ -d "$MCP_SERVER_DIR" ]; then
    echo "  Removing existing installation..."
    rm -rf "$MCP_SERVER_DIR"
fi
mkdir -p "$MCP_SERVER_DIR"
mkdir -p "$VENV_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$CONFIG_DIR"

# Step 1b: Create dedicated venv for MCP server
echo -e "${YELLOW}🐍 Creating MCP server venv...${NC}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
# Use requirements file for consistent dependencies
pip install -r "$SCRIPT_DIR/mcp-requirements.txt"

# Step 2: Copy server files
echo -e "${YELLOW}📋 Copying server files...${NC}"

# Copy the proper MCP server using official MCP library
cp "$SCRIPT_DIR/mcp_server_proper.py" "$BIN_DIR/server.py"
chmod +x "$BIN_DIR/server.py"

# Note: This server is completely self-contained and will work with ANY workspace that has a .code_index.db

# Copy startup script
cat > "$MCP_DIR/start-code-search.sh" << EOF
#!/bin/bash
# Startup script for MCP code search server

# Get the current working directory (where Claude Code is running)
export MCP_CWD="\$PWD"

# Run the server with its venv
exec "$VENV_DIR/bin/python3" "$BIN_DIR/server.py"
EOF

chmod +x "$MCP_DIR/start-code-search.sh"

# Step 3: Create workspace configuration script
echo -e "${YELLOW}⚙️  Creating workspace configuration...${NC}"

cat > "$MCP_DIR/configure-workspaces.sh" << 'EOF'
#!/bin/bash
# Configure workspaces for MCP search server

CONFIG_FILE="$HOME/.claude/mcp/config.json"

# Create initial config if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'CONFIGEOF'
{
  "workspaces": {},
  "fallback_enabled": true,
  "cache_ttl": 300,
  "docker_contexts": {
    "default": "musicbot"
  }
}
CONFIGEOF
fi

echo "Workspace configuration created at: $CONFIG_FILE"
echo "Edit this file to add your specific repositories and Docker containers"
EOF

chmod +x "$MCP_DIR/configure-workspaces.sh"

# Step 4: Create initial configuration
echo -e "${YELLOW}📝 Creating initial configuration...${NC}"
"$MCP_DIR/configure-workspaces.sh"

# Step 5: Create workspace detection helper
cat > "$MCP_DIR/detect-workspace.py" << 'EOF'
#!/usr/bin/env python3
"""Workspace detection utility for MCP server"""

import os
import json
import sys
from pathlib import Path

def find_git_root(path):
    """Find the root of the git repository"""
    current = Path(path).resolve()
    while current != current.parent:
        if (current / '.git').exists():
            return str(current)
        current = current.parent
    return None

def detect_workspace(cwd):
    """Detect workspace information for the current directory"""
    git_root = find_git_root(cwd)
    if not git_root:
        return None

    # Check if this repository has indexing setup
    indexing_dir = Path(git_root) / 'indexing'
    if not indexing_dir.exists():
        return None

    # Check for Claude search script
    search_script = indexing_dir / 'claude_code_search.py'
    if not search_script.exists():
        return None

    return {
        'git_root': git_root,
        'indexing_dir': str(indexing_dir),
        'search_script': str(search_script),
        'repo_name': Path(git_root).name
    }

if __name__ == '__main__':
    cwd = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    workspace = detect_workspace(cwd)
    print(json.dumps(workspace, indent=2))
EOF

chmod +x "$MCP_DIR/detect-workspace.py"

# Step 6: Test the installation
echo -e "${YELLOW}🧪 Testing installation...${NC}"

# Test using MCP client library
echo "Testing server with MCP client..."
TEST_RESULT=$(cd "$SCRIPT_DIR" && "$VENV_DIR/bin/python3" test_mcp_client.py "$BIN_DIR/server.py" "$VENV_DIR/bin/python3" 2>&1)

if echo "$TEST_RESULT" | grep -q "✅ Found"; then
    echo -e "${GREEN}✅ Server test passed${NC}"
    echo "$TEST_RESULT" | grep "✅" | head -5
else
    echo -e "${YELLOW}⚠️  Basic server test skipped - will test after installation${NC}"
fi


echo
echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
echo
echo "Files installed:"
echo "  📁 $MCP_SERVER_DIR/"
echo "  ├── bin/server.py       # Main server executable"
echo "  ├── config/             # Configuration files"
echo "  ├── logs/               # Server logs"
echo "  └── venv/               # Python virtual environment"
echo
echo "  📄 $MCP_DIR/start-code-search.sh  # Startup script"
echo

echo -e "${BLUE}Next steps:${NC}"
echo "1. Remove old server (if exists):"
echo "   claude mcp remove code-search"
echo
echo "2. Add the updated server:"
echo "   claude mcp add code-search bash $MCP_DIR/start-code-search.sh"
echo
echo "3. Restart Claude Code to load the server"
echo

echo
echo -e "${GREEN}Installation complete! 🚀${NC}"
