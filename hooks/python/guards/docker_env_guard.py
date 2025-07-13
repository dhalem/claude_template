"""Guard to ensure Docker services have required .env files before launching.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402


class DockerEnvGuard(BaseGuard):
    """Prevents launching Docker services without required .env files."""

    def __init__(self):
        super().__init__(
            name="Docker Environment File Guard",
            description="Ensures Docker services have required .env files before launching",
        )

        # Map of service directories to their required .env files
        self.env_requirements = {
            "gemini_playlist_suggester": [".env"],
            "syncer": [".env"],
            "syncer_v2": [".env"],
            "monitoring": [],  # Some services may not need .env
            "sonos_server": [],  # SMAPI server uses config.py instead
        }

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        command = context.command.strip().lower()

        # Patterns that indicate Docker compose commands
        docker_patterns = [
            r"docker\s+-c\s+\w+\s+compose.*up",
            r"docker\s+compose.*up",
            r"docker-compose.*up",
            r"docker\s+-c\s+\w+\s+compose.*run",
            r"docker\s+compose.*run",
            r"docker-compose.*run",
        ]

        # Check if this is a docker compose up/run command
        for pattern in docker_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return self._check_env_files(context.command)

        return False

    def _check_env_files(self, command: str) -> bool:
        """Check if required .env files exist for the service being launched."""
        # Try to determine the current directory or service
        service_dir = self._detect_service_directory(command)

        if not service_dir:
            # Can't determine service, trigger to be safe
            return True

        # Check if this is a known service
        for service_name, required_files in self.env_requirements.items():
            if service_name in service_dir:
                # Check if all required .env files exist
                for env_file in required_files:
                    env_path = os.path.join(service_dir, env_file)
                    if not os.path.exists(env_path):
                        return True  # Missing required .env file
                break

        return False

    def _detect_service_directory(self, command: str) -> str:
        """Try to detect which service directory we're in."""
        # Check if command includes a -f flag with path
        compose_file_match = re.search(r"-f\s+([^\s]+docker-compose[^\s]*)", command)
        if compose_file_match:
            compose_path = compose_file_match.group(1)
            return os.path.dirname(compose_path)

        # Otherwise use current working directory
        cwd = os.getcwd()

        # Check if we're in a service subdirectory
        path_parts = cwd.split(os.sep)
        for service_name in self.env_requirements:
            if service_name in path_parts:
                # Find the service directory
                for i, part in enumerate(path_parts):
                    if part == service_name:
                        return os.sep.join(path_parts[: i + 1])

        return cwd

    def get_message(self, context: GuardContext) -> str:
        service_dir = self._detect_service_directory(context.command)
        service_name = "unknown"
        missing_files = []

        # Determine which service and what's missing
        if service_dir:
            for svc_name, required_files in self.env_requirements.items():
                if svc_name in service_dir:
                    service_name = svc_name
                    for env_file in required_files:
                        env_path = os.path.join(service_dir, env_file)
                        if not os.path.exists(env_path):
                            missing_files.append(env_file)
                    break

        if not missing_files:
            missing_files = [".env"]  # Default if we can't determine

        return f"""🚫 DOCKER ENV FILE MISSING: Cannot launch without environment configuration!

Command: {context.command}
Service: {service_name}
Missing: {', '.join(missing_files)}

❌ PROBLEM: Launching Docker services without .env files causes:
  - Missing API keys (services fail to start)
  - Wrong database connections
  - Authentication failures
  - Services crash on startup
  - Hours of debugging "why isn't it working?"

✅ CORRECT APPROACH:

1. CHECK FOR SAMPLE FILE:
   # Most services provide a sample.env or .env.example
   ls -la | grep -E "(sample.env|.env.example|.env.sample)"

2. CREATE .ENV FROM SAMPLE:
   # Copy and edit the sample file
   cp sample.env .env
   # OR
   cp .env.example .env

3. CONFIGURE REQUIRED VALUES:
   # Edit .env and set required values:
   vim .env

   # Common required settings:
   - Database credentials (ENV_DB_HOST, ENV_DB_PASSWORD)
   - API keys (GOOGLE_API_KEY, OPENAI_API_KEY, etc.)
   - Service URLs (SPOTIFY_CLIENT_ID, etc.)
   - Port configurations

4. VERIFY .ENV EXISTS:
   ls -la .env
   # Should show the file with proper permissions

5. THEN LAUNCH:
   {context.command}

📋 SERVICE-SPECIFIC REQUIREMENTS:

**gemini_playlist_suggester**:
  - Needs: .env with API keys (Google, OpenAI, Anthropic, etc.)
  - Check: gemini_playlist_suggester/sample.env

**syncer**:
  - Needs: .env with Spotify/Tidal credentials
  - Check: syncer/.env.example

**syncer_v2**:
  - Needs: .env for Dagster configuration
  - Check: syncer_v2/.env.example

💡 SECURITY TIPS:
  - Never commit .env files (should be in .gitignore)
  - Use strong passwords for database connections
  - Keep API keys secure and rotate regularly
  - Different .env files for dev/staging/production

⚠️ WHY THIS MATTERS:
Without proper .env configuration, services either fail to start
or run with wrong settings, leading to data corruption, failed
API calls, and hours of debugging mysterious failures."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.BLOCK
