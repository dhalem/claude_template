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

# Working test suite for test-script-integrity-guard.sh
# This version runs one test at a time to avoid hanging issues

set -euo pipefail

GUARD_SCRIPT="/home/dhalem/github/claude_template/hooks/test-script-integrity-guard.sh"

echo "🧪 Test Script Integrity Guard - Working Test Suite"
echo "=================================================="
echo ""

# Individual test function that runs in isolation
run_single_test() {
    local test_name="$1"
    local input="$2"
    local expected_exit="$3"

    echo "Test: $test_name"

    # Create a temporary script to run this single test
    local temp_script
    temp_script=$(mktemp)
    cat > "$temp_script" << EOF
#!/bin/bash
set -euo pipefail
echo '$input' | '$GUARD_SCRIPT' >/dev/null 2>&1
exit \$?
EOF
    chmod +x "$temp_script"

    # Run the test with timeout
    local actual_exit=0
    timeout 5 "$temp_script" || actual_exit=$?
    rm -f "$temp_script"

    # Handle timeout case (exit code 124)
    if [ $actual_exit -eq 124 ]; then
        echo "❌ FAIL: $test_name (timed out - possible guard issue)"
        return 1
    elif [ $actual_exit -eq $expected_exit ]; then
        echo "✅ PASS: $test_name (exit code $actual_exit)"
        return 0
    else
        echo "❌ FAIL: $test_name (expected $expected_exit, got $actual_exit)"
        return 1
    fi
}

# Run tests
TOTAL=0
PASSED=0

echo "Test 1: Should block run_tests.sh modification"
if run_single_test "Block run_tests.sh" '{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh"}}' 2; then
    ((PASSED++))
fi
((TOTAL++))
echo ""

echo "Test 2: Should block .pre-commit-config.yaml modification"
if run_single_test "Block .pre-commit-config.yaml" '{"tool_name": "Edit", "tool_input": {"file_path": ".pre-commit-config.yaml"}}' 2; then
    ((PASSED++))
fi
((TOTAL++))
echo ""

echo "Test 3: Should block test file modification"
if run_single_test "Block test file" '{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_example.py"}}' 2; then
    ((PASSED++))
fi
((TOTAL++))
echo ""

echo "Test 4: Should allow regular file modification"
if run_single_test "Allow regular file" '{"tool_name": "Edit", "tool_input": {"file_path": "src/regular.py"}}' 0; then
    ((PASSED++))
fi
((TOTAL++))
echo ""

echo "Test 5: Should handle malformed JSON"
if run_single_test "Handle malformed JSON" 'invalid json' 1; then
    ((PASSED++))
fi
((TOTAL++))
echo ""

echo "Test 6: Should ignore non-Edit tools"
if run_single_test "Ignore non-Edit tools" '{"tool_name": "Bash", "tool_input": {"command": "echo test"}}' 0; then
    ((PASSED++))
fi
((TOTAL++))
echo ""

echo "📊 Final Results:"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $((TOTAL - PASSED))"
echo "📝 Total:  $TOTAL"

if [ $PASSED -eq $TOTAL ]; then
    echo ""
    echo "🎉 All tests passed! Guard implementation is complete and working correctly."
    exit 0
else
    echo ""
    echo "🚨 Some tests failed. Guard needs fixes."
    exit 1
fi
