"""File operation guards.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402
from utils.patterns import (  # noqa: E402
    CLAUDE_DIR_PATTERN,
    MOCK_CODE_PATTERNS,
    PRECOMMIT_CONFIG_PATTERN,
    matches_any_pattern,
)


class MockCodeGuard(BaseGuard):
    """Prevents creation of forbidden mock/simulation code."""

    def __init__(self):
        super().__init__(
            name="Mock Code Prevention", description="Blocks forbidden mock/simulation code without permission"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name not in ["Edit", "Write", "MultiEdit"]:
            return False

        # Check content being written
        content_to_check = ""
        if context.content:
            content_to_check += context.content
        if context.new_string:
            content_to_check += "\n" + context.new_string

        if not content_to_check:
            return False

        return matches_any_pattern(content_to_check, MOCK_CODE_PATTERNS)

    def get_message(self, context: GuardContext) -> str:
        matching_patterns = []
        content_to_check = ""
        if context.content:
            content_to_check += context.content
        if context.new_string:
            content_to_check += "\n" + context.new_string

        for pattern in MOCK_CODE_PATTERNS:
            if pattern.search(content_to_check):
                matching_patterns.append(pattern.pattern)

        patterns_str = "\n".join(f"  - {pattern}" for pattern in matching_patterns)

        return f"""🚨 MOCK CODE DETECTION: Forbidden patterns found!

Detected patterns:
{patterns_str}

❌ RULE VIOLATION: MOCKS AND SIMULATIONS ARE STRICTLY FORBIDDEN

📜 FROM CLAUDE.md RULES:
  - Mocks prove code compiles, not that features work
  - Real integration testing is mandatory
  - Mock-only testing causes features that pass tests but fail in production

REAL EXAMPLES OF MOCK FAILURES:
  - Mocked database tests passed, real queries failed
  - Mocked API tests passed, real endpoints broken
  - Mocked file operations passed, container paths wrong

🔒 MANDATORY PERMISSION PROTOCOL:
  1. STOP immediately - Do not write any mock code
  2. Ask user permission with detailed justification
  3. Get explicit written approval before proceeding

✅ ALTERNATIVES:
  - Use real integration tests with actual services
  - Test against real databases/APIs
  - Use containerized test environments

💡 Remember: Mocks lie. Real tests reveal truth."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class PreCommitConfigGuard(BaseGuard):
    """Prevents unauthorized changes to .pre-commit-config.yaml."""

    def __init__(self):
        super().__init__(
            name="Pre-Commit Config Protection", description="Guards .pre-commit-config.yaml modifications"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name not in ["Edit", "Write", "MultiEdit"]:
            return False

        if not context.file_path:
            return False

        return bool(PRECOMMIT_CONFIG_PATTERN.search(context.file_path))

    def get_message(self, context: GuardContext) -> str:
        return f"""🚨 PRE-COMMIT CONFIG PROTECTION: Unauthorized modification detected!

File: {context.file_path}

❌ RULE VIOLATION FROM CLAUDE.md:
  'PRE-COMMIT HOOKS MAY NEVER BE DISABLED WITHOUT EXPLICIT USER PERMISSION'

🔒 FORBIDDEN PRACTICES:
  - Commenting out hooks
  - Adding --exit-zero or bypass flags to working hooks
  - Using exclude patterns to skip validation
  - Disabling hooks temporarily 'just for this commit'

✅ MANDATORY PROTOCOL WHEN HOOKS FAIL:
  1. READ the hook error message - it tells you exactly what to fix
  2. FIX THE CODE - don't bypass the check
  3. UPDATE DOCUMENTATION when required (INDEX.md, etc.)
  4. NEVER disable the hook - that defeats the purpose

🛡️  WHY THIS PROTECTION EXISTS:
  - Pre-commit hooks prevent production issues
  - Maintain code quality and enforce documentation standards
  - Disabling them has caused real production failures
  - Hours of debugging required when bypassed

💡 TO GET PERMISSION:
  1. Ask user for explicit written permission
  2. Provide detailed justification for the change
  3. Explain why hook bypass is needed vs fixing the underlying issue"""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class HookInstallationGuard(BaseGuard):
    """Blocks direct modifications to ~/.claude/ directory."""

    def __init__(self):
        super().__init__(
            name="Hook Installation Protection", description="Blocks direct edits/copies, enforces install script usage"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        # Check for file operations on .claude directory
        if context.tool_name in ["Edit", "Write", "MultiEdit"]:
            if context.file_path and CLAUDE_DIR_PATTERN.search(context.file_path):
                return True

        # Check for Bash cp/copy operations targeting .claude directory
        if context.tool_name == "Bash" and context.command:
            if "cp" in context.command and ".claude/" in context.command:
                return True

        return False

    def get_message(self, context: GuardContext) -> str:
        if context.tool_name == "Bash":
            operation_desc = f"Copy command: {context.command}"
        else:
            operation_desc = f"File operation: {context.tool_name} on {context.file_path}"

        return f"""🚨 DIRECT HOOK MODIFICATION BLOCKED: Use install script instead!

{operation_desc}

WHY THIS IS BLOCKED:
  - Direct modifications to ~/.claude/ bypass version control
  - Changes are lost when hooks are reinstalled
  - No automatic backups are created
  - Breaks the repository-first development workflow
  - Makes debugging and maintenance difficult
  - The install script handles proper backup and deployment

CORRECT WORKFLOW:
  1. Make changes in repository: /home/dhalem/github/sptodial_one/spotidal/hooks/
  2. Test your changes
  3. Run the install script: cd hooks && ./install-hooks.sh
  4. The script will:
     - Create timestamped backups of existing files
     - Install all hooks properly
     - Validate syntax
     - Show installation summary

BENEFITS OF USING INSTALL SCRIPT:
  - Preserves existing customizations as backups
  - Ensures consistent deployment
  - Provides installation verification
  - Maintains audit trail of changes

💡 Quick tip:
  The script backs up to: ~/.claude/*.backup.TIMESTAMP
  You can always restore from backups if needed"""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK
