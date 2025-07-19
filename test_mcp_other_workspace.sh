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

# Test MCP servers in another workspace
set -euo pipefail

echo "=== Testing MCP Servers in Other Workspace ==="
echo ""

# Check if a directory was provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 /path/to/other/workspace"
    echo "Example: $0 /home/user/my-project"
    exit 1
fi

TARGET_DIR="$1"

# Verify target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Directory does not exist: $TARGET_DIR"
    exit 1
fi

echo "📍 Testing in: $TARGET_DIR"
cd "$TARGET_DIR"

# Step 1: Check Claude CLI registration (global for CLI)
echo ""
echo "1. Checking global MCP registration (Claude CLI)..."
if command -v claude &> /dev/null; then
    claude mcp list

    if claude mcp list | grep -q "code-search"; then
        echo "✅ MCP servers are globally registered"
    else
        echo "❌ MCP servers not registered globally"
        echo "   Run: ./install-mcp-central.sh in claude_template"
        exit 1
    fi
else
    echo "⚠️  Claude CLI not found - skipping CLI tests"
fi

# Step 2: Test if we need a local .mcp.json
echo ""
echo "2. Checking for local .mcp.json..."
if [ -f ".mcp.json" ]; then
    echo "📄 Found existing .mcp.json"
    # Check if it points to central installation
    if grep -q "claude_template" ".mcp.json"; then
        echo "⚠️  WARNING: .mcp.json points to claude_template directory"
        echo "   This will break in other workspaces!"
    elif grep -q ".claude/mcp/central" ".mcp.json"; then
        echo "✅ .mcp.json uses central installation"
    fi
else
    echo "📝 No .mcp.json found (OK for CLI, Desktop uses global config)"
fi

# Step 3: Test actual MCP functionality
echo ""
echo "3. Testing MCP server functionality..."

# Create a test file
TEST_FILE="test_mcp_workspace.py"
cat > "$TEST_FILE" << 'EOF'
def example_function():
    """Test function for MCP review"""
    unused_variable = 123  # This should be flagged
    print("Hello from another workspace!")
    return True
EOF

echo "📄 Created test file: $TEST_FILE"

# Test with Claude CLI
if command -v claude &> /dev/null; then
    echo ""
    echo "🧪 Testing code-review server..."
    TEMP_LOG=$(mktemp)

    timeout 30 claude --debug --dangerously-skip-permissions \
        -p "Use the mcp__code-review__review_code tool to review $TEST_FILE in directory $TARGET_DIR" \
        > "$TEMP_LOG" 2>&1 || true

    if grep -q "MCP server \"code-review\": Tool call succeeded" "$TEMP_LOG"; then
        echo "✅ Code review server works in this workspace!"
        echo ""
        echo "Sample output:"
        grep -A5 "Code Review" "$TEMP_LOG" | head -10 || true
    else
        echo "❌ Code review server failed"
        echo ""
        echo "Debug info:"
        if grep -q "mcp__code-review__review_code" "$TEMP_LOG"; then
            echo "  - Tool was recognized"
        else
            echo "  - Tool was NOT recognized"
        fi

        if ! claude mcp list | grep -q "code-review"; then
            echo "  - Server not registered with Claude CLI"
            echo "  - Solution: Run ./install-mcp-central.sh"
        fi
    fi

    rm -f "$TEMP_LOG"
fi

# Cleanup
rm -f "$TEST_FILE"

echo ""
echo "=== Summary ==="
echo ""
echo "For MCP servers to work in other workspaces:"
echo ""
echo "1. Claude Code CLI:"
echo "   - Servers must be globally registered (claude mcp add)"
echo "   - No .mcp.json needed in other workspaces"
echo "   - Registration is system-wide"
echo ""
echo "2. Claude Desktop:"
echo "   - Uses ~/.config/claude/claude_desktop_config.json"
echo "   - OR project-specific .mcp.json (takes precedence)"
echo "   - Must use central installation paths"
echo ""
echo "3. Central Installation:"
echo "   - Located at: ~/.claude/mcp/central/"
echo "   - Shared by all workspaces"
echo "   - Run install-mcp-central.sh to set up"
echo ""
