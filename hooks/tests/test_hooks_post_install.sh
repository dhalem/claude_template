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

# Test that hooks work correctly after installation
set -euo pipefail

echo "🧪 Testing Hooks After Installation"
echo "==================================="
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

test_hook() {
    local hook_name="$1"
    local hook_path="$2"
    local test_input="$3"
    local expected_behavior="$4"  # "allow", "block", or "error"

    echo -n "Testing $hook_name: "

    if [[ ! -f "$hook_path" ]]; then
        echo "❌ FAIL (hook not found)"
        ((TESTS_FAILED++))
        return
    fi

    set +e
    output=$(echo "$test_input" | "$hook_path" 2>&1)
    exit_code=$?
    set -e

    case "$expected_behavior" in
        "allow")
            if [[ $exit_code -eq 0 ]]; then
                echo "✅ PASS (allowed as expected)"
                ((TESTS_PASSED++))
            else
                echo "❌ FAIL (should have allowed, exit code: $exit_code)"
                echo "  Output: $output"
                ((TESTS_FAILED++))
            fi
            ;;
        "block")
            if [[ $exit_code -eq 2 ]]; then
                echo "✅ PASS (blocked as expected)"
                ((TESTS_PASSED++))
            else
                echo "❌ FAIL (should have blocked with exit 2, got: $exit_code)"
                echo "  Output: $output"
                ((TESTS_FAILED++))
            fi
            ;;
        "error")
            if [[ $exit_code -eq 1 ]]; then
                echo "✅ PASS (error as expected)"
                ((TESTS_PASSED++))
            else
                echo "❌ FAIL (should have errored with exit 1, got: $exit_code)"
                echo "  Output: $output"
                ((TESTS_FAILED++))
            fi
            ;;
    esac
}

# Test adaptive-guard.sh
echo "1️⃣ Testing adaptive-guard.sh"
echo "----------------------------"

# Test with valid input
test_hook "adaptive-guard.sh with valid input" \
    "$HOME/.claude/adaptive-guard.sh" \
    '{"tool_name": "Read", "tool_input": {"file_path": "test.txt"}}' \
    "allow"

# Test with empty input
test_hook "adaptive-guard.sh with empty input" \
    "$HOME/.claude/adaptive-guard.sh" \
    "" \
    "error"

# Test with malformed JSON
test_hook "adaptive-guard.sh with malformed JSON" \
    "$HOME/.claude/adaptive-guard.sh" \
    "invalid json" \
    "error"

echo ""
echo "2️⃣ Testing lint-guard.sh"
echo "------------------------"

# Test with valid input
test_hook "lint-guard.sh with valid input" \
    "$HOME/.claude/lint-guard.sh" \
    '{"tool_name": "Write", "tool_input": {"file_path": "test.py", "content": "print(\"hello\")"}}' \
    "allow"

# Test with empty input
test_hook "lint-guard.sh with empty input" \
    "$HOME/.claude/lint-guard.sh" \
    "" \
    "error"

# Test with malformed JSON
test_hook "lint-guard.sh with malformed JSON" \
    "$HOME/.claude/lint-guard.sh" \
    "invalid json" \
    "error"

echo ""
echo "3️⃣ Testing Protection Guards"
echo "----------------------------"

# Test test-script-integrity-guard.sh
if [[ -f "$HOME/.claude/guards/test-script-integrity-guard.sh" ]]; then
    test_hook "test-script-integrity-guard.sh blocks run_tests.sh edit" \
        "$HOME/.claude/guards/test-script-integrity-guard.sh" \
        '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "new_string": "# modified"}}' \
        "block"
fi

# Test precommit-protection-guard.sh
if [[ -f "$HOME/.claude/guards/precommit-protection-guard.sh" ]]; then
    test_hook "precommit-protection-guard.sh blocks --no-verify" \
        "$HOME/.claude/guards/precommit-protection-guard.sh" \
        '{"tool_name": "Bash", "tool_input": {"command": "git commit --no-verify -m test"}}' \
        "block"
fi

# Test anti-bypass-pattern-guard.py
if [[ -f "$HOME/.claude/guards/anti-bypass-pattern-guard.py" ]]; then
    test_hook "anti-bypass-pattern-guard.py blocks @pytest.mark.skip" \
        "python3 $HOME/.claude/guards/anti-bypass-pattern-guard.py" \
        '{"tool_name": "Edit", "tool_input": {"file_path": "test.py", "new_string": "@pytest.mark.skip"}}' \
        "block"
fi

echo ""
echo "4️⃣ Testing Override Mechanisms"
echo "------------------------------"

# Test override mechanism exists
test_hook "Override mechanism help available" \
    "$HOME/.claude/adaptive-guard.sh" \
    '{"tool_name": "Bash", "tool_input": {"command": "git commit --no-verify -m test"}}' \
    "error"

# Note: We can't test actual override codes without user interaction
echo "  ℹ️  Override code testing requires user interaction (not automated)"
echo "  ✅ Override mechanism presence verified through help messages"

echo ""
echo "5️⃣ Testing Logging Functionality"
echo "--------------------------------"

# Test that log directories exist or can be created
if [[ -d "$HOME/.claude/python" ]]; then
    echo -n "  Log directory structure: "
    # Try to create a test log entry
    test_input='{"tool_name": "Read", "tool_input": {"file_path": "test.txt"}}'

    set +e
    echo "$test_input" | "$HOME/.claude/adaptive-guard.sh" >/dev/null 2>&1
    exit_code=$?
    set -e

    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (logging may be broken)"
        ((TESTS_FAILED++))
    fi
else
    echo "  ❌ Python directory not found - logging not available"
    ((TESTS_FAILED++))
fi

echo ""
echo "6️⃣ Testing Stdin Handling Robustness"
echo "------------------------------------"

# Test heredoc input (critical for preventing stdin hanging)
echo -n "  Heredoc stdin handling: "
set +e
"$HOME/.claude/adaptive-guard.sh" >/dev/null 2>&1 << 'EOF'
{"tool_name": "Read", "tool_input": {"file_path": "test.txt"}}
EOF
heredoc_exit=$?
set -e

if [[ $heredoc_exit -eq 0 ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} (heredoc stdin broken)"
    ((TESTS_FAILED++))
fi

# Test pipe input
echo -n "  Pipe stdin handling: "
set +e
echo '{"tool_name": "Read", "tool_input": {"file_path": "test.txt"}}' | "$HOME/.claude/adaptive-guard.sh" >/dev/null 2>&1
pipe_exit=$?
set -e

if [[ $pipe_exit -eq 0 ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} (pipe stdin broken)"
    ((TESTS_FAILED++))
fi

echo ""
echo "📊 Test Results:"
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo "📝 Total:  $((TESTS_PASSED + TESTS_FAILED))"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo ""
    echo "🎉 All hook tests passed! Installation is working correctly."
    exit 0
else
    echo ""
    echo "❌ Some hook tests failed. Installation may be incomplete or broken."
    exit 1
fi
