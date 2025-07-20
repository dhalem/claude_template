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

# Pre-Install Hook Tests - Fixed Version

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Find directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$HOOKS_DIR")"
PYTHON_DIR="$HOOKS_DIR/python"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Find Python
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/venv/bin/python3" ]; then
    PYTHON_CMD="$PROJECT_ROOT/venv/bin/python3"
fi

# Simpler test function that doesn't hang
run_test_simple() {
    local test_name="$1"
    local expected_exit="$2"
    shift 2

    echo -n "  $test_name: "

    set +e
    "$@" >/dev/null 2>&1
    local actual_exit=$?
    set -e

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (expected exit $expected_exit, got $actual_exit)"
        ((TESTS_FAILED++))
    fi
}

# Test function for commands with input
run_test_with_input() {
    local test_name="$1"
    local input="$2"
    local expected_exit="$3"
    shift 3

    echo -n "  $test_name: "

    set +e
    echo "$input" | "$@" >/dev/null 2>&1
    local actual_exit=$?
    set -e

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (expected exit $expected_exit, got $actual_exit)"
        ((TESTS_FAILED++))
    fi
}

echo "🧪 Pre-Install Hook Tests (Fixed)"
echo "=================================="
echo ""

echo "1️⃣ Testing Python main.py stdin handling"
echo "-----------------------------------------"

if [ -f "$PYTHON_DIR/main.py" ]; then
    # Test with valid JSON input
    run_test_with_input "Valid JSON input" \
        '{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}' \
        0 \
        "$PYTHON_CMD" "$PYTHON_DIR/main.py" "adaptive"

    # Test with empty input using input redirection instead of echo
    run_test_simple "Empty stdin" \
        1 \
        bash -c "$PYTHON_CMD $PYTHON_DIR/main.py adaptive < /dev/null"

    # Test with malformed JSON
    run_test_with_input "Malformed JSON" \
        'not json' \
        1 \
        "$PYTHON_CMD" "$PYTHON_DIR/main.py" "adaptive"

    # Test with JSON from command line
    run_test_simple "JSON as argument" \
        0 \
        "$PYTHON_CMD" "$PYTHON_DIR/main.py" "adaptive" '{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}'
else
    echo -e "${RED}  Python main.py not found${NC}"
    ((TESTS_FAILED++))
fi

echo ""

echo "2️⃣ Testing shell wrapper scripts"
echo "---------------------------------"

# Test adaptive-guard.sh (be careful with stdin handling)
if [ -f "$HOOKS_DIR/adaptive-guard.sh" ]; then
    echo "  Testing adaptive-guard.sh:"

    # Test valid input
    run_test_with_input "Valid input" \
        '{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}' \
        0 \
        "$HOOKS_DIR/adaptive-guard.sh"

    # Test empty input with file redirection to avoid hanging
    echo -n "  Empty input: "
    set +e
    "$HOOKS_DIR/adaptive-guard.sh" < /dev/null >/dev/null 2>&1
    exit_code=$?
    set -e

    if [ $exit_code -eq 1 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (expected exit 1, got $exit_code)"
        ((TESTS_FAILED++))
    fi

    # Test git no-verify blocking (should return exit 2 for blocking now)
    run_test_with_input "Git no-verify block" \
        '{"tool_name":"Bash","tool_input":{"command":"git commit --no-verify -m test"}}' \
        2 \
        "$HOOKS_DIR/adaptive-guard.sh"
else
    echo -e "${RED}  adaptive-guard.sh not found${NC}"
    ((TESTS_FAILED++))
fi

# Test lint-guard.sh
if [ -f "$HOOKS_DIR/lint-guard.sh" ]; then
    echo "  Testing lint-guard.sh:"

    run_test_with_input "Valid Python file" \
        '{"tool_name":"Write","tool_input":{"file_path":"test.py","content":"print(\"hello\")"}}' \
        0 \
        "$HOOKS_DIR/lint-guard.sh"

    # Test empty input with file redirection
    echo -n "  Empty input: "
    set +e
    "$HOOKS_DIR/lint-guard.sh" < /dev/null >/dev/null 2>&1
    exit_code=$?
    set -e

    if [ $exit_code -eq 1 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (expected exit 1, got $exit_code)"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}  lint-guard.sh not found${NC}"
    ((TESTS_FAILED++))
fi

echo ""

echo "3️⃣ Testing protection guards"
echo "-----------------------------"

# Test protection guards with proper exit codes
if [ -f "$HOOKS_DIR/test-script-integrity-guard.sh" ]; then
    echo "  Testing test-script-integrity-guard.sh:"

    run_test_with_input "Block run_tests.sh edit" \
        '{"tool_name":"Edit","tool_input":{"file_path":"run_tests.sh","new_string":"# modified"}}' \
        2 \
        "$HOOKS_DIR/test-script-integrity-guard.sh"

    run_test_with_input "Allow normal file edit" \
        '{"tool_name":"Edit","tool_input":{"file_path":"normal.py","new_string":"# code"}}' \
        0 \
        "$HOOKS_DIR/test-script-integrity-guard.sh"
else
    echo -e "${RED}  test-script-integrity-guard.sh not found${NC}"
    ((TESTS_FAILED++))
fi

if [ -f "$HOOKS_DIR/precommit-protection-guard.sh" ]; then
    echo "  Testing precommit-protection-guard.sh:"

    run_test_with_input "Block --no-verify" \
        '{"tool_name":"Bash","tool_input":{"command":"git commit --no-verify -m test"}}' \
        2 \
        "$HOOKS_DIR/precommit-protection-guard.sh"

    run_test_with_input "Allow regular commit" \
        '{"tool_name":"Bash","tool_input":{"command":"git commit -m test"}}' \
        0 \
        "$HOOKS_DIR/precommit-protection-guard.sh"
else
    echo -e "${RED}  precommit-protection-guard.sh not found${NC}"
    ((TESTS_FAILED++))
fi

if [ -f "$HOOKS_DIR/anti-bypass-pattern-guard.py" ]; then
    echo "  Testing anti-bypass-pattern-guard.py:"

    run_test_with_input "Block @pytest.mark.skip" \
        '{"tool_name":"Edit","tool_input":{"file_path":"test.py","new_string":"@pytest.mark.skip"}}' \
        2 \
        "$PYTHON_CMD" "$HOOKS_DIR/anti-bypass-pattern-guard.py"

    run_test_with_input "Allow normal code" \
        '{"tool_name":"Edit","tool_input":{"file_path":"test.py","new_string":"def test(): pass"}}' \
        0 \
        "$PYTHON_CMD" "$HOOKS_DIR/anti-bypass-pattern-guard.py"
else
    echo -e "${RED}  anti-bypass-pattern-guard.py not found${NC}"
    ((TESTS_FAILED++))
fi

echo ""

echo "📊 Pre-Install Test Results:"
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo "📝 Total:  $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All pre-install tests passed!${NC}"
    echo "Hooks are ready for installation."
    exit 0
else
    echo ""
    echo -e "${RED}❌ Pre-install tests failed.${NC}"
    echo "Fix issues before installing hooks."
    exit 1
fi
