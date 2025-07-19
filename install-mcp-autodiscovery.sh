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

echo "🚀 Installing MCP Servers with Auto-Discovery"
echo "============================================="

# Check we're in the right directory
if [ ! -f "indexing/mcp_review_server.py" ]; then
    echo "❌ Error: Must run from claude_template repository root"
    exit 1
fi

# Auto-discovery paths (following MCP_SERVER_GUIDE.md)
CODE_REVIEW_DIR="$HOME/.claude/mcp/code-review"
CODE_SEARCH_DIR="$HOME/.claude/mcp/code-search"

# Create auto-discovery directory structure
echo "📁 Creating auto-discovery directory structure..."
mkdir -p "$CODE_REVIEW_DIR/bin" "$CODE_REVIEW_DIR/src" "$CODE_REVIEW_DIR/logs"
mkdir -p "$CODE_SEARCH_DIR/bin" "$CODE_SEARCH_DIR/src" "$CODE_SEARCH_DIR/logs"

# Copy servers to auto-discovery locations (MUST be named server.py)
echo "📦 Installing servers for auto-discovery..."
cp mcp_review_autodiscovery.py "$CODE_REVIEW_DIR/bin/server.py"
cp mcp_search_autodiscovery.py "$CODE_SEARCH_DIR/bin/server.py"
chmod +x "$CODE_REVIEW_DIR/bin/server.py"
chmod +x "$CODE_SEARCH_DIR/bin/server.py"

# Copy source modules
echo "📦 Installing source modules..."
cp -r indexing/src/* "$CODE_REVIEW_DIR/src/"
cp -r indexing/src/* "$CODE_SEARCH_DIR/src/"

# Create isolated virtual environments for each server
echo "🐍 Setting up isolated Python environments..."

# Code Review Server venv
if [ ! -d "$CODE_REVIEW_DIR/venv" ]; then
    python3 -m venv "$CODE_REVIEW_DIR/venv"
fi
"$CODE_REVIEW_DIR/venv/bin/pip" install --upgrade pip
"$CODE_REVIEW_DIR/venv/bin/pip" install -r indexing/requirements.txt

# Code Search Server venv
if [ ! -d "$CODE_SEARCH_DIR/venv" ]; then
    python3 -m venv "$CODE_SEARCH_DIR/venv"
fi
"$CODE_SEARCH_DIR/venv/bin/pip" install --upgrade pip
"$CODE_SEARCH_DIR/venv/bin/pip" install -r indexing/requirements.txt

# Remove explicit MCP configuration (auto-discovery doesn't need it)
echo "🔄 Removing explicit MCP configuration for auto-discovery..."
CONFIG_FILE="$HOME/.config/claude/claude_desktop_config.json"

if [ -f "$CONFIG_FILE" ]; then
    # Backup existing config
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"

    # Remove MCP servers section if it exists
    if command -v jq > /dev/null; then
        jq 'del(.mcpServers)' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        echo "✅ Removed explicit MCP configuration - using auto-discovery"
    else
        echo "⚠️  jq not available - please manually remove mcpServers from $CONFIG_FILE"
    fi
else
    # Create minimal config
    mkdir -p "$(dirname "$CONFIG_FILE")"
    echo '{}' > "$CONFIG_FILE"
fi

echo "✅ Auto-Discovery MCP server installation complete!"
echo ""
echo "📍 Servers installed for auto-discovery:"
echo "  - code-review: $CODE_REVIEW_DIR/bin/server.py"
echo "  - code-search: $CODE_SEARCH_DIR/bin/server.py"
echo ""
echo "🔄 Please restart Claude Code to load the servers"
echo ""
echo "📋 Available servers via auto-discovery:"
echo "  - mcp__code-review__review_code"
echo "  - mcp__code-search__search_code"
echo "  - mcp__code-search__list_symbols"
echo "  - mcp__code-search__get_search_stats"
echo ""
echo "🐛 Debug with: claude --debug -p 'hello world'"
