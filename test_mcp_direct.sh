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

echo "Testing MCP servers directly..."
echo "Current directory: $(pwd)"
echo ""

# Test if servers can be called directly
echo "=== Testing code-review server ==="
claude --debug --dangerously-skip-permissions -p 'Use the code-review MCP tool to review the file mcp_minimal_test.py' 2>&1 | grep -E "mcp|MCP|code-review|Tool|error|Error" | head -20

echo ""
echo "=== Testing code-search server ==="
claude --debug --dangerously-skip-permissions -p 'Use the code-search MCP tool to search for "def main" in this directory' 2>&1 | grep -E "mcp|MCP|code-search|Tool|error|Error" | head -20
