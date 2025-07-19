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

echo "🧹 Cleaning up conflicting MCP server installations"

# Create backup of current state
BACKUP_DIR="$HOME/.claude/cleanup_backup_$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup at: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup old installations before removal
if [ -d "$HOME/.claude/mcp/code-review" ]; then
    echo "📦 Backing up old code-review installation..."
    cp -r "$HOME/.claude/mcp/code-review" "$BACKUP_DIR/"
fi

if [ -d "$HOME/.claude/mcp/code-search" ]; then
    echo "📦 Backing up old code-search installation..."
    cp -r "$HOME/.claude/mcp/code-search" "$BACKUP_DIR/"
fi

# Remove old conflicting installations
echo "🗑️  Removing old MCP installations..."
rm -rf "$HOME/.claude/mcp/code-review"
rm -rf "$HOME/.claude/mcp/code-search"
rm -rf "$HOME/.claude/mcp/servers"
rm -f "$HOME/.claude/mcp/code-search-server.py"

# Keep only central installation
echo "✅ Keeping central installation at: $HOME/.claude/mcp/central/"

# List what remains
echo ""
echo "📋 Remaining MCP installations:"
find "$HOME/.claude/mcp" -name "server.py" -type f 2>/dev/null | grep -v backup | head -5

# Verify configuration
CONFIG_FILE="$HOME/.config/claude/claude_desktop_config.json"
echo ""
echo "⚙️  Current configuration:"
if [ -f "$CONFIG_FILE" ]; then
    cat "$CONFIG_FILE"
else
    echo "❌ Configuration file not found: $CONFIG_FILE"
fi

echo ""
echo "✅ Cleanup complete!"
echo "📍 Backup created at: $BACKUP_DIR"
echo "🔄 Please restart Claude Code to use the central installation"
