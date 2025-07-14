"""Guard to ensure Python scripts are run using the venv Python binary."""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402


class PythonVenvGuard(BaseGuard):
    """Ensures Python scripts are run using the venv Python binary."""

    def __init__(self):
        super().__init__(
            name="Python Venv Enforcement",
            description="Ensures Python scripts are run using the venv Python binary",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        command = context.command.strip()

        # Skip git commit commands - they may contain "python" in commit messages
        if "git commit" in command.lower():
            return False

        # Skip other commands that commonly contain "python" in text but don't execute Python
        excluded_commands = [
            r"^grep\s+",  # grep commands
            r"^find\s+",  # find commands
            r"^sed\s+",   # sed commands
            r"^awk\s+",   # awk commands
        ]

        for pattern in excluded_commands:
            if re.search(pattern, command, re.IGNORECASE):
                return False

        # Special case: echo/cat commands that don't pipe to python
        if re.search(r"^(echo|cat)\s+", command, re.IGNORECASE) and not re.search(r"\|\s*python3?", command, re.IGNORECASE):
            return False

        # Patterns that indicate running Python scripts without venv
        python_patterns = [
            r"(^|[;&|]|\s)\s*python\s+",  # python at start or after separators
            r"(^|[;&|]|\s)\s*python3\s+",  # python3 at start or after separators
            r"(^|[;&|]|\s)\s*python3\.\d+\s+",  # python3.11 at start or after separators
            r"\|\s*python($|\s)",  # piped to python
            r"\|\s*python3($|\s)",  # piped to python3
            r";\s*python($|\s)",  # after semicolon
            r";\s*python3($|\s)",  # after semicolon
            r"&&\s*python($|\s)",  # after &&
            r"&&\s*python3($|\s)",  # after &&
            r"\bpython\s+\S+\.py\b",  # python script.py anywhere
            r"\bpython3\s+\S+\.py\b",  # python3 script.py anywhere
        ]

        # Check if any pattern matches
        for pattern in python_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                # Check if it's already using venv path
                if "venv/bin/python" in command:
                    return False
                # Check if it's a system command we should allow
                return not self._is_allowed_system_command(command)

        return False

    def _is_allowed_system_command(self, command: str) -> bool:
        """Check if this is an allowed system Python command."""
        allowed_patterns = [
            r"python\s+-m\s+venv",  # Creating venv
            r"python3\s+-m\s+venv",  # Creating venv
            r"python\s+--version",  # Checking version
            r"python3\s+--version",  # Checking version
            r"python\s+-V",  # Checking version
            r"python3\s+-V",  # Checking version
            r"which\s+python",  # Checking which python
            r"whereis\s+python",  # Finding python
            r"type\s+python",  # Checking python type
        ]

        return any(re.search(pattern, command, re.IGNORECASE) for pattern in allowed_patterns)

    def get_message(self, context: GuardContext) -> str:
        # Try to extract the script name
        script_match = re.search(r"python3?\s+([^\s]+\.py)", context.command)
        script_name = script_match.group(1) if script_match else "script.py"

        return f"""🐍 PYTHON VENV ENFORCEMENT: Use venv Python binary!

Command: {context.command}

❌ PROBLEM: Running Python directly without activated venv

⚠️  CRITICAL ISSUES:
  - Wrong Python interpreter (system vs venv)
  - Missing project dependencies
  - Inconsistent package versions
  - Import errors for project modules
  - Different behavior than production

✅ CORRECT APPROACH:

1. ACTIVATE VENV FIRST (MANDATORY):
   cd /home/dhalem/github/sptodial_one/spotidal
   [ ! -d "venv" ] && ./setup-venv.sh  # Setup if needed
   source venv/bin/activate
   which python3  # Should show: ./venv/bin/python3

2. THEN RUN YOUR SCRIPT:
   python3 {script_name}  # Now uses venv Python

3. OR USE FULL PATH (if activation not possible):
   ./venv/bin/python3 {script_name}

📋 VENV CONTAINS CRITICAL PACKAGES:
  - SoCo 0.28.0 (Sonos integration)
  - MySQL connector (database access)
  - Testing tools (pytest, etc.)
  - Linting tools (ruff, black, mypy)
  - All requirements.txt dependencies

🔍 TO VERIFY VENV IS ACTIVE:
   which python3
   # Should output: /home/dhalem/github/sptodial_one/spotidal/venv/bin/python3
   # NOT: /usr/bin/python3

💡 PRO TIP: Add this to your session start:
   cd /home/dhalem/github/sptodial_one/spotidal && source venv/bin/activate

⚠️  WHY THIS MATTERS:
Without venv, you're using system Python which lacks project
dependencies, uses wrong versions, and behaves differently than
the production environment. This wastes hours debugging "missing"
packages and inconsistent behavior."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK
