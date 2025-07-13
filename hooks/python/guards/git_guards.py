"""Git-related safety guards.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re  # noqa: E402

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402
from utils.patterns import (  # noqa: E402
    GIT_CHECKOUT_PATTERNS,
    GIT_FORCE_PUSH_PATTERNS,
    GIT_NO_VERIFY_PATTERN,
    PRECOMMIT_CONFIG_PATTERN,
    matches_any_pattern,
)


class GitNoVerifyGuard(BaseGuard):
    """Prevents bypassing pre-commit hooks with --no-verify flag."""

    def __init__(self):
        super().__init__(
            name="Git No-Verify Prevention", description="Prevents bypassing pre-commit hooks without permission"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False
        return bool(GIT_NO_VERIFY_PATTERN.search(context.command))

    def get_message(self, context: GuardContext) -> str:
        return f"""🚨 SECURITY ALERT: Git --no-verify detected!

Command: {context.command}

Pre-commit hooks exist to:
  - Prevent production issues
  - Maintain code quality
  - Enforce documentation standards
  - Run critical tests

Your project rules explicitly forbid bypassing hooks without permission.

❌ WHY THIS IS DANGEROUS:
  Pre-commit hooks prevent production issues and maintain code quality.
  Bypassing them has caused real incidents in this project.

✅ Suggested alternatives:
  1. Fix the underlying issue causing hook failures
  2. Temporarily disable specific hooks in .pre-commit-config.yaml
  3. Use 'git commit' without --no-verify and address failures"""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class GitForcePushGuard(BaseGuard):
    """Prevents dangerous git force pushes."""

    def __init__(self):
        super().__init__(
            name="Git Force Push Prevention", description="Blocks dangerous force pushes that rewrite history"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False
        return matches_any_pattern(context.command, GIT_FORCE_PUSH_PATTERNS)

    def get_message(self, context: GuardContext) -> str:
        return f"""🚨 DANGEROUS OPERATION: Git force push detected!

Command: {context.command}

WHY FORCE PUSH IS DANGEROUS:
  - Rewrites remote repository history
  - Can permanently delete other people's commits
  - Breaks local repositories for all team members
  - Makes code review and debugging extremely difficult
  - Can cause permanent data loss if not careful

WHEN FORCE PUSH MIGHT BE NEEDED (RARE):
  - Removing sensitive data accidentally committed
  - Fixing a broken rebase on a personal feature branch
  - Cleaning up commits before merging (only on personal branches)

