"""Git Hook Protection Guard.

Prevents modification or removal of git hooks to ensure security controls
remain in place. Git hooks enforce code quality and security standards.

REMINDER: Update HOOKS.md when modifying this guard!
"""

import logging
import re
from typing import Optional

from base_guard import BaseGuard, GuardAction, GuardContext

logger = logging.getLogger(__name__)


class GitHookProtectionGuard(BaseGuard):
    """Prevents modification or removal of git hooks."""

    def __init__(self):
        super().__init__(
            name="Git Hook Protection",
            description="Prevents disabling, modifying, or removing git hooks"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        """Check if the command attempts to modify git hooks."""
        if context.tool_name != "Bash":
            return False

        command = context.command or context.tool_input.get("command", "")
        if not command:
            return False

        # Patterns that indicate git hook manipulation
        dangerous_patterns = [
            # Direct hook file operations
            r'\.git/hooks/',
            r'\.git\\hooks\\',

            # Moving/renaming hooks
            r'\bmv\s+.*\.git.*hooks',
            r'\brename\s+.*\.git.*hooks',

            # Removing hooks
            r'\brm\s+.*\.git.*hooks',
            r'\bremove\s+.*\.git.*hooks',
            r'\bdelete\s+.*\.git.*hooks',

            # Modifying hooks
            r'\bchmod\s+.*\.git.*hooks',
            r'\btouch\s+.*\.git.*hooks',
            r'\becho.*>.*\.git.*hooks',
            r'\bcat.*>.*\.git.*hooks',

            # Disabling pre-commit
            r'pre-commit\s+uninstall',
            r'SKIP=',
            r'--no-verify',

            # Git config to disable hooks
            r'git\s+config.*hooks\..*false',
            r'git\s+config.*core\.hooksPath',
            r'core\.hooksPath.*none',
            r'core\.hooksPath.*false',
            r'core\.hooksPath.*/dev/null',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(
                    "Git hook manipulation attempt detected: %s",
                    command[:100]
                )
                return True

        return False

    def get_message(self, context: GuardContext) -> Optional[str]:
        """Return warning message about git hook protection."""
        command = context.command or context.tool_input.get("command", "")

        return f"""🚨 GIT HOOK PROTECTION VIOLATION

Command attempted: {command[:200]}

❌ SECURITY VIOLATION: Attempting to modify or disable git hooks!

Git hooks are critical security controls that:
- Enforce code quality standards
- Run security scans
- Prevent committing sensitive data
- Ensure tests pass before commits
- Maintain consistent code formatting

WHY THIS IS BLOCKED:
- Disabling hooks bypasses security controls
- Could allow malicious or broken code to be committed
- Violates established development practices
- Has caused production incidents in the past

✅ LEGITIMATE ALTERNATIVES:
If you're having issues with git hooks:
1. Fix the underlying issue causing hook failures
2. Report problems with specific hooks
3. Request updates to hook configuration
4. Use proper debugging techniques

NEVER attempt to:
- Move or rename .git/hooks files
- Use --no-verify to bypass checks
- Modify hook permissions
- Uninstall pre-commit

Remember: Git hooks exist to protect the codebase and catch issues early.
Bypassing them puts the entire project at risk."""

    def get_default_action(self) -> GuardAction:
        """Return default action - always block hook modifications."""
        return GuardAction.BLOCK
