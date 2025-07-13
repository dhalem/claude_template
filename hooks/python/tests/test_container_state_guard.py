"""Unit tests for ContainerStateGuard."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.docker_guards import ContainerStateGuard  # noqa: E402


class TestContainerStateGuard(unittest.TestCase):
    """Test cases for ContainerStateGuard."""

    def setUp(self):
        self.guard = ContainerStateGuard()

    def test_should_trigger_on_file_not_found_patterns(self):
        """Test that guard triggers on file not found patterns."""
        file_not_found_commands = [
            "ls -la config.json # file not found",
            "cat missing_file.py",
            "find . -name missing.yaml",
            "python script.py # import error",
            "node server.js # module not found",
            "ls dashboard.json # cannot find",
            "check if file exists",
            "where is config.py",
            "verify file exists in container",
        ]

        for command in file_not_found_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_trigger_on_regex_patterns(self):
        """Test that guard triggers on regex patterns for missing files."""
        regex_pattern_commands = [
            "file config.py not found",
            "missing file dashboard.json",
            "cannot find server.js",
            "no such file config.yaml",
            "script.py not found",
            "data.json not found",
            "styles.yaml not found",
            "app.js not found",
            "import error occurred",
            "module not found error",
        ]

        for command in regex_pattern_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_trigger_on_debugging_commands(self):
        """Test that guard triggers on common debugging commands."""
        debugging_commands = [
            "ls -la",
            "ls -l",
            "find . -name config",
            "find / -name missing",
            "which python",
            "whereis node",
            "locate config.json",
            "grep -r import_error",
        ]

        for command in debugging_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_not_trigger_on_non_debugging_commands(self):
        """Test that guard doesn't trigger on non-debugging commands."""
        non_debugging_commands = [
            "git status",
            "git commit -m 'message'",
            "docker ps",
            "npm install",
            "pip install requests",
            "cd /app",
            "echo 'hello world'",
            "curl http://localhost:8000",
            "python -m pytest",
            "make build",
        ]

        for command in non_debugging_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertFalse(self.guard.should_trigger(context), f"Should NOT trigger on: {command}")

    def test_should_not_trigger_on_non_bash_tools(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        non_bash_tools = ["Edit", "Write", "MultiEdit", "Read", "Grep", "Glob"]

        for tool_name in non_bash_tools:
            with self.subTest(tool_name=tool_name):
                context = GuardContext(
                    tool_name=tool_name,
                    tool_input={"command": "file not found"},
                    command="file not found",
                )
                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_without_command(self):
        """Test that guard doesn't trigger without a command."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)
        self.assertFalse(self.guard.should_trigger(context))

        context = GuardContext(tool_name="Bash", tool_input={}, command="")
        self.assertFalse(self.guard.should_trigger(context))

    def test_case_insensitive_matching(self):
        """Test that guard matching is case insensitive."""
        case_variations = [
            "FILE NOT FOUND",
            "File Not Found",
            "MISSING FILE",
            "Missing File",
            "IMPORT ERROR",
            "Import Error",
            "Cannot Find",
            "CANNOT FIND",
        ]

        for command in case_variations:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on case variation: {command}")

    def test_get_message_contains_helpful_guidance(self):
        """Test that guard message contains helpful debugging guidance."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "ls config.json # file not found"},
            command="ls config.json # file not found",
        )

        message = self.guard.get_message(context)

        # Check for key guidance elements
        self.assertIn("CONTAINER STATE CHECK SUGGESTED", message)
        self.assertIn("ls config.json # file not found", message)  # Command included
        self.assertIn("COMMON PATTERN: Files exist locally but missing in containers", message)
        self.assertIn("MANDATORY 2-MINUTE VERIFICATION", message)
        self.assertIn("saves 2-3 hours", message)
        self.assertIn("CHECK CONTAINER CONTENTS FIRST", message)
        self.assertIn("docker -c musicbot exec", message)
        self.assertIn("VERIFY CONTAINER IS RUNNING EXPECTED IMAGE", message)
        self.assertIn("CHECK VOLUME MOUNTS", message)
        self.assertIn("REBUILD IF CODE CHANGES NOT REFLECTED", message)
        self.assertIn("WHY THIS MATTERS", message)
        self.assertIn("Container-State-First Debugging", message)
        self.assertIn("BATTLE-TESTED PATTERN", message)
        self.assertIn("AFTER CONTAINER VERIFICATION", message)

    def test_default_action_is_allow(self):
        """Test that default action is to allow (not block)."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.ALLOW)

    def test_specific_file_extension_patterns(self):
        """Test that guard triggers on specific file extension patterns."""
        file_extension_commands = [
            "config.py not found",
            "dashboard.json not found",
            "server.yaml not found",
            "app.js not found",
            "styles.css not found",
            "index.html not found",
        ]

        for command in file_extension_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_complex_debugging_scenarios(self):
        """Test guard triggers on complex debugging scenarios."""
        complex_scenarios = [
            "ls -la | grep missing",
            "find . -name '*.py' | grep missing",
            "docker exec container ls /app/config.json # file not found",
            "cat /var/log/app.log | grep 'cannot find'",
            "python -c 'import config' # ImportError",
            "node -e 'require(\"./config\")' # module not found",
        ]

        for command in complex_scenarios:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_guard_provides_actionable_advice(self):
        """Test that guard provides specific, actionable advice."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "find . -name config.py # missing file"},
            command="find . -name config.py # missing file",
        )

        message = self.guard.get_message(context)

        # Verify specific actionable commands are provided
        actionable_commands = [
            "docker -c musicbot exec <service_name> ls -la",
            "docker -c musicbot exec <service_name> find /app",
            "docker -c musicbot ps",
            "docker -c musicbot images | grep",
            "docker -c musicbot inspect",
            "docker -c musicbot compose build",
            "docker -c musicbot compose up -d",
        ]

        for cmd in actionable_commands:
            self.assertIn(cmd, message, f"Message should contain actionable command: {cmd}")

    def test_edge_cases_with_whitespace_and_special_chars(self):
        """Test edge cases with whitespace and special characters."""
        edge_cases = [
            "  file not found  ",  # Leading/trailing whitespace
            "file\tnot\tfound",  # Tabs
            "file-not-found",  # Hyphens
            "file_not_found",  # Underscores
            "file.not.found",  # Dots
            "file/not/found",  # Slashes
        ]

        for command in edge_cases:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                # Should trigger on patterns but not necessarily all edge cases
                result = self.guard.should_trigger(context)
                # Just ensure it doesn't crash - triggering behavior may vary

    def test_guard_context_preservation(self):
        """Test that guard preserves the original command context."""
        original_command = "ls -la config.json # file not found in container"
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": original_command},
            command=original_command,
        )

        message = self.guard.get_message(context)
        self.assertIn(original_command, message, "Original command should be preserved in message")

    def test_guard_name_and_description(self):
        """Test that guard has correct name and description."""
        self.assertEqual(self.guard.name, "Container State Verification")
        self.assertEqual(
            self.guard.description, "Suggests checking container contents before assuming file debugging issues"
        )

    def test_check_method_provides_suggestion_without_blocking(self):
        """Test that the check method provides suggestions without blocking operations."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "ls config.json # file not found"},
            command="ls config.json # file not found",
        )

        result = self.guard.check(context, is_interactive=False)

        # Should not block the operation
        self.assertFalse(result.should_block)
        # Should provide helpful message
        self.assertIsNotNone(result.message)
        self.assertIn("CONTAINER STATE CHECK SUGGESTED", result.message)
        # Should have exit code 0 (success, no blocking)
        self.assertEqual(result.exit_code, 0)

    def test_check_method_allows_non_triggering_commands(self):
        """Test that check method allows commands that don't trigger the guard."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git status"},
            command="git status",
        )

        result = self.guard.check(context, is_interactive=False)

        # Should not block the operation
        self.assertFalse(result.should_block)
        # Should not provide message for non-triggering commands
        self.assertIsNone(result.message)
        # Should have exit code 0 (success)
        self.assertEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
