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

# Test for Exit Code Fix - Guards must return exit code 2 for blocking

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Find project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_exit="$3"

    echo -n "  $test_name: "

    set +e
    eval "$command" >/dev/null 2>&1
    local actual_exit=$?
    set -e

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo -e "${GREEN}✅ PASS${NC} (exit $actual_exit)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (expected exit $expected_exit, got $actual_exit)"
        ((TESTS_FAILED++))
    fi
}

echo "🧪 Exit Code Fix Tests"
echo "====================="
echo ""

echo "1️⃣ Testing Python main.py exit codes directly"
echo "---------------------------------------------"

# Test blocking command with Python main.py directly
run_test "Python main.py blocks with exit 2" \
    "echo '{\"tool_name\": \"Bash\", \"tool_input\": {\"command\": \"git commit --no-verify -m test\"}}' | $PROJECT_ROOT/venv/bin/python3 hooks/python/main.py adaptive" \
    2

# Test allowing command with Python main.py directly
run_test "Python main.py allows with exit 0" \
    "echo '{\"tool_name\": \"Read\", \"tool_input\": {\"file_path\": \"test.txt\"}}' | $PROJECT_ROOT/venv/bin/python3 hooks/python/main.py adaptive" \
    0

echo ""
echo "2️⃣ Testing protection guards"
echo "---------------------------"

# Test local hook scripts (development)
run_test "Local precommit guard blocks with exit 2" \
    "echo '{\"tool_name\": \"Bash\", \"tool_input\": {\"command\": \"git commit --no-verify -m test\"}}' | hooks/precommit-protection-guard.sh" \
    2

run_test "Local test script guard blocks with exit 2" \
    "echo '{\"tool_name\": \"Edit\", \"tool_input\": {\"file_path\": \"run_tests.sh\", \"new_string\": \"# modified\"}}' | hooks/test-script-integrity-guard.sh" \
    2

run_test "Local anti-bypass guard blocks with exit 2" \
    "echo '{\"tool_name\": \"Edit\", \"tool_input\": {\"file_path\": \"test.py\", \"new_string\": \"@pytest.mark.skip\"}}' | $PROJECT_ROOT/venv/bin/python3 hooks/anti-bypass-pattern-guard.py" \
    2

echo ""
echo "3️⃣ Testing error cases return exit 1"
echo "-----------------------------------"

# Test malformed JSON returns exit 1 (error, not block)
run_test "Malformed JSON returns exit 1" \
    "echo 'invalid json' | $PROJECT_ROOT/venv/bin/python3 hooks/python/main.py adaptive" \
    1

# Test empty input returns exit 1 (error, not block)
run_test "Empty input returns exit 1" \
    "echo '' | $PROJECT_ROOT/venv/bin/python3 hooks/python/main.py adaptive" \
    1

echo ""
echo "4️⃣ Testing Critical Exit Code Requirements"
echo "-----------------------------------------"

echo "  🔍 Verifying main.py contains 'sys.exit(2)' for blocking..."
if grep -q "sys\.exit(2)" hooks/python/main.py; then
    echo -e "  ${GREEN}✅ PASS${NC} (main.py uses sys.exit(2) for blocking)"
    ((TESTS_PASSED++))
else
    echo -e "  ${RED}❌ FAIL${NC} (main.py missing sys.exit(2))"
    ((TESTS_FAILED++))
fi

echo "  🔍 Verifying base_guard.py sets exit_code = 2..."
if grep -q "exit_code = 2" hooks/python/base_guard.py; then
    echo -e "  ${GREEN}✅ PASS${NC} (base_guard.py sets exit_code = 2)"
    ((TESTS_PASSED++))
else
    echo -e "  ${RED}❌ FAIL${NC} (base_guard.py missing exit_code = 2)"
    ((TESTS_FAILED++))
fi

echo ""
echo "📊 Exit Code Fix Test Results:"
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo "📝 Total:  $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All exit code tests passed!${NC}"
    echo "Guards are properly returning exit code 2 for blocking."
    exit 0
else
    echo ""
    echo -e "${RED}❌ Exit code tests failed.${NC}"
    echo "Guards are not returning correct exit codes."
    exit 1
fi
