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

# Central MCP Server Installation Script - FIXED VERSION
echo "🚀 Installing Central MCP Servers (Cross-Workspace Support)"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create central installation directory
CENTRAL_DIR="$HOME/.claude/mcp/central"
echo "📁 Creating central directory: $CENTRAL_DIR"
mkdir -p "$CENTRAL_DIR/code-search"
mkdir -p "$CENTRAL_DIR/code-review"

# Install code-search server
echo "📦 Installing code-search server..."
cp "$SCRIPT_DIR/indexing/mcp_search_server.py" "$CENTRAL_DIR/code-search/server.py"
cp -r "$SCRIPT_DIR/indexing/src" "$CENTRAL_DIR/code-search/"

# Install code-review server
echo "📦 Installing code-review server..."
cp "$SCRIPT_DIR/indexing/mcp_review_server.py" "$CENTRAL_DIR/code-review/server.py"
cp -r "$SCRIPT_DIR/indexing/src" "$CENTRAL_DIR/code-review/"

# Make servers executable
chmod +x "$CENTRAL_DIR/code-search/server.py"
chmod +x "$CENTRAL_DIR/code-review/server.py"

# Create Python virtual environment for the central installation
echo "🐍 Setting up Python environment..."
cd "$CENTRAL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/indexing/requirements.txt"

# Create a portable configuration using $HOME
echo "⚙️  Creating portable MCP configuration..."

# For Claude Desktop - Update global config
CONFIG_DIR="$HOME/.config/claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_FILE" ]; then
    echo "📋 Backing up existing Claude Desktop config..."
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Write configuration with $HOME variable (will be expanded at runtime)
cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "code-search": {
      "command": "$HOME/.claude/mcp/central/venv/bin/python",
      "args": ["$HOME/.claude/mcp/central/code-search/server.py"],
      "env": {
        "PYTHONPATH": "$HOME/.claude/mcp/central/code-search"
      }
    },
    "code-review": {
      "command": "$HOME/.claude/mcp/central/venv/bin/python",
      "args": ["$HOME/.claude/mcp/central/code-review/server.py"],
      "env": {
        "PYTHONPATH": "$HOME/.claude/mcp/central/code-review"
      }
    }
  }
}
EOF

# For Claude Code CLI - Register servers
echo ""
echo "📱 Registering servers with Claude Code CLI..."
if command -v claude &> /dev/null; then
    # Remove old registrations first
    claude mcp remove code-search 2>/dev/null || true
    claude mcp remove code-review 2>/dev/null || true

    # Add new registrations with central paths
    claude mcp add code-search "$HOME/.claude/mcp/central/venv/bin/python" "$HOME/.claude/mcp/central/code-search/server.py"
    claude mcp add code-review "$HOME/.claude/mcp/central/venv/bin/python" "$HOME/.claude/mcp/central/code-review/server.py"

    echo "✅ Servers registered with Claude Code CLI"
    claude mcp list
else
    echo "⚠️  Claude Code CLI not found - skipping CLI registration"
    echo "   You can manually add servers later with:"
    echo "   claude mcp add code-search $HOME/.claude/mcp/central/venv/bin/python $HOME/.claude/mcp/central/code-search/server.py"
    echo "   claude mcp add code-review $HOME/.claude/mcp/central/venv/bin/python $HOME/.claude/mcp/central/code-review/server.py"
fi

# Create a template .mcp.json for other projects
TEMPLATE_FILE="$CENTRAL_DIR/mcp.json.template"
cat > "$TEMPLATE_FILE" << 'EOF'
{
  "mcpServers": {
    "code-search": {
      "command": "~/.claude/mcp/central/venv/bin/python",
      "args": ["~/.claude/mcp/central/code-search/server.py"],
      "env": {
        "PYTHONPATH": "~/.claude/mcp/central/code-search"
      }
    },
    "code-review": {
      "command": "~/.claude/mcp/central/venv/bin/python",
      "args": ["~/.claude/mcp/central/code-review/server.py"],
      "env": {
        "PYTHONPATH": "~/.claude/mcp/central/code-review"
      }
    }
  }
}
EOF

echo ""
echo "✅ Central MCP server installation complete!"
echo "📍 Installed to: $CENTRAL_DIR"
echo "⚙️  Desktop config: $CONFIG_FILE"
echo "📄 Template config: $TEMPLATE_FILE"
echo ""
echo "🔄 For Claude Desktop: Restart Claude Code to load the new servers"
echo "📱 For Claude Code CLI: Servers already registered"
echo ""
echo "📋 To use in other workspaces:"
echo "   1. Copy template: cp $TEMPLATE_FILE /path/to/project/.mcp.json"
echo "   2. For CLI: Servers are globally registered, will work everywhere"
echo "   3. For Desktop: Will use central installation automatically"
echo ""
echo "⚠️  Required: export GEMINI_API_KEY='your-key' for code-review server"
