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

# Final test for test-script-integrity-guard.sh

set -euo pipefail

GUARD_SCRIPT="/home/dhalem/github/claude_template/hooks/test-script-integrity-guard.sh"
PASSED=0
FAILED=0

test_guard() {
    local test_name="$1"
    local input="$2"
    local expected_exit="$3"

    echo "Testing: $test_name"

    # Run the guard with timeout to prevent hanging
    local actual_exit=0
    timeout 10 bash -c "echo '$input' | '$GUARD_SCRIPT' >/dev/null 2>&1" || actual_exit=$?

    if [ $actual_exit -eq $expected_exit ]; then
        echo "✅ PASS: $test_name (exit code $actual_exit)"
        ((PASSED++))
    else
        echo "❌ FAIL: $test_name (expected $expected_exit, got $actual_exit)"
        ((FAILED++))
    fi
    echo ""
}

echo "🧪 Final Guard Test Suite"
echo "========================"
echo ""

# Test cases
test_guard "Block run_tests.sh" '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh"}}' 2
test_guard "Block .pre-commit-config.yaml" '{"tool_name": "Edit", "tool_input": {"file_path": ".pre-commit-config.yaml"}}' 2
test_guard "Block test file" '{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_example.py"}}' 2
test_guard "Allow regular file" '{"tool_name": "Edit", "tool_input": {"file_path": "src/regular.py"}}' 0
test_guard "Handle malformed JSON" 'invalid json' 1
test_guard "Ignore non-Edit tools" '{"tool_name": "Bash", "tool_input": {"command": "echo test"}}' 0

echo "📊 Results:"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! Guard is working correctly."
    exit 0
else
    echo ""
    echo "🚨 Some tests failed."
    exit 1
fi
