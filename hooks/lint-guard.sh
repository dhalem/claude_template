#!/bin/bash

# ---------------------------------------------------------------------
# CLAUDE CODE LINT GUARD - PYTHON WRAPPER
# ---------------------------------------------------------------------
#
# This script is a wrapper that calls the Python implementation of the
# lint guard system. The Python version provides enhanced functionality,
# better error handling, and comprehensive auto-fix capabilities.
#
# MIGRATION NOTE:
# - Original shell implementation archived in archive/shell_originals/
# - Python implementation provides all original functionality plus improvements
# - For details see: python/README.md and HOOKS.md
#
# ---------------------------------------------------------------------

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to Python implementation
PYTHON_HOOKS_DIR="$SCRIPT_DIR/python"

# Check if Python implementation exists
if [[ ! -d "$PYTHON_HOOKS_DIR" ]]; then
    echo "ERROR: Python hooks directory not found: $PYTHON_HOOKS_DIR" >&2
    echo "Please ensure the Python implementation is properly installed." >&2
    exit 1
fi

if [[ ! -f "$PYTHON_HOOKS_DIR/main.py" ]]; then
    echo "ERROR: Python main.py not found: $PYTHON_HOOKS_DIR/main.py" >&2
    echo "Please ensure the Python implementation is properly installed." >&2
    exit 1
fi

# Source environment variables if .env files exist
# First check for main .env (contains API keys)
MAIN_ENV="$SCRIPT_DIR/.env"
if [[ -f "$MAIN_ENV" ]]; then
    set -a  # Mark variables for export
    # shellcheck source=/dev/null
    source "$MAIN_ENV"
    set +a
fi

# Then source hooks-specific .env if it exists
HOOKS_ENV="$SCRIPT_DIR/.env.hooks"
if [[ -f "$HOOKS_ENV" ]]; then
    set -a  # Mark variables for export
    # shellcheck source=/dev/null
    source "$HOOKS_ENV"
    set +a
fi

# Read JSON input from stdin
INPUT_JSON=$(cat)

# Call Python implementation (stay in original directory for correct file paths)
python3 "$PYTHON_HOOKS_DIR/main.py" lint <<< "$INPUT_JSON"

# Exit with the same code as the Python implementation
exit $?
