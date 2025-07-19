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

echo "🚀 Installing Debug MCP Servers"
echo "==============================="

# Auto-discovery paths
CODE_REVIEW_DIR="$HOME/.claude/mcp/code-review"
CODE_SEARCH_DIR="$HOME/.claude/mcp/code-search"

# Backup existing servers
if [ -f "$CODE_REVIEW_DIR/bin/server.py" ]; then
    echo "📦 Backing up existing review server..."
    cp "$CODE_REVIEW_DIR/bin/server.py" "$CODE_REVIEW_DIR/bin/server.py.backup.$(date +%Y%m%d_%H%M%S)"
fi

if [ -f "$CODE_SEARCH_DIR/bin/server.py" ]; then
    echo "📦 Backing up existing search server..."
    cp "$CODE_SEARCH_DIR/bin/server.py" "$CODE_SEARCH_DIR/bin/server.py.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Install debug versions
echo "📦 Installing debug servers..."
cp mcp_working_server.py "$CODE_REVIEW_DIR/bin/server.py"
chmod +x "$CODE_REVIEW_DIR/bin/server.py"

# Fix shebang to use venv python
echo "🔧 Fixing shebang for code-review server..."
sed -i "1s|.*|#!$CODE_REVIEW_DIR/venv/bin/python|" "$CODE_REVIEW_DIR/bin/server.py"

# For search server, copy and fix shebang
cp mcp_search_autodiscovery.py "$CODE_SEARCH_DIR/bin/server.py"
chmod +x "$CODE_SEARCH_DIR/bin/server.py"
echo "🔧 Fixing shebang for code-search server..."
sed -i "1s|.*|#!$CODE_SEARCH_DIR/venv/bin/python|" "$CODE_SEARCH_DIR/bin/server.py"

# CRITICAL: Copy source modules (servers need these to work!)
echo "📦 Installing source modules..."
cp -r indexing/src/* "$CODE_REVIEW_DIR/src/"
cp -r indexing/src/* "$CODE_SEARCH_DIR/src/"

echo "✅ Debug servers installed!"
echo ""
echo "📋 Log files will be created at:"
echo "  - $CODE_REVIEW_DIR/logs/debug_*.log"
echo ""
echo "🔄 Please restart Claude Code and run:"
echo "   claude --debug -p 'hello world'"
echo ""
echo "Then check the debug log with:"
echo "   tail -f $CODE_REVIEW_DIR/logs/debug_*.log"
