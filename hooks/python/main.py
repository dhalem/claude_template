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

        # Create registry and check guards
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
