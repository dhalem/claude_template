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
Test suite for anti-bypass-pattern-guard.py
Using TDD approach - tests written first, then implementation
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestAntiBypassPatternGuard(unittest.TestCase):
    """Test cases for anti-bypass pattern detection guard"""

    def setUp(self):
        """Set up test environment"""
        self.guard_path = Path(__file__).parent.parent / "anti-bypass-pattern-guard.py"

    def run_guard(self, tool_input):
        """Helper to run guard with given input"""
        if not self.guard_path.exists():
            self.skipTest("Guard not implemented yet")

        result = subprocess.run(
            [sys.executable, str(self.guard_path)],
            input=json.dumps(tool_input),
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr

    def test_blocks_skip_test_pattern(self):
        """Test that guard blocks @pytest.mark.skip patterns"""
        tool_input = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "test_example.py",
                "new_string": "@pytest.mark.skip\ndef test_something():\n    pass"
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 2, "Should block @pytest.mark.skip pattern")
        self.assertIn("BYPASS PATTERN DETECTED", stderr)
        self.assertIn("@pytest.mark.skip", stderr)

    def test_blocks_stages_manual_pattern(self):
        """Test that guard blocks stages: [manual] in pre-commit config"""
        tool_input = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": ".pre-commit-config.yaml",
                "new_string": "hooks:\n  - id: tests\n    stages: [manual]"
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 2, "Should block stages: [manual] pattern")
        self.assertIn("stages: [manual]", stderr)

    def test_blocks_no_verify_comment(self):
        """Test that guard blocks comments suggesting --no-verify"""
        tool_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "commit_script.sh",
                "content": "#!/bin/bash\n# Use git commit --no-verify to skip tests\ngit commit -m 'update'"
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 2, "Should block --no-verify in comments")
        self.assertIn("--no-verify", stderr)

    def test_blocks_fast_mode_implementation(self):
        """Test that guard blocks fast/quick mode implementations"""
        tool_input = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "run_tests.sh",
                "new_string": 'if [ "$1" = "--fast" ]; then\n  pytest -k "not slow"\nfi'
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 2, "Should block fast mode implementations")
        self.assertIn("fast mode", stderr.lower())

    def test_allows_legitimate_code(self):
        """Test that guard allows legitimate code changes"""
        tool_input = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "example.py",
                "new_string": "def calculate_sum(a, b):\n    return a + b"
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 0, "Should allow legitimate code")

    def test_detects_multiple_patterns(self):
        """Test that guard detects multiple bypass patterns"""
        tool_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "test_utils.py",
                "content": """
import pytest

@pytest.mark.skip("Temporarily disabled")
def test_one():
    pass

@pytest.mark.slow
def test_two():
    # Run with -k "not slow" to skip
    pass
"""
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 2, "Should block multiple bypass patterns")
        # Check that it found 3 patterns
        self.assertIn("found 3 bypass patterns", stderr.lower())

    def test_case_insensitive_detection(self):
        """Test that guard detects patterns case-insensitively"""
        tool_input = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "test.sh",
                "new_string": "# FAST MODE: pytest --FAST"
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 2, "Should detect patterns case-insensitively")

    def test_override_mechanism(self):
        """Test that override mechanism works"""
        os.environ["HOOK_OVERRIDE_CODE"] = "TEST123"

        tool_input = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "test_example.py",
                "new_string": "@pytest.mark.skip\ndef test_something():\n    pass"
            }
        }

        exit_code, stdout, stderr = self.run_guard(tool_input)

        self.assertEqual(exit_code, 0, "Should allow with override code")
        self.assertIn("OVERRIDE APPLIED", stderr)

        # Clean up
        del os.environ["HOOK_OVERRIDE_CODE"]

    def test_logs_bypass_attempts(self):
        """Test that guard logs bypass attempts"""
        log_path = Path.home() / ".claude/logs/bypass_patterns.log"

        # Clear log if exists
        if log_path.exists():
            log_path.unlink()

        tool_input = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "test.py",
                "new_string": "@pytest.mark.skip"
            }
        }

        self.run_guard(tool_input)

        if log_path.exists():
            log_content = log_path.read_text()
            self.assertIn("BYPASS PATTERN", log_content)
            # Check either the pattern or the matched text is logged
            self.assertTrue("@pytest.mark.skip" in log_content or "Matched: @pytest.mark.skip" in log_content)
        else:
            self.skipTest("Logging not implemented yet")

    def test_handles_malformed_json(self):
        """Test that guard handles malformed JSON gracefully"""
        if not self.guard_path.exists():
            self.skipTest("Guard not implemented yet")

        result = subprocess.run(
            [sys.executable, str(self.guard_path)],
            input="invalid json",
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 1, "Should exit with error code 1 for malformed JSON")
        self.assertIn("Invalid JSON", result.stderr)

if __name__ == "__main__":
    unittest.main(verbosity=2)
