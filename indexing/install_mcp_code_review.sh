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
if [ ! -f "mcp_code_review_server_v2.py" ]; then
    echo "Error: mcp_code_review_server_v2.py not found in current directory"
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
cp mcp_code_review_server_v2.py "$TARGET_BIN/server.py"
chmod +x "$TARGET_BIN/server.py"

# Always update src files
echo "Copying required source files..."

# Check if reviewer src exists
REVIEWER_SRC="../reviewer/src"
if [ -d "$REVIEWER_SRC" ]; then
    cp "$REVIEWER_SRC/file_collector.py" "$TARGET_SRC/" || {
        echo "Error: Failed to copy file_collector.py"
        exit 1
    }
    cp "$REVIEWER_SRC/gemini_client.py" "$TARGET_SRC/" || {
        echo "Error: Failed to copy gemini_client.py"
        exit 1
    }
    cp "$REVIEWER_SRC/review_formatter.py" "$TARGET_SRC/" || {
        echo "Error: Failed to copy review_formatter.py"
        exit 1
    }
    echo "Source files copied successfully"
else
    echo "Error: Reviewer source files not found at $REVIEWER_SRC"
    echo "Please ensure these files exist:"
    echo "  - $REVIEWER_SRC/file_collector.py"
    echo "  - $REVIEWER_SRC/gemini_client.py"
    echo "  - $REVIEWER_SRC/review_formatter.py"
    exit 1
fi

# Create or update the MCP venv
echo "Setting up MCP virtual environment..."
if [ ! -d "$TARGET_DIR/venv" ]; then
    python3 -m venv "$TARGET_DIR/venv"
fi

# Always update dependencies
"$TARGET_DIR/venv/bin/pip" install --upgrade pip
"$TARGET_DIR/venv/bin/pip" install mcp google-generativeai

# Install any additional dependencies
if [ -f "../reviewer/requirements.txt" ]; then
    echo "Installing additional dependencies..."
    "$TARGET_DIR/venv/bin/pip" install -r "../reviewer/requirements.txt"
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
