# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Base classes for the Claude Code hook guard system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class GuardAction(Enum):
    """Possible actions a guard can take."""

    ALLOW = "allow"
    BLOCK = "block"


@dataclass
class GuardContext:
    """Context information passed to guards for decision making."""

    tool_name: str
    tool_input: Dict[str, Any]
    command: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    new_string: Optional[str] = None
    raw_input: Dict[str, Any] = None

    @classmethod
    def from_claude_input(cls, input_json: Dict[str, Any]) -> "GuardContext":
        """Create a GuardContext from Claude Code hook input."""
        tool_name = input_json.get("tool_name", "")
        tool_input = input_json.get("tool_input", {})

        # Extract common fields
        command = tool_input.get("command")
        file_path = tool_input.get("file_path")
        content = tool_input.get("content")
        new_string = tool_input.get("new_string")

        # Handle MultiEdit edits array
        if tool_name == "MultiEdit" and "edits" in tool_input:
            # Combine all new_strings for pattern matching
            new_strings = []
            for edit in tool_input.get("edits", []):
                if "new_string" in edit:
                    new_strings.append(edit["new_string"])
            if new_strings:
                new_string = "\n".join(new_strings)
            else:
                # Empty edits array should have empty string, not None
                new_string = ""

        return cls(
            tool_name=tool_name,
            tool_input=tool_input,
            command=command,
            file_path=file_path,
            content=content,
            new_string=new_string,
            raw_input=input_json,
        )


@dataclass
class GuardResult:
    """Result of a guard check."""

    should_block: bool
    message: Optional[str] = None
    exit_code: int = 0

    def __post_init__(self):
        """Set exit code based on should_block."""
        if self.should_block:
            self.exit_code = 2  # Critical: exit 2 blocks, exit 1 doesn't!


