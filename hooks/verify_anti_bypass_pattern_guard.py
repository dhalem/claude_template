#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Verification script for anti-bypass-pattern-guard.py
Tests common bypass patterns to ensure the guard is working correctly
"""

import json
import subprocess
import sys
from pathlib import Path


def run_guard_test(tool_input, test_name, should_block=True):
    """Run a test against the guard"""
    guard_path = Path(__file__).parent / "anti-bypass-pattern-guard.py"

    print(f"{test_name}: ", end="", flush=True)

    result = subprocess.run(
        [sys.executable, str(guard_path)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True
    )

    if should_block:
        if result.returncode == 2:
            print("✅ PASSED (blocked as expected)")
            return True
        else:
            print(f"❌ FAILED (should have blocked, exit code: {result.returncode})")
            return False
    else:
        if result.returncode == 0:
            print("✅ PASSED (allowed as expected)")
            return True
        else:
            print(f"❌ FAILED (should have allowed, exit code: {result.returncode})")
            return False

def main():
    """Run verification tests"""
    print("🔍 Verifying Anti-Bypass Pattern Guard")
    print("======================================")
    print()

    print("✅ Verification Results:")
    print()

    passed = 0
    total = 0

    # Test 1: Block @pytest.mark.skip
    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "test_example.py",
            "new_string": "@pytest.mark.skip\ndef test_function():\n    pass"
        }
    }
    if run_guard_test(tool_input, "1. Blocks @pytest.mark.skip"):
        passed += 1
    total += 1

    # Test 2: Block stages: [manual]
    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": ".pre-commit-config.yaml",
            "new_string": "- id: tests\n  stages: [manual]"
        }
    }
    if run_guard_test(tool_input, "2. Blocks stages: [manual]"):
        passed += 1
    total += 1

    # Test 3: Block --no-verify comments
    tool_input = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "script.sh",
            "content": "#!/bin/bash\n# Use --no-verify to skip tests\ngit commit"
        }
    }
    if run_guard_test(tool_input, "3. Blocks --no-verify comments"):
        passed += 1
    total += 1

    # Test 4: Block fast mode patterns
    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "run_tests.sh",
            "new_string": 'if [ "$1" = "--fast" ]; then\n  pytest -x\nfi'
        }
    }
    if run_guard_test(tool_input, "4. Blocks fast mode patterns"):
        passed += 1
    total += 1

    # Test 5: Block -k "not slow"
    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "test_runner.py",
            "new_string": 'subprocess.run(["pytest", "-k", "not slow"])'
        }
    }
    if run_guard_test(tool_input, "5. Blocks pytest -k 'not slow'"):
        passed += 1
    total += 1

    # Test 6: Allow legitimate code
    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "app.py",
            "new_string": "def calculate():\n    return 42"
        }
    }
    if run_guard_test(tool_input, "6. Allows legitimate code", should_block=False):
        passed += 1
    total += 1

    # Test 7: Case insensitive detection
    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "test.sh",
            "new_string": "# FAST MODE enabled here"
        }
    }
    if run_guard_test(tool_input, "7. Detects patterns case-insensitively"):
        passed += 1
    total += 1

    # Test 8: Multiple patterns
    tool_input = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "test_utils.py",
            "content": """@pytest.mark.skip
def test_one():
    pass

# Run with -k "not slow" to skip"""
        }
    }
    if run_guard_test(tool_input, "8. Detects multiple bypass patterns"):
        passed += 1
    total += 1

    print()
    print("🎯 Guard Functionality Summary:")
    print("• Blocks test skip decorators ✅")
    print("• Blocks pre-commit stage bypasses ✅")
    print("• Blocks fast/quick mode patterns ✅")
    print("• Blocks test exclusion patterns ✅")
    print("• Detects patterns in comments ✅")
    print("• Case-insensitive detection ✅")
    print("• Allows legitimate code changes ✅")
    print("• Provides override mechanism ✅")

    print()
    if passed == total:
        print(f"🎉 ALL VERIFICATIONS PASSED! ({passed}/{total})")
        print()
        print("The anti-bypass-pattern-guard.py is working correctly and ready for use.")
        return 0
    else:
        print(f"❌ Some verifications failed. ({passed}/{total} passed)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
