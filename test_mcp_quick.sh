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

# Quick test script for MCP servers

echo "=== MCP Server Quick Test ==="
echo ""

# Step 1: Check if servers are configured
echo "1. Checking MCP server configuration..."
claude mcp list > /tmp/mcp_list.txt 2>&1

if grep -q "No MCP servers configured" /tmp/mcp_list.txt; then
    echo "❌ No MCP servers configured!"
    echo ""
    echo "Run this to add servers from .mcp.json:"
    echo 'cat .mcp.json | jq -r '"'"'.mcpServers | to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"'"'"' | bash'
    exit 1
else
    echo "✅ MCP servers found:"
    cat /tmp/mcp_list.txt
fi

echo ""

# Step 2: Test protocol response
echo "2. Testing server protocol responses..."

# Extract server info from .mcp.json
if [ -f ".mcp.json" ]; then
    # Test code-review server
    REVIEW_CMD=$(jq -r '.mcpServers["code-review"].command' .mcp.json)
    REVIEW_SERVER=$(jq -r '.mcpServers["code-review"].args[0]' .mcp.json)

    if [ "$REVIEW_CMD" != "null" ] && [ "$REVIEW_SERVER" != "null" ]; then
        echo -n "   Testing code-review server... "
        if echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0.0"},"capabilities":{}},"id":1}' | \
           timeout 5 "$REVIEW_CMD" "$REVIEW_SERVER" 2>/dev/null | grep -q '"protocolVersion"'; then
            echo "✅ Responds to protocol"
        else
            echo "❌ No protocol response"
        fi
    fi

    # Test code-search server
    SEARCH_CMD=$(jq -r '.mcpServers["code-search"].command' .mcp.json)
    SEARCH_SERVER=$(jq -r '.mcpServers["code-search"].args[0]' .mcp.json)

    if [ "$SEARCH_CMD" != "null" ] && [ "$SEARCH_SERVER" != "null" ]; then
        echo -n "   Testing code-search server... "
        if echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0.0"},"capabilities":{}},"id":1}' | \
           timeout 5 "$SEARCH_CMD" "$SEARCH_SERVER" 2>/dev/null | grep -q '"protocolVersion"'; then
            echo "✅ Responds to protocol"
        else
            echo "❌ No protocol response"
        fi
    fi
fi

echo ""

# Step 3: Test actual tool call
echo "3. Testing MCP tool call through Claude..."
echo "   (This may take a moment...)"

# Create test file
cat > test_mcp_target.py << 'EOF'
def test_function():
    """Test function with issues"""
    x = 1  # unused variable
    return "Hello"
EOF

# Test the tool
TEMP_LOG=$(mktemp)
timeout 30 claude --debug --dangerously-skip-permissions \
    -p "Use the mcp__code-review__review_code tool to review test_mcp_target.py" \
    > "$TEMP_LOG" 2>&1 || true

# Check results
if grep -q "MCP server \"code-review\": Tool call succeeded" "$TEMP_LOG"; then
    echo "✅ MCP tool call succeeded!"
    echo ""
    echo "Sample output:"
    grep -A5 "Code Review Report" "$TEMP_LOG" | head -10 || true
else
    echo "❌ MCP tool call failed"
    echo ""
    echo "Debug info:"
    if grep -q "mcp__code-review__review_code" "$TEMP_LOG"; then
        echo "  - Tool was recognized by Claude"
    else
        echo "  - Tool was NOT recognized by Claude"
    fi

    if grep -q "MCP server \"code-review\": Calling MCP tool" "$TEMP_LOG"; then
        echo "  - Server was called but failed"
    else
        echo "  - Server was never called"
    fi
fi

# Cleanup
rm -f test_mcp_target.py "$TEMP_LOG" /tmp/mcp_list.txt

echo ""
echo "=== Test Complete ==="
