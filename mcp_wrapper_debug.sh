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

# Wrapper script to debug MCP server startup issues

# Create debug directory
DEBUG_DIR="$HOME/mcp_debug_logs"
mkdir -p "$DEBUG_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$DEBUG_DIR/wrapper_$TIMESTAMP.log"

# Log startup information
{
    echo "=== MCP Wrapper Debug Log ==="
    echo "Timestamp: $(date)"
    echo "Script: $0"
    echo "Arguments: $*"
    echo "PWD: $PWD"
    echo "USER: $USER"
    echo "HOME: $HOME"
    echo "PATH: $PATH"
    echo "PYTHON: $(which python3 || echo 'python3 not found')"
    echo "Parent PID: $PPID"
    echo "Parent process: $(ps -p $PPID -o comm= 2>/dev/null || echo 'unknown')"
    echo ""
    echo "=== Environment Variables ==="
    env | sort
    echo ""
    echo "=== Starting actual server ==="
} > "$LOG_FILE" 2>&1

# The actual command to run (passed as arguments)
if [ $# -eq 0 ]; then
    echo "Error: No command provided" >> "$LOG_FILE"
    exit 1
fi

# Execute the command and capture output
exec "$@" 2>&1 | tee -a "$LOG_FILE"
