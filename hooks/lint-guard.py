#!/usr/bin/env python3
"""Python wrapper for lint-guard.sh - drop-in replacement."""

import os
import sys

# Add the hooks directory to Python path
hooks_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, hooks_dir)

from python.main import run_lint_guard

if __name__ == "__main__":
    # Read from stdin if no arguments, otherwise use first argument
    if len(sys.argv) > 1:
        input_data = sys.argv[1]
    else:
        input_data = sys.stdin.read()

    exit_code = run_lint_guard(input_data)
    sys.exit(exit_code)
