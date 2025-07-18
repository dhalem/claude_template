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

echo "Installing MCP Code Review Server..."
echo "====================================="

# Check if running from correct directory
if [ ! -f "mcp_review_server.py" ]; then
    echo "Error: mcp_review_server.py not found in current directory"
    echo "Please run this script from the indexing directory"
    exit 1
fi

# Target directory
TARGET_DIR="$HOME/.claude/mcp/code-review"
TARGET_BIN="$TARGET_DIR/bin"
TARGET_SRC="$TARGET_DIR/src"

# Check if MCP directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating MCP code-review directory structure..."
    mkdir -p "$TARGET_BIN" "$TARGET_SRC"
fi

# Backup existing server if it exists
if [ -f "$TARGET_BIN/server.py" ]; then
    BACKUP_NAME="server.py.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backing up existing server to: $BACKUP_NAME"
    cp "$TARGET_BIN/server.py" "$TARGET_BIN/$BACKUP_NAME"
fi

# Copy the new server
echo "Installing new server..."
cp mcp_review_server.py "$TARGET_BIN/server.py"
chmod +x "$TARGET_BIN/server.py"

# Always update src files
echo "Copying required source files..."

# Check if local src exists
LOCAL_SRC="src"
if [ -d "$LOCAL_SRC" ]; then
    cp "$LOCAL_SRC/file_collector.py" "$TARGET_SRC/" || {
        echo "Error: Failed to copy file_collector.py"
        exit 1
    }
    cp "$LOCAL_SRC/gemini_client.py" "$TARGET_SRC/" || {
        echo "Error: Failed to copy gemini_client.py"
        exit 1
    }
    cp "$LOCAL_SRC/review_formatter.py" "$TARGET_SRC/" || {
        echo "Error: Failed to copy review_formatter.py"
        exit 1
    }
    echo "Source files copied successfully"
else
    echo "Error: Local source files not found at $LOCAL_SRC"
    echo "Please ensure these files exist:"
    echo "  - $LOCAL_SRC/file_collector.py"
    echo "  - $LOCAL_SRC/gemini_client.py"
    echo "  - $LOCAL_SRC/review_formatter.py"
    exit 1
fi

# Create or update the MCP venv
echo "Setting up MCP virtual environment..."
if [ ! -d "$TARGET_DIR/venv" ]; then
    python3 -m venv "$TARGET_DIR/venv"
fi

# Always update dependencies
"$TARGET_DIR/venv/bin/pip" install --upgrade pip

# Install dependencies from requirements file if available
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    "$TARGET_DIR/venv/bin/pip" install -r "requirements.txt"
elif [ -f "../reviewer/requirements.txt" ]; then
    echo "Installing dependencies from reviewer requirements.txt..."
    "$TARGET_DIR/venv/bin/pip" install -r "../reviewer/requirements.txt"
else
    echo "Installing basic dependencies..."
    "$TARGET_DIR/venv/bin/pip" install mcp google-generativeai
fi

echo ""
echo "Installation complete!"
echo "====================="
echo ""
echo "To use the fixed MCP code review server:"
echo "1. Restart Claude Code (exit and start again)"
echo "2. The server will automatically load with the fix"
echo "3. Test with: mcp__code-review__review_code"
echo ""
echo "Server installed at: $TARGET_BIN/server.py"
echo "Logs will be at: $HOME/.claude/mcp/code-review/logs/"
echo ""

# Kill existing server processes to force reload
echo "Stopping existing MCP code review servers..."
pkill -f "mcp/code-review/bin/server.py" 2>/dev/null || true
echo "Done. Please restart Claude Code."
