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

# Simple integration test to verify all guards are working
set -euo pipefail

echo "🧪 Protection Guards Simple Integration Test"
echo "==========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$HOOKS_DIR")"

# Find Python executable
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/venv/bin/python3" ]; then
    PYTHON_CMD="$PROJECT_ROOT/venv/bin/python3"
fi

# Test each guard individually first
echo "1️⃣ Testing test-script-integrity-guard.sh..."
"$HOOKS_DIR/verify_test_script_integrity_guard.sh"
echo ""

echo "2️⃣ Testing precommit-protection-guard.sh..."
"$HOOKS_DIR/verify_precommit_protection_guard.sh"
echo ""

echo "3️⃣ Testing anti-bypass-pattern-guard.py..."
"$PYTHON_CMD" "$HOOKS_DIR/verify_anti_bypass_pattern_guard.py"
echo ""

echo "✅ All protection guards verified individually!"
echo ""
echo "🛡️ Test Protection System Status:"
echo "• Test Script Integrity Guard: ✅ Operational"
echo "• Pre-commit Protection Guard: ✅ Operational"
echo "• Anti-bypass Pattern Guard: ✅ Operational"
echo ""
echo "The test protection system is fully functional and will prevent:"
echo "• Modifications to run_tests.sh or .pre-commit-config.yaml"
echo "• Attempts to bypass pre-commit hooks (--no-verify, uninstall, etc.)"
echo "• Code patterns that skip or bypass tests (@skip, --fast, etc.)"
echo ""
echo "🎉 INTEGRATION TEST PASSED!"
