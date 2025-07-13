#!/usr/bin/env python3
"""Main entry points for Claude Code hook system.

REMINDER: Update HOOKS.md when adding/removing guards from create_registry()!
"""

import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_guard import GuardContext  # noqa: E402
from guards import (  # noqa: E402
    ContainerRebuildReminder,
    ContainerStateGuard,
    ConversationLogGuard,
    DatabaseSchemaReminder,
    DirectoryAwarenessGuard,
    DockerEnvGuard,
    DockerRestartGuard,
    DockerWithoutComposeGuard,
    EnvBypassGuard,
    GitCheckoutSafetyGuard,
    GitForcePushGuard,
    GitHookProtectionGuard,
    GitNoVerifyGuard,
    HookInstallationGuard,
    MetaCognitiveGuard,
    MockCodeGuard,
    PipInstallGuard,
    PreCommitConfigGuard,
    TempFileLocationGuard,
    TestSuiteEnforcementGuard,
)
from guards.lint_guards import LintGuard  # noqa: E402
from guards.path_guards import AbsolutePathCdGuard, CurlHeadRequestGuard  # noqa: E402
from guards.python_venv_guard import PythonVenvGuard  # noqa: E402
from registry import GuardRegistry  # noqa: E402
from utils.json_parser import parse_claude_input  # noqa: E402
from utils.user_interaction import is_interactive  # noqa: E402


def create_registry() -> GuardRegistry:
    """Create and populate the guard registry."""
    registry = GuardRegistry()

    # Bash-specific guards
    registry.register(GitNoVerifyGuard(), ["Bash"])
    registry.register(GitForcePushGuard(), ["Bash"])
    registry.register(GitCheckoutSafetyGuard(), ["Bash"])
    registry.register(GitHookProtectionGuard(), ["Bash"])
    registry.register(DockerRestartGuard(), ["Bash"])
    registry.register(DockerWithoutComposeGuard(), ["Bash"])
    registry.register(DockerEnvGuard(), ["Bash"])
    registry.register(ContainerStateGuard(), ["Bash"])
    registry.register(DirectoryAwarenessGuard(), ["Bash"])
    registry.register(TestSuiteEnforcementGuard(), ["Bash"])
    registry.register(EnvBypassGuard(), ["Bash"])
    registry.register(PipInstallGuard(), ["Bash"])
    registry.register(PythonVenvGuard(), ["Bash"])
    registry.register(AbsolutePathCdGuard(), ["Bash"])
    registry.register(CurlHeadRequestGuard(), ["Bash"])

    # File operation guards
    registry.register(MockCodeGuard(), ["Edit", "Write", "MultiEdit"])
    registry.register(PreCommitConfigGuard(), ["Edit", "Write", "MultiEdit"])
    registry.register(HookInstallationGuard(), ["Edit", "Write", "MultiEdit", "Bash"])
    registry.register(ContainerRebuildReminder(), ["Edit", "Write", "MultiEdit"])
    registry.register(DatabaseSchemaReminder(), ["Edit", "Write", "MultiEdit"])
    registry.register(TempFileLocationGuard(), ["Write"])

    # Meta-cognitive guards (analyzes Claude responses for all tools)
    registry.register(MetaCognitiveGuard(), ["Bash", "Edit", "Write", "MultiEdit"])

    # Conversation log analysis (analyzes conversation history)
    registry.register(ConversationLogGuard(), ["Bash", "Edit", "Write", "MultiEdit"])

    return registry


def run_adaptive_guard(input_data: str = None) -> int:
    """Run the adaptive guard system (replacement for adaptive-guard.sh)."""
    try:
        # Parse input
        input_json = parse_claude_input(input_data)
        context = GuardContext.from_claude_input(input_json)

        # GLOBAL OVERRIDE CHECK - If valid override code provided, bypass ALL guards
        override_code = os.environ.get('HOOK_OVERRIDE_CODE')
        if override_code:
            if _validate_global_override(override_code, context):
                print("✅ Override code accepted - allowing command to proceed")
                return 0  # Success - bypass all guards

        # No valid override - run normal guard checks
        registry = create_registry()
        result = registry.check_all(context, is_interactive())

        return result.exit_code

    except ValueError as e:
        print(f"Input error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        return 1


def run_lint_guard(input_data: str = None) -> int:
    """Run the lint guard system (replacement for lint-guard.sh)."""
    try:
        # Parse input
        input_json = parse_claude_input(input_data)
        context = GuardContext.from_claude_input(input_json)

        # Run lint guard for auto-fixing
        lint_guard = LintGuard()
        result = lint_guard.check(context, is_interactive())

        # Print message if provided
        if result.message:
            print(result.message)

        return result.exit_code

    except ValueError as e:
        print(f"Input error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        return 1


def _validate_global_override(code: str, context: GuardContext) -> bool:
    """Validate TOTP override code globally and log the attempt."""
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

        # Validate TOTP code format
        if not code.isdigit() or len(code) != 6:
            _log_failed_override("global_override_checker", context, code)
            return False

        # Try pyotp first (preferred)
        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            if totp.verify(code, valid_window=1):
                _log_successful_override("global_override_checker", context, code)
                return True
        except ImportError:
            pass

        # Fallback TOTP implementation
        secret_bytes = base64.b32decode(secret.upper() + '=' * (-len(secret) % 8))
        time_step = int(time.time() // 30)

        # Check current time step and one before/after for clock skew
        for offset in [-1, 0, 1]:
            msg = struct.pack('>Q', time_step + offset)
            hmac_hash = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
            offset_bits = hmac_hash[-1] & 0xf
            truncated = struct.unpack('>I', hmac_hash[offset_bits:offset_bits + 4])[0]
            truncated &= 0x7fffffff
            totp_code = str(truncated % 1000000).zfill(6)

            if code == totp_code:
                _log_successful_override("global_override_checker", context, code)
                return True

        # Invalid code
        _log_failed_override("global_override_checker", context, code)
        return False

    except Exception:
        # If anything goes wrong, fail safely and log attempt
        _log_failed_override("global_override_checker", context, code)
        return False


def _log_successful_override(guard_name: str, context: GuardContext, code: str) -> None:
    """Log successful override usage for audit purposes."""
    import datetime
    import json
    import os

    try:
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event": "hook_override_successful",
            "guard": guard_name,
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


def _log_failed_override(guard_name: str, context: GuardContext, code: str) -> None:
    """Log failed override attempt for security monitoring."""
    import datetime
    import json
    import os

    try:
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event": "hook_override_failed",
            "guard": guard_name,
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


def main():
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 main.py [adaptive|lint] [input_json]")
        sys.exit(1)

    guard_type = sys.argv[1]
    input_data = sys.argv[2] if len(sys.argv) > 2 else None

    if guard_type == "adaptive":
        exit_code = run_adaptive_guard(input_data)
    elif guard_type == "lint":
        exit_code = run_lint_guard(input_data)
    else:
        print(f"Unknown guard type: {guard_type}")
        sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
