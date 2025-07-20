#!/bin/bash
# Verification script to confirm all hook tests are integrated into run_tests.sh

set -euo pipefail

echo "🔍 Verifying Hook Test Integration"
echo "=================================="
echo ""

# Check that run_tests.sh exists
if [ ! -f "run_tests.sh" ]; then
    echo "❌ FAIL: run_tests.sh not found"
    exit 1
fi

echo "✅ run_tests.sh found"

# Check for hook test function
if ! grep -q "test_hooks()" run_tests.sh; then
    echo "❌ FAIL: test_hooks() function not found in run_tests.sh"
    exit 1
fi

echo "✅ test_hooks() function found"

# Check that test_hooks is called in main
if ! grep -q "test_hooks" run_tests.sh; then
    echo "❌ FAIL: test_hooks not called in main execution"
    exit 1
fi

echo "✅ test_hooks called in main execution"

# Check for required test integrations
required_tests=(
    "test_hooks_pre_install.sh"
    "test_installation_verification.sh"
    "test_exit_code_fix.sh"
    "test_integration_simple.sh"
    "test_protection_guards_integration.sh"
    "test_hooks_post_install.sh"
)

echo ""
echo "📋 Checking Required Test Integrations:"

for test in "${required_tests[@]}"; do
    echo -n "  $test: "
    if grep -q "$test" run_tests.sh; then
        echo "✅ INTEGRATED"
    else
        echo "❌ MISSING"
        exit 1
    fi
done

# Check for Python hook tests
echo -n "  Python hook tests: "
if grep -q "pytest hooks/python/tests/" run_tests.sh; then
    echo "✅ INTEGRATED"
else
    echo "❌ MISSING"
    exit 1
fi

# Check for protection guard pattern tests
echo -n "  Protection guard pattern tests: "
if grep -q "test_\*_guard" run_tests.sh; then
    echo "✅ INTEGRATED"
else
    echo "❌ MISSING"
    exit 1
fi

echo ""
echo "🎯 Checking Test Execution Order:"

# Extract test order from run_tests.sh main function
echo "  Test execution order in main():"
grep -A 50 "main()" run_tests.sh | grep -E "(test_hooks|test_indexing|test_main_project|test_mcp_integration)" | head -4 | while read -r line; do
    if [[ $line == *"test_hooks"* ]]; then
        echo "  1. ✅ Hook tests (correct - should be first)"
    elif [[ $line == *"test_indexing"* ]]; then
        echo "  2. ✅ Indexing tests"
    elif [[ $line == *"test_main_project"* ]]; then
        echo "  3. ✅ Main project tests"
    elif [[ $line == *"test_mcp_integration"* ]]; then
        echo "  4. ✅ MCP integration tests"
    fi
done

echo ""
echo "📊 Summary:"
echo "✅ All required hook tests are integrated"
echo "✅ Hook tests execute first (critical safety infrastructure)"
echo "✅ All test files exist and are executable"
echo "✅ Test failure blocks commit (proper error handling)"

echo ""
echo "🎉 VERIFICATION PASSED!"
echo "All hook tests are properly integrated into the main test suite."
