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

# Test suite for test-script-integrity-guard.sh
# Using TDD approach - tests written first, then implementation

set -euo pipefail

# Test framework functions
TESTS_PASSED=0
TESTS_FAILED=0
# TEST_OUTPUT variable removed - was unused

assert_exit_code() {
    local expected=$1
    local actual=$2
    local test_name="$3"

    if [ "$actual" -eq "$expected" ]; then
        echo "✅ PASS: $test_name (exit code $actual)"
        ((TESTS_PASSED++))
    else
        echo "❌ FAIL: $test_name (expected exit code $expected, got $actual)"
        ((TESTS_FAILED++))
    fi
}

assert_contains() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    if echo "$actual" | grep -q "$expected"; then
        echo "✅ PASS: $test_name (contains '$expected')"
        ((TESTS_PASSED++))
    else
        echo "❌ FAIL: $test_name (expected to contain '$expected')"
        echo "Actual output: $actual"
        ((TESTS_FAILED++))
    fi
}

# Setup test environment
setup_test_env() {
    TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR"

    # Create mock files that the guard should protect
    echo "#!/bin/bash" > run_tests.sh
    chmod +x run_tests.sh

    mkdir -p .git/hooks tests indexing/tests
    echo "yaml config" > .pre-commit-config.yaml
    echo "# CLAUDE.md" > CLAUDE.md

    # Copy the guard script (will be created after tests)
    if [ -f "../test-script-integrity-guard.sh" ]; then
        cp "../test-script-integrity-guard.sh" ./
        chmod +x test-script-integrity-guard.sh
    fi

    # Get correct path to guard script
    GUARD_SCRIPT=""
    if [ -f "./test-script-integrity-guard.sh" ]; then
        GUARD_SCRIPT="./test-script-integrity-guard.sh"
    elif [ -f "../test-script-integrity-guard.sh" ]; then
        GUARD_SCRIPT="../test-script-integrity-guard.sh"
    else
        # Use absolute path as fallback
        GUARD_SCRIPT="/home/dhalem/github/claude_template/hooks/test-script-integrity-guard.sh"
    fi
}

cleanup_test_env() {
    cd /
    rm -rf "$TEST_DIR"
}

# Test 1: Guard should block editing run_tests.sh
test_blocks_run_tests_modification() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        # Simulate Edit tool call to run_tests.sh
        TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "old_string": "#!/bin/bash", "new_string": "#!/bin/bash\n# FAST MODE"}}'

        set +e  # Allow commands to fail
        output=$(echo "$TEST_INPUT" | $GUARD_SCRIPT 2>&1)
        exit_code=$?
        set -e  # Re-enable exit on error

        assert_exit_code 2 $exit_code "Block run_tests.sh modification"
        assert_contains "TEST PROTECTION" "$output" "Shows test protection warning"
    else
        echo "⏭️  SKIP: test_blocks_run_tests_modification (guard not found)"
    fi

    cleanup_test_env
}

# Test 2: Guard should block pre-commit config changes
test_blocks_precommit_config_modification() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": ".pre-commit-config.yaml", "old_string": "yaml config", "new_string": "yaml config\n  stages: [manual]"}}'

        set +e  # Allow commands to fail
        output=$(echo "$TEST_INPUT" | $GUARD_SCRIPT 2>&1)
        exit_code=$?
        set -e  # Re-enable exit on error

        assert_exit_code 2 $exit_code "Block pre-commit config modification"
        assert_contains "MANDATORY FULL TEST SUITE" "$output" "Shows test enforcement warning"
    else
        echo "⏭️  SKIP: test_blocks_precommit_config_modification (guard not found)"
    fi

    cleanup_test_env
}

# Test 3: Guard should block test directory modifications
test_blocks_test_directory_modification() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_example.py", "old_string": "", "new_string": "# @pytest.mark.skip"}}'

        set +e  # Allow commands to fail
        output=$(echo "$TEST_INPUT" | $GUARD_SCRIPT 2>&1)
        exit_code=$?
        set -e  # Re-enable exit on error

        assert_exit_code 2 $exit_code "Block test file modification"
        assert_contains "test directory" "$output" "Shows test directory protection warning"
    else
        echo "⏭️  SKIP: test_blocks_test_directory_modification (guard not found)"
    fi

    cleanup_test_env
}

