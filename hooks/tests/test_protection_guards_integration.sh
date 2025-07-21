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

# Integration test for all protection guards working together
set -euo pipefail

echo "🧪 Test Protection Guards Integration Test"
echo "=========================================="
echo ""
echo "Testing all three guards work together to protect test integrity..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$HOOKS_DIR")"

# Find Python interpreter
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/venv/bin/python3" ]; then
    PYTHON_CMD="$PROJECT_ROOT/venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="venv/bin/python3"
fi

# Guard paths
TEST_SCRIPT_GUARD="$HOOKS_DIR/test-script-integrity-guard.sh"
PRECOMMIT_GUARD="$HOOKS_DIR/precommit-protection-guard.sh"
ANTIBYPASS_GUARD="$HOOKS_DIR/anti-bypass-pattern-guard.py"

TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local guard_script="$2"
    local test_input="$3"
    local expected_exit="$4"

    echo -n "$test_name: "

    set +e
    if [[ "$guard_script" == *"$PYTHON_CMD"* ]]; then
        # For Python scripts, run directly
        echo "$test_input" | $guard_script >/dev/null 2>&1
        local actual_exit=$?
    else
        # For shell scripts
        echo "$test_input" | "$guard_script" >/dev/null 2>&1
        local actual_exit=$?
    fi
    set -e

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo "✅ PASS"
        ((TESTS_PASSED++))
    else
        echo "❌ FAIL (expected exit $expected_exit, got $actual_exit)"
        ((TESTS_FAILED++))
    fi
}

echo "1️⃣ Test Script Integrity Guard Tests:"
echo "-------------------------------------"

# Test 1: Block run_tests.sh modification
run_test "Block run_tests.sh edit" "$TEST_SCRIPT_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "new_string": "# Fast mode"}}' 2

# Test 2: Block pre-commit config modification
run_test "Block .pre-commit-config.yaml edit" "$TEST_SCRIPT_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": ".pre-commit-config.yaml", "new_string": "stages: [manual]"}}' 2

# Test 3: Allow normal file edit
run_test "Allow normal file edit" "$TEST_SCRIPT_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "app.py", "new_string": "print(hello)"}}' 0

echo ""
echo "2️⃣ Pre-commit Protection Guard Tests:"
echo "-------------------------------------"

# Test 4: Block git commit --no-verify
run_test "Block git commit --no-verify" "$PRECOMMIT_GUARD" \
    '{"tool_name": "Bash", "tool_input": {"command": "git commit --no-verify -m test"}}' 2

# Test 5: Block pre-commit uninstall
run_test "Block pre-commit uninstall" "$PRECOMMIT_GUARD" \
    '{"tool_name": "Bash", "tool_input": {"command": "pre-commit uninstall"}}' 2

# Test 6: Allow regular git commit
run_test "Allow regular git commit" "$PRECOMMIT_GUARD" \
    '{"tool_name": "Bash", "tool_input": {"command": "git commit -m \"feat: add feature\""}}' 0

echo ""
echo "3️⃣ Anti-bypass Pattern Guard Tests:"
echo "------------------------------------"

# Test 7: Block @pytest.mark.skip
run_test "Block @pytest.mark.skip" "$PYTHON_CMD $ANTIBYPASS_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "test.py", "new_string": "@pytest.mark.skip"}}' 2

# Test 8: Block fast mode pattern
run_test "Block fast mode pattern" "$PYTHON_CMD $ANTIBYPASS_GUARD" \
    '{"tool_name": "Write", "tool_input": {"file_path": "run.sh", "content": "if [ \"$1\" = \"--fast\" ]; then"}}' 2

# Test 9: Allow normal Python code
run_test "Allow normal Python code" "$PYTHON_CMD $ANTIBYPASS_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "app.py", "new_string": "def hello(): pass"}}' 0

echo ""
echo "4️⃣ Cross-Guard Integration Tests:"
echo "---------------------------------"

# Test 10: Attempt to add skip marker to test file (should be blocked by anti-bypass)
run_test "Block skip marker in test file" "$PYTHON_CMD $ANTIBYPASS_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_example.py", "new_string": "@pytest.mark.skip\ndef test_function(): pass"}}' 2

# Test 11: Attempt to modify run_tests.sh to add fast mode (should be blocked by both guards)
run_test "Block fast mode in run_tests.sh" "$TEST_SCRIPT_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "new_string": "if [ \"$1\" = \"--fast\" ]; then"}}' 2

# Test 12: Attempt to bypass with command (should be blocked by precommit guard)
run_test "Block SKIP environment variable" "$PRECOMMIT_GUARD" \
    '{"tool_name": "Bash", "tool_input": {"command": "SKIP=tests git commit -m test"}}' 2

echo ""
echo "5️⃣ Override Mechanism Tests:"
echo "----------------------------"

# Test 13: Test override works for test-script-integrity-guard
HOOK_OVERRIDE_CODE="TEST123" run_test "Override test script guard" "$TEST_SCRIPT_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "new_string": "# Authorized change"}}' 0

# Test 14: Test override works for precommit-protection-guard
HOOK_OVERRIDE_CODE="TEST123" run_test "Override precommit guard" "$PRECOMMIT_GUARD" \
    '{"tool_name": "Bash", "tool_input": {"command": "git commit --no-verify -m authorized"}}' 0

# Test 15: Test override works for anti-bypass-pattern-guard
HOOK_OVERRIDE_CODE="TEST123" run_test "Override anti-bypass guard" "$PYTHON_CMD $ANTIBYPASS_GUARD" \
    '{"tool_name": "Edit", "tool_input": {"file_path": "test.py", "new_string": "@pytest.mark.skip"}}' 0

echo ""
echo "📊 Integration Test Results:"
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo "📝 Total:  $((TESTS_PASSED + TESTS_FAILED))"

echo ""
echo "🛡️ Protection System Summary:"
echo "• Test Script Integrity Guard: Protects run_tests.sh and .pre-commit-config.yaml ✅"
echo "• Pre-commit Protection Guard: Prevents bypassing pre-commit hooks ✅"
echo "• Anti-bypass Pattern Guard: Blocks test skip patterns and fast modes ✅"
echo "• All guards support override mechanism for authorized changes ✅"
echo "• Guards work independently but provide comprehensive protection ✅"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo "🎉 ALL INTEGRATION TESTS PASSED!"
    echo ""
    echo "The test protection system is fully operational and ready to prevent"
    echo "any attempts to bypass or disable the mandatory full test suite."
    exit 0
else
    echo ""
    echo "❌ Some integration tests failed."
    exit 1
fi
