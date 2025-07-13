"""Rule #0 enforcement guard for file writes.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402


class RuleZeroReminderGuard(BaseGuard):
    """Ensures all file writes include a Rule #0 reminder comment."""

    def __init__(self):
        super().__init__(
            name="Rule #0 Reminder Guard",
            description="Ensures files include a reminder about Rule #0: Check CLAUDE.md BEFORE acting",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        """Trigger on Write and MultiEdit tools only if Rule #0 comment is missing."""
        if context.tool_name not in ["Write", "MultiEdit"]:
            return False

        # Check if content already has Rule #0 comment
        content = self._get_content(context)
        if not content:
            return True  # Empty content needs Rule #0

        return not self._has_rule_zero_comment(content)

    def get_message(self, context: GuardContext) -> str:
        """Return message explaining Rule #0 requirement."""
        # Only return message if should_trigger is True
        if not self.should_trigger(context):
            return ""

        file_path = context.tool_input.get("file_path", "the file")

        # Determine comment style based on file extension
        comment_examples = self._get_comment_examples(file_path)

        return f"""📋 RULE #0 REMINDER REQUIRED: Add a comment explaining Rule #0!

File: {file_path}

❌ PROBLEM: Every file must include a reminder about Rule #0

🚨 WHAT IS RULE #0?
Rule #0 is the MANDATORY FIRST ACTION for every request:
1. Read CLAUDE.md COMPLETELY before responding
2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
3. Read INDEX.md files for relevant directories
4. Search for rules related to the request
5. Only proceed after confirming no violations

"Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes."

✅ ADD THIS COMMENT TO YOUR FILE:
{comment_examples}

⚠️ WHY THIS MATTERS:
- Rule #0 violations have caused real harm (woke up user's wife, broke production)
- Every file should remind us to check rules BEFORE acting
- This prevents costly mistakes that violate CLAUDE.md rules
- It's a constant reminder that we must read and follow ALL rules

💡 PLACEMENT:
- Add near the top of the file (after shebang/imports if applicable)
- Make it prominent so it's seen immediately
- Adjust comment style based on file type

🔍 This guard ensures we never forget the most important rule:
CHECK THE RULES BEFORE ACTING, NOT AFTER MAKING MISTAKES!"""

    def _get_content(self, context: GuardContext) -> str:
        """Extract file content from context."""
        if context.tool_name == "Write":
            return context.tool_input.get("content", "")
        elif context.tool_name == "MultiEdit":
            # For MultiEdit, check if we're creating a new file (empty old_string in first edit)
            edits = context.tool_input.get("edits", [])
            if edits and edits[0].get("old_string", "") == "":
                return edits[0].get("new_string", "")
        return ""

    def _has_rule_zero_comment(self, content: str) -> bool:
        """Check if content contains a Rule #0 comment (case insensitive)."""
        content_lower = content.lower()

        # Look for various Rule #0 patterns
        rule_zero_patterns = ["rule #0", "rule 0", "rule zero", "mandatory first action"]

        return any(pattern in content_lower for pattern in rule_zero_patterns)

    def _get_comment_examples(self, file_path: str) -> str:
        """Get appropriate comment examples based on file type."""
        ext = os.path.splitext(file_path)[1].lower()

        # Python/Shell style comments
        if ext in [".py", ".sh", ".bash", ".yml", ".yaml"]:
            return """# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm"""

        # JavaScript/TypeScript/CSS style comments
        elif ext in [".js", ".ts", ".jsx", ".tsx", ".css", ".scss"]:
            return """/* RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
 * 1. Read CLAUDE.md COMPLETELY before responding
 * 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
 * 3. Read INDEX.md files for relevant directories
 * 4. Search for rules related to the request
 * 5. Only proceed after confirming no violations
 * Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
 *
 * GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
 * NEVER weaken, disable, or bypass guards - they prevent real harm
 */"""

        # HTML/XML style comments
        elif ext in [".html", ".xml", ".svg"]:
            return """<!-- RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
     1. Read CLAUDE.md COMPLETELY before responding
     2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
     3. Read INDEX.md files for relevant directories
     4. Search for rules related to the request
     5. Only proceed after confirming no violations
     Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.

     GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
     NEVER weaken, disable, or bypass guards - they prevent real harm
-->"""

        # SQL style comments
        elif ext in [".sql"]:
            return """-- RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
-- 1. Read CLAUDE.md COMPLETELY before responding
-- 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
-- 3. Read INDEX.md files for relevant directories
-- 4. Search for rules related to the request
-- 5. Only proceed after confirming no violations
-- Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes."""

        # Markdown
        elif ext in [".md"]:
            return """[//]: # (RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST)
[//]: # (1. Read CLAUDE.md COMPLETELY before responding)
[//]: # (2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate)
[//]: # (3. Read INDEX.md files for relevant directories)
[//]: # (4. Search for rules related to the request)
[//]: # (5. Only proceed after confirming no violations)
[//]: # (Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.)"""

        # Default to hash comments
        else:
            return """# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes."""

    def get_default_action(self) -> GuardAction:
        """Default to blocking to enforce Rule #0 compliance.

        Can be overridden for specific contexts (e.g., lint mode compatibility).
        """
        # Check if there's an override set (for lint mode compatibility)
        if hasattr(self, "_override_action"):
            return self._override_action
        return GuardAction.BLOCK