# Test 4: Guard should allow non-protected file modifications
test_allows_regular_file_modification() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": "src/regular_file.py", "old_string": "", "new_string": "print(\"hello\")"}}'

        set +e  # Allow commands to fail
        output=$(echo "$TEST_INPUT" | $GUARD_SCRIPT 2>&1)
        exit_code=$?
        set -e  # Re-enable exit on error

        assert_exit_code 0 $exit_code "Allow regular file modification"
    else
        echo "⏭️  SKIP: test_allows_regular_file_modification (guard not found)"
    fi

    cleanup_test_env
}

# Test 5: Guard should provide override mechanism
test_provides_override_mechanism() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "old_string": "#!/bin/bash", "new_string": "#!/bin/bash\n# Authorized change"}}'

        set +e  # Allow commands to fail
        output=$(echo "$TEST_INPUT" | $GUARD_SCRIPT 2>&1)
        exit_code=$?
        set -e  # Re-enable exit on error

        assert_exit_code 2 $exit_code "Block modification initially"
        assert_contains "HOOK_OVERRIDE_CODE" "$output" "Shows override mechanism"
    else
        echo "⏭️  SKIP: test_provides_override_mechanism (guard not found)"
    fi

    cleanup_test_env
}

# Test 6: Guard should work with override code
test_works_with_override_code() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        # Set override environment variable
        export HOOK_OVERRIDE_CODE="TEST123"

        TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "old_string": "#!/bin/bash", "new_string": "#!/bin/bash\n# Authorized change"}}'

        set +e  # Allow commands to fail
        output=$(echo "$TEST_INPUT" | $GUARD_SCRIPT 2>&1)
        exit_code=$?
        set -e  # Re-enable exit on error

        assert_exit_code 0 $exit_code "Allow modification with override"
        assert_contains "OVERRIDE APPLIED" "$output" "Shows override confirmation"

        unset HOOK_OVERRIDE_CODE
    else
        echo "⏭️  SKIP: test_works_with_override_code (guard not found)"
    fi

    cleanup_test_env
}

# Test 7: Guard should handle malformed JSON
test_handles_malformed_json() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        set +e  # Allow commands to fail
        output=$(echo "invalid json" | $GUARD_SCRIPT 2>&1)
        exit_code=$?
        set -e  # Re-enable exit on error

        assert_exit_code 1 $exit_code "Handle malformed JSON with error exit code"
    else
        echo "⏭️  SKIP: test_handles_malformed_json (guard not found)"
    fi

    cleanup_test_env
}

# Test 8: Guard should log protection attempts
test_logs_protection_attempts() {
    setup_test_env

    if [ -n "$GUARD_SCRIPT" ]; then
        TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh", "old_string": "#!/bin/bash", "new_string": "#!/bin/bash\n# FAST MODE"}}'

        output=$(echo "$TEST_INPUT" | $GUARD_SCRIPT 2>&1)

        # Check if log file was created and contains entry
        LOG_PATH="$HOME/.claude/logs/test_protection.log"
        if [ -f "$LOG_PATH" ]; then
            assert_contains "run_tests.sh" "$(cat "$LOG_PATH")" "Logs protection attempt"
        else
            echo "⏭️  SKIP: Log file check (logging not implemented yet)"
        fi
    else
        echo "⏭️  SKIP: test_logs_protection_attempts (guard not found)"
    fi

    cleanup_test_env
}

# Run all tests
main() {
    echo "🧪 Running Test Script Integrity Guard Test Suite"
    echo "================================================="
    echo ""

    # Run TDD tests (these will fail initially)
    test_blocks_run_tests_modification
    test_blocks_precommit_config_modification
    test_blocks_test_directory_modification
    test_allows_regular_file_modification
    test_provides_override_mechanism
    test_works_with_override_code
    test_handles_malformed_json
    test_logs_protection_attempts

    echo ""
    echo "📊 Test Results:"
    echo "✅ Passed: $TESTS_PASSED"
    echo "❌ Failed: $TESTS_FAILED"
    echo "📝 Total:  $((TESTS_PASSED + TESTS_FAILED))"

    if [ $TESTS_FAILED -gt 0 ]; then
        echo ""
        echo "🚨 Some tests failed. This is expected in TDD - implement the guard to make tests pass."
        exit 1
    else
        echo ""
        echo "🎉 All tests passed! Guard implementation is complete."
        exit 0
    fi
}

# Only run if executed directly (not sourced)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
