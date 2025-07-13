"""Path and navigation safety guards.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import re
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402


class AbsolutePathCdGuard(BaseGuard):
    """Enforces absolute paths for cd commands to prevent navigation confusion."""

    def __init__(self):
        """Initialize the AbsolutePathCdGuard."""
        super().__init__(
            name="Absolute Path CD", description="Requires absolute paths for cd commands to prevent getting lost"
        )

        # Pattern to match cd commands with relative paths
        # Matches cd followed by something that doesn't start with:
        # - / (absolute path)
        # - ~ (home directory)
        # - $ (variable expansion)
        # - - (cd -)
        self.cd_relative_pattern = re.compile(r"\bcd\s+(?![/~$-])[^\s;&|]+", re.IGNORECASE)

        # Allowed exceptions for common safe operations
        self.safe_cd_patterns = [
            re.compile(r"\bcd\s*$", re.IGNORECASE),  # cd (go home)
            re.compile(r"\bcd\s*[;&|]", re.IGNORECASE),  # cd followed by command separator
        ]

    def should_trigger(self, context: GuardContext) -> bool:
        """Check if the guard should trigger for this command."""
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        # Split command into individual commands separated by &&, ||, ; or |
        # This helps avoid matching cd patterns within strings or complex commands
        command_parts = re.split(r"[;&|]", context.command)

        for part in command_parts:
            part = part.strip()
            # Only check parts that actually start with cd
            if re.match(r"\s*cd\s+", part, re.IGNORECASE):
                # Check if it's a cd command with relative path
                if self.cd_relative_pattern.search(part):
                    # Check if this specific part is a safe cd pattern
                    if not any(safe_pattern.search(part) for safe_pattern in self.safe_cd_patterns):
                        return True

        return False

    def get_message(self, context: GuardContext) -> str:
        """Get the user message for when the guard is triggered."""
        return f"""🧭 ABSOLUTE PATH REQUIRED: Relative cd command detected!

Command: {context.command}

⚠️  DIRECTORY NAVIGATION SAFETY RULE:
  'Always use absolute paths for cd commands to prevent getting lost'

❌ PROBLEMATIC PATTERNS:
  cd subdir              # Relative path - where are we going?
  cd ../other            # Relative navigation - unpredictable
  cd some/nested/path    # Relative path - depends on current location

✅ SAFE ALTERNATIVES:
  cd /absolute/path/to/target
  cd ~/project/subdir
  cd $HOME/project/subdir
  cd /home/dhalem/github/sptodial_one/spotidal/subdir

✅ ALLOWED EXCEPTIONS:
  cd -      # Go back to previous directory
  cd        # Go to home directory
  cd ~      # Go to home directory
  cd $HOME  # Go to home directory

🗂️  COMMON ABSOLUTE PATHS FOR THIS PROJECT:
  cd /home/dhalem/github/sptodial_one/spotidal                    # Repository root
  cd /home/dhalem/github/sptodial_one/spotidal/sonos_server       # Sonos SMAPI
  cd /home/dhalem/github/sptodial_one/spotidal/syncer             # Workers
  cd /home/dhalem/github/sptodial_one/spotidal/gemini_playlist_suggester  # AI Backend

💡 RECOMMENDED APPROACH:
  1. Use 'pwd' to verify current location
  2. Use absolute paths for cd commands
  3. This prevents navigation confusion and lost sessions

This guard helps maintain directory awareness and prevents unexpected navigation."""

    def get_default_action(self) -> GuardAction:
        """Return the default action for this guard."""
        # Block relative cd commands as they can cause navigation confusion
        return GuardAction.BLOCK


class CurlHeadRequestGuard(BaseGuard):
    """Prevents inefficient curl HEAD requests that waste time."""

    def __init__(self):
        """Initialize the CurlHeadRequestGuard."""
        super().__init__(
            name="Curl HEAD Request Prevention",
            description="Prevents inefficient curl HEAD requests that rarely provide useful information",
        )

        # Pattern to match curl commands with HEAD requests
        # Match curl (including ./curl_wrapper.sh) followed by HEAD request flags
        self.curl_head_patterns = [
            re.compile(r"\bcurl[^\s]*\s+.*?-I\b", re.IGNORECASE),  # curl -I (HEAD method)
            re.compile(r"\bcurl[^\s]*\s+.*?--head\b", re.IGNORECASE),  # curl --head
            re.compile(r"\bcurl[^\s]*\s+.*?-X\s+HEAD\b", re.IGNORECASE),  # curl -X HEAD
            re.compile(r"\bcurl[^\s]*\s+.*?--request\s+HEAD\b", re.IGNORECASE),  # curl --request HEAD
        ]

        # Exceptions where HEAD might be legitimate
        # Match specific health check URL patterns, not just any occurrence
        self.legitimate_head_patterns = [
            re.compile(r"/health[_-]?check", re.IGNORECASE),  # /health-check, /health_check
            re.compile(r"/ping\b", re.IGNORECASE),  # /ping endpoint
            re.compile(r"/status\b", re.IGNORECASE),  # /status endpoint (not just 'status' anywhere)
            re.compile(r"/alive\b", re.IGNORECASE),  # /alive endpoint
            re.compile(r"/healthz\b", re.IGNORECASE),  # /healthz (Kubernetes style)
        ]

    def should_trigger(self, context: GuardContext) -> bool:
        """Check if the guard should trigger for this command."""
        if context.tool_name != "Bash":
            return False
        if not context.command:
            return False

        # Check if it's a curl command with HEAD request
        has_head_request = any(pattern.search(context.command) for pattern in self.curl_head_patterns)
        if not has_head_request:
            return False

        # Allow legitimate HEAD requests for health checks
        is_legitimate = any(pattern.search(context.command) for pattern in self.legitimate_head_patterns)
        return not is_legitimate

    def get_message(self, context: GuardContext) -> str:
        """Get the user message for when the guard is triggered."""
        return f"""🚫 INEFFICIENT HEAD REQUEST: curl HEAD request detected!

Command: {context.command}

⚠️  WHY HEAD REQUESTS WASTE TIME:
  - HEAD responses often lack useful debugging information
  - You frequently follow up with GET requests anyway
  - Most APIs return minimal headers that don't help troubleshooting
  - Time spent on HEAD + GET > time spent on just GET

❌ PROBLEMATIC PATTERNS:
  curl -I http://server/api/endpoint          # Gets headers only, then you need data
  curl --head http://server/status            # Limited info, follow with GET anyway
  curl -X HEAD http://server/healthcheck      # Just do GET for complete response

✅ MORE EFFICIENT ALTERNATIVES:
  curl -s http://server/api/endpoint          # Get full response immediately
  curl -v http://server/api/endpoint          # Verbose mode shows headers + body
  curl -i http://server/api/endpoint          # Include headers in output with body
  ./curl_wrapper.sh -s http://server/endpoint # Use project wrapper script

✅ LEGITIMATE HEAD REQUEST EXCEPTIONS:
  - Health check endpoints where you only need status code
  - Testing if large resources exist before downloading
  - Checking Last-Modified headers for caching

💡 RECOMMENDED APPROACH:
  1. Start with GET request to see full response
  2. Use -v flag if you need to see headers and timing
  3. Use -i flag to include headers with response body
  4. Only use HEAD when you specifically need just headers

This guard prevents the common pattern of "let me check headers first"
that usually leads to needing the full response anyway."""

    def get_default_action(self) -> GuardAction:
        """Return the default action for this guard."""
        # Block inefficient HEAD requests by default
        return GuardAction.BLOCK
