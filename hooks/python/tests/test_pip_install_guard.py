"""Unit tests for PipInstallGuard."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.awareness_guards import PipInstallGuard  # noqa: E402


class TestPipInstallGuard(unittest.TestCase):
    """Test cases for PipInstallGuard."""

    def setUp(self):
        self.guard = PipInstallGuard()

    def test_should_trigger_on_basic_pip_install(self):
        """Test that guard triggers on basic pip install commands."""
        pip_commands = [
            "pip install requests",
            "pip3 install django",
            "python -m pip install flask",
            "python3 -m pip install numpy",
            "pip install requests==2.28.0",
            "pip install 'django>=3.0'",
            "pip install package[extra]",
        ]

        for command in pip_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_not_trigger_on_requirements_install(self):
        """Test that guard doesn't trigger when installing from requirements file."""
        requirements_commands = [
            "pip install -r requirements.txt",
            "pip3 install -r requirements-dev.txt",
            "pip install --requirement requirements.txt",
            "python -m pip install -r requirements.txt",
            "pip install -r requirements/base.txt",
        ]

        for command in requirements_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertFalse(self.guard.should_trigger(context), f"Should NOT trigger on: {command}")

    def test_should_not_trigger_on_pip_upgrade(self):
        """Test that guard doesn't trigger on pip upgrade commands."""
        upgrade_commands = [
            "pip install --upgrade pip",
            "pip3 install --upgrade pip",
            "python -m pip install --upgrade pip",
            "python3 -m pip install --upgrade pip",
        ]

        for command in upgrade_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertFalse(self.guard.should_trigger(context), f"Should NOT trigger on: {command}")

    def test_should_not_trigger_on_user_install(self):
        """Test that guard doesn't trigger on user installation commands."""
        user_commands = [
            "pip install --user requests",
            "pip3 install --user django",
            "python -m pip install --user flask",
        ]

        for command in user_commands:
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
                    tool_input={"command": "pip install requests"},
                    command="pip install requests",
                )
                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_without_command(self):
        """Test that guard doesn't trigger without a command."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)
        self.assertFalse(self.guard.should_trigger(context))

        context = GuardContext(tool_name="Bash", tool_input={}, command="")
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_pip_commands(self):
        """Test that guard doesn't trigger on non-pip commands."""
        non_pip_commands = [
            "npm install package",
            "apt install python3-pip",
            "brew install pip",
            "git clone repo",
            "docker build .",
            "make install",
        ]

        for command in non_pip_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertFalse(self.guard.should_trigger(context), f"Should NOT trigger on: {command}")

    def test_case_insensitive_matching(self):
        """Test that guard matching is case insensitive."""
        case_variations = [
            "PIP INSTALL requests",
            "Pip Install Django",
            "PIP3 INSTALL flask",
            "PYTHON -M PIP INSTALL numpy",
        ]

        for command in case_variations:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on case variation: {command}")

    def test_get_message_extracts_package_name(self):
        """Test that guard message extracts and includes package name."""
        test_cases = [
            ("pip install requests", "requests"),
            ("pip install django==3.2", "django==3.2"),
            ("pip install 'flask>=1.0'", "'flask>=1.0'"),
            ("pip install numpy[testing]", "numpy[testing]"),
        ]

        for command, expected_package in test_cases:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                message = self.guard.get_message(context)
                self.assertIn(expected_package, message, f"Message should contain package: {expected_package}")

    def test_get_message_contains_helpful_guidance(self):
        """Test that guard message contains helpful guidance."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "pip install requests"},
            command="pip install requests",
        )

        message = self.guard.get_message(context)

        # Check for key guidance elements
        self.assertIn("PIP INSTALL BLOCKED", message)
        self.assertIn("pip install requests", message)  # Original command
        self.assertIn("WHY DIRECT PIP INSTALL IS PROBLEMATIC", message)
        self.assertIn("CORRECT APPROACH", message)
        self.assertIn("requirements.txt", message)
        self.assertIn("ADD TO REQUIREMENTS FILE", message)
        self.assertIn('echo "requests"', message)  # Package-specific example
        self.assertIn("FIND THE RIGHT REQUIREMENTS FILE", message)
        self.assertIn("PIN EXACT VERSIONS", message)
        self.assertIn("UPDATE DOCKER IMAGE", message)
        self.assertIn("docker -c musicbot compose build", message)
        self.assertIn("SPECIAL CASES", message)
        self.assertIn("pip install --upgrade pip", message)
        self.assertIn("pip install -r requirements.txt", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_complex_pip_commands(self):
        """Test guard handles complex pip commands correctly."""
        complex_cases = [
            # Should trigger
            ("pip install -U requests", True),
            ("pip install --upgrade requests", True),
            ("pip install -e .", True),
            ("pip install git+https://github.com/user/repo.git", True),
            ("pip install requests && pip install flask", True),
            # Should not trigger
            ("pip install -r requirements.txt && pip install -r requirements-dev.txt", False),
            ("pip install --user requests && echo done", False),
            ("cd project && pip install -r requirements.txt", False),
        ]

        for command, should_trigger in complex_cases:
            with self.subTest(command=command, should_trigger=should_trigger):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                result = self.guard.should_trigger(context)
                self.assertEqual(result, should_trigger, f"Command: {command}")

    def test_whitespace_handling(self):
        """Test guard handles various whitespace patterns."""
        whitespace_commands = [
            "  pip install requests  ",
            "pip  install   requests",
            "pip\tinstall\trequests",
            "\npip install requests\n",
        ]

        for command in whitespace_commands:
            with self.subTest(command=repr(command)):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {repr(command)}")

    def test_guard_name_and_description(self):
        """Test that guard has correct name and description."""
        self.assertEqual(self.guard.name, "Pip Install Prevention")
        self.assertEqual(
            self.guard.description, "Directs pip install usage to requirements files for dependency management"
        )

    def test_message_provides_actionable_commands(self):
        """Test that guard provides specific, actionable commands."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "pip install flask==2.0.1"},
            command="pip install flask==2.0.1",
        )

        message = self.guard.get_message(context)

        # Verify specific actionable commands are provided
        actionable_elements = [
            'echo "flask==2.0.1" >> requirements.txt',
            'find . -name "requirements*.txt"',
            "pip install -r requirements.txt",
            "pip freeze | grep flask",
            "docker -c musicbot compose build",
            "pip-compile requirements.in",
        ]

        for element in actionable_elements:
            self.assertIn(element, message, f"Message should contain actionable element: {element}")


if __name__ == "__main__":
    unittest.main()
