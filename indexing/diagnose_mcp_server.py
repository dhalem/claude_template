# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Diagnostic script to test MCP code review server file collection."""

import os
import sys
from pathlib import Path


def diagnose_file_collection(directory: str):
    """Diagnose file collection issues in a directory."""
    print("=== MCP Code Review Server File Collection Diagnostics ===")
    print(f"Target directory: {directory}")
    print()

    # Check directory existence
    dir_path = Path(directory)
    print(f"Directory exists: {dir_path.exists()}")
    print(f"Directory is dir: {dir_path.is_dir()}")

    if not dir_path.exists() or not dir_path.is_dir():
        print("❌ ISSUE: Directory does not exist or is not a directory")
        return

    # Check file collector
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from file_collector import FileCollector

        collector = FileCollector()
        files = collector.collect_files(directory)

        print("✅ File collector loaded successfully")
        print(f"Files found: {len(files)}")

        if files:
            py_files = [p for p in files.keys() if p.endswith('.py')]
            print(f"Python files: {len(py_files)}")
            print("Sample files:")
            for f in sorted(files.keys())[:10]:
                print(f"  {f}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")
        else:
            print("❌ ISSUE: No files found")

            # Debug why no files found
            print("\n=== Debugging No Files Found ===")

            # Check for Python files manually
            py_files = list(dir_path.glob('*.py'))
            print(f"Python files in root: {len(py_files)}")
            if py_files:
                for f in py_files[:5]:
                    print(f"  {f.name}")

            # Check gitignore
            gitignore_path = dir_path / '.gitignore'
            if gitignore_path.exists():
                print(f"Gitignore exists: {gitignore_path}")
                with open(gitignore_path) as f:
                    content = f.read()
                print(f"Gitignore patterns: {len(content.splitlines())} lines")

                # Test specific pattern that caused the bug
                gitignore_patterns = collector._load_gitignore(dir_path)
                test_file = dir_path / 'server.py'
                if test_file.exists():
                    matches_gitignore = collector._matches_gitignore(test_file, gitignore_patterns)
                    should_include = collector._should_include_file(test_file)
                    print(f"server.py: matches_gitignore={matches_gitignore}, should_include={should_include}")

    except ImportError as e:
        print(f"❌ ISSUE: Cannot import file_collector: {e}")
        print("This suggests the MCP server installation is missing or outdated")
    except Exception as e:
        print(f"❌ ISSUE: Error during file collection: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python diagnose_mcp_server.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    diagnose_file_collection(directory)