class BaseGuard(ABC):
    """Abstract base class for all guards."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def check_override(self, context: GuardContext) -> bool:
        """Check if a valid override code is provided via HOOK_OVERRIDE_CODE environment variable.

        Returns:
            bool: True if override is valid and should allow the command, False otherwise
        """
        import os

        override_code = os.environ.get('HOOK_OVERRIDE_CODE')
        if not override_code:
            return False

        # Validate TOTP code
        if self._validate_totp(override_code):
            self._log_override(context, override_code)
            return True

        # Log failed override attempt
        self._log_failed_override(context, override_code)
        return False

    def _validate_totp(self, code: str) -> bool:
        """Validate TOTP code using pyotp.

        Args:
            code: 6-digit TOTP code from Google Authenticator

        Returns:
            bool: True if code is valid, False otherwise
        """
        import os

        try:
            # Try to import pyotp, fall back to simple validation if not available
            try:
                import pyotp
            except ImportError:
                # For testing/development without pyotp installed
                # This should be removed in production
                return self._validate_simple_totp(code)

            # Get TOTP secret from environment
            totp_secret = os.environ.get('HOOK_OVERRIDE_SECRET')
            if not totp_secret:
                return False

            # Create TOTP instance and validate
            totp = pyotp.TOTP(totp_secret)

            # Check current and previous window (allows for clock skew)
            return totp.verify(code, valid_window=1)

        except Exception:
            # If anything goes wrong with TOTP validation, fail safely
            return False

    def _validate_simple_totp(self, code: str) -> bool:
        """Simple TOTP validation for development/testing without pyotp.

        This is a basic implementation that should be replaced with proper
        pyotp validation in production.
        """
        import base64
        import hashlib
        import hmac
        import os
        import struct
        import time

        try:
            # Get secret from environment
            secret = os.environ.get('HOOK_OVERRIDE_SECRET')
            if not secret:
                return False

            # Simple validation - check if code matches expected format
            if not code.isdigit() or len(code) != 6:
                return False

            # For development: accept a test code
            if secret == "TESTKEY" and code == "123456":
                return True

            # Basic TOTP algorithm implementation
            secret_bytes = base64.b32decode(secret.upper() + '=' * (-len(secret) % 8))
            time_step = int(time.time() // 30)

            # Check current time step and one before/after
            for offset in [-1, 0, 1]:
                msg = struct.pack('>Q', time_step + offset)
                hmac_hash = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
                offset_bits = hmac_hash[-1] & 0xf
                truncated = struct.unpack('>I', hmac_hash[offset_bits:offset_bits + 4])[0]
                truncated &= 0x7fffffff
                totp_code = str(truncated % 1000000).zfill(6)

                if code == totp_code:
                    return True

            return False

        except Exception:
            # If anything goes wrong, fail safely
            return False

    def _log_override(self, context: GuardContext, code: str) -> None:
        """Log successful override usage for audit purposes."""
        import datetime
        import json
        import os

        try:
            log_entry = {
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "event": "hook_override_successful",
                "guard": self.name,
                "tool": context.tool_name,
                "command": context.command,
                "file_path": context.file_path,
                "code_used": code[-3:] + "***",  # Only log last 3 digits for security
                "context": {
                    "working_directory": os.getcwd(),
                    "tool_input": str(context.tool_input)[:200] + "..." if len(str(context.tool_input)) > 200 else str(context.tool_input)
                }
            }

            log_path = os.environ.get('HOOK_OVERRIDE_LOG_PATH', os.path.join(os.path.expanduser('~'), '.claude', 'hook_overrides.log'))

            with open(log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception:
            # Don't fail override if logging fails
            pass

    def _log_failed_override(self, context: GuardContext, code: str) -> None:
        """Log failed override attempt for security monitoring."""
        import datetime
        import json
        import os

        try:
            log_entry = {
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "event": "hook_override_failed",
                "guard": self.name,
                "tool": context.tool_name,
                "command": context.command,
                "code_attempted": code[-3:] + "***",  # Only log last 3 digits
                "context": {
                    "working_directory": os.getcwd()
                }
            }

            log_path = os.environ.get('HOOK_OVERRIDE_LOG_PATH', os.path.join(os.path.expanduser('~'), '.claude', 'hook_overrides.log'))

            with open(log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception:
            # Don't fail if logging fails
            pass

    @abstractmethod
    def should_trigger(self, context: GuardContext) -> bool:
        """Determine if this guard should activate for the given context."""
        pass

    @abstractmethod
    def get_message(self, context: GuardContext) -> str:
        """Get the warning message to display to the user."""
        pass

    @abstractmethod
    def get_default_action(self) -> GuardAction:
        """Return the default action for non-interactive mode."""
        pass

    def check(self, context: GuardContext, is_interactive: bool = False) -> GuardResult:
        """Main entry point for guard checking."""
        if not self.should_trigger(context):
            return GuardResult(should_block=False)

        # Check for valid override code first
        if self.check_override(context):
            return GuardResult(should_block=False, message="✅ Override code accepted - allowing command to proceed")

        message = self.get_message(context)

        if is_interactive:
            # In interactive mode, prompt user
            user_choice = self._prompt_user(message)
            should_block = not user_choice
        else:
            # In non-interactive mode, use default action
            default_action = self.get_default_action()
            should_block = default_action == GuardAction.BLOCK

            # Handle None message case
            if message is not None:
                if should_block:
                    message += "\n\n🚨 Non-interactive mode: Blocking by default (safety-first policy)"
                    message += "\n🚨 RULE FAILURE: This operation violates established safety policies"
                    # Add override instructions
                    message += "\n\n🔓 To override this block with explicit approval:"
                    message += "\n   1. Ask the human operator for an override code"
                    message += "\n   2. Re-run with: HOOK_OVERRIDE_CODE=<code> <your command>"
                    message += "\n\n⚠️  Override codes are time-limited and require human authorization."
                else:
                    message += "\n\n⚠️  Non-interactive mode: Allowing by default (configure policy if needed)"

        return GuardResult(should_block=should_block, message=message)

    def _prompt_user(self, message: str) -> bool:
        """Prompt user for permission in interactive mode."""
        if message is not None:
            print(message)
            print()

        response = input("Do you want to allow this action? (y/N): ").strip().lower()
        print()

        if response in ["y", "yes"]:
            print("⚠️  User authorized potentially dangerous action")
            return True
        else:
            print("❌ Action blocked by user")
            return False
