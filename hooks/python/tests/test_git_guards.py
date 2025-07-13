"""Unit tests for Git-related guards."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.git_guards import (  # noqa: E402
    GitCheckoutSafetyGuard,
    GitForcePushGuard,
    GitNoVerifyGuard,
    PreCommitConfigGuard,
)


class TestGitNoVerifyGuard(unittest.TestCase):
    """Test cases for GitNoVerifyGuard."""

    def setUp(self):
        self.guard = GitNoVerifyGuard()

    def test_should_trigger_on_no_verify(self):
        """Test that guard triggers on --no-verify commands."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git commit -m 'test' --no-verify"},
            command="git commit -m 'test' --no-verify",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_with_extra_args(self):
        """Test that guard triggers with additional arguments."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git commit -a -m 'fix bug' --no-verify --author='Test User'"},
            command="git commit -a -m 'fix bug' --no-verify --author='Test User'",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_normal_commit(self):
        """Test that guard doesn't trigger on normal git commands."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "git commit -m 'test'"}, command="git commit -m 'test'"
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_bash(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        context = GuardContext(tool_name="Edit", tool_input={"file_path": "test.py"}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_empty_command(self):
        """Test that guard doesn't trigger on empty commands."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_command(self):
        """Test that error message contains the problematic command."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git commit -m 'test' --no-verify"},
            command="git commit -m 'test' --no-verify",
        )

        message = self.guard.get_message(context)
        self.assertIn("git commit -m 'test' --no-verify", message)
        self.assertIn("--no-verify", message)
        self.assertIn("Pre-commit hooks exist to", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_non_interactive_blocks_by_default(self):
        """Test non-interactive mode blocks by default."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git commit -m 'test' --no-verify"},
            command="git commit -m 'test' --no-verify",
        )

        result = self.guard.check(context, is_interactive=False)

        self.assertTrue(result.should_block)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("safety-first policy", result.message)

    def test_check_passes_when_not_triggered(self):
        """Test that check passes when guard doesn't trigger."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "git commit -m 'test'"}, command="git commit -m 'test'"
        )

        result = self.guard.check(context, is_interactive=False)

        self.assertFalse(result.should_block)
        self.assertEqual(result.exit_code, 0)


class TestGitForcePushGuard(unittest.TestCase):
    """Test cases for GitForcePushGuard."""

    def setUp(self):
        self.guard = GitForcePushGuard()

    def test_should_trigger_on_force_flag(self):
        """Test that guard triggers on --force flag."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git push origin main --force"},
            command="git push origin main --force",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_f_flag(self):
        """Test that guard triggers on -f flag."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "git push origin main -f"}, command="git push origin main -f"
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_f_flag_at_end(self):
        """Test that guard triggers on -f flag at end of command."""
        context = GuardContext(tool_name="Bash", tool_input={"command": "git push -f"}, command="git push -f")

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_normal_push(self):
        """Test that guard doesn't trigger on normal push."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "git push origin main"}, command="git push origin main"
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_force_with_lease(self):
        """Test that guard doesn't trigger on --force-with-lease (safer)."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git push origin main --force-with-lease"},
            command="git push origin main --force-with-lease",
        )

        # This should not trigger as --force-with-lease is safer than --force
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_bash(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        context = GuardContext(tool_name="Write", tool_input={"file_path": "test.py"}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_mentions_alternatives(self):
        """Test that message mentions safer alternatives."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git push origin main --force"},
            command="git push origin main --force",
        )

        message = self.guard.get_message(context)
        self.assertIn("--force-with-lease", message)
        self.assertIn("git revert", message)
        self.assertIn("permanent data loss", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_non_interactive_blocks_by_default(self):
        """Test non-interactive mode blocks by default."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git push origin main --force"},
            command="git push origin main --force",
        )

        result = self.guard.check(context, is_interactive=False)

        self.assertTrue(result.should_block)
        self.assertEqual(result.exit_code, 2)


class TestGitGuardEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for Git guards."""

    def test_git_no_verify_guard_case_insensitive(self):
        """Test that git no-verify guard is case insensitive."""
        guard = GitNoVerifyGuard()

        test_cases = ["GIT COMMIT --NO-VERIFY", "Git Commit --No-Verify", "git COMMIT --no-VERIFY"]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_git_no_verify_guard_with_whitespace_variations(self):
        """Test git no-verify with various whitespace patterns."""
        guard = GitNoVerifyGuard()

        test_cases = [
            "git  commit   --no-verify",  # Multiple spaces
            "git\tcommit\t--no-verify",  # Tabs
            "  git commit --no-verify  ",  # Leading/trailing spaces
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_git_no_verify_with_similar_but_safe_commands(self):
        """Test commands that contain no-verify but aren't git commit."""
        guard = GitNoVerifyGuard()

        safe_cases = [
            "git push --no-verify",  # Different git command
            "echo 'git commit --no-verify'",  # Echo statement
            "grep --no-verify file.txt",  # Different tool
            "git config --global commit.gpgsign false",  # Different git operation
        ]

        for command in safe_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                # Only git commit --no-verify should trigger
                if "git commit" in command and "--no-verify" in command:
                    self.assertTrue(guard.should_trigger(context))
                else:
                    self.assertFalse(guard.should_trigger(context))

    def test_git_force_push_with_complex_refs(self):
        """Test force push with complex reference specifications."""
        guard = GitForcePushGuard()

        complex_cases = [
            "git push origin HEAD:refs/heads/feature --force",
            "git push --force origin +refs/heads/*:refs/heads/*",
            "git push origin feature:main -f",
            "git push --force upstream HEAD~3:main",
        ]

        for command in complex_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_git_force_push_safe_alternatives(self):
        """Test that safe alternatives don't trigger the guard."""
        guard = GitForcePushGuard()

        safe_alternatives = [
            "git push --force-with-lease origin main",
            "git push --force-with-lease=origin/main",
            "git push origin main --force-with-lease",
            "git revert HEAD",
            "git reset --soft HEAD~1",
        ]

        for command in safe_alternatives:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(guard.should_trigger(context))

    def test_git_commands_with_shell_operators(self):
        """Test git commands combined with shell operators."""
        git_no_verify_guard = GitNoVerifyGuard()
        git_force_push_guard = GitForcePushGuard()

        shell_operator_cases = [
            "git status && git commit --no-verify",
            "git commit --no-verify || echo 'failed'",
            "git commit --no-verify; git push",
            "git status && git push --force",
            "git push --force && echo 'done'",
        ]

        for command in shell_operator_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                if "--no-verify" in command:
                    self.assertTrue(git_no_verify_guard.should_trigger(context))
                if "--force" in command and "--force-with-lease" not in command:
                    self.assertTrue(git_force_push_guard.should_trigger(context))

    def test_git_guards_with_environment_variables(self):
        """Test git commands with environment variables."""
        git_no_verify_guard = GitNoVerifyGuard()
        git_force_push_guard = GitForcePushGuard()

        env_var_cases = [
            "GIT_AUTHOR_NAME='Test' git commit --no-verify",
            "FORCE_PUSH=true git push --force",
            "export GIT_EDITOR=vim && git commit --no-verify",
        ]

        for command in env_var_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                if "--no-verify" in command:
                    self.assertTrue(git_no_verify_guard.should_trigger(context))
                if "--force" in command and "--force-with-lease" not in command:
                    self.assertTrue(git_force_push_guard.should_trigger(context))

    def test_git_guards_message_includes_command(self):
        """Test that guard messages include the problematic command."""
        git_no_verify_guard = GitNoVerifyGuard()
        git_force_push_guard = GitForcePushGuard()

        no_verify_context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git commit -m 'test' --no-verify"},
            command="git commit -m 'test' --no-verify",
        )

        force_push_context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git push origin main --force"},
            command="git push origin main --force",
        )

        no_verify_message = git_no_verify_guard.get_message(no_verify_context)
        force_push_message = git_force_push_guard.get_message(force_push_context)

        # Messages should include the actual command for context
        self.assertIn("git commit -m 'test' --no-verify", no_verify_message)
        self.assertIn("git push origin main --force", force_push_message)

    def test_git_guards_interactive_vs_non_interactive(self):
        """Test behavior difference between interactive and non-interactive modes."""
        git_no_verify_guard = GitNoVerifyGuard()

        context = GuardContext(
            tool_name="Bash", tool_input={"command": "git commit --no-verify"}, command="git commit --no-verify"
        )

        # Non-interactive should always block
        non_interactive_result = git_no_verify_guard.check(context, is_interactive=False)
        self.assertTrue(non_interactive_result.should_block)
        self.assertEqual(non_interactive_result.exit_code, 2)
        self.assertIn("safety-first policy", non_interactive_result.message)

        # Both modes should have the same default action (BLOCK)
        self.assertEqual(git_no_verify_guard.get_default_action(), GuardAction.BLOCK)


