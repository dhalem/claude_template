#!/usr/bin/env python3

import json
import logging
from pathlib import Path

# Configure logging for script output
logging.basicConfig(level=logging.INFO, format="%(message)s")


def update_settings():
    """Update Claude Code settings.json to add PostToolUse lint hooks."""
    settings_path = Path.home() / ".claude" / "settings.json"

    # Load existing settings
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {"hooks": {}}

    # Ensure hooks key exists
    if "hooks" not in settings:
        settings["hooks"] = {}

    # Add PostToolUse hooks if not present
    if "PostToolUse" not in settings["hooks"]:
        settings["hooks"]["PostToolUse"] = []

    # Add lint guard for file operations
    lint_hook_config = {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "~/.claude/lint-guard.sh"}],
    }

    # Check if already exists (avoid duplicates)
    existing_matchers = [hook.get("matcher") for hook in settings["hooks"]["PostToolUse"]]

    if "Edit" not in existing_matchers:
        settings["hooks"]["PostToolUse"].append(lint_hook_config)

        # Also add for Write and MultiEdit
        for tool in ["Write", "MultiEdit"]:
            tool_hook = lint_hook_config.copy()
            tool_hook["matcher"] = tool
            settings["hooks"]["PostToolUse"].append(tool_hook)

        logging.info("✅ Added PostToolUse lint hooks for Edit, Write, MultiEdit")
    else:
        logging.info("ℹ️ PostToolUse hooks already exist")

    # Save updated settings
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    logging.info("✅ Updated %s", settings_path)
    logging.info("ℹ️ Restart Claude Code to activate PostToolUse hooks")


if __name__ == "__main__":
    update_settings()
