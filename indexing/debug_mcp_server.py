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

"""Debug script to test MCP server startup issues."""

import asyncio
import os
import sys

# Simulate MCP environment
if '__file__' in globals():
    print("Removing __file__ to simulate MCP environment...")
    del globals()['__file__']

print("=== MCP Server Debug ===")
print(f"Python: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print(f"sys.argv[0]: {sys.argv[0]}")

# Try to import the server
try:
    # Add path as the server would
    current_script = os.path.abspath(sys.argv[0])
    current_dir = os.path.dirname(current_script)
    sys.path.insert(0, current_dir)

    print(f"\nAdding to path: {current_dir}")

    # Import the server module
    import mcp_code_review_server_v2 as server_module

    print("\n✓ Server module imported successfully")
    print(f"  Module location: {getattr(server_module, '__file__', 'No __file__')}")
    print(f"  Has main: {hasattr(server_module, 'main')}")
    print(f"  Has current_dir: {hasattr(server_module, 'current_dir')}")

    if hasattr(server_module, 'current_dir'):
        print(f"  Server's current_dir: {server_module.current_dir}")

        # Check if reviewer src is accessible
        reviewer_src = os.path.join(server_module.current_dir, "..", "reviewer", "src")
        print(f"\n  Reviewer src path: {reviewer_src}")
        print(f"  Reviewer src exists: {os.path.exists(reviewer_src)}")

        if os.path.exists(reviewer_src):
            print(f"  Files: {os.listdir(reviewer_src)}")

    # Test imports
    print("\nTesting required imports...")
    try:
        from file_collector import FileCollector
        print("  ✓ FileCollector imported")
    except ImportError as e:
        print(f"  ✗ FileCollector import failed: {e}")

    try:
        from gemini_client import GeminiClient
        print("  ✓ GeminiClient imported")
    except ImportError as e:
        print(f"  ✗ GeminiClient import failed: {e}")

    try:
        from review_formatter import ReviewFormatter
        print("  ✓ ReviewFormatter imported")
    except ImportError as e:
        print(f"  ✗ ReviewFormatter import failed: {e}")

    # Test creating a server instance
    print("\nTesting server initialization...")

    async def test_server():
        try:
            # Call main but cancel immediately
            task = asyncio.create_task(server_module.main())
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print("  ✓ Server main() started successfully")
                return True
        except Exception as e:
            print(f"  ✗ Server main() failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    success = asyncio.run(test_server())

    if success:
        print("\n✅ Server appears to be working correctly!")
    else:
        print("\n❌ Server has startup issues")

except Exception as e:
    print(f"\n❌ Failed to import server: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test the installed location
print("\n=== Testing Installed Server ===")
installed_server = os.path.expanduser("~/.claude/mcp/code-review/bin/server.py")
if os.path.exists(installed_server):
    print(f"Installed server found at: {installed_server}")

    # Check the start script
    start_script = os.path.expanduser("~/.claude/mcp/code-review/start-server.sh")
    if os.path.exists(start_script):
        print(f"Start script found at: {start_script}")
        with open(start_script, 'r') as f:
            print("Start script contents:")
            print(f.read())
else:
    print("Installed server not found")
