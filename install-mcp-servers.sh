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

# Central MCP Server Installation Script
echo "🚀 Installing Central MCP Servers"

# Create central installation directory
CENTRAL_DIR="$HOME/.claude/mcp/central"
echo "📁 Creating central directory: $CENTRAL_DIR"
mkdir -p "$CENTRAL_DIR/code-search"
mkdir -p "$CENTRAL_DIR/code-review"

# Install code-search server
echo "📦 Installing code-search server..."
cp indexing/mcp_search_server.py "$CENTRAL_DIR/code-search/server.py"
cp -r indexing/src "$CENTRAL_DIR/code-search/"

# Install code-review server
echo "📦 Installing code-review server..."
cp indexing/mcp_review_server.py "$CENTRAL_DIR/code-review/server.py"
cp -r indexing/src "$CENTRAL_DIR/code-review/"

# Make servers executable
chmod +x "$CENTRAL_DIR/code-search/server.py"
chmod +x "$CENTRAL_DIR/code-review/server.py"

# Create Python virtual environment for the central installation
echo "🐍 Setting up Python environment..."
cd "$CENTRAL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r "$OLDPWD/indexing/requirements.txt"

# Update Claude desktop configuration
CONFIG_FILE="$HOME/.config/claude/claude_desktop_config.json"
echo "⚙️  Updating Claude configuration: $CONFIG_FILE"

# Create backup of existing config
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Write new configuration
cat > "$CONFIG_FILE" << 'EOF'
{
  "mcpServers": {
    "code-search": {
      "command": "/home/dhalem/.claude/mcp/central/venv/bin/python",
      "args": ["/home/dhalem/.claude/mcp/central/code-search/server.py"],
      "env": {
        "PYTHONPATH": "/home/dhalem/.claude/mcp/central/code-search"
      }
    },
    "code-review": {
      "command": "/home/dhalem/.claude/mcp/central/venv/bin/python",
      "args": ["/home/dhalem/.claude/mcp/central/code-review/server.py"],
      "env": {
        "PYTHONPATH": "/home/dhalem/.claude/mcp/central/code-review"
      }
    }
  }
}
EOF

echo "✅ Central MCP server installation complete!"
echo "📍 Installed to: $CENTRAL_DIR"
echo "⚙️  Configuration: $CONFIG_FILE"
echo ""
echo "🔄 Please restart Claude Code to load the new servers"
echo ""
echo "📋 Available servers:"
echo "  - code-search: Search code symbols and content"
echo "  - code-review: AI-powered code review using Gemini"
