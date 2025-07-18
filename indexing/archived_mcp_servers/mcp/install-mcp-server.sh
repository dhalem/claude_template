#!/bin/bash
# Installation script for MCP code search server
# Installs the server to ~/.claude/mcp/ following the same pattern as hooks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_DIR="$HOME/.claude/mcp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo -e "${BLUE}🔧 MCP Code Search Server Installation${NC}"
echo "=== MCP Server Installation ==="

# Function to create backup
create_backup() {
    local file="$1"
    if [ -f "$file" ]; then
        local backup_file="${file}.backup.${TIMESTAMP}"
        cp "$file" "$backup_file"
        echo -e "${YELLOW}📋 Backed up existing file: $(basename "$file") -> $(basename "$backup_file")${NC}"
    fi
}

# Create MCP directory structure
echo -e "\n${BLUE}📁 Creating directory structure...${NC}"
mkdir -p "$MCP_DIR/logs"
echo "Created: $MCP_DIR"
echo "Created: $MCP_DIR/logs"

# Install server files with backups
echo -e "\n${BLUE}📦 Installing MCP server files...${NC}"

# Server script
create_backup "$MCP_DIR/code-search-server.py"
cp "$SCRIPT_DIR/code-search-server.py" "$MCP_DIR/"
chmod +x "$MCP_DIR/code-search-server.py"
echo "Installed: code-search-server.py"

# Startup script
create_backup "$MCP_DIR/start-search-server.sh"
cp "$SCRIPT_DIR/start-search-server.sh" "$MCP_DIR/"
chmod +x "$MCP_DIR/start-search-server.sh"
echo "Installed: start-search-server.sh"

# Configuration script
create_backup "$MCP_DIR/configure-workspaces.sh"
cp "$SCRIPT_DIR/configure-workspaces.sh" "$MCP_DIR/"
chmod +x "$MCP_DIR/configure-workspaces.sh"
echo "Installed: configure-workspaces.sh"

# Configuration file (only if it doesn't exist)
if [ ! -f "$MCP_DIR/config.json" ]; then
    cp "$SCRIPT_DIR/config.json" "$MCP_DIR/"
    echo "Installed: config.json (default configuration)"
else
    echo "Skipped: config.json (already exists)"
fi

# Validate installation
echo -e "\n${BLUE}✅ Validating installation...${NC}"

ERRORS=0

# Check if all files exist
for file in code-search-server.py start-search-server.sh configure-workspaces.sh config.json; do
    if [ -f "$MCP_DIR/$file" ]; then
        echo "✓ $file"
    else
        echo -e "${RED}✗ $file (missing)${NC}"
        ((ERRORS++))
    fi
done

# Check if files are executable
for script in code-search-server.py start-search-server.sh configure-workspaces.sh; do
    if [ -x "$MCP_DIR/$script" ]; then
        echo "✓ $script (executable)"
    else
        echo -e "${RED}✗ $script (not executable)${NC}"
        ((ERRORS++))
    fi
done

# Test configuration loading
echo -e "\n${BLUE}🧪 Testing server initialization...${NC}"
cd "$MCP_DIR"
if python3 -c "
import json
import sys
from pathlib import Path
sys.path.insert(0, '.')
import importlib.util
spec = importlib.util.spec_from_file_location('server', 'code-search-server.py')
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)
server = server_module.WorkspaceAwareSearchServer()
print('✓ Server initialization successful')
print(f'✓ Configuration loaded: {len(server.config[\"workspaces\"])} workspace(s)')
" 2>/dev/null; then
    echo "✓ Server can be imported and initialized"
else
    echo -e "${RED}✗ Server initialization failed${NC}"
    ((ERRORS++))
fi

# Check Claude Code availability
echo -e "\n${BLUE}🔍 Checking Claude Code...${NC}"
if command -v claude >/dev/null 2>&1; then
    echo "✓ Claude Code CLI available"

    # Show current MCP servers
    echo -e "\n${BLUE}📋 Current MCP servers:${NC}"
    claude mcp list || echo "No MCP servers configured"

    echo -e "\n${BLUE}🚀 To add the MCP server, run:${NC}"
    echo "claude mcp add code-search bash $MCP_DIR/start-search-server.sh"
else
    echo -e "${YELLOW}⚠️  Claude Code CLI not found${NC}"
    echo "Please install Claude Code to use the MCP server"
fi

# Configuration guidance
echo -e "\n${BLUE}⚙️  Configuration:${NC}"
echo "Edit $MCP_DIR/config.json to configure workspaces:"
echo "{"
echo "  \"workspaces\": {"
echo "    \"/path/to/your/repo\": {"
echo "      \"docker_context\": \"your-context\","
echo "      \"container_name\": \"your-container\","
echo "      \"indexing_path\": \"/app/indexing\""
echo "    }"
echo "  }"
echo "}"

# Summary
echo -e "\n${BLUE}📊 Installation Summary${NC}"
echo "=== MCP Server Installation ==="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Installation completed successfully!${NC}"
    echo -e "   📁 Server installed to: $MCP_DIR"
    echo -e "   📋 Configuration file: $MCP_DIR/config.json"
    echo -e "   📝 Logs directory: $MCP_DIR/logs"
    echo -e "\n${GREEN}🎉 Next steps:${NC}"
    echo "   1. Configure workspaces in config.json"
    echo "   2. Add to Claude Code: claude mcp add code-search bash $MCP_DIR/start-search-server.sh"
    echo "   3. Start using code search tools in Claude Code!"
else
    echo -e "${RED}❌ Installation completed with $ERRORS error(s)${NC}"
    echo "Please review the errors above and try again."
    exit 1
fi

echo -e "\n${BLUE}🔗 Documentation: docs/SEARCH_MCP.md${NC}"
