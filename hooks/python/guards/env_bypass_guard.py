"""Guard to prevent bypassing guards via environment variables.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402


class EnvBypassGuard(BaseGuard):
    """Prevents setting environment variables that could bypass guards."""

    def __init__(self):
        super().__init__(
            name="Environment Variable Bypass Prevention",
            description="Blocks attempts to set environment variables that bypass guards",
        )

        # Patterns that might be used to bypass guards
        self.bypass_patterns = [
            # Claude-specific patterns
            r"CLAUDE[_\-]?SKIP[_\-]?GUARDS?",
            r"CLAUDE[_\-]?DISABLE[_\-]?GUARDS?",
            r"CLAUDE[_\-]?BYPASS[_\-]?GUARDS?",
            r"CLAUDE[_\-]?NO[_\-]?GUARDS?",
            r"CLAUDECODE[_\-]?SKIP[_\-]?GUARDS?",
            r"CLAUDECODE[_\-]?DISABLE[_\-]?GUARDS?",
            # General guard bypass patterns
            r"SKIP[_\-]?GUARDS?",
            r"DISABLE[_\-]?GUARDS?",
            r"BYPASS[_\-]?GUARDS?",
            r"NO[_\-]?GUARDS?",
            r"GUARDS?[_\-]?SKIP",
            r"GUARDS?[_\-]?DISABLE",
            r"GUARDS?[_\-]?BYPASS",
            # Test bypass patterns
            r"TEST[_\-]?SKIP",
            r"SKIP[_\-]?TESTS?",
            r"BYPASS[_\-]?TESTS?",
            r"DISABLE[_\-]?TESTS?",
            r"NO[_\-]?TESTS?",
            r"FORCE[_\-]?PASS",
            r"ALWAYS[_\-]?PASS",
            r"IGNORE[_\-]?FAIL(?:URE)?S?",
            # Common short forms used with git/test commands
            r"SKIP",  # Catches bare SKIP=...
        ]

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        command = context.command.strip()

        # Check for export/set commands
        has_export_set = re.search(r"\b(export|set)\s+", command, re.IGNORECASE)

        # Check for env command
        has_env = re.search(r"\benv\s+", command, re.IGNORECASE)

        # Check for direct environment variable syntax (VAR=value command)
        # This catches patterns like: SKIP=true git commit
        has_direct_env = False
        for pattern in self.bypass_patterns:
            # Check if pattern appears at start of command or after whitespace, followed by =
            # and then eventually followed by a command (with value and space in between)
            if re.search(rf"(?:^|\s){pattern}\s*=[^\s]+\s+", command, re.IGNORECASE):
                has_direct_env = True
                break

        # Must have either export/set, env, or direct syntax
        if not has_export_set and not has_env and not has_direct_env:
            return False

        # Check if any bypass pattern is being set
        return any(re.search(rf"(?:^|\s){pattern}\s*=", command, re.IGNORECASE) for pattern in self.bypass_patterns)

    def get_message(self, context: GuardContext) -> str:
        return f"""🚫 ENVIRONMENT BYPASS ATTEMPT DETECTED!

Command: {context.command}

❌ SECURITY VIOLATION: Attempting to set environment variables that bypass guards!

WHY THIS IS BLOCKED:
  - Guards exist to prevent production issues
  - Bypassing guards has caused real incidents
  - Test enforcement is mandatory for code quality
  - Environment variables should not disable safety features

WHAT YOU'RE TRYING TO DO:
  You appear to be setting an environment variable that could:
  - Skip tests or guards
  - Disable safety checks
  - Force tests to pass
  - Bypass pre-commit hooks

✅ CORRECT APPROACH:
  1. Fix the underlying issue causing failures
  2. Never bypass safety mechanisms
  3. If a guard is incorrectly blocking valid work:
     - Report the issue
     - Get explicit permission to modify guard behavior
     - Update the guard properly, not bypass it

🔒 SECURITY POLICY:
  - No environment variables may bypass guards
  - No environment variables may skip tests
  - All safety mechanisms must remain active
  - Guards can only be modified through proper channels

If you believe this is blocking legitimate work, please:
  1. Document the specific issue
  2. Get explicit user permission
  3. Modify the guard itself, not bypass it

Remember: Guards have prevented real production issues.
Bypassing them puts the system at risk."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK
