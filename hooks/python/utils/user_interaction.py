"""User interaction utilities for Claude Code hooks."""

import sys


def is_interactive() -> bool:
    """Check if running in an interactive terminal.

    Returns:
        True if all stdin/stdout/stderr are connected to a TTY.
    """
    return sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()


def get_user_permission(message: str, default: str = "n") -> bool:
    """Get user permission for an action.

    Args:
        message: Message to display to user
        default: Default choice if user just presses enter ("y" or "n")

    Returns:
        True if user allows, False if user denies
    """
    if not is_interactive():
        # Non-interactive mode, use default
        print(message, file=sys.stderr)
        if default.lower() == "y":
            print("⚠️  Non-interactive mode: Allowing by default", file=sys.stderr)
            return True
        else:
            print("🚨 Non-interactive mode: Blocking by default (safety-first policy)", file=sys.stderr)
            print("🚨 RULE FAILURE: This operation violates established safety policies", file=sys.stderr)
            return False

    # Interactive mode
    print(message, file=sys.stderr)
    print(file=sys.stderr)

    if default.lower() == "y":
        prompt = "Do you want to allow this action? (Y/n): "
    else:
        prompt = "Do you want to allow this action? (y/N): "

    try:
        response = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        response = ""

    print(file=sys.stderr)

    # Handle default
    if not response:
        response = default.lower()

    if response in ["y", "yes"]:
        print("⚠️  User authorized potentially dangerous action", file=sys.stderr)
        return True
    else:
        print("❌ Action blocked by user", file=sys.stderr)
        return False
