"""Docker-related safety guards.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext, GuardResult  # noqa: E402
from utils.patterns import (  # noqa: E402
    DOCKER_RESTART_PATTERNS,
    DOCKER_SAFE_COMMANDS,
    DOCKER_WITHOUT_COMPOSE_PATTERN,
    matches_any_pattern,
)


class DockerRestartGuard(BaseGuard):
    """Prevents catastrophic use of docker restart after code changes."""

    def __init__(self):
        super().__init__(name="Docker Restart Prevention", description="Stops catastrophic restart after code changes")

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        command = context.command.strip()

        # Skip comments
        if command.startswith("#"):
            return False

        # Skip if docker restart is in a string (grep, echo, etc)
        words = command.split()
        if words and words[0].lower() in ["grep", "echo", "cat", "vim", "sed", "awk"]:
            return False

        return matches_any_pattern(context.command, DOCKER_RESTART_PATTERNS)

    def get_message(self, context: GuardContext) -> str:
        return f"""🚨 CRITICAL ERROR: Docker restart detected after code changes!

Command: {context.command}

❌ WHY THIS IS CATASTROPHIC:
  - 'docker restart' only stops/starts containers with EXISTING images
  - Your code changes are NOT loaded into the running container
  - This previously broke entire SMAPI service (June 30, 2025)
  - Hours of debugging required to recover from this mistake

✅ CORRECT PROCEDURE AFTER CODE CHANGES:
  1. docker -c musicbot compose build service-name
  2. docker -c musicbot compose up -d service-name
  3. Test that your changes actually work

🔍 VERIFICATION REQUIRED:
  - Check logs: docker -c musicbot compose logs service-name
  - Test API: ./curl_wrapper.sh -s http://musicbot:PORT/endpoint

💡 Quick status check:
  docker -c musicbot compose ps

⚠️  Why this rule exists:
  Docker restart has broken entire services in this project.
  It only stops/starts containers with EXISTING images."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class DockerWithoutComposeGuard(BaseGuard):
    """Enforces docker-compose usage for container management."""

    def __init__(self):
        super().__init__(
            name="Docker Without Compose Prevention",
            description="Enforces docker-compose usage for container management",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        command = context.command.strip()

        # Skip comments
        if command.startswith("#"):
            return False

        # Skip if docker is in a string (grep, echo, etc)
        words = command.split()
        if words and words[0].lower() in ["grep", "echo", "cat", "vim", "sed", "awk"]:
            return False

        # Check if it's a docker command without compose
        if not DOCKER_WITHOUT_COMPOSE_PATTERN.search(command):
            return False

        # Allow safe commands
        return not DOCKER_SAFE_COMMANDS.search(command)

    def get_message(self, context: GuardContext) -> str:
        return f"""🚨 DOCKER WITHOUT COMPOSE DETECTED: Use docker-compose instead!

Command: {context.command}

WHY THIS IS BLOCKED:
  - Direct docker commands bypass docker-compose.yml configuration
  - Can create orphaned containers outside of compose management
  - Ignores network, volume, and dependency configurations
  - Makes debugging and maintenance extremely difficult
  - Previously caused SMAPI service breakage (June 30, 2025)

MANDATORY DOCKER PROTOCOL (from CLAUDE.md):
  - ALWAYS use docker-compose for container management
  - NEVER create ad-hoc containers with 'docker run'
  - NEVER bypass docker-compose for service operations

CORRECT COMMANDS:
  Instead of: docker run ...
  Use: docker -c musicbot compose run ...

  Instead of: docker start/stop container_name
  Use: docker -c musicbot compose start/stop service_name

  Instead of: docker create ...
  Use: Define service in docker-compose.yml

  Instead of: docker build ...
  Use: docker -c musicbot compose build service_name

ALLOWED EXCEPTIONS:
  - docker ps (viewing containers)
  - docker logs (checking logs)
  - docker container access (for debugging)
  - docker images (listing images)
  - docker system prune (cleanup)

💡 Why this rule exists:
  Ad-hoc docker commands have broken the entire system.
  Docker-compose ensures proper configuration and dependencies."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK


class ContainerStateGuard(BaseGuard):
    """Suggests container verification when debugging missing files that might exist locally but not in containers."""

    def __init__(self):
        super().__init__(
            name="Container State Verification",
            description="Suggests checking container contents before assuming file debugging issues",
        )

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        command = context.command.lower()

        # Trigger on file-related debugging patterns
        debugging_patterns = [
            r"file.*not.*found",
            r"missing.*file",
            r"cannot.*find",
            r"no.*such.*file",
            r".*\.(py|js|json|yaml|yml|css|html).*not.*found",
            r"import.*error",
            r"module.*not.*found",
            r"ls.*\|.*grep.*missing",
            r"find.*-name.*missing",
            r"where.*is.*file",
            r"check.*if.*exists",
            r"verify.*file.*exists",
        ]

        # Also trigger on common debugging commands that suggest file issues
        debugging_indicators = [
            "file not found",
            "missing file",
            "cannot find",
            "no such file",
            "where is",
            "find . -name",
            "find / -name",
            "import error",
            "module not found",
            "ls -la",
            "ls -l",
            "which",
            "whereis",
            "locate",
        ]

        # Check patterns first
        for pattern in debugging_patterns:
            if re.search(pattern, command):
                return True

        # Check if command contains debugging indicators
        return any(indicator in command for indicator in debugging_indicators)

    def get_message(self, context: GuardContext) -> str:
        return f"""🐳 CONTAINER STATE CHECK SUGGESTED: Before file debugging!

Command: {context.command}

⚠️ COMMON PATTERN: Files exist locally but missing in containers

🔍 MANDATORY 2-MINUTE VERIFICATION (saves 2-3 hours):

1. CHECK CONTAINER CONTENTS FIRST:
   docker -c musicbot exec <service_name> ls -la /path/to/expected/file
   docker -c musicbot exec <service_name> find /app -name "filename*"

2. VERIFY CONTAINER IS RUNNING EXPECTED IMAGE:
   docker -c musicbot ps
   docker -c musicbot images | grep <service_name>

3. CHECK VOLUME MOUNTS (if applicable):
   docker -c musicbot inspect <container_name> | grep -A10 "Mounts"

4. REBUILD IF CODE CHANGES NOT REFLECTED:
   docker -c musicbot compose build <service_name>
   docker -c musicbot compose up -d <service_name>

💡 WHY THIS MATTERS:
- Container-State-First Debugging saves 2-3 hours per debugging cycle
- Local files ≠ container files (different environments)
- Volume mounts may not be working as expected
- Old container images may be running (before your changes)

🚨 BATTLE-TESTED PATTERN:
This guard exists because debugging locally often wastes hours when the
issue is simply that files don't exist in the container environment.

✅ AFTER CONTAINER VERIFICATION:
If files exist in container, then proceed with local debugging."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.ALLOW  # Don't block, just provide helpful guidance

    def check(self, context: GuardContext, is_interactive: bool = False) -> GuardResult:
        """Override check method to provide suggestion without blocking."""
        if not self.should_trigger(context):
            return GuardResult(should_block=False)

        message = self.get_message(context)
        # Return suggestion without blocking (should_block=False)
        return GuardResult(should_block=False, message=message)
