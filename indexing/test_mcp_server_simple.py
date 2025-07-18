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

"""Simple test to verify MCP server __file__ fix works."""

import logging
import os
import subprocess

# Configure logging for test output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
import sys


def test_file_name_error():
    """Test that the server handles missing __file__."""
    # Create a test script that simulates MCP environment
    test_script = """
import os
import sys

# Simulate MCP environment where __file__ is not defined
if '__file__' in globals():
    del globals()['__file__']

# Now try to import the server
try:
    # Add the directory to path
    import_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0, os.path.join(import_dir, 'indexing'))

    # This should work without NameError
    import mcp_code_review_server_v2 as server

    logger.info("SUCCESS: Server imported without NameError")
    logger.info(f"Server has main function: {hasattr(server, 'main')}")
    logger.info(f"Server has current_dir: {hasattr(server, 'current_dir')}")

except NameError as e:
    if '__file__' in str(e):
        logger.error(f"FAILED: NameError with __file__: {e}")
        sys.exit(1)
    else:
        raise
except Exception as e:
    logger.error(f"FAILED: Other error: {type(e).__name__}: {e}")
    sys.exit(1)
"""

    # Run the test
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    logger.info("=== Test Output ===")
    logger.info(result.stdout)
    if result.stderr:
        logger.info("=== Stderr ===")
        logger.info(result.stderr)

    return result.returncode == 0 and "SUCCESS" in result.stdout


def test_direct_import():
    """Test direct import in current Python environment."""
    logger.info("\n=== Direct Import Test ===")

    # Save current __file__ if it exists
    original_file = globals().get('__file__')

    try:
        # Remove __file__ to simulate MCP environment
        if '__file__' in globals():
            del globals()['__file__']

        # Add path and import
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))), 'indexing'))

        # This should work
        import mcp_code_review_server_v2 as server

        logger.info("SUCCESS: Direct import worked without __file__")
        logger.info(f"Server module location: {server.__file__ if hasattr(server, '__file__') else 'No __file__ attribute'}")
        logger.info(f"Has main: {hasattr(server, 'main')}")
        logger.info(f"Has current_dir: {hasattr(server, 'current_dir')}")

        return True

    except NameError as e:
        if '__file__' in str(e):
            logger.error(f"FAILED: NameError related to __file__: {e}")
            return False
        raise

    finally:
        # Restore __file__ if it existed
        if original_file is not None:
            globals()['__file__'] = original_file


def test_installed_server():
    """Test the installed server."""
    logger.info("\n=== Installed Server Test ===")

    installed_path = os.path.expanduser("~/.claude/mcp/code-review/bin/server.py")

    if not os.path.exists(installed_path):
        logger.info(f"Installed server not found at {installed_path}")
        return False

    # Test running the installed server
    result = subprocess.run(
        [sys.executable, installed_path, "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )

    # Should not have NameError
    if "NameError" in result.stderr and "__file__" in result.stderr:
        logger.info("FAILED: Installed server has NameError with __file__")
        logger.info(f"Stderr: {result.stderr}")
        return False

    logger.info("SUCCESS: Installed server runs without __file__ NameError")
    return True


if __name__ == "__main__":
    logger.info("Testing MCP Code Review Server __file__ handling...\n")

    tests = [
        ("Subprocess __file__ test", test_file_name_error),
        ("Direct import test", test_direct_import),
        ("Installed server test", test_installed_server),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                logger.info(f"✓ {name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {name} FAILED with exception: {e}")
            failed += 1

    logger.info(f"\n{'='*50}")
    logger.info(f"Tests passed: {passed}/{len(tests)}")
    logger.info(f"Tests failed: {failed}/{len(tests)}")

    sys.exit(0 if failed == 0 else 1)
