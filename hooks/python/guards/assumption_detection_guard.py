# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations

"""Guard to detect assumption-based language that indicates operating from memory.

This guard helps prevent Claude from making dangerous assumptions rather than
verifying current state, which has led to real harm in the past.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402


class AssumptionDetectionGuard(BaseGuard):
    """Detects assumption-based language that indicates operating from memory rather than verification."""

    # Patterns that indicate Claude is making assumptions
    ASSUMPTION_PATTERNS = [
        r"\bI know\b",  # Matches "I know", "I know that", "I know this", etc.
        r"\bAs I mentioned\b",
        r"\bI'm familiar with\b",
        r"\bBased on my understanding\b",
        r"\bI'll just quickly\b",
        r"\bI already\b",
        r"\bI recently\b",
        r"\bFrom what I remember\b",
        r"\bIf I recall\b",
        r"\bI believe\b",
        r"\bI think I\b",
        r"\bI assume\b",
        r"\bI'm assuming\b",
        r"\bI'm pretty sure\b",
        r"\bI'm confident that\b",
        r"\bObviously\b",
        r"\bOf course\b",
        r"\bClearly\b(?![- ]defined)",  # Exclude "Clearly-defined"
        r"\bIt's clear that\b",
        r"\bWe know that\b",
        r"\bIt's well known\b",
        r"\bEveryone knows\b",
        r"\bAs we discussed\b",
        r"\bAs I said\b",
        r"\bLike I mentioned\b",
        r"\bI'm certain\b",
        r"\bWithout a doubt\b",
        r"\bDefinitely\b",
        r"\bSurely\b",
        r"\bMust be\b",
        r"\bHas to be\b",
        r"\bShould be\b",
        r"\bProbably\b",
        r"\bLikely\b",
        r"\bI expect\b",
        r"\bI imagine\b",
        r"\bI suppose\b",
        r"\bI presume\b",
        r"\bPresuming\b",
        r"\bAssuming\b",
    ]

    def __init__(self):
        super().__init__(
            name="Assumption Detection Guard",
            description="Detects language indicating assumptions rather than verification",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        """Trigger on any tool that involves Claude's responses."""
        # Check all tools where Claude might write assumption-based text
        return context.tool_name in ["Write", "Edit", "MultiEdit", "Bash"]

    def get_message(self, context: GuardContext) -> str:
        """Analyze content for assumption patterns."""
        content = self._extract_content(context)
        if not content:
            return ""

        detected_patterns = []
        for pattern in self.ASSUMPTION_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                detected_patterns.extend(matches)

        if not detected_patterns:
            return ""

        # Build warning message
        unique_patterns = list(set(detected_patterns))[:5]  # Show max 5 examples

        return f"""🚨 ASSUMPTION LANGUAGE DETECTED

You're using phrases that indicate assumptions rather than verification:
{chr(10).join(f'  ❌ "{p}"' for p in unique_patterns)}

⚠️  PROBLEM: These phrases suggest you're operating from memory instead of checking current state.

✅ REQUIRED ACTIONS:
1. Read CLAUDE.md COMPLETELY before continuing
2. Verify the current state with appropriate tools
3. Base your response on fresh verification, not memory
4. Replace assumptions with facts from actual checks

📋 EXAMPLES OF BETTER APPROACHES:
- Instead of "I know that X" → Check and say "I verified that X"
- Instead of "I believe Y" → Test and say "Testing shows Y"
- Instead of "Obviously Z" → Explain "Z because [specific evidence]"
- Instead of "I recently saw" → Re-check and say "Current state shows"

🔍 Rule #0 states: "ASSUMPTIONS KILL PROJECTS - Check current state"

⚠️  This guard helps prevent the arrogance of assuming without verifying.
Real harm has occurred from acting on assumptions instead of facts."""

    def _extract_content(self, context: GuardContext) -> str:
        """Extract text content from the context based on tool type."""
        if context.tool_name == "Write":
            return context.tool_input.get("content", "")
        elif context.tool_name in ["Edit", "MultiEdit"]:
            if context.tool_name == "Edit":
                return context.tool_input.get("new_string", "")
            else:  # MultiEdit
                edits = context.tool_input.get("edits", [])
                return " ".join(edit.get("new_string", "") for edit in edits)
        elif context.tool_name == "Bash":
            # Check bash commands for assumption-based comments
            return context.command or ""
        return ""

    def get_default_action(self) -> GuardAction:
        """Default to warning (non-blocking) to educate rather than frustrate."""
        return GuardAction.ALLOW
