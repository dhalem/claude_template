#!/bin/bash
# Quick manual test

set -euo pipefail

echo "🧪 Manual Test"
echo "=============="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARD_SCRIPT="$SCRIPT_DIR/test-script-integrity-guard.sh"

if [ -f "$GUARD_SCRIPT" ]; then
    echo "✅ Guard script found: $GUARD_SCRIPT"

    # Test 1: Should block run_tests.sh modification
    echo "Testing run_tests.sh modification..."
    TEST_INPUT='{"tool_name": "Edit", "tool_input": {"file_path": "run_tests.sh"}}'

    set +e  # Allow commands to fail
    echo "$TEST_INPUT" | "$GUARD_SCRIPT" >/dev/null 2>&1
    exit_code=$?
    set -e  # Re-enable exit on error

    echo "Exit code: $exit_code"

    if [ $exit_code -eq 2 ]; then
        echo "✅ PASS: Correctly blocked modification (exit code 2)"
    else
        echo "❌ FAIL: Expected exit code 2, got $exit_code"
    fi

else
    echo "❌ Guard script not found: $GUARD_SCRIPT"
fi
