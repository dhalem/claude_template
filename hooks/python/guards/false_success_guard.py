# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations

"""Guard to detect false success claims without proper verification evidence.

This guard helps prevent Claude from claiming success (like "works perfectly",
"all tests pass") without providing actual evidence of verification, which has
led to real harm in the past.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402


class FalseSuccessGuard(BaseGuard):
    """Detects false success claims that lack proper verification evidence."""

    # Patterns that indicate claims of success
    SUCCESS_PATTERNS = [
        r"\bworks?(?:\s+perfectly|(?:\s+(?:correctly|fine|well|great|properly))?)?\b",
        r"\bsuccessfully\s+(?:implemented|completed|tested|fixed|resolved|deployed)\b",
        r"\beverything\s+(?:is\s+)?(?:working|works|fine|good|ready)\b",
        r"\ball\s+tests?\s+(?:pass(?:ed|ing)?|succeed(?:ed|ing)?)\b",
        r"\bverified\s+(?:and\s+)?(?:working|functional|correct)\b",
        r"\bconfirmed\s+(?:working|functional|correct|success)\b",
        r"\btested\s+(?:and\s+)?(?:working|functional|passing)\b",
        r"\bready\s+(?:to\s+(?:go|deploy|use|merge))\b",
        r"\bproblem\s+(?:is\s+)?(?:solved|fixed|resolved)\b",
        r"\bissue\s+(?:is\s+)?(?:resolved|fixed|solved)\b",
        r"\bbug\s+(?:is\s+)?(?:fixed|resolved|eliminated)\b",
        r"\b(?:fully|completely)\s+(?:working|functional|implemented|tested)\b",
        r"\bno\s+(?:issues?|problems?|errors?)\b",
        r"\bshould\s+(?:be\s+)?(?:working|good|fine)\s+now\b",
        r"\b(?:looks?|seems?|appears?)\s+(?:good|fine|working|correct|like\s+it\s+works?|to\s+(?:be\s+)?working)(?:\s+(?:to\s+me|now))?\b",
        r"\bvalidated\s+(?:and\s+)?(?:working|correct)\b",
        r"\bdeployed\s+successfully\b",
        r"\bmission\s+accomplished\b",
        r"\btask\s+(?:is\s+)?(?:complete|done|finished)\b",
        r"\bfeature\s+(?:is\s+)?(?:complete|ready|working)\b",
        r"\bimplementation\s+(?:is\s+)?(?:complete|ready|working)\b",
        r"\bshould\s+work\s+(?:fine|correctly|properly|well)\b",
        r"\bprobably\s+works?\s+(?:now|fine|correctly)\b",
    ]

    # Patterns that indicate proper verification evidence
    EVIDENCE_PATTERNS = [
        r"```[\s\S]*?```",  # Code blocks with output
        r"\$.*\n.*",  # Command line output
        r"\b(?:PASSED|FAILED|ERROR|OK)\b",  # Test results
        r"exit\s+code:\s*\d+",  # Exit codes
        r"status:\s*\d+",  # HTTP status codes
        r"test.*(?:passed|failed)",  # Test descriptions
        r"assertion.*(?:passed|failed)",  # Assertion results
        r"benchmark.*\d+",  # Performance metrics
        r"coverage.*\d+%",  # Coverage metrics
        r"error.*count:\s*\d+",  # Error counts
        r"response.*time:\s*\d+",  # Response times
        r"memory.*usage:\s*\d+",  # Resource usage
        r"(?:before|after):\s*\d+",  # Before/after metrics
        r"✓.*\d+",  # Checkmarks with counts
        r"❌.*\d+",  # Error marks with counts
        r"⚠️.*\d+",  # Warning marks with counts
        r"(?:see|check|view|run):\s*\w+",  # References to verification commands
        r"screenshot.*shows",  # Visual evidence
        r"log.*shows",  # Log evidence
        r"output.*confirms",  # Output confirmation
    ]

    def __init__(self):
        super().__init__(
            name="False Success Detection Guard",
            description="Detects success claims without proper verification evidence",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        """Trigger on tools where Claude might make false success claims."""
        return context.tool_name in ["Write", "Edit", "MultiEdit", "Bash"]

    def get_message(self, context: GuardContext) -> str:
        """Analyze content for success claims without evidence."""
        content = self._extract_content(context)
        if not content:
            return ""

        # Find success claims
        success_claims = []
        for pattern in self.SUCCESS_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                success_claims.extend(matches)

        if not success_claims:
            return ""

        # Check for verification evidence
        has_evidence = self._has_verification_evidence(content)

        if has_evidence:
            # Has both claims and evidence - this is good!
            return ""

        # Success claims without evidence - this is problematic
        unique_claims = list(set(success_claims))[:5]  # Show max 5 examples

        return f"""🚨 FALSE SUCCESS CLAIM DETECTED

You're claiming success without providing verification evidence:
{chr(10).join(f'  ❌ "{claim}"' for claim in unique_claims)}

⚠️  PROBLEM: Success claims without evidence have caused REAL HARM in the past.

📋 FROM POSTMORTEMS:
- "The guard works perfectly" → Guard was completely non-functional
- "All tests pass" → Tests were never actually run
- "Successfully implemented" → Feature broken in production
- "Verified and working" → Based on invalid testing

✅ REQUIRED EVIDENCE (include at least ONE):
1. **Actual test output** with PASS/FAIL results
2. **Command execution results** showing exit codes
3. **Screenshots** of working functionality
4. **Log excerpts** showing successful operations
5. **Performance metrics** (timing, coverage, etc.)
6. **Error counts** showing reduction/elimination
7. **Before/after comparisons** with measurable improvements

📋 EXAMPLES OF PROPER VERIFICATION:
- "Tests pass: ✓ 15 passed, 0 failed (see output above)"
- "Command succeeded: exit code 0" + actual command output
- "Performance improved: 30s → 0.1s (see benchmark results)"
- "Zero errors found in log scan (see error count: 0)"

🔍 Rule #0 states: "TRUST BUT VERIFY - Evidence required"

⚠️  This guard prevents the dangerous pattern of claiming success
without proof, which has led to production failures and broken features.

💡 QUICK FIX: Add evidence of your success claim before proceeding."""

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
            # Check bash commands and descriptions for success claims
            return context.command or ""
        return ""

    def _has_verification_evidence(self, content: str) -> bool:
        """Check if content contains actual verification evidence."""
        for pattern in self.EVIDENCE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    def get_default_action(self) -> GuardAction:
        """Default to warning (non-blocking) to educate rather than frustrate."""
        return GuardAction.ALLOW
