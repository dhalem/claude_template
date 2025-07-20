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

# Installation Verification Tests
# NON-DESTRUCTIVE - Only tests existing installation

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Find directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$HOOKS_DIR")"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "  $test_name: "

    set +e
    eval "$test_command" >/dev/null 2>&1
    local exit_code=$?
    set -e

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((TESTS_FAILED++))
    fi
}

echo "🔧 Installation Verification Tests (Non-Destructive)"
echo "=================================================="
echo ""

# Check if hooks are installed
if [ ! -d "$HOME/.claude" ]; then
    echo -e "${RED}❌ ERROR: .claude directory does not exist${NC}"
    echo "Please run ./hooks/install-hooks-python-only.sh first"
    exit 1
fi

echo "✅ Found existing Claude installation"
echo ""

echo "1️⃣ Testing Directory Structure"
echo "------------------------------"

run_test "Claude config directory exists" \
    "test -d '$HOME/.claude'"

run_test "Python directory exists" \
    "test -d '$HOME/.claude/python'"

run_test "Python guards directory exists" \
    "test -d '$HOME/.claude/python/guards'"

run_test "Settings file exists" \
    "test -f '$HOME/.claude/settings.json'"

echo ""
echo "2️⃣ Testing Wrapper Scripts"
echo "-------------------------"

run_test "adaptive-guard.sh exists" \
    "test -f '$HOME/.claude/adaptive-guard.sh'"

run_test "lint-guard.sh exists" \
    "test -f '$HOME/.claude/lint-guard.sh'"

run_test "adaptive-guard.sh is executable" \
    "test -x '$HOME/.claude/adaptive-guard.sh'"

run_test "lint-guard.sh is executable" \
    "test -x '$HOME/.claude/lint-guard.sh'"

echo ""
echo "3️⃣ Testing Protection Guards"
echo "---------------------------"

run_test "Main Python guard module exists" \
    "test -f '$HOME/.claude/python/main.py'"

run_test "Base guard module exists" \
    "test -f '$HOME/.claude/python/base_guard.py'"

run_test "Registry module exists" \
    "test -f '$HOME/.claude/python/registry.py'"

run_test "Guards init exists" \
    "test -f '$HOME/.claude/python/guards/__init__.py'"

echo ""
echo "4️⃣ Testing Configuration"
echo "-----------------------"

run_test "Settings JSON is valid" \
    "python3 -m json.tool '$HOME/.claude/settings.json' >/dev/null"

run_test "Python modules importable" \
    "cd '$HOME/.claude/python' && '$PROJECT_ROOT/venv/bin/python3' -c 'import guards, base_guard, registry'"

echo ""
echo "📊 Results:"
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo "📝 Total:  $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All installation verification tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Installation verification tests failed.${NC}"
    exit 1
fi
