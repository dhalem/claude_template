#!/usr/bin/env python3

# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Centralized JSON parser for shell-based Claude guards.

This script provides a command-line interface to the centralized JSON parsing
utility, allowing shell scripts to use consistent JSON parsing without
embedding Python one-liners.

Usage:
    echo "$json_input" | ./parse_claude_input.py --field tool_name
    echo "$json_input" | ./parse_claude_input.py --field tool_input.command
    echo "$json_input" | ./parse_claude_input.py --field tool_input.file_path
    echo "$json_input" | ./parse_claude_input.py --validate-only
"""

import argparse
import os
import sys

# Add the Python hooks directory to path to import json_parser
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, 'python')
if os.path.exists(python_dir):
    sys.path.insert(0, python_dir)

try:
    from utils.json_parser import parse_claude_input
except ImportError:
    # Fallback if the utils module isn't available
    import json

    def parse_claude_input(input_data=None):
        if input_data is None:
            input_data = sys.stdin.read()

        if not input_data.strip():
            raise ValueError("No input data provided")

        try:
            data = json.loads(input_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {e}")

        if not isinstance(data, dict):
            raise ValueError("Input must be a JSON object")

        # Normalize tool_name field
        if "tool" in data and "tool_name" not in data:
            data["tool_name"] = data["tool"]

        # Normalize tool_input field
        if "tool_input" not in data:
            if "toolInput" in data:
                data["tool_input"] = data["toolInput"]
            elif "parameters" in data:
                data["tool_input"] = data["parameters"]
            else:
                data["tool_input"] = {}

        return data


def get_nested_field(data, field_path):
    """Get a nested field from data using dot notation (e.g., 'tool_input.command')"""
    parts = field_path.split('.')
    current = data

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return ""

    return str(current) if current is not None else ""


def main():
    parser = argparse.ArgumentParser(
        description="Parse Claude Code hook JSON input"
    )
    parser.add_argument(
        "--field",
        help="Field to extract (supports dot notation, e.g., tool_input.command)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate JSON, don't extract fields"
    )

    args = parser.parse_args()

    try:
        # Parse the input
        data = parse_claude_input()

        if args.validate_only:
            # Just validation - exit with success if we got here
            sys.exit(0)
        elif args.field:
            # Extract and print the requested field
            value = get_nested_field(data, args.field)
            print(value)
        else:
            # No field specified - print the entire parsed JSON
            import json
            print(json.dumps(data, indent=2))

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
