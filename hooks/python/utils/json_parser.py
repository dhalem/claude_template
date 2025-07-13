"""JSON parsing utilities for Claude Code hook input."""

import json
import sys
from typing import Any, Dict, Optional


def parse_claude_input(input_data: Optional[str] = None) -> Dict[str, Any]:
    """Parse Claude Code hook JSON input.

    Args:
        input_data: JSON string. If None, reads from stdin.

    Returns:
        Parsed JSON as dictionary.

    Raises:
        ValueError: If JSON is invalid or required fields are missing.
    """
    if input_data is None:
        # Read from stdin
        try:
            input_data = sys.stdin.read()
        except Exception as e:
            raise ValueError(f"Failed to read from stdin: {e}")

    if not input_data.strip():
        raise ValueError("No input data provided")

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON input: {e}")

    # Validate required fields
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object")

    if "tool_name" not in data and "tool" not in data:
        raise ValueError("Missing required field: tool_name or tool")

    # Normalize tool_name field (some versions use "tool" instead)
    if "tool" in data and "tool_name" not in data:
        data["tool_name"] = data["tool"]

    # Ensure tool_input exists (handle both snake_case and camelCase)
    if "tool_input" not in data:
        # Try toolInput field (camelCase format used by Claude Code)
        if "toolInput" in data:
            data["tool_input"] = data["toolInput"]
        # Try parameters field (older format)
        elif "parameters" in data:
            data["tool_input"] = data["parameters"]
        else:
            data["tool_input"] = {}

    return data
