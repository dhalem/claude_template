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

# Debug test for test-script-integrity-guard.sh

set -euo pipefail

GUARD_SCRIPT="/home/dhalem/github/claude_template/hooks/test-script-integrity-guard.sh"

echo "🔍 Debug Test - Finding Issue"
echo "============================="

# Test each case in complete isolation
echo ""
echo "Test 1: run_tests.sh"
echo '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh"}}' | timeout 5 "$GUARD_SCRIPT" >/dev/null 2>&1
echo "Exit code: $?"

echo ""
echo "Test 2: .pre-commit-config.yaml"
echo '{"tool_name": "Edit", "tool_input": {"file_path": ".pre-commit-config.yaml"}}' | timeout 5 "$GUARD_SCRIPT" >/dev/null 2>&1
echo "Exit code: $?"

echo ""
echo "Test 3: test file"
echo '{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_example.py"}}' | timeout 5 "$GUARD_SCRIPT" >/dev/null 2>&1
echo "Exit code: $?"

echo ""
echo "Test 4: regular file"
echo '{"tool_name": "Edit", "tool_input": {"file_path": "src/regular_file.py"}}' | timeout 5 "$GUARD_SCRIPT" >/dev/null 2>&1
echo "Exit code: $?"

echo ""
echo "Test 5: malformed JSON"
echo 'invalid json' | timeout 5 "$GUARD_SCRIPT" >/dev/null 2>&1
echo "Exit code: $?"

echo ""
echo "✅ All individual tests completed successfully"