SAFER ALTERNATIVES:
  1. Use 'git push --force-with-lease' (checks remote hasn't changed)
  2. Create a new branch instead of rewriting history
  3. Use 'git revert' to undo commits safely
  4. Communicate with team before any force push

This operation requires explicit permission due to high risk."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class GitCheckoutSafetyGuard(BaseGuard):
    """Prevents losing uncommitted work with git checkout/switch/restore/reset commands."""

    def __init__(self):
        super().__init__(
            name="Git Checkout/Reset Safety",
            description="Prevents accidentally losing uncommitted work with checkout/reset commands",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        # Only trigger on potentially dangerous checkout operations
        command = context.command.strip()

        # Safe operations that don't lose work
        safe_patterns = [
            r"git\s+checkout\s+-b\s+",  # Creating new branch
            r"git\s+checkout\s+--\s+",  # Checking out specific files only
            r"git\s+switch\s+-c\s+",  # Creating new branch with switch
            r"git\s+switch\s+--create\s+",  # Creating new branch with switch --create
            r"git\s+restore\s+--staged",  # Only unstaging files
            r"git\s+reset\s+--soft",  # Soft reset (preserves working directory)
        ]

        # Check if it's a safe operation
        for safe_pattern in safe_patterns:
            if re.search(safe_pattern, command, re.IGNORECASE):
                return False

        # Check if it matches checkout patterns that could lose work
        return matches_any_pattern(command, GIT_CHECKOUT_PATTERNS)

    def get_message(self, context: GuardContext) -> str:
        return f"""🚨 GIT CHECKOUT/RESET SAFETY WARNING: Potential work loss detected!

Command: {context.command}

❌ WHY THIS IS DANGEROUS:
  - Uncommitted changes may be permanently lost
  - Staged changes can be discarded
  - Untracked files may be deleted
  - Work in progress could disappear without warning
  - git reset --hard DESTROYS ALL local changes
  - Previous incidents have caused hours of lost work

🔍 BEFORE PROCEEDING, CHECK:
  1. git status           # See what changes exist
  2. git stash list       # Check for existing stashes
  3. git diff            # Review uncommitted changes
  4. git diff --cached   # Review staged changes

✅ SAFE ALTERNATIVES:
  1. Commit your work first:
     git add -A && git commit -m "WIP: save current work"

  2. Stash your changes:
     git stash push -m "work in progress before operation"

  3. Create a backup branch:
     git branch backup-$(date +%Y%m%d-%H%M%S)
     git add -A && git commit -m "backup before operation"

  4. For reset operations, use safer alternatives:
     - git reset --soft HEAD~1  (keeps changes in staging)
     - git restore --staged .   (unstage files safely)
     - git checkout -- <file>   (restore specific files)

  5. For switching branches safely:
     git stash && git checkout <branch> && git stash pop

💡 INCIDENT PREVENTION:
This guard exists because checkout/reset operations have caused work loss multiple times.
Always save your work before switching contexts or resetting."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class PreCommitConfigGuard(BaseGuard):
    """Prevents modifications to .pre-commit-config.yaml that would disable or weaken test enforcement."""

    def __init__(self):
        super().__init__(
            name="Pre-commit Config Protection",
            description="Prevents disabling or weakening pre-commit hooks without permission",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        # Only check Edit and MultiEdit tools that modify files
        if context.tool_name not in ("Edit", "MultiEdit"):
            return False

        # Check if editing .pre-commit-config.yaml
        file_path = context.tool_input.get("file_path", "")
        if not file_path or not PRECOMMIT_CONFIG_PATTERN.search(file_path):
            return False

        # Check for dangerous modifications
        if context.tool_name == "Edit":
            new_string = context.tool_input.get("new_string", "")
            return self._contains_dangerous_modification(new_string)
        elif context.tool_name == "MultiEdit":
            edits = context.tool_input.get("edits", [])
            return any(self._contains_dangerous_modification(edit.get("new_string", "")) for edit in edits)

        return False

    def _contains_dangerous_modification(self, new_string: str) -> bool:
        """Check if the modification contains dangerous patterns."""
        dangerous_patterns = [
            r"--exit-zero",  # Makes hooks always pass
            r"--no-verify",  # Bypasses verification
            r"exclude:\s*\^.*\$$",  # Overly broad exclusions
            r"fail_fast:\s*false",  # Prevents stopping on first failure
            r"skip:\s*\[.*\]",  # Skipping hooks entirely
            r"stages:\s*\[\]",  # Empty stages (disables hooks)
            r"#.*(?:ruff|black|mypy|flake8|pytest)",  # Commenting out specific tools
        ]

        return any(re.search(pattern, new_string, re.IGNORECASE) for pattern in dangerous_patterns)

    def get_message(self, context: GuardContext) -> str:
        return f"""🚨 PRE-COMMIT CONFIG PROTECTION: Dangerous modification detected!

File: {context.tool_input.get('file_path', 'unknown')}

❌ WHY THIS IS DANGEROUS:
  - Pre-commit hooks prevent production issues
  - Disabling tests has caused real production failures
  - Weakening enforcement bypasses critical quality checks
  - Code quality standards exist for a reason
  - Previous incidents were caused by bypassing hooks

🔍 DANGEROUS PATTERNS DETECTED:
  - --exit-zero flags (makes failing hooks pass)
  - --no-verify usage (bypasses verification)
  - Overly broad exclude patterns
  - Commenting out critical tools (ruff, black, mypy, pytest)
  - Disabling hooks entirely with skip lists
  - Empty stages configurations

✅ SAFE ALTERNATIVES:
  1. Fix the underlying code issues causing hook failures
  2. Add specific file exclusions if truly needed:
     exclude: '^(specific/path/file\\.py)$'
  3. Temporarily disable specific hooks with justification:
     # TODO: Re-enable after fixing XYZ issue
  4. Get explicit user permission for any hook modifications

💡 REMEMBER:
  The hooks are there to help you - they catch issues before they become
  production problems. Always fix the code, not the checks.

🚨 INCIDENT HISTORY:
  Previous attempts to weaken pre-commit enforcement have caused:
  - Production failures that could have been prevented
  - Hours of debugging time wasted
  - Code quality regressions
  - Security vulnerabilities

This guard exists because modifying pre-commit config to bypass failures
is almost always the wrong solution."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK
