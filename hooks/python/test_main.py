#!/usr/bin/env python3
"""Test entry point for Python hooks - simplified for parallel testing."""

import json
import os
import sys

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_guard import GuardContext
from guards.awareness_guards import DirectoryAwarenessGuard, TestSuiteEnforcementGuard
from guards.docker_guards import DockerRestartGuard, DockerWithoutComposeGuard
from guards.file_guards import HookInstallationGuard, MockCodeGuard, PreCommitConfigGuard
from guards.git_guards import GitForcePushGuard, GitNoVerifyGuard
from guards.reminder_guards import ContainerRebuildReminder, DatabaseSchemaReminder, TempFileLocationGuard
from registry import GuardRegistry


def create_registry() -> GuardRegistry:
    """Create and populate the guard registry."""
    registry = GuardRegistry()

    # Bash-specific guards
    registry.register(GitNoVerifyGuard(), ["Bash"])
    registry.register(GitForcePushGuard(), ["Bash"])
    registry.register(DockerRestartGuard(), ["Bash"])
    registry.register(DockerWithoutComposeGuard(), ["Bash"])
    registry.register(DirectoryAwarenessGuard(), ["Bash"])
    registry.register(TestSuiteEnforcementGuard(), ["Bash"])

    # File operation guards
    registry.register(MockCodeGuard(), ["Edit", "Write", "MultiEdit"])
    registry.register(PreCommitConfigGuard(), ["Edit", "Write", "MultiEdit"])
    registry.register(HookInstallationGuard(), ["Edit", "Write", "MultiEdit", "Bash"])
    registry.register(ContainerRebuildReminder(), ["Edit", "Write", "MultiEdit"])
    registry.register(DatabaseSchemaReminder(), ["Edit", "Write", "MultiEdit"])
    registry.register(TempFileLocationGuard(), ["Write"])

    return registry


def main(input_data: str = None) -> int:
    """Main hook entry point for testing."""
    try:
        # Get input data
        if input_data is None:
            if len(sys.argv) > 1:
                input_data = sys.argv[1]
            else:
                input_data = sys.stdin.read()

        # Parse input
        if isinstance(input_data, str):
            input_json = json.loads(input_data)
        else:
            input_json = input_data

        context = GuardContext.from_claude_input(input_json)

        # Create registry and check guards
        registry = create_registry()

        # For testing purposes, always run in non-interactive mode
        result = registry.check_all(context, is_interactive=False)

        if result.message:
            print(result.message)

        return result.exit_code

    except ValueError as e:
        print(f"Input error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
