#!/usr/bin/env python3
"""Test runner for Claude Code hook system.

REMINDER: Update HOOKS.md when adding new test files!
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def discover_and_run_tests():
    """Discover and run all tests in the tests directory."""
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return appropriate exit code
    if result.wasSuccessful():
        print(f"\n✅ All tests passed! ({result.testsRun} tests)")
        return 0
    else:
        print(f"\n❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return 1


if __name__ == "__main__":
    exit_code = discover_and_run_tests()
    sys.exit(exit_code)
