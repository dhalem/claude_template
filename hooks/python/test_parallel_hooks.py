#!/usr/bin/env python3
"""
Parallel testing system for Python and Shell hook implementations.

This script tests both Python and shell hook implementations with identical
inputs to ensure they produce equivalent behavior before migrating.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Add the python hooks directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_main import main as python_hook_main


@dataclass
class TestCase:
    """Represents a test case for hook comparison."""

    name: str
    input_json: Dict
    description: str
    expected_shell_behavior: Optional[str] = None  # "allow", "block", or None for auto-detect


@dataclass
class TestResult:
    """Results from running a test case."""

    name: str
    python_exit_code: int
    shell_exit_code: int
    python_output: str
    shell_output: str
    matches: bool
    notes: str = ""


class ParallelHookTester:
    """Tests Python and shell hooks in parallel to ensure equivalent behavior."""

    def __init__(self):
        self.test_cases = []
        self.shell_hook_path = "/home/dhalem/github/sptodial_one/spotidal/hooks/adaptive-guard.sh"
        self.comprehensive_hook_path = "/home/dhalem/github/sptodial_one/spotidal/hooks/comprehensive-guard.sh"

    def add_test_case(self, test_case: TestCase):
        """Add a test case to the suite."""
        self.test_cases.append(test_case)

    def setup_default_test_cases(self):
        """Setup comprehensive test cases covering all guard types."""

        # Git No-Verify Tests
        self.add_test_case(
            TestCase(
                name="git_no_verify_basic",
                input_json={"tool_name": "Bash", "tool_input": {"command": "git commit -m 'test' --no-verify"}},
                description="Basic git commit with --no-verify flag",
                expected_shell_behavior="block",
            )
        )

        self.add_test_case(
            TestCase(
                name="git_commit_normal",
                input_json={"tool_name": "Bash", "tool_input": {"command": "git commit -m 'normal commit'"}},
                description="Normal git commit without --no-verify",
                expected_shell_behavior="allow",
            )
        )

        # Docker Restart Tests
        self.add_test_case(
            TestCase(
                name="docker_restart_container",
                input_json={"tool_name": "Bash", "tool_input": {"command": "docker restart my-container"}},
                description="Docker restart command",
                expected_shell_behavior="block",
            )
        )

        self.add_test_case(
            TestCase(
                name="docker_compose_restart",
                input_json={"tool_name": "Bash", "tool_input": {"command": "docker compose restart service"}},
                description="Docker compose restart command",
                expected_shell_behavior="block",
            )
        )

        self.add_test_case(
            TestCase(
                name="docker_ps_safe",
                input_json={"tool_name": "Bash", "tool_input": {"command": "docker ps"}},
                description="Safe docker ps command",
                expected_shell_behavior="allow",
            )
        )

        # Git Force Push Tests
        self.add_test_case(
            TestCase(
                name="git_force_push",
                input_json={"tool_name": "Bash", "tool_input": {"command": "git push origin main --force"}},
                description="Git force push command",
                expected_shell_behavior="block",
            )
        )

        self.add_test_case(
            TestCase(
                name="git_force_with_lease",
                input_json={"tool_name": "Bash", "tool_input": {"command": "git push origin main --force-with-lease"}},
                description="Git force push with lease (safer)",
                expected_shell_behavior="allow",
            )
        )

        # Mock Code Prevention Tests
        self.add_test_case(
            TestCase(
                name="mock_code_write",
                input_json={
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "test.py",
                        "content": "import unittest.mock\n@mock.patch('service')\ndef test():\n    pass",
                    },
                },
                description="Writing file with mock code",
                expected_shell_behavior="block",
            )
        )

        self.add_test_case(
            TestCase(
                name="normal_python_write",
                input_json={
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "test.py",
                        "content": "import requests\ndef get_data():\n    return requests.get('http://api.com')",
                    },
                },
                description="Writing normal Python code",
                expected_shell_behavior="allow",
            )
        )

        # Pre-commit Config Protection Tests
        self.add_test_case(
            TestCase(
                name="precommit_config_edit",
                input_json={
                    "tool_name": "Edit",
                    "tool_input": {"file_path": ".pre-commit-config.yaml", "old_string": "old", "new_string": "new"},
                },
                description="Editing pre-commit config file",
                expected_shell_behavior="block",
            )
        )

        # Hook Installation Protection Tests
        self.add_test_case(
            TestCase(
                name="claude_dir_edit",
                input_json={
                    "tool_name": "Edit",
                    "tool_input": {
                        "file_path": "/home/user/.claude/settings.json",
                        "old_string": "old",
                        "new_string": "new",
                    },
                },
                description="Direct edit of .claude directory file",
                expected_shell_behavior="block",
            )
        )

        self.add_test_case(
            TestCase(
                name="claude_dir_copy",
                input_json={"tool_name": "Bash", "tool_input": {"command": "cp hook.sh ~/.claude/"}},
                description="Copy to .claude directory",
                expected_shell_behavior="block",
            )
        )

        # Docker Without Compose Tests
        self.add_test_case(
            TestCase(
                name="docker_run_without_compose",
                input_json={"tool_name": "Bash", "tool_input": {"command": "docker run -it ubuntu bash"}},
                description="Docker run without compose",
                expected_shell_behavior="block",
            )
        )

        self.add_test_case(
            TestCase(
                name="docker_compose_proper",
                input_json={"tool_name": "Bash", "tool_input": {"command": "docker -c musicbot compose up -d"}},
                description="Proper docker compose command",
                expected_shell_behavior="allow",
            )
        )

        # Directory Awareness Tests
        self.add_test_case(
            TestCase(
                name="relative_script_execution",
                input_json={"tool_name": "Bash", "tool_input": {"command": "./run_script.sh"}},
                description="Relative script execution",
                expected_shell_behavior="allow",  # Shell shows warning but allows
            )
        )

        # Test Suite Enforcement Tests
        self.add_test_case(
            TestCase(
                name="completion_claim",
                input_json={"tool_name": "Bash", "tool_input": {"command": "echo 'Feature complete'"}},
                description="Completion claim without tests",
                expected_shell_behavior="block",
            )
        )

        # Container Rebuild Reminder Tests (non-blocking)
        self.add_test_case(
            TestCase(
                name="dockerfile_edit",
                input_json={
                    "tool_name": "Edit",
                    "tool_input": {
                        "file_path": "Dockerfile",
                        "old_string": "FROM ubuntu",
                        "new_string": "FROM ubuntu:20.04",
                    },
                },
                description="Editing Dockerfile (should show reminder)",
                expected_shell_behavior="allow",
            )
        )

        # Database Schema Reminder Tests (non-blocking)
        self.add_test_case(
            TestCase(
                name="sql_query_write",
                input_json={
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "query.py",
                        "content": "cursor.execute('SELECT * FROM tracks WHERE album_id = 5')",
                    },
                },
                description="Writing SQL query (should show reminder)",
                expected_shell_behavior="allow",
            )
        )

        # Temp File Location Tests (non-blocking)
        self.add_test_case(
            TestCase(
                name="temp_file_root",
                input_json={
                    "tool_name": "Write",
                    "tool_input": {"file_path": "test_feature.py", "content": "print('testing')"},
                },
                description="Creating temp file in root (should show warning)",
                expected_shell_behavior="allow",
            )
        )

    def run_python_hook(self, input_json: Dict) -> Tuple[int, str]:
        """Run the Python hook implementation."""
        try:
            # Capture stdout/stderr
            import io
            from contextlib import redirect_stderr, redirect_stdout

            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            # Convert input to JSON string like the shell version expects
            json_input = json.dumps(input_json)

            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Simulate command line args for main function
                    old_argv = sys.argv
                    sys.argv = ["main.py", json_input]
                    exit_code = python_hook_main()
                    sys.argv = old_argv

                    if exit_code is None:
                        exit_code = 0

            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
            except Exception as e:
                exit_code = 1
                stderr_capture.write(f"Error: {str(e)}")

            # Combine stdout and stderr for comparison
            output = stdout_capture.getvalue() + stderr_capture.getvalue()
            return exit_code, output.strip()

        except Exception as e:
            return 1, f"Python hook error: {str(e)}"

    def run_shell_hook(self, input_json: Dict, hook_path: str) -> Tuple[int, str]:
        """Run the shell hook implementation."""
        try:
            json_input = json.dumps(input_json)

            # Run shell hook with JSON input via stdin
            process = subprocess.run([hook_path], input=json_input, text=True, capture_output=True, timeout=30)

            # Combine stdout and stderr for comparison
            output = (process.stdout + process.stderr).strip()
            return process.returncode, output

        except subprocess.TimeoutExpired:
            return 1, "Shell hook timeout"
        except Exception as e:
            return 1, f"Shell hook error: {str(e)}"

    def normalize_output(self, output: str) -> str:
        """Normalize output for comparison by removing interactive prompts."""
        lines = output.split("\n")
        normalized_lines = []

        for line in lines:
            # Skip interactive prompt lines
            if "Do you want to allow this action?" in line:
                continue
            if line.strip().startswith("(y/N):"):
                continue
            if line.strip() == "":
                continue

            normalized_lines.append(line.strip())

        return "\n".join(normalized_lines)

    def compare_results(
        self, test_case: TestCase, python_result: Tuple[int, str], shell_result: Tuple[int, str]
    ) -> TestResult:
        """Compare Python and shell hook results."""
        python_exit_code, python_output = python_result
        shell_exit_code, shell_output = shell_result

        # Normalize outputs for comparison
        python_normalized = self.normalize_output(python_output)
        shell_normalized = self.normalize_output(shell_output)

        # Determine if results match
        exit_codes_match = python_exit_code == shell_exit_code

        # For blocking operations, exit code is more important than exact output
        if test_case.expected_shell_behavior == "block":
            matches = exit_codes_match and python_exit_code != 0 and shell_exit_code != 0
        elif test_case.expected_shell_behavior == "allow":
            matches = exit_codes_match and python_exit_code == 0 and shell_exit_code == 0
        else:
            # Auto-detect based on shell behavior
            matches = exit_codes_match

        notes = ""
        if not exit_codes_match:
            notes += f"Exit codes differ: Python={python_exit_code}, Shell={shell_exit_code}. "

        # Check if outputs convey similar meaning (for reminders vs blocks)
        if "BLOCKED" in shell_normalized.upper() and "blocked" not in python_normalized.lower():
            notes += "Shell blocks but Python doesn't. "
        elif "BLOCKED" in python_normalized.upper() and "blocked" not in shell_normalized.lower():
            notes += "Python blocks but Shell doesn't. "

        return TestResult(
            name=test_case.name,
            python_exit_code=python_exit_code,
            shell_exit_code=shell_exit_code,
            python_output=python_output,
            shell_output=shell_output,
            matches=matches,
            notes=notes.strip(),
        )

    def run_tests(self, verbose: bool = False) -> List[TestResult]:
        """Run all test cases and return results."""
        results = []

        print(f"Running {len(self.test_cases)} parallel hook tests...")
        print("=" * 80)

        for i, test_case in enumerate(self.test_cases, 1):
            print(f"[{i:2d}/{len(self.test_cases)}] {test_case.name}: {test_case.description}")

            # Run Python hook
            python_result = self.run_python_hook(test_case.input_json)

            # Run shell hook (try adaptive-guard.sh first, fallback to comprehensive-guard.sh)
            shell_result = self.run_shell_hook(test_case.input_json, self.shell_hook_path)

            # Compare results
            result = self.compare_results(test_case, python_result, shell_result)
            results.append(result)

            # Show immediate result
            status = "✅ PASS" if result.matches else "❌ FAIL"
            print(f"      {status} - Exit codes: Python={result.python_exit_code}, Shell={result.shell_exit_code}")

            if not result.matches or verbose:
                if result.notes:
                    print(f"      Notes: {result.notes}")
                if verbose:
                    print(f"      Python output: {result.python_output[:100]}...")
                    print(f"      Shell output: {result.shell_output[:100]}...")

            print()

        return results

    def print_summary(self, results: List[TestResult]):
        """Print test summary."""
        passed = sum(1 for r in results if r.matches)
        total = len(results)

        print("=" * 80)
        print(f"PARALLEL HOOK TEST SUMMARY: {passed}/{total} tests passed")
        print("=" * 80)

        if passed == total:
            print("🎉 ALL TESTS PASSED! Python hooks are equivalent to shell hooks.")
            print("✅ Safe to proceed with migration.")
        else:
            print(f"❌ {total - passed} tests failed. Migration readiness issues detected.")
            print("\nFailed tests:")
            for result in results:
                if not result.matches:
                    print(f"  - {result.name}: {result.notes}")

        print()

        # Show behavior breakdown
        blocking_tests = [r for r in results if r.python_exit_code != 0 or r.shell_exit_code != 0]
        allowing_tests = [r for r in results if r.python_exit_code == 0 and r.shell_exit_code == 0]

        print("Behavior Analysis:")
        print(f"  - Blocking operations: {len(blocking_tests)}")
        print(f"  - Allowing operations: {len(allowing_tests)}")
        print(f"  - Exit code mismatches: {len([r for r in results if r.python_exit_code != r.shell_exit_code])}")


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Python vs Shell hook implementations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--test", "-t", help="Run specific test case by name")
    args = parser.parse_args()

    tester = ParallelHookTester()
    tester.setup_default_test_cases()

    if args.test:
        # Run specific test
        test_cases = [tc for tc in tester.test_cases if tc.name == args.test]
        if not test_cases:
            print(f"Test case '{args.test}' not found.")
            print("Available tests:")
            for tc in tester.test_cases:
                print(f"  - {tc.name}: {tc.description}")
            return 1
        tester.test_cases = test_cases

    # Run tests
    results = tester.run_tests(verbose=args.verbose)

    # Print summary
    tester.print_summary(results)

    # Return exit code based on results
    passed = sum(1 for r in results if r.matches)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
