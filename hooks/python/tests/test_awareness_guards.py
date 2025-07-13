"""Unit tests for awareness guards."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.awareness_guards import DirectoryAwarenessGuard, TestSuiteEnforcementGuard  # noqa: E402


class TestDirectoryAwarenessGuard(unittest.TestCase):
    """Test cases for DirectoryAwarenessGuard."""

    def setUp(self):
        self.guard = DirectoryAwarenessGuard()

    def test_should_trigger_on_relative_path_commands(self):
        """Test that guard triggers on commands with relative paths."""
        test_cases = [
            "cd relative/path",
            "./run_script.sh",
            "../config/setup.sh",
            "script.sh",
            "python local_script.py",
            "make build",
            "npm install",
            "yarn start",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_absolute_path_commands(self):
        """Test that guard doesn't trigger on absolute path commands."""
        test_cases = [
            "cd /absolute/path",
            "/usr/bin/script.sh",
            "python /full/path/script.py",
            "ls /home/user/documents",
            "/bin/cat /etc/hosts",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_location_independent_commands(self):
        """Test that guard doesn't trigger on location-independent commands."""
        test_cases = ["ls", "git status", "docker ps", "ps aux", "top", "htop", "whoami", "date"]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_when_pwd_already_present(self):
        """Test that guard doesn't trigger when command already starts with pwd."""
        test_cases = ["pwd && ./run_script.sh", "pwd; cd relative/path", "pwd && make build"]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_bash_tools(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        context = GuardContext(
            tool_name="Edit", tool_input={"file_path": "./relative/file.py"}, file_path="./relative/file.py"
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_empty_command(self):
        """Test that guard doesn't trigger on empty commands."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_project_structure(self):
        """Test that message contains project structure information."""
        context = GuardContext(tool_name="Bash", tool_input={"command": "./run_script.sh"}, command="./run_script.sh")

        message = self.guard.get_message(context)

        self.assertIn("DIRECTORY AWARENESS", message)
        self.assertIn("./run_script.sh", message)
        self.assertIn("PROJECT STRUCTURE REFERENCE", message)
        self.assertIn("spotidal/", message)
        self.assertIn("sonos_server", message)
        self.assertIn("gemini_playlist_suggester", message)
        self.assertIn("pwd", message)

    def test_default_action_is_allow(self):
        """Test that default action is to allow (warning only)."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.ALLOW)


class TestTestSuiteEnforcementGuard(unittest.TestCase):
    """Test cases for TestSuiteEnforcementGuard."""

    def setUp(self):
        self.guard = TestSuiteEnforcementGuard()

    def test_should_trigger_on_completion_claims(self):
        """Test that guard triggers on completion claim commands."""
        test_cases = [
            "echo 'Feature complete'",
            "echo 'Implementation done'",
            "echo 'Tests finished'",
            "echo 'System working'",
            "echo 'Ready for production'",
            "echo 'Bug fixed'",
            "echo 'All tests passed'",
            "echo 'Feature complete'",
            "echo 'Implementation complete'",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_progress_statements(self):
        """Test that guard doesn't trigger on progress statements."""
        test_cases = [
            "echo 'Starting work'",
            "echo 'In progress'",
            "echo 'Testing in progress'",
            "git commit -m 'Work in progress'",
            "echo 'Debugging issue'",
            "echo 'Implementing feature'",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_echo_commands(self):
        """Test that guard doesn't trigger on non-completion commands."""
        test_cases = ["ls files", "cat README.md", "git status", "docker ps", "make build"]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_bash_tools(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        context = GuardContext(
            tool_name="Write", tool_input={"content": "Feature complete"}, content="Feature complete"
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_empty_command(self):
        """Test that guard doesn't trigger on empty commands."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_test_commands(self):
        """Test that message contains all required test commands."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "echo 'Feature complete'"}, command="echo 'Feature complete'"
        )

        message = self.guard.get_message(context)

        # Check for main structure
        self.assertIn("TEST ENFORCEMENT", message)
        self.assertIn("echo 'Feature complete'", message)
        self.assertIn("FULL containerized test suite", message)

        # Check for all service test commands
        self.assertIn("./run_full_test_suite.sh", message)
        self.assertIn("./run_all_real_integration_tests.sh", message)
        self.assertIn("./run-react-tests.sh all", message)
        self.assertIn("./run_integration_tests.sh --playlists 25", message)
        self.assertIn("./run_worker_tests.sh", message)

        # Check for golden testing rule
        self.assertIn("GOLDEN TESTING RULE", message)
        self.assertIn("./curl_wrapper.sh", message)
        self.assertIn("docker compose up", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)


class TestAwarenessGuardEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for awareness guards."""

    def test_directory_awareness_with_complex_commands(self):
        """Test directory awareness with complex command patterns."""
        guard = DirectoryAwarenessGuard()

        complex_cases = [
            ("./script.sh arg1 arg2", True),  # Script with arguments
            ("cd ../parent && ./child_script.sh", True),  # Command chaining
            ("make build VERBOSE=1", True),  # Make with variables
            ("npm install --production", True),  # NPM with flags
            ("python -m pytest tests/", True),  # Python module with relative path
            ("docker run -v ./data:/app/data ubuntu", True),  # Docker with relative mount
        ]

        for command, should_trigger in complex_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertEqual(guard.should_trigger(context), should_trigger)

    def test_directory_awareness_with_quoted_paths(self):
        """Test directory awareness with quoted relative paths."""
        guard = DirectoryAwarenessGuard()

        quoted_cases = [
            "cd 'relative path with spaces'",
            'cd "another relative path"',
            "./script with spaces.sh",
            'python "local script.py"',
        ]

        for command in quoted_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_test_suite_enforcement_with_variations(self):
        """Test test suite enforcement with completion claim variations."""
        guard = TestSuiteEnforcementGuard()

        completion_variations = [
            ('echo "Feature is complete"', True),
            ("echo 'Implementation finished successfully'", True),
            ("echo 'All tests are passing'", True),
            ("echo 'System is now working'", True),
            ("echo 'Bug has been fixed'", True),
            ("echo 'Development complete'", True),
            ("echo 'Starting the feature'", False),  # Not completion
            ("echo 'Work is in progress'", False),  # Not completion
            ("echo 'Currently debugging'", False),  # Not completion
        ]

        for command, should_trigger in completion_variations:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertEqual(guard.should_trigger(context), should_trigger)

    def test_test_suite_enforcement_case_insensitive(self):
        """Test that test suite enforcement is case insensitive."""
        guard = TestSuiteEnforcementGuard()

        case_variations = [
            "echo 'FEATURE COMPLETE'",
            "echo 'Feature Complete'",
            "echo 'feature complete'",
            "echo 'IMPLEMENTATION DONE'",
            "echo 'Tests FINISHED'",
        ]

        for command in case_variations:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_awareness_guards_with_shell_operators(self):
        """Test awareness guards with shell operators."""
        dir_guard = DirectoryAwarenessGuard()
        test_guard = TestSuiteEnforcementGuard()

        shell_operator_cases = [
            ("ls && ./script.sh", True, False),  # Directory aware but not completion
            ("cd dir && echo 'Feature complete'", True, True),  # Both
            ("./build.sh || echo 'Build failed'", True, False),  # Directory only
            ("echo 'Tests finished' && git commit", False, True),  # Test enforcement only
        ]

        for command, dir_should_trigger, test_should_trigger in shell_operator_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertEqual(dir_guard.should_trigger(context), dir_should_trigger)
                self.assertEqual(test_guard.should_trigger(context), test_should_trigger)

    def test_awareness_guards_interactive_behavior(self):
        """Test awareness guards behavior in different modes."""
        dir_guard = DirectoryAwarenessGuard()
        test_guard = TestSuiteEnforcementGuard()

        dir_context = GuardContext(tool_name="Bash", tool_input={"command": "./script.sh"}, command="./script.sh")

        test_context = GuardContext(
            tool_name="Bash", tool_input={"command": "echo 'Feature complete'"}, command="echo 'Feature complete'"
        )

        # Directory awareness should allow (warning only)
        dir_result = dir_guard.check(dir_context, is_interactive=False)
        self.assertFalse(dir_result.should_block)
        self.assertEqual(dir_result.exit_code, 0)

        # Test enforcement should block
        test_result = test_guard.check(test_context, is_interactive=False)
        self.assertTrue(test_result.should_block)
        self.assertEqual(test_result.exit_code, 2)

    def test_awareness_guards_message_completeness(self):
        """Test that awareness guard messages contain all required information."""
        dir_guard = DirectoryAwarenessGuard()
        test_guard = TestSuiteEnforcementGuard()

        dir_context = GuardContext(tool_name="Bash", tool_input={"command": "./deploy.sh"}, command="./deploy.sh")

        test_context = GuardContext(
            tool_name="Bash", tool_input={"command": "echo 'System ready'"}, command="echo 'System ready'"
        )

        dir_message = dir_guard.get_message(dir_context)
        test_message = test_guard.get_message(test_context)

        # Directory awareness message requirements
        dir_required_content = [
            "DIRECTORY AWARENESS",
            "./deploy.sh",
            "pwd",
            "PROJECT STRUCTURE REFERENCE",
            "spotidal/",
            "sonos_server",
            "gemini_playlist_suggester",
        ]

        for content in dir_required_content:
            self.assertIn(content, dir_message, f"Missing in dir message: {content}")

        # Test enforcement message requirements
        test_required_content = [
            "TEST ENFORCEMENT",
            "echo 'System ready'",
            "FULL containerized test suite",
            "./run_full_test_suite.sh",
            "./run_all_real_integration_tests.sh",
            "./run-react-tests.sh all",
            "GOLDEN TESTING RULE",
            "./curl_wrapper.sh",
        ]

        for content in test_required_content:
            self.assertIn(content, test_message, f"Missing in test message: {content}")

    def test_awareness_guards_performance_with_long_commands(self):
        """Test awareness guards performance with very long commands."""
        dir_guard = DirectoryAwarenessGuard()
        test_guard = TestSuiteEnforcementGuard()

        # Create very long commands
        long_args = " ".join([f"arg{i}" for i in range(100)])
        long_dir_command = f"./script.sh {long_args}"
        long_test_command = f"echo 'Feature complete with many details: {long_args}'"

        dir_context = GuardContext(tool_name="Bash", tool_input={"command": long_dir_command}, command=long_dir_command)

        test_context = GuardContext(
            tool_name="Bash", tool_input={"command": long_test_command}, command=long_test_command
        )

        # Should still trigger correctly despite long commands
        self.assertTrue(dir_guard.should_trigger(dir_context))
        self.assertTrue(test_guard.should_trigger(test_context))

        # Messages should handle long commands gracefully
        dir_message = dir_guard.get_message(dir_context)
        test_message = test_guard.get_message(test_context)

        # Should contain the command (possibly truncated but recognizable)
        self.assertIn("./script.sh", dir_message)
        self.assertIn("Feature complete", test_message)


if __name__ == "__main__":
    unittest.main()
