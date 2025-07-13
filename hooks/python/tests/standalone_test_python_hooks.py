#!/usr/bin/env python3
"""Standalone test for Python hooks implementation."""

import json
import os
import sys

# Add hooks directory to path
hooks_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(hooks_dir, "python"))

from main import run_adaptive_guard  # noqa: E402


def test_git_no_verify():
    """Test Git no-verify guard."""
    test_input = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit -m test --no-verify"}})

    print("Testing Git no-verify guard...")
    print(f"Input: {test_input}")

    exit_code = run_adaptive_guard(test_input)
    print(f"Exit code: {exit_code}")

    if exit_code != 2:
        raise AssertionError(f"Expected exit code 2 (block), got {exit_code}")
    print("✅ Git no-verify guard test passed")


def test_normal_git_command():
    """Test that normal git commands pass through."""
    test_input = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit -m test"}})

    print("\nTesting normal git command...")
    print(f"Input: {test_input}")

    exit_code = run_adaptive_guard(test_input)
    print(f"Exit code: {exit_code}")

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0 (allow), got {exit_code}")
    print("✅ Normal git command test passed")


def test_docker_restart():
    """Test Docker restart guard."""
    test_input = json.dumps({"tool_name": "Bash", "tool_input": {"command": "docker restart my-container"}})

    print("\nTesting Docker restart guard...")
    print(f"Input: {test_input}")

    exit_code = run_adaptive_guard(test_input)
    print(f"Exit code: {exit_code}")

    if exit_code != 2:
        raise AssertionError(f"Expected exit code 2 (block), got {exit_code}")
    print("✅ Docker restart guard test passed")


def test_mock_code_detection():
    """Test mock code detection."""
    test_input = json.dumps(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "test.py",
                "content": 'import unittest.mock\n@mock.patch("requests.get")\ndef test_api():\n    pass',
            },
        }
    )

    print("\nTesting mock code detection...")
    print(f"Input: {test_input}")

    exit_code = run_adaptive_guard(test_input)
    print(f"Exit code: {exit_code}")

    if exit_code != 2:
        raise AssertionError(f"Expected exit code 2 (block), got {exit_code}")
    print("✅ Mock code detection test passed")


if __name__ == "__main__":
    print("Running Python hooks implementation tests...\n")

    try:
        test_git_no_verify()
        test_normal_git_command()
        test_docker_restart()
        test_mock_code_detection()

        print("\n🎉 All tests passed! Python hooks implementation is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
