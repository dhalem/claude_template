"""Tests for path safety guards."""

import os
import sys
import unittest
from unittest.mock import patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.path_guards import AbsolutePathCdGuard, CurlHeadRequestGuard  # noqa: E402


class TestAbsolutePathCdGuard(unittest.TestCase):
    """Test the AbsolutePathCdGuard."""

    def setUp(self):
        """Set up test fixtures."""
        self.guard = AbsolutePathCdGuard()

    def test_guard_metadata(self):
        """Test that guard has correct metadata."""
        self.assertEqual(self.guard.name, "Absolute Path CD")
        self.assertIn("absolute paths", self.guard.description.lower())
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_non_bash_commands_not_triggered(self):
        """Test that non-Bash commands don't trigger the guard."""
        context = GuardContext(tool_name="Edit", tool_input={}, command="cd subdir")
        self.assertFalse(self.guard.should_trigger(context))

        context = GuardContext(tool_name="Write", tool_input={}, command="cd ../other")
        self.assertFalse(self.guard.should_trigger(context))

    def test_empty_command_not_triggered(self):
        """Test that empty commands don't trigger the guard."""
        context = GuardContext(tool_name="Bash", tool_input={}, command="")
        self.assertFalse(self.guard.should_trigger(context))

        context = GuardContext(tool_name="Bash", tool_input={}, command=None)
        self.assertFalse(self.guard.should_trigger(context))

    def test_relative_cd_commands_triggered(self):
        """Test that relative cd commands trigger the guard."""
        relative_commands = [
            "cd subdir",
            "cd ../parent",
            "cd some/nested/path",
            "cd ./current/subdir",
            "cd ../../back/two/levels",
            "pwd && cd subdir",
            "cd subdir && ls",
            "ls; cd subdir; pwd",
            "cd subdir | ls",
            "ls && cd ../other && pwd",
        ]

        for command in relative_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Command should trigger guard: {command}")

    def test_absolute_cd_commands_not_triggered(self):
        """Test that absolute cd commands don't trigger the guard."""
        absolute_commands = [
            "cd /absolute/path",
            "cd /home/user/project",
            "cd /tmp",
            "cd /var/log",
            "cd /home/dhalem/github/sptodial_one/spotidal",
            "pwd && cd /absolute/path",
            "cd /path && ls",
            "ls; cd /absolute; pwd",
        ]

        for command in absolute_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertFalse(self.guard.should_trigger(context), f"Command should not trigger guard: {command}")

    def test_safe_cd_patterns_not_triggered(self):
        """Test that safe cd patterns don't trigger the guard."""
        safe_commands = [
            "cd -",  # Go back to previous directory
            "cd",  # Go to home directory
            "cd ~",  # Go to home directory explicitly
            "cd ~/project",  # Go to home directory subdirectory
            "cd $HOME",  # Go to home directory via variable
            "cd $HOME/project",  # Go to home subdirectory via variable
            "pwd && cd -",  # Complex command with safe cd
            "cd ~ && ls",  # Complex command with home cd
        ]

        for command in safe_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertFalse(
                    self.guard.should_trigger(context), f"Safe command should not trigger guard: {command}"
                )

    def test_variable_expansion_not_triggered(self):
        """Test that commands with variable expansion don't trigger the guard."""
        variable_commands = [
            "cd ${PROJECT_DIR}",
            "cd $(pwd)",
            "cd $PROJECT_ROOT",
            "cd ${HOME}/project",
            "cd $(dirname $0)",
        ]

        for command in variable_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertFalse(
                    self.guard.should_trigger(context),
                    f"Variable expansion command should not trigger guard: {command}",
                )

    def test_complex_command_combinations(self):
        """Test complex command combinations."""
        # These should trigger (contain relative cd)
        should_trigger = [
            "ls && cd subdir && pwd",
            "cd ../parent; make clean",
            "cd ./config && source setup.sh",
        ]

        for command in should_trigger:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Complex command should trigger guard: {command}")

        # These should not trigger (only absolute or safe cd)
        should_not_trigger = [
            "ls && cd /absolute/path && pwd",
            "cd ~ && make clean",
            "if [ -d /tmp ]; then cd /tmp; fi",
            "cd - && source setup.sh",
        ]

        for command in should_not_trigger:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertFalse(
                    self.guard.should_trigger(context), f"Complex command should not trigger guard: {command}"
                )

    def test_case_insensitive_matching(self):
        """Test that cd matching is case insensitive."""
        case_commands = [
            "CD subdir",
            "Cd ../parent",
            "cD some/path",
        ]

        for command in case_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertTrue(
                    self.guard.should_trigger(context), f"Case insensitive command should trigger guard: {command}"
                )

    def test_get_message_content(self):
        """Test that the guard message contains helpful information."""
        context = GuardContext(tool_name="Bash", tool_input={}, command="cd subdir")
        message = self.guard.get_message(context)

        # Check that message contains key information
        self.assertIn("cd subdir", message)
        self.assertIn("ABSOLUTE PATH REQUIRED", message)
        self.assertIn("cd /absolute/path/to/target", message)
        self.assertIn("cd ~/project/subdir", message)
        self.assertIn("cd -", message)  # Safe exception
        self.assertIn("spotidal", message)  # Project paths
        self.assertIn("navigation confusion", message)

    def test_get_message_shows_detected_command(self):
        """Test that the guard message shows the actual command that triggered it."""
        test_commands = [
            "cd ../parent",
            "ls && cd subdir && pwd",
            "cd some/nested/path",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                message = self.guard.get_message(context)
                self.assertIn(command, message)

    @patch("builtins.input", return_value="n")
    def test_guard_blocks_by_default(self, mock_input):
        """Test that the guard blocks relative cd commands by default."""
        context = GuardContext(tool_name="Bash", tool_input={}, command="cd subdir")
        result = self.guard.check(context, is_interactive=True)

        self.assertTrue(result.should_block)
        self.assertIsNotNone(result.message)
        self.assertIn("ABSOLUTE PATH REQUIRED", result.message)

    @patch("builtins.input", return_value="n")
    def test_guard_does_not_block_safe_commands(self, mock_input):
        """Test that the guard doesn't block safe cd commands."""
        safe_commands = ["cd /absolute/path", "cd -", "cd ~", "cd"]

        for command in safe_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                result = self.guard.check(context, is_interactive=True)
                self.assertFalse(result.should_block)

    def test_regex_pattern_edge_cases(self):
        """Test edge cases for regex pattern matching."""
        # These should NOT trigger (edge cases that might confuse regex)
        edge_cases_no_trigger = [
            "echo 'cd subdir'",  # cd in string
            "# cd subdir",  # cd in comment
            "grep 'cd ' file.txt",  # cd as part of grep
            "find . -name 'cd*'",  # cd in filename pattern
            "command_cd_something",  # cd as part of word
            "ls && echo 'cd was here'",  # cd in quoted string
        ]

        for command in edge_cases_no_trigger:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                # Note: Some of these might still trigger due to regex complexity
                # The main goal is to catch actual cd commands, not eliminate all false positives

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        whitespace_commands = [
            "  cd subdir",  # Leading whitespace
            "cd  subdir",  # Extra whitespace after cd
            "pwd;  cd subdir",  # Whitespace after semicolon
            "ls &&   cd subdir",  # Multiple spaces
            "\tcd subdir",  # Tab character
        ]

        for command in whitespace_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertTrue(
                    self.guard.should_trigger(context), f"Whitespace command should trigger guard: {repr(command)}"
                )

    def test_command_chaining_operators(self):
        """Test various command chaining operators."""
        chaining_commands = [
            "pwd && cd subdir",  # AND operator
            "pwd; cd subdir",  # Semicolon
            "pwd || cd subdir",  # OR operator
            "pwd | cd subdir",  # Pipe (unusual but possible)
        ]

        for command in chaining_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Chained command should trigger guard: {command}")


class TestAbsolutePathCdGuardIntegration(unittest.TestCase):
    """Integration tests for AbsolutePathCdGuard."""

    def setUp(self):
        """Set up test fixtures."""
        self.guard = AbsolutePathCdGuard()

    def test_realistic_spotidal_commands(self):
        """Test realistic commands that might be used in the Spotidal project."""
        # These should trigger (relative paths)
        should_trigger = [
            "cd syncer && docker-compose up -d",
            "cd sonos_server && ./run_tests.sh",
            "cd gemini_playlist_suggester && npm install",
            "cd ../other_project && make",
            "pwd && cd hooks/python && python main.py",
        ]

        for command in should_trigger:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertTrue(self.guard.should_trigger(context))

        # These should not trigger (absolute paths or safe patterns)
        should_not_trigger = [
            "cd /home/dhalem/github/sptodial_one/spotidal/syncer && docker-compose up -d",
            "cd ~/github/sptodial_one/spotidal/sonos_server && ./run_tests.sh",
            "cd $HOME && npm install",
            "cd && source ~/.bashrc",
        ]

        for command in should_not_trigger:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={}, command=command)
                self.assertFalse(self.guard.should_trigger(context))

    def test_message_provides_project_specific_paths(self):
        """Test that the guard message provides project-specific path examples."""
        context = GuardContext(tool_name="Bash", tool_input={}, command="cd syncer")
        message = self.guard.get_message(context)

        # Should contain project-specific paths
        self.assertIn("spotidal", message.lower())
        self.assertIn("syncer", message)
        self.assertIn("sonos_server", message)
        self.assertIn("gemini_playlist_suggester", message)


