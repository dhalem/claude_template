"""Directory awareness and test enforcement guards.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402
from utils.patterns import COMPLETION_PATTERNS, LOCATION_DEPENDENT_PATTERNS, matches_any_pattern  # noqa: E402


class DirectoryAwarenessGuard(BaseGuard):
    """Enforces directory verification before location-dependent commands."""

    def __init__(self):
        super().__init__(
            name="Directory Awareness", description="Enforces pwd verification for location-dependent commands"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        # Skip if command already starts with pwd (user is being safe)
        if context.command.strip().startswith("pwd"):
            return False

        return matches_any_pattern(context.command, LOCATION_DEPENDENT_PATTERNS)

    def get_message(self, context: GuardContext) -> str:
        return f"""📍 DIRECTORY AWARENESS: Location-dependent command detected!

Command: {context.command}

⚠️  RULE FROM CLAUDE.md:
  'ALWAYS run pwd before ANY command that could be location-dependent'

🗂️  PROJECT STRUCTURE REFERENCE:
  Root: spotidal/ (for ./run_tests.sh, ./curl_wrapper.sh, docker commands)
  Sonos: cd sonos_server
  AI Backend: cd gemini_playlist_suggester
  React App: cd gemini_playlist_suggester/react-app
  Workers: cd syncer
  Syncer v2: cd syncer_v2
  Monitoring: cd monitoring

💡 RECOMMENDED APPROACH:
  1. Run 'pwd' first to verify current directory
  2. Then run your location-dependent command
  3. Or use absolute paths to avoid ambiguity

This warning helps prevent running commands in the wrong directory."""

    def get_default_action(self) -> GuardAction:
        # This is more of a reminder, so allow by default but warn
        return GuardAction.ALLOW


class TestSuiteEnforcementGuard(BaseGuard):
    """Prevents completion claims without proper test execution."""

    def __init__(self):
        super().__init__(name="Test Suite Enforcement", description="Prevents completion claims without proper testing")

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        return matches_any_pattern(context.command, COMPLETION_PATTERNS)

    def get_message(self, context: GuardContext) -> str:
        return f"""🧪 TEST ENFORCEMENT: Completion claim detected!

Command: {context.command}

❌ RULE FROM CLAUDE.md:
  'NEVER claim work is complete without running the FULL containerized test suite'

🚫 FORBIDDEN PRACTICES:
  - Creating one-off test files (test_something.py)
  - Running individual tests and claiming success
  - Skipping test suite 'because it worked manually'
  - Saying 'tests should pass' without running them

📋 MANDATORY TEST COMMANDS BY SERVICE:

  SONOS SMAPI SERVER:
    cd sonos_server && ./run_full_test_suite.sh

  AI PLAYLIST SUGGESTER:
    cd gemini_playlist_suggester && ./run_all_real_integration_tests.sh

  REACT WEB APP:
    cd gemini_playlist_suggester/react-app && ./run-react-tests.sh all

  SYNCER V2 (Dagster):
    cd syncer_v2/integration_tests && ./run_integration_tests.sh --playlists 25

  WORKER SERVICES:
    cd syncer && ./run_worker_tests.sh

🏆 GOLDEN TESTING RULE - NO FEATURE IS COMPLETE UNTIL:
  ✅ API endpoints verified with ./curl_wrapper.sh
  ✅ Real service integration tested (not mocks)
  ✅ End-to-end user workflow validated
  ✅ Error scenarios tested and handled
  ✅ ACTUALLY RUNS - docker compose up must work
  ✅ NO LYING - Never claim work done without verifying execution
  ✅ COMMITTED TO GIT - Work isn't safe until committed
  ✅ FULL CONTAINERIZED TEST SUITE PASSES - ALL tests must pass

⚠️  WHY THIS MATTERS:
  Individual manual tests miss integration issues, race conditions,
  and edge cases. The containerized test suite catches problems
  that destroy production systems."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class PipInstallGuard(BaseGuard):
    """Prevents direct pip install commands and directs to requirements files."""

    def __init__(self):
        super().__init__(
            name="Pip Install Prevention",
            description="Directs pip install usage to requirements files for dependency management",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        command = context.command.lower().strip()

        # Patterns to detect pip install commands
        pip_patterns = [
            r"pip\s+install",
            r"pip3\s+install",
            r"python\s+-m\s+pip\s+install",
            r"python3\s+-m\s+pip\s+install",
        ]

        # Check if it's a pip install command
        for pattern in pip_patterns:
            if re.search(pattern, command):
                # Allow if it's installing from requirements file
                if any(req in command for req in ["-r requirements", "--requirement requirements", "requirements.txt"]):
                    return False
                # Allow if it's a system-wide tool installation with specific flags
                return not ("--user" in command or "--upgrade pip" in command)

        return False

    def get_message(self, context: GuardContext) -> str:
        # Extract package name if possible
        command = context.command
        package_match = re.search(r"install\s+([a-zA-Z0-9\-_\[\]<>=.]+)", command)
        package = package_match.group(1) if package_match else "package"

        return f"""📦 PIP INSTALL BLOCKED: Use requirements files for dependency management!

Command: {context.command}

❌ WHY DIRECT PIP INSTALL IS PROBLEMATIC:
  - No version pinning leads to inconsistent environments
  - Dependencies not tracked in version control
  - Different versions across team members/deployments
  - Breaks reproducible builds
  - Makes debugging dependency issues difficult
  - Docker builds won't include the package

✅ CORRECT APPROACH:

1. ADD TO REQUIREMENTS FILE:
   # For the main service, add to appropriate requirements.txt:
   echo "{package}" >> requirements.txt

   # Or with version pinning (recommended):
   echo "{package}==X.Y.Z" >> requirements.txt

2. FIND THE RIGHT REQUIREMENTS FILE:
   # List all requirements files:
   find . -name "requirements*.txt" -not -path "./venv/*" -not -path "./.venv/*"

   # Common locations:
   - ./requirements.txt (root)
   - ./requirements-dev.txt (dev dependencies)
   - ./sonos_server/requirements.txt
   - ./syncer/requirements.txt
   - ./gemini_playlist_suggester/requirements.txt

3. INSTALL FROM REQUIREMENTS:
   pip install -r requirements.txt

   # For development dependencies:
   pip install -r requirements-dev.txt

4. PIN EXACT VERSIONS (BEST PRACTICE):
   # Generate pinned versions:
   pip freeze | grep {package} >> requirements.txt

   # Or use pip-tools for better management:
   pip-compile requirements.in

5. UPDATE DOCKER IMAGE:
   # After updating requirements, rebuild containers:
   docker -c musicbot compose build <service>
   docker -c musicbot compose up -d <service>

💡 SPECIAL CASES:

- Installing pip itself: pip install --upgrade pip ✅ (allowed)
- User installations: pip install --user package ✅ (allowed)
- From requirements: pip install -r requirements.txt ✅ (allowed)
- Editable installs: pip install -e . (add to requirements-dev.txt)

🔧 FOR TEMPORARY TESTING:
If you absolutely need to test a package temporarily:
1. Use a virtual environment
2. Document why it's temporary
3. Add to requirements.txt before committing

📋 PRO TIP:
Use pip-tools for better dependency management:
- requirements.in (human-edited)
- requirements.txt (pip-compile generated)

This ensures consistent, reproducible environments across all deployments!"""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK
