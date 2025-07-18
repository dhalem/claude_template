#!/bin/bash
# Script to check MCP server logs

LOG_DIR="$HOME/.claude/mcp/code-search/logs"

echo "=== MCP Server Logs ==="
echo "Log directory: $LOG_DIR"
echo

# Find the most recent log file
LATEST_LOG=$(ls -t "$LOG_DIR"/mcp_server_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "No log files found!"
    exit 1
fi

echo "Latest log file: $(basename "$LATEST_LOG")"
echo "File size: $(ls -lh "$LATEST_LOG" | awk '{print $5}')"
echo "Last modified: $(ls -l "$LATEST_LOG" | awk '{print $6, $7, $8}')"
echo
echo "=== Last 100 lines of log ==="
tail -100 "$LATEST_LOG"

# Also check if there are any stderr logs
if [ -f "$LOG_DIR/stderr.log" ]; then
    echo
    echo "=== stderr.log ==="
    tail -50 "$LOG_DIR/stderr.log"
fi
