#!/bin/bash

# ============================================================================
# CLAUDE CODE SAFETY HOOKS TESTING SCRIPT
# ============================================================================
#
# This script tests the installed Claude Code safety hooks to ensure they're
# working correctly and protecting against dangerous operations.
#
# WHAT THIS TESTS:
# - Hook installation integrity
# - JSON configuration validity
# - Script syntax and executability
# - Basic hook triggering (safe patterns only)
#
# USAGE:
#   cd hooks
#   ./test-hooks.sh
#
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Helper functions
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${YELLOW}Testing: $test_name${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS: $test_name${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL: $test_name${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    local expected_in_output="$3"

    echo -e "${YELLOW}Testing: $test_name${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    local output
    output=$(eval "$test_command" 2>&1 || true)

    if echo "$output" | grep -q "$expected_in_output"; then
        echo -e "${GREEN}✓ PASS: $test_name${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL: $test_name${NC}"
        echo -e "${RED}Expected to find: $expected_in_output${NC}"
        echo -e "${RED}Actual output: $output${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Claude Code Safety Hooks Testing${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Test 1: Check if Claude directory exists
CLAUDE_DIR="$HOME/.claude"
run_test "Claude config directory exists" "test -d '$CLAUDE_DIR'"

# Test 2: Check if guard script exists
run_test "Guard script exists" "test -f '$CLAUDE_DIR/comprehensive-guard.sh'"

# Test 3: Check if guard script is executable
run_test "Guard script is executable" "test -x '$CLAUDE_DIR/comprehensive-guard.sh'"

# Test 4: Check if settings.json exists
run_test "Settings JSON exists" "test -f '$CLAUDE_DIR/settings.json'"

# Test 5: Validate JSON syntax
run_test "Settings JSON is valid" "jq empty '$CLAUDE_DIR/settings.json'"

# Test 6: Check if jq is available
run_test "jq command available" "command -v jq"

# Test 7: Validate bash script syntax
run_test "Guard script syntax valid" "bash -n '$CLAUDE_DIR/comprehensive-guard.sh'"

# Test 8: Check hook configuration structure
run_test "Hook configuration has required structure" "jq -e '.hooks | length > 0' '$CLAUDE_DIR/settings.json'"

# Test 9: Check if all tool matchers are present
run_test "Bash tool matcher present" "jq -e '.hooks[] | select(.matcher.tool == \"Bash\")' '$CLAUDE_DIR/settings.json'"
run_test "Edit tool matcher present" "jq -e '.hooks[] | select(.matcher.tool == \"Edit\")' '$CLAUDE_DIR/settings.json'"
run_test "MultiEdit tool matcher present" "jq -e '.hooks[] | select(.matcher.tool == \"MultiEdit\")' '$CLAUDE_DIR/settings.json'"
run_test "Write tool matcher present" "jq -e '.hooks[] | select(.matcher.tool == \"Write\")' '$CLAUDE_DIR/settings.json'"

# Test 10: Check documentation section exists
run_test "Documentation section present" "jq -e '._documentation' '$CLAUDE_DIR/settings.json'"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${YELLOW}Functional Hook Testing${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Test hook functionality with safe mock inputs
# Note: These tests simulate hook input without actually triggering Claude Code

# Test 11: Git no-verify detection
TEST_INPUT='{"tool": "Bash", "parameters": {"command": "git commit -m \"test\" --no-verify"}}'
run_test_with_output "Git no-verify guard detection" \
    "echo '$TEST_INPUT' | '$CLAUDE_DIR/comprehensive-guard.sh' || true" \
    "bypass pre-commit hooks"

# Test 12: Docker restart detection
TEST_INPUT='{"tool": "Bash", "parameters": {"command": "docker restart my-container"}}'
run_test_with_output "Docker restart guard detection" \
    "echo '$TEST_INPUT' | '$CLAUDE_DIR/comprehensive-guard.sh' || true" \
    "Docker restart detected"

# Test 13: Directory awareness detection
TEST_INPUT='{"tool": "Bash", "parameters": {"command": "./run-tests.sh"}}'
run_test_with_output "Directory awareness guard detection" \
    "echo '$TEST_INPUT' | '$CLAUDE_DIR/comprehensive-guard.sh' || true" \
    "Location-dependent command detected"

# Test 14: Test enforcement detection
TEST_INPUT='{"tool": "Bash", "parameters": {"command": "echo \"Implementation complete\""}}'
run_test_with_output "Test enforcement guard detection" \
    "echo '$TEST_INPUT' | '$CLAUDE_DIR/comprehensive-guard.sh' || true" \
    "Completion claim detected"

# Test 15: Mock code detection
TEST_INPUT='{"tool": "Edit", "parameters": {"file_path": "/tmp/test.py", "old_string": "", "new_string": "@mock.patch(\"some.service\")"}}'
run_test_with_output "Mock code guard detection" \
    "echo '$TEST_INPUT' | '$CLAUDE_DIR/comprehensive-guard.sh' || true" \
    "MOCK CODE DETECTION"

# Test 16: Pre-commit config protection
TEST_INPUT='{"tool": "Edit", "parameters": {"file_path": "/path/to/.pre-commit-config.yaml", "old_string": "", "new_string": "# disabled"}}'
run_test_with_output "Pre-commit config guard detection" \
    "echo '$TEST_INPUT' | '$CLAUDE_DIR/comprehensive-guard.sh' || true" \
    "PRE-COMMIT CONFIG PROTECTION"

# Test 17: Safe command passthrough (should not trigger any guards)
TEST_INPUT='{"tool": "Bash", "parameters": {"command": "ls -la"}}'
run_test "Safe command passthrough" \
    "echo '$TEST_INPUT' | '$CLAUDE_DIR/comprehensive-guard.sh'"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${YELLOW}Test Results Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}Tests Completed:${NC}"
echo "  Total Tests: $TOTAL_TESTS"
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}Your Claude Code safety hooks are properly installed and functional.${NC}"
    echo ""
    echo -e "${YELLOW}What this means:${NC}"
    echo "  ✅ Hook installation is correct"
    echo "  ✅ All safety guards are active"
    echo "  ✅ Configuration is valid"
    echo "  ✅ Scripts are executable and working"
    echo ""
    echo -e "${YELLOW}Next time Claude Code runs dangerous commands, you'll see:${NC}"
    echo "  🚨 Warning messages explaining the risk"
    echo "  📋 Guidance on safer alternatives"
    echo "  🔒 Permission prompts for risky actions"
    echo ""
    EXIT_CODE=0
else
    echo -e "${RED}❌ SOME TESTS FAILED!${NC}"
    echo -e "${RED}Your hook installation may not be working correctly.${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting steps:${NC}"
    echo "  1. Re-run the installation: ./install-hooks.sh"
    echo "  2. Check file permissions: ls -la $CLAUDE_DIR/"
    echo "  3. Validate JSON manually: jq . $CLAUDE_DIR/settings.json"
    echo "  4. Check script syntax: bash -n $CLAUDE_DIR/comprehensive-guard.sh"
    echo "  5. Ensure jq is installed: which jq"
    echo ""
    EXIT_CODE=1
fi

echo -e "${BLUE}============================================================================${NC}"
echo -e "${YELLOW}Hook System Status${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Show current hook configuration
echo -e "${YELLOW}Installed Guards:${NC}"
if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
    jq -r '._documentation.guards_implemented[]?' "$CLAUDE_DIR/settings.json" 2>/dev/null | while IFS= read -r guard; do
        echo "  🛡️  $guard"
    done || echo "  ⚠️  Could not read guard list from settings"
else
    echo "  ❌ Settings file not found"
fi
echo ""

echo -e "${YELLOW}Installation Locations:${NC}"
echo "  📁 Config Directory: $CLAUDE_DIR"
echo "  📜 Guard Script: $CLAUDE_DIR/comprehensive-guard.sh"
echo "  ⚙️  Settings: $CLAUDE_DIR/settings.json"
echo ""

if [[ -f "$CLAUDE_DIR/settings.json.backup" ]]; then
    echo -e "${YELLOW}Backup Available:${NC}"
    echo "  💾 Previous settings backed up to: $CLAUDE_DIR/settings.json.backup"
    echo ""
fi

echo -e "${BLUE}Remember: These hooks protect you from mistakes that have caused real harm.${NC}"
echo -e "${BLUE}When a hook blocks an action, it's following documented safety rules.${NC}"
echo ""

exit $EXIT_CODE
