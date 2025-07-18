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

echo "Testing installed MCP Code Review Server..."
echo "=========================================="

INSTALL_DIR="$HOME/.claude/mcp/code-review"

# Check server file exists
if [ ! -f "$INSTALL_DIR/bin/server.py" ]; then
    echo "❌ Server not found at $INSTALL_DIR/bin/server.py"
    exit 1
fi
echo "✓ Server file exists"

# Check src files exist
for file in file_collector.py gemini_client.py review_formatter.py; do
    if [ ! -f "$INSTALL_DIR/src/$file" ]; then
        echo "❌ Missing source file: $file"
        exit 1
    fi
done
echo "✓ All source files present"

# Check venv exists
if [ ! -d "$INSTALL_DIR/venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi
echo "✓ Virtual environment exists"

# Test importing the server without __file__
echo ""
echo "Testing server import without __file__..."
"$INSTALL_DIR/venv/bin/python3" -c "
import sys
import os

# Remove __file__ to simulate MCP environment
if '__file__' in globals():
    del globals()['__file__']

# Set working directory
os.chdir('$INSTALL_DIR/bin')
sys.path.insert(0, '.')

try:
    import server
    print('✓ Server imported successfully')
    print(f'  Has main: {hasattr(server, \"main\")}')
except NameError as e:
    if '__file__' in str(e):
        print(f'❌ NameError with __file__: {e}')
        sys.exit(1)
    raise
except Exception as e:
    print(f'❌ Import failed: {type(e).__name__}: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Import test failed!"
    exit 1
fi

# Test that the start script works (without actually starting the server)
echo ""
echo "Testing start script..."
if [ -f "$INSTALL_DIR/start-server.sh" ]; then
    echo "✓ Start script exists"

    # Test that the venv python exists
    if [ -x "$INSTALL_DIR/venv/bin/python3" ]; then
        echo "✓ Virtual environment Python is executable"
    else
        echo "❌ Virtual environment Python not executable"
        exit 1
    fi
else
    echo "❌ Start script not found"
    exit 1
fi

echo ""
echo "✅ All tests passed! The MCP server is properly installed."
echo ""
echo "Next steps:"
echo "1. Restart Claude Code"
echo "2. The server should appear in the MCP servers list"
echo "3. Test with: mcp__code-review__review_code"
