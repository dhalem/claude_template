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

"""Test Claude Installation Safety Guard"""

import json
import subprocess
import sys
from pathlib import Path

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

# Find the guard script
GUARD_PATH = Path(__file__).parent.parent / 'claude-installation-safety-guard.py'


def run_guard(test_input: dict) -> int:
    """Run the guard with given input and return exit code"""
    input_json = json.dumps(test_input)

    result = subprocess.run(
        ['python3', str(GUARD_PATH)],
        input=input_json,
        capture_output=True,
        text=True
    )

    return result.returncode


def test_blocked_operations():
    """Test operations that should be blocked"""
    print(f"{YELLOW}Testing blocked operations...{NC}")

    blocked_tests = [
        # Creating new install scripts
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "install-new-thing.sh", "content": "#!/bin/bash"}
        },
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "setup-mcp-servers.sh", "content": "#!/bin/bash"}
        },

        # Direct .claude modifications
        {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf ~/.claude"}
        },
        {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf $HOME/.claude/settings.json"}
        },
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "/home/user/.claude/settings.json", "content": "{}"}
        },

        # Dangerous operations
        {
            "tool_name": "Bash",
            "tool_input": {"command": "chmod 777 ~/.claude"}
        },
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo '{}' > ~/.claude/settings.json"}
        },

        # Editing install scripts
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": "install-hooks.sh", "old_string": "foo", "new_string": "bar"}
        },

        # Creating install scripts via shell
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo '#!/bin/bash' > install-custom.sh"}
        },
    ]

    failed = 0
    for i, test in enumerate(blocked_tests):
        exit_code = run_guard(test)
        if exit_code == 2:
            print(f"{GREEN}✓ Test {i+1}: Correctly blocked dangerous operation{NC}")
        else:
            print(f"{RED}✗ Test {i+1}: Failed to block dangerous operation{NC}")
            print(f"  Input: {json.dumps(test)}")
            failed += 1

    return failed


def test_allowed_operations():
    """Test operations that should be allowed"""
    print(f"\n{YELLOW}Testing allowed operations...{NC}")

    allowed_tests = [
        # safe_install.sh is allowed
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "./safe_install.sh", "content": "#!/bin/bash"}
        },
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": "./safe_install.sh", "old_string": "foo", "new_string": "bar"}
        },

        # Reading .claude is allowed
        {
            "tool_name": "Bash",
            "tool_input": {"command": "ls ~/.claude"}
        },
        {
            "tool_name": "Bash",
            "tool_input": {"command": "cat ~/.claude/settings.json"}
        },

        # Normal file operations
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "test.py", "content": "print('hello')"}
        },
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'test' > output.txt"}
        },

        # Other tools
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "test.txt"}
        },
    ]

    failed = 0
    for i, test in enumerate(allowed_tests):
        exit_code = run_guard(test)
        if exit_code == 0:
            print(f"{GREEN}✓ Test {i+1}: Correctly allowed safe operation{NC}")
        else:
            print(f"{RED}✗ Test {i+1}: Incorrectly blocked safe operation{NC}")
            print(f"  Input: {json.dumps(test)}")
            failed += 1

    return failed


def main():
    """Run all tests"""
    print(f"{BLUE}Testing Claude Installation Safety Guard{NC}")
    print(f"{BLUE}========================================{NC}")

    if not GUARD_PATH.exists():
        print(f"{RED}ERROR: Guard script not found at {GUARD_PATH}{NC}")
        return 1

    total_failed = 0

    # Run blocked operations tests
    failed = test_blocked_operations()
    total_failed += failed

    # Run allowed operations tests
    failed = test_allowed_operations()
    total_failed += failed

    # Summary
    print(f"\n{BLUE}Test Summary{NC}")
    print(f"{BLUE}============{NC}")

    if total_failed == 0:
        print(f"{GREEN}✓ All tests passed!{NC}")
        print(f"{GREEN}Installation safety guard is working correctly{NC}")
        return 0
    else:
        print(f"{RED}✗ {total_failed} tests failed{NC}")
        print(f"{RED}Installation safety guard needs attention{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
