#!/bin/bash
# Installation script for simple MCP code search server
# Installs to ~/.claude/mcp/ following the hooks pattern

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

echo -e "${BLUE}🔧 Simple MCP Code Search Server Installation${NC}"
echo "=== Simple MCP Installation ==="

# Function to create backup
create_backup() {
    local file="$1"
    if [ -f "$file" ]; then
        local backup_file="${file}.backup.${TIMESTAMP}"
        cp "$file" "$backup_file"
        echo -e "${YELLOW}📋 Backed up: $(basename "$file") -> $(basename "$backup_file")${NC}"
    fi
}

# Create MCP directory structure
echo -e "\n${BLUE}📁 Creating directory structure...${NC}"
mkdir -p "$MCP_DIR/logs"
echo "Created: $MCP_DIR"
echo "Created: $MCP_DIR/logs"

# Install simple server files
echo -e "\n${BLUE}📦 Installing simple MCP server...${NC}"

# Simple server script
create_backup "$MCP_DIR/simple_mcp_server.py"
cp "$SCRIPT_DIR/simple_mcp_server.py" "$MCP_DIR/"
chmod +x "$MCP_DIR/simple_mcp_server.py"
echo "Installed: simple_mcp_server.py"

# Create startup script for simple server
create_backup "$MCP_DIR/start-simple-server.sh"
cat > "$MCP_DIR/start-simple-server.sh" << 'EOF'
#!/bin/bash
# Startup script for simple MCP code search server

# Get the current working directory (where Claude Code is running)
WORKSPACE_DIR="$PWD"

# Change to workspace directory
cd "$WORKSPACE_DIR"

# Start the server from the MCP directory but with workspace context
exec python3 "$HOME/.claude/mcp/simple_mcp_server.py"
EOF
chmod +x "$MCP_DIR/start-simple-server.sh"
echo "Created: start-simple-server.sh"

# Copy claude_code_search dependencies to MCP directory
echo -e "\n${BLUE}📦 Installing search dependencies...${NC}"
create_backup "$MCP_DIR/claude_code_search.py"
cp "$SCRIPT_DIR/../claude_code_search.py" "$MCP_DIR/"
echo "Installed: claude_code_search.py"

create_backup "$MCP_DIR/search_code.py"
cp "$SCRIPT_DIR/../search_code.py" "$MCP_DIR/"
echo "Installed: search_code.py"

# Validate installation
echo -e "\n${BLUE}✅ Validating installation...${NC}"

ERRORS=0

# Check if all files exist
for file in simple_mcp_server.py start-simple-server.sh claude_code_search.py search_code.py; do
    if [ -f "$MCP_DIR/$file" ]; then
        echo "✓ $file"
    else
        echo -e "${RED}✗ $file (missing)${NC}"
        ((ERRORS++))
    fi
done

# Check if executable files are executable
for script in simple_mcp_server.py start-simple-server.sh; do
    if [ -x "$MCP_DIR/$script" ]; then
        echo "✓ $script (executable)"
    else
        echo -e "${RED}✗ $script (not executable)${NC}"
        ((ERRORS++))
    fi
done

# Test server initialization
echo -e "\n${BLUE}🧪 Testing server initialization...${NC}"
cd "$PWD"  # Stay in current directory for workspace context
if python3 "$MCP_DIR/simple_mcp_server.py" <<< '{"method": "tools/list", "params": {}}' >/dev/null 2>&1; then
    echo "✓ Server can be started and responds to requests"
else
    echo -e "${RED}✗ Server initialization failed${NC}"
    ((ERRORS++))
fi

# Check Claude Code availability
echo -e "\n${BLUE}🔍 Checking Claude Code...${NC}"
if command -v claude >/dev/null 2>&1; then
    echo "✓ Claude Code CLI available"

    echo -e "\n${BLUE}🚀 To add the MCP server, run:${NC}"
    echo "claude mcp add simple-search bash $MCP_DIR/start-simple-server.sh"
else
    echo -e "${YELLOW}⚠️  Claude Code CLI not found${NC}"
    echo "Please install Claude Code to use the MCP server"
fi

# Usage instructions
echo -e "\n${BLUE}📖 Usage Instructions:${NC}"
echo "1. The server uses local filesystem search (no Docker needed)"
echo "2. It automatically detects the workspace from current directory"
echo "3. Works with any repository that has a search index"
echo "4. Provides 4 search tools: search_code, list_symbols, explore_file, search_in_files"

# Summary
echo -e "\n${BLUE}📊 Installation Summary${NC}"
echo "=== Simple MCP Installation ==="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Installation completed successfully!${NC}"
    echo -e "   📁 Server installed to: $MCP_DIR"
    echo -e "   📝 Logs directory: $MCP_DIR/logs"
    echo -e "\n${GREEN}🎉 Next steps:${NC}"
    echo "   1. Add to Claude Code: claude mcp add simple-search bash $MCP_DIR/start-simple-server.sh"
    echo "   2. Start using search tools in any repository with a search index!"
    echo "   3. The server will automatically use the local search index"
else
    echo -e "${RED}❌ Installation completed with $ERRORS error(s)${NC}"
    echo "Please review the errors above and try again."
    exit 1
fi

echo -e "\n${BLUE}🔗 No configuration needed - works out of the box!${NC}"
