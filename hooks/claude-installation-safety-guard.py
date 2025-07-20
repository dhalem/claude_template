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
Claude Installation Safety Guard

This guard prevents dangerous operations that could damage Claude installations.

What it blocks:
1. Creating new install scripts (only safe_install.sh allowed)
2. Direct modifications to ~/.claude without using safe_install.sh
3. Destructive rm -rf operations on Claude directories
4. Bypassing safety mechanisms

Exit codes:
- 0: Operation allowed
- 2: Operation blocked (dangerous pattern detected)
"""

import json
import re
import sys


class InstallationSafetyGuard:
    """Guard against dangerous installation operations"""

    def __init__(self):
        self.blocked_patterns = [
            # Block creation of new install scripts
            (r'install[_-].*\.sh', 'Creating new install scripts'),
            (r'setup[_-].*\.sh', 'Creating new setup scripts'),

            # Block direct .claude modifications
            (r'rm\s+-rf?\s+.*\.claude', 'Destructive removal of .claude directory'),
            (r'rm\s+-rf?\s+\$HOME/\.claude', 'Destructive removal of .claude directory'),
            (r'rm\s+-rf?\s+~/\.claude', 'Destructive removal of .claude directory'),

            # Block dangerous file operations
            (r'>\s*~?/\.claude/settings\.json', 'Direct overwrite of Claude settings'),
            (r'>\s*\$HOME/\.claude/settings\.json', 'Direct overwrite of Claude settings'),

            # Block dangerous chmod operations
            (r'chmod\s+777\s+.*\.claude', 'Dangerous permissions on .claude directory'),
        ]

        self.safe_install_path = './safe_install.sh'

    def check_write_operation(self, tool_input: dict) -> tuple[bool, str]:
        """Check Write tool operations"""
        if 'file_path' not in tool_input:
            return True, ""

        file_path = tool_input['file_path']

        # Check if creating a new install script
        if re.search(r'install[_-].*\.sh$', file_path) and file_path != self.safe_install_path:
            return False, f"Creating new install script '{file_path}' is forbidden. Use only safe_install.sh"

        if re.search(r'setup[_-](mcp|hooks|claude).*\.sh$', file_path):
            return False, f"Creating new setup script '{file_path}' is forbidden. Use only safe_install.sh"

        # Check if directly modifying .claude directory
        if '/.claude/' in file_path and '/safe_install.sh' not in file_path:
            return False, "Direct modification of .claude directory is forbidden. Use safe_install.sh"

        return True, ""

    def check_bash_operation(self, tool_input: dict) -> tuple[bool, str]:
        """Check Bash tool operations"""
        if 'command' not in tool_input:
            return True, ""

        command = tool_input['command']

        # Check against blocked patterns
        for pattern, reason in self.blocked_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"{reason}: {command}"

        # Check for creation of install scripts via echo/cat
        if re.search(r'(echo|cat).*>\s*[^/]*install[_-].*\.sh', command):
            return False, "Creating install scripts via shell redirection is forbidden"

        # Check for dangerous .claude operations
        if '.claude' in command:
            # Allow reading/listing operations
            if re.match(r'^(ls|cat|head|tail|grep|find)\s+', command):
                return True, ""

            # Block modifications without safe_install.sh
            if 'safe_install.sh' not in command:
                if any(cmd in command for cmd in ['rm', 'mv', 'cp', '>', 'chmod']):
                    return False, f"Direct .claude modifications forbidden. Use safe_install.sh: {command}"

        return True, ""

    def check_edit_operation(self, tool_input: dict) -> tuple[bool, str]:
        """Check Edit/MultiEdit operations"""
        if 'file_path' not in tool_input:
            return True, ""

        file_path = tool_input['file_path']

        # Don't allow editing install scripts (except safe_install.sh)
        if re.search(r'install[_-].*\.sh$', file_path) and file_path != self.safe_install_path:
            return False, "Editing install scripts is forbidden. Use only safe_install.sh"

        # Don't allow direct edits to .claude files
        if '/.claude/' in file_path:
            return False, "Direct editing of .claude files is forbidden. Use safe_install.sh"

        return True, ""

    def process(self, input_data: dict) -> int:
        """Process the input and check for dangerous operations"""
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        # Check based on tool type
        if tool_name == 'Write':
            allowed, reason = self.check_write_operation(tool_input)
        elif tool_name == 'Bash':
            allowed, reason = self.check_bash_operation(tool_input)
        elif tool_name in ['Edit', 'MultiEdit']:
            allowed, reason = self.check_edit_operation(tool_input)
        else:
            # Allow other tools
            return 0

        if not allowed:
            print("\n🚨 INSTALLATION SAFETY GUARD FIRED 🚨", file=sys.stderr)
            print(f"\nBLOCKED: {reason}", file=sys.stderr)
            print("\n⚠️  CRITICAL SAFETY RULE:", file=sys.stderr)
            print("  - Use ONLY ./safe_install.sh for ALL installations", file=sys.stderr)
            print("  - NEVER create new install scripts", file=sys.stderr)
            print("  - NEVER modify .claude directory directly", file=sys.stderr)
            print("  - ALWAYS backup before making changes", file=sys.stderr)
            print("\n📖 See CLAUDE.md section: 'INSTALLATION SAFETY - USE ONLY safe_install.sh'", file=sys.stderr)
            print("\n❌ Operation blocked for safety", file=sys.stderr)
            return 2

        return 0


def main():
    """Main entry point"""
    # Read input
    try:
        input_line = sys.stdin.read().strip()
        if not input_line:
            print("Error: No input provided", file=sys.stderr)
            return 1

        input_data = json.loads(input_line)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 1

    # Process with guard
    guard = InstallationSafetyGuard()
    return guard.process(input_data)


if __name__ == "__main__":
    sys.exit(main())
