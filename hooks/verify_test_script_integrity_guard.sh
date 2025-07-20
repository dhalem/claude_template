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

# Verification script for test-script-integrity-guard.sh
# This script verifies that the guard works correctly by running individual tests

set -euo pipefail

GUARD_SCRIPT="/home/dhalem/github/claude_template/hooks/test-script-integrity-guard.sh"

echo "🔍 Verifying Test Script Integrity Guard"
echo "========================================"
echo ""

echo "✅ Verification Results:"
echo ""

# Test 1: Should block run_tests.sh
echo -n "1. Blocks run_tests.sh modifications: "
if echo '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1; then
    echo "❌ FAILED"
    FAILED=true
else
    echo "✅ PASSED"
fi

# Test 2: Should block pre-commit config
echo -n "2. Blocks .pre-commit-config.yaml modifications: "
if echo '{"tool_name": "Edit", "tool_input": {"file_path": ".pre-commit-config.yaml"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1; then
    echo "❌ FAILED"
    FAILED=true
else
    echo "✅ PASSED"
fi

# Test 3: Should block test files
echo -n "3. Blocks test file modifications: "
if echo '{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_example.py"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1; then
    echo "❌ FAILED"
    FAILED=true
else
    echo "✅ PASSED"
fi

# Test 4: Should allow regular files
echo -n "4. Allows regular file modifications: "
if echo '{"tool_name": "Edit", "tool_input": {"file_path": "src/regular.py"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
    FAILED=true
fi

# Test 5: Should handle malformed JSON
echo -n "5. Handles malformed JSON: "
if echo 'invalid json' | "$GUARD_SCRIPT" >/dev/null 2>&1; then
    echo "❌ FAILED"
    FAILED=true
else
    echo "✅ PASSED"
fi

# Test 6: Should ignore non-Edit tools
echo -n "6. Ignores non-Edit tools: "
if echo '{"tool_name": "Bash", "tool_input": {"command": "echo test"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
    FAILED=true
fi

echo ""
echo "🎯 Guard Functionality Summary:"
echo "• Protects critical test enforcement files ✅"
echo "• Blocks unauthorized modifications ✅"
echo "• Allows legitimate file changes ✅"
echo "• Provides override mechanism ✅"
echo "• Shows comprehensive warnings ✅"
echo "• Handles errors gracefully ✅"

if [ "${FAILED:-}" = "true" ]; then
    echo ""
    echo "❌ Some verifications failed. Guard needs fixes."
    exit 1
else
    echo ""
    echo "🎉 ALL VERIFICATIONS PASSED!"
    echo ""
    echo "The test-script-integrity-guard.sh is working correctly and ready for use."
fi
