#!/usr/bin/env python3
"""Guard that prevents creation of install scripts other than safe_install.sh.

This guard blocks any attempt to create new installation scripts that could
potentially damage the Claude installation. Only safe_install.sh is allowed.
"""

import os
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardContext  # noqa: E402


class InstallScriptPreventionGuard(BaseGuard):
    """Prevents creation of install scripts other than safe_install.sh."""

    def __init__(self):
        super().__init__(
            name="InstallScriptPreventionGuard",
            description="Prevents creation of dangerous installation scripts"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        """Check if attempting to create an install script."""
        if context.tool_name not in ["Write", "Edit", "MultiEdit"]:
            return False

        # Get the file path
        file_path = ""
        if hasattr(context, 'file_path'):
            file_path = context.file_path
        elif 'file_path' in context.tool_input:
            file_path = context.tool_input['file_path']
        elif hasattr(context, 'tool_input') and hasattr(context.tool_input, 'get'):
            file_path = context.tool_input.get('file_path', '')

        if not file_path:
            return False

        # Check if it's an install script
        file_name = file_path.split('/')[-1].lower()

        # Allow safe_install.sh
        if file_name == 'safe_install.sh':
            return False

        # Block any other install scripts
        install_patterns = [
            r'^install.*\.sh$',
            r'^setup.*\.sh$',
            r'^deploy.*\.sh$',
            r'.*install.*claude.*\.sh$',
            r'.*setup.*claude.*\.sh$',
            r'.*install.*hook.*\.sh$',
            r'.*install.*mcp.*\.sh$'
        ]

        for pattern in install_patterns:
            if re.match(pattern, file_name, re.IGNORECASE):
                return True

        # Also check file content for install-like operations on .claude
        content = ""
        if context.tool_name == "Write" and 'content' in context.tool_input:
            content = context.tool_input['content']
        elif context.tool_name in ["Edit", "MultiEdit"]:
            if 'new_string' in context.tool_input:
                content = context.tool_input['new_string']
            elif 'edits' in context.tool_input:
                content = ' '.join([edit.get('new_string', '') for edit in context.tool_input['edits']])

        if content:
            # Check for dangerous patterns in content
            dangerous_patterns = [
                r'cp.*~\/\.claude',
                r'mv.*~\/\.claude',
                r'rm.*~\/\.claude',
                r'mkdir.*~\/\.claude',
                r'install.*~\/\.claude'
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

        return False

    def get_message(self, context: GuardContext) -> str:
        """Get the warning message."""
        file_path = ""
        if hasattr(context, 'file_path'):
            file_path = context.file_path
        elif 'file_path' in context.tool_input:
            file_path = context.tool_input['file_path']

        return f"""🚨 INSTALLATION SCRIPT CREATION BLOCKED!

File: {file_path}

ONLY safe_install.sh is allowed for installations!

WHY THIS IS BLOCKED:
  - Multiple install scripts caused confusion and system damage
  - Direct .claude modifications destroyed Claude installations
  - Lack of backups made recovery impossible
  - Users lost work due to careless installation procedures

CRITICAL RULE:
  - THE ONLY INSTALL SCRIPT: ./safe_install.sh
  - This script guarantees:
    ✅ Mandatory backup of .claude directory
    ✅ Safe installation procedures
    ✅ Rollback instructions if needed
    ✅ User confirmation before changes

FORBIDDEN:
  - Creating new install-*.sh scripts
  - Creating setup-*.sh scripts
  - Any script that modifies ~/.claude
  - Bypassing safe_install.sh

If you need to add installation steps:
  1. Add them to safe_install.sh
  2. Ensure backup is created first
  3. Test thoroughly before committing"""

    def get_default_action(self) -> str:
        """Default to blocking."""
        return "block"


if __name__ == "__main__":
    # Test the guard
    from base_guard import GuardContext

    test_cases = [
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "install-new.sh", "content": "echo installing"},
            "should_trigger": True
        },
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "safe_install.sh", "content": "echo safe"},
            "should_trigger": False
        },
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "setup-hooks.sh", "content": "echo setup"},
            "should_trigger": True
        }
    ]

    guard = InstallScriptPreventionGuard()
    for test in test_cases:
        ctx = GuardContext(
            tool_name=test["tool_name"],
            tool_input=test["tool_input"]
        )
        triggered = guard.should_trigger(ctx)
        expected = test["should_trigger"]
        status = "✓" if triggered == expected else "✗"
        print(f"{status} Test: {test['tool_input']['file_path']} - Triggered: {triggered}")
