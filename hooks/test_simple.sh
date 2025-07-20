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

# Simple test for test-script-integrity-guard.sh

set -euo pipefail

GUARD_SCRIPT="/home/dhalem/github/claude_template/hooks/test-script-integrity-guard.sh"
TESTS_PASSED=0
TESTS_FAILED=0

test_result() {
    local test_name="$1"
    local expected_exit="$2"
    local actual_exit="$3"

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo "✅ PASS: $test_name (exit code $actual_exit)"
        ((TESTS_PASSED++))
    else
        echo "❌ FAIL: $test_name (expected $expected_exit, got $actual_exit)"
        ((TESTS_FAILED++))
    fi
}

echo "🧪 Test Script Integrity Guard - Simple Test Suite"
echo "=================================================="
echo ""

# Test 1: Block run_tests.sh modification
echo "Test 1: Block run_tests.sh modification"
set +e
echo '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1
exit_code=$?
set -e
test_result "Block run_tests.sh modification" 2 $exit_code

# Test 2: Block .pre-commit-config.yaml modification
echo "Test 2: Block .pre-commit-config.yaml modification"
set +e
echo '{"tool_name": "Edit", "tool_input": {"file_path": ".pre-commit-config.yaml"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1
exit_code=$?
set -e
test_result "Block .pre-commit-config.yaml modification" 2 $exit_code

# Test 3: Block test file modification
echo "Test 3: Block test file modification"
set +e
echo '{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_example.py"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1
exit_code=$?
set -e
test_result "Block test file modification" 2 $exit_code

# Test 4: Allow regular file modification
echo "Test 4: Allow regular file modification"
set +e
echo '{"tool_name": "Edit", "tool_input": {"file_path": "src/regular_file.py"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1
exit_code=$?
set -e
test_result "Allow regular file modification" 0 $exit_code

# Test 5: Handle malformed JSON
echo "Test 5: Handle malformed JSON"
set +e
echo 'invalid json' | "$GUARD_SCRIPT" >/dev/null 2>&1
exit_code=$?
set -e
test_result "Handle malformed JSON" 1 $exit_code

# Test 6: Test override mechanism
echo "Test 6: Test override mechanism works"
set +e
export HOOK_OVERRIDE_CODE="TEST123"
echo '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh"}}' | "$GUARD_SCRIPT" >/dev/null 2>&1
exit_code=$?
unset HOOK_OVERRIDE_CODE
set -e
test_result "Override mechanism allows modification" 0 $exit_code

echo ""
echo "📊 Final Results:"
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo "📝 Total:  $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! Guard implementation is complete."
    exit 0
else
    echo ""
    echo "🚨 Some tests failed."
    exit 1
fi