class TestGitCheckoutSafetyGuard(unittest.TestCase):
    """Test cases for GitCheckoutSafetyGuard."""

    def setUp(self):
        self.guard = GitCheckoutSafetyGuard()

    def test_should_trigger_on_dangerous_checkout(self):
        """Test that guard triggers on dangerous checkout commands."""
        dangerous_commands = [
            "git checkout main",
            "git checkout feature-branch",
            "git switch main",
            "git switch feature-branch",
            "git restore .",
            "git restore src/",
            "git checkout HEAD~1",
            "git checkout abc123",
            "git switch -",
            "git reset HEAD~1",
            "git reset --hard",
            "git reset --hard HEAD~2",
            "git reset --mixed HEAD^",
            "Git Checkout Main",  # Case insensitive
            "GIT RESET --HARD",  # Case insensitive
        ]

        for command in dangerous_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_not_trigger_on_safe_checkout(self):
        """Test that guard doesn't trigger on safe checkout commands."""
        safe_commands = [
            "git checkout -b new-branch",
            "git checkout -b feature/new-feature",
            "git checkout -- file.txt",
            "git checkout -- src/",
            "git switch -c new-branch",
            "git switch --create feature-branch",
            "git restore --staged file.txt",
            "git restore --staged .",
            "git reset --soft HEAD~1",
        ]

        for command in safe_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertFalse(self.guard.should_trigger(context), f"Should NOT trigger on: {command}")

    def test_should_not_trigger_on_non_bash_tools(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        non_bash_tools = ["Edit", "Write", "MultiEdit", "Read", "Grep"]

        for tool_name in non_bash_tools:
            with self.subTest(tool_name=tool_name):
                context = GuardContext(
                    tool_name=tool_name,
                    tool_input={"command": "git checkout main"},
                    command="git checkout main",
                )
                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_without_command(self):
        """Test that guard doesn't trigger without a command."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_git_commands(self):
        """Test that guard doesn't trigger on non-git commands."""
        non_git_commands = [
            "ls -la",
            "echo 'checkout'",
            "npm install",
            "docker checkout",  # Not git
            "python checkout.py",
        ]

        for command in non_git_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_safety_info(self):
        """Test that guard message contains essential safety information."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git checkout main"},
            command="git checkout main",
        )

        message = self.guard.get_message(context)

        # Check for key safety elements
        self.assertIn("GIT CHECKOUT/RESET SAFETY WARNING", message)
        self.assertIn("git checkout main", message)
        self.assertIn("WHY THIS IS DANGEROUS", message)
        self.assertIn("uncommitted changes", message)
        self.assertIn("git status", message)
        self.assertIn("git stash", message)
        self.assertIn("git add -A && git commit", message)
        self.assertIn("INCIDENT PREVENTION", message)
        self.assertIn("work loss", message)

        # Test reset-specific message
        reset_context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git reset --hard HEAD~1"},
            command="git reset --hard HEAD~1",
        )
        reset_message = self.guard.get_message(reset_context)
        self.assertIn("git reset --hard DESTROYS", reset_message)
        self.assertIn("git reset --soft HEAD~1", reset_message)
        self.assertIn("checkout/reset operations", reset_message)

    def test_default_action_is_block(self):
        """Test that default action is to block (safety-first)."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_message_includes_command_context(self):
        """Test that message includes the specific command being blocked."""
        test_commands = [
            "git checkout main",
            "git switch feature-branch",
            "git restore .",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                message = self.guard.get_message(context)
                self.assertIn(command, message)

    def test_interactive_vs_non_interactive_behavior(self):
        """Test behavior in interactive vs non-interactive modes."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git checkout main"},
            command="git checkout main",
        )

        # Non-interactive should always block (safety-first)
        non_interactive_result = self.guard.check(context, is_interactive=False)
        self.assertTrue(non_interactive_result.should_block)
        self.assertEqual(non_interactive_result.exit_code, 2)
        self.assertIn("safety-first policy", non_interactive_result.message)

        # Default action should be BLOCK
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        edge_cases = [
            ("git checkout", False),  # Just "git checkout" without target
            ("git checkout .", True),  # Checkout current directory
            ("git checkout HEAD", True),  # Checkout HEAD
            ("git checkout @", True),  # Checkout HEAD (@ syntax)
            ("   git checkout main   ", True),  # Whitespace handling
            ("GIT CHECKOUT MAIN", True),  # Case insensitivity
            ("git reset", False),  # Just "git reset" without flags/target
            ("git reset --soft", False),  # Soft reset should be safe (incomplete command)
            ("git reset --hard .", True),  # Hard reset of current directory
            ("GIT RESET --HARD HEAD~1", True),  # Case insensitive reset
        ]

        for command, should_trigger in edge_cases:
            with self.subTest(command=command, should_trigger=should_trigger):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                result = self.guard.should_trigger(context)
                self.assertEqual(result, should_trigger, f"Command: {command}")


class TestPreCommitConfigGuard(unittest.TestCase):
    """Test cases for PreCommitConfigGuard."""

    def setUp(self):
        self.guard = PreCommitConfigGuard()

    def test_should_trigger_on_edit_precommit_config(self):
        """Test that guard triggers when editing .pre-commit-config.yaml with dangerous content."""
        dangerous_content = """
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: ruff check --exit-zero  # This is dangerous!
        language: system
"""

        context = GuardContext(
            tool_name="Edit",
            tool_input={
                "file_path": "/project/.pre-commit-config.yaml",
                "new_string": dangerous_content,
            },
            command=None,
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_multiedit_precommit_config(self):
        """Test that guard triggers on MultiEdit with dangerous patterns."""
        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={
                "file_path": "/project/.pre-commit-config.yaml",
                "edits": [
                    {
                        "old_string": "entry: ruff check",
                        "new_string": "entry: ruff check --exit-zero",
                    }
                ],
            },
            command=None,
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_safe_precommit_edit(self):
        """Test that guard doesn't trigger on safe pre-commit config changes."""
        safe_content = """
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: ruff check  # Safe - no dangerous flags
        language: system
"""

        context = GuardContext(
            tool_name="Edit",
            tool_input={
                "file_path": "/project/.pre-commit-config.yaml",
                "new_string": safe_content,
            },
            command=None,
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_precommit_file(self):
        """Test that guard doesn't trigger on other YAML files."""
        context = GuardContext(
            tool_name="Edit",
            tool_input={
                "file_path": "/project/docker-compose.yaml",
                "new_string": "version: '3.8'\nservices: {}\n",
            },
            command=None,
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_edit_tools(self):
        """Test that guard doesn't trigger on non-file-editing tools."""
        non_edit_tools = ["Bash", "Read", "Grep", "Glob", "LS"]

        for tool_name in non_edit_tools:
            with self.subTest(tool_name=tool_name):
                context = GuardContext(
                    tool_name=tool_name,
                    tool_input={"command": "some command"},
                    command="some command",
                )
                self.assertFalse(self.guard.should_trigger(context))

    def test_dangerous_patterns_detection(self):
        """Test detection of various dangerous patterns."""
        dangerous_patterns = [
            "--exit-zero",
            "--no-verify",
            "exclude: ^.*$",
            "fail_fast: false",
            "skip: [ruff, black]",
            "stages: []",
            "# ruff check",  # Commenting out tools
            "# black .",
            "# mypy src/",
            "# pytest tests/",
        ]

        for pattern in dangerous_patterns:
            with self.subTest(pattern=pattern):
                context = GuardContext(
                    tool_name="Edit",
                    tool_input={
                        "file_path": "/.pre-commit-config.yaml",
                        "new_string": f"repos:\n  - repo: local\n    hooks:\n      - id: test\n        {pattern}\n",
                    },
                    command=None,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should detect dangerous pattern: {pattern}")

    def test_case_insensitive_detection(self):
        """Test that pattern detection is case insensitive."""
        case_variations = [
            "--EXIT-ZERO",
            "--Exit-Zero",
            "EXCLUDE: ^.*$",
            "Fail_Fast: False",
            "# RUFF check",
            "# Black .",
        ]

        for pattern in case_variations:
            with self.subTest(pattern=pattern):
                context = GuardContext(
                    tool_name="Edit",
                    tool_input={
                        "file_path": "/.pre-commit-config.yaml",
                        "new_string": f"repos:\n  - repo: local\n    hooks:\n      - id: test\n        {pattern}\n",
                    },
                    command=None,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should detect case variation: {pattern}")

    def test_get_message_contains_incident_history(self):
        """Test that error message contains incident history and alternatives."""
        context = GuardContext(
            tool_name="Edit",
            tool_input={
                "file_path": "/.pre-commit-config.yaml",
                "new_string": "entry: ruff check --exit-zero",
            },
            command=None,
        )

        message = self.guard.get_message(context)

        # Check for key safety elements
        self.assertIn("PRE-COMMIT CONFIG PROTECTION", message)
        self.assertIn("WHY THIS IS DANGEROUS", message)
        self.assertIn("production issues", message)
        self.assertIn("DANGEROUS PATTERNS DETECTED", message)
        self.assertIn("--exit-zero", message)
        self.assertIn("SAFE ALTERNATIVES", message)
        self.assertIn("Fix the underlying code issues", message)
        self.assertIn("INCIDENT HISTORY", message)
        self.assertIn("production failures", message)
        self.assertIn("Hours of debugging time", message)

    def test_default_action_is_block(self):
        """Test that default action is to block (safety-first)."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_multiedit_with_multiple_dangerous_edits(self):
        """Test MultiEdit with multiple edits containing dangerous patterns."""
        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={
                "file_path": "/.pre-commit-config.yaml",
                "edits": [
                    {
                        "old_string": "entry: ruff check",
                        "new_string": "entry: ruff check --exit-zero",
                    },
                    {
                        "old_string": "fail_fast: true",
                        "new_string": "fail_fast: false",
                    },
                ],
            },
            command=None,
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_multiedit_with_safe_edits_only(self):
        """Test MultiEdit with only safe edits."""
        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={
                "file_path": "/.pre-commit-config.yaml",
                "edits": [
                    {
                        "old_string": "language: python",
                        "new_string": "language: system",
                    },
                    {
                        "old_string": "minimum_pre_commit_version: 2.15.0",
                        "new_string": "minimum_pre_commit_version: 3.0.0",
                    },
                ],
            },
            command=None,
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_edge_cases_with_empty_inputs(self):
        """Test edge cases with empty or missing inputs."""
        edge_cases = [
            # Empty file path
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": "", "new_string": "--exit-zero"},
                "should_trigger": False,
            },
            # Missing file path
            {
                "tool_name": "Edit",
                "tool_input": {"new_string": "--exit-zero"},
                "should_trigger": False,
            },
            # Empty new_string
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/.pre-commit-config.yaml", "new_string": ""},
                "should_trigger": False,
            },
            # Missing new_string
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/.pre-commit-config.yaml"},
                "should_trigger": False,
            },
        ]

        for i, case in enumerate(edge_cases):
            with self.subTest(case=i):
                context = GuardContext(
                    tool_name=case["tool_name"],
                    tool_input=case["tool_input"],
                    command=None,
                )
                result = self.guard.should_trigger(context)
                self.assertEqual(result, case["should_trigger"], f"Edge case {i} failed")


if __name__ == "__main__":
    unittest.main()
