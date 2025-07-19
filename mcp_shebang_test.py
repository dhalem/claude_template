#!/usr/bin/env python3
"""Test which Python interpreter is being used."""

import os
import sys
from pathlib import Path

# Write startup info immediately
log_file = Path.home() / ".claude" / "mcp" / "code-review" / "logs" / "shebang_test.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

with open(log_file, "w") as f:
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"sys.path: {sys.path}\n")
    f.write(f"Working directory: {os.getcwd()}\n")
    f.write(f"Script location: {__file__}\n")

    # Check if MCP is available
    try:
        import mcp
        f.write(f"MCP found at: {mcp.__file__}\n")
    except ImportError as e:
        f.write(f"MCP not found: {e}\n")
        f.write("\nTrying to find venv...\n")

        # Look for venv in parent directory
        script_dir = Path(__file__).parent.parent
        venv_python = script_dir / "venv" / "bin" / "python"
        if venv_python.exists():
            f.write(f"Found venv python at: {venv_python}\n")
            f.write("Current python is NOT using venv!\n")
            f.write(f"\nSOLUTION: Change shebang to: #!{venv_python}\n")
        else:
            f.write(f"No venv found at: {venv_python}\n")

# Exit immediately to see the log
sys.exit(0)
