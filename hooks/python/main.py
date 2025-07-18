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
    # TestSuiteEnforcementGuard disabled per user request
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

    # Universal guards (apply to all tool types)
    registry.register(LintGuard(), ["*"])
    registry.register(MetaCognitiveGuard(), ["*"])
    registry.register(ConversationLogGuard(), ["*"])

    return registry


def main():
    """Main entry point for the hook system."""
    if len(sys.argv) < 2:
        print("Error: No tool name provided", file=sys.stderr)
        sys.exit(1)

    tool_name = sys.argv[1]

    # Parse the rest of the arguments as JSON
    if len(sys.argv) > 2:
        json_input = " ".join(sys.argv[2:])
    else:
        json_input = ""

    try:
        # Parse the JSON input
        parsed_input = parse_claude_input(json_input)

        # Create guard context
        context = GuardContext(
            tool_name=tool_name,
            tool_args=parsed_input,
            command=parsed_input.get("command", ""),
            file_path=parsed_input.get("file_path", ""),
            content=parsed_input.get("content", ""),
            old_string=parsed_input.get("old_string", ""),
            new_string=parsed_input.get("new_string", "")
        )

        # Create registry and check all guards
        registry = create_registry()
        result = registry.check_all(context, is_interactive())

        # Exit with error code if any guard blocks
        if result.should_block:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