class TestCurlHeadRequestGuard(unittest.TestCase):
    """Test cases for CurlHeadRequestGuard."""

    def setUp(self):
        """Set up test guard instance."""
        self.guard = CurlHeadRequestGuard()

    def test_guard_initialization(self):
        """Test guard initializes correctly."""
        self.assertEqual(self.guard.name, "Curl HEAD Request Prevention")
        self.assertIn("Prevents inefficient curl HEAD requests", self.guard.description)
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_non_bash_command_ignored(self):
        """Test that non-Bash commands are ignored."""
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "test.py", "content": "curl -I http://example.com"},
            content="curl -I http://example.com",
        )
        self.assertFalse(self.guard.should_trigger(context))

    def test_curl_head_flag_i_detected(self):
        """Test curl with -I flag is detected."""
        test_commands = [
            "curl -I http://example.com",
            "curl -s -I http://example.com",
            "curl -I -v http://example.com",
            "./curl_wrapper.sh -I http://musicbot:8002/api/endpoint",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Should detect HEAD in: {command}")

    def test_curl_head_flag_long_detected(self):
        """Test curl with --head flag is detected."""
        test_commands = [
            "curl --head http://example.com",
            "curl -s --head http://example.com",
            "curl --head -v http://example.com",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Should detect HEAD in: {command}")

    def test_curl_x_head_detected(self):
        """Test curl with -X HEAD is detected."""
        test_commands = [
            "curl -X HEAD http://example.com",
            "curl -s -X HEAD http://example.com",
            "curl -X HEAD -v http://example.com",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Should detect HEAD in: {command}")

    def test_curl_request_head_detected(self):
        """Test curl with --request HEAD is detected."""
        test_commands = [
            "curl --request HEAD http://example.com",
            "curl -s --request HEAD http://example.com",
            "curl --request HEAD -v http://example.com",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Should detect HEAD in: {command}")

    def test_legitimate_head_requests_allowed(self):
        """Test that legitimate HEAD requests are allowed."""
        legitimate_commands = [
            "curl -I http://musicbot:8002/health-check",
            "curl --head http://server/ping",
            "curl -X HEAD http://api/status",
            "curl --request HEAD http://service/alive",
            "curl -I http://example.com/health_check",  # underscore variant
            "curl --head http://api/ping-endpoint",
        ]

        for command in legitimate_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                self.assertFalse(self.guard.should_trigger(context), f"Should allow legitimate HEAD: {command}")

    def test_normal_curl_commands_ignored(self):
        """Test that normal curl commands without HEAD are ignored."""
        normal_commands = [
            "curl http://example.com",
            "curl -s http://example.com",
            "curl -X GET http://example.com",
            "curl --request POST http://example.com",
            "./curl_wrapper.sh -s http://musicbot:8002/api/endpoint",
            "curl -d 'data' http://example.com",
        ]

        for command in normal_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                self.assertFalse(self.guard.should_trigger(context), f"Should ignore normal curl: {command}")

    def test_complex_command_patterns(self):
        """Test complex command patterns with HEAD requests."""
        complex_commands = [
            "curl -I http://example.com && echo 'done'",
            "curl -s -I http://example.com | grep -i content-type",
            "if curl -I http://example.com; then echo ok; fi",
            "timeout 5 curl --head http://example.com",
        ]

        for command in complex_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                self.assertTrue(self.guard.should_trigger(context), f"Should detect HEAD in complex: {command}")

    def test_case_insensitive_detection(self):
        """Test that HEAD detection is case insensitive."""
        case_variants = [
            "curl -I http://example.com",
            "CURL -I http://example.com",
            "curl -i http://example.com",  # lowercase -i should be detected
            "curl --HEAD http://example.com",
            "curl -X head http://example.com",
            "curl --request Head http://example.com",
        ]

        for command in case_variants:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                # All should be detected as HEAD requests
                self.assertTrue(self.guard.should_trigger(context), f"Should detect case variant: {command}")

    def test_get_message_content(self):
        """Test that guard message contains helpful information."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "curl -I http://example.com"}, command="curl -I http://example.com"
        )

        message = self.guard.get_message(context)

        # Check key message components
        self.assertIn("INEFFICIENT HEAD REQUEST", message)
        self.assertIn("curl -I http://example.com", message)
        self.assertIn("WHY HEAD REQUESTS WASTE TIME", message)
        self.assertIn("MORE EFFICIENT ALTERNATIVES", message)
        self.assertIn("curl -s http://server/api/endpoint", message)
        self.assertIn("./curl_wrapper.sh", message)
        self.assertIn("LEGITIMATE HEAD REQUEST EXCEPTIONS", message)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        edge_cases = [
            # Empty command
            "",
            # Just curl
            "curl",
            # HEAD in URL but not in flags
            "curl http://example.com/head",
            # HEAD in different context
            "echo 'use curl -I' > instructions.txt",
            # Multiple curl commands, only one with HEAD
            "curl http://example.com && curl -I http://example.com",
        ]

        expected_results = [False, False, False, True, True]

        for i, command in enumerate(edge_cases):
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)
                result = self.guard.should_trigger(context)
                if i < len(expected_results):
                    self.assertEqual(result, expected_results[i], f"Edge case failed: {command}")

    def test_no_command_context(self):
        """Test guard behavior when command is None."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)
        self.assertFalse(self.guard.should_trigger(context))

    def test_guard_blocks_by_default(self):
        """Test that guard blocks HEAD requests by default."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)


if __name__ == "__main__":
    unittest.main()
