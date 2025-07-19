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

echo "🔍 Checking MCP Debug Logs"
echo "=========================="

LOG_DIR="$HOME/.claude/mcp/code-review/logs"

# Find the most recent log file (any log type)
DEBUG_LOG=$(find "$LOG_DIR" -name "*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | awk '{print $2}')

# Also show simple logs if they exist
echo "🔍 Checking for simple_*.log files..."
find "$LOG_DIR" -name "simple_*.log" -type f -mmin -10 -ls 2>/dev/null | tail -5

# Show all recent logs
echo "📂 Recent log files:"
find "$LOG_DIR" -name "*.log" -type f -mmin -60 -ls 2>/dev/null | tail -10
echo ""

if [ -z "$DEBUG_LOG" ]; then
    echo "❌ No debug logs found!"
    echo "Please run: claude --debug -p 'hello world'"
    exit 1
fi

echo "📋 Found debug log: $DEBUG_LOG"
echo "📊 Log size: $(wc -l < "$DEBUG_LOG") lines"
echo ""
echo "🔍 Last 50 lines of log:"
echo "========================"
tail -50 "$DEBUG_LOG"

echo ""
echo "💡 To see full log: cat $DEBUG_LOG"
echo "💡 To follow log: tail -f $DEBUG_LOG"
