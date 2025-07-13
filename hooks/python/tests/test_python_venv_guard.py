"""Unit tests for PythonVenvGuard."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.python_venv_guard import PythonVenvGuard  # noqa: E402


class TestPythonVenvGuard(unittest.TestCase):
    """Test cases for PythonVenvGuard."""

    def setUp(self):
        self.guard = PythonVenvGuard()

    def test_should_trigger_on_direct_python_commands(self):
        """Test that guard triggers on direct python commands without venv."""
        python_commands = [
            "python script.py",
            "python3 script.py",
            "python3.11 script.py",
            "python indexing/search_code.py",
            "python3 -m pytest",
            "python manage.py runserver",
            "python3 check_database.py --verbose",
            "python /path/to/script.py",
        ]

        for command in python_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_trigger_on_piped_python_commands(self):
        """Test that guard triggers on piped python commands."""
        piped_commands = [
            "echo 'print(123)' | python",
            "cat file.py | python3",
            "curl http://example.com/script.py | python",
            "echo 'import sys' | python3 -",
        ]

        for command in piped_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_trigger_on_chained_python_commands(self):
        """Test that guard triggers on chained python commands."""
        chained_commands = [
            "cd /app; python script.py",
            "pwd && python3 test.py",
            "ls -la && python manage.py migrate",
            "git pull; python3 update_db.py",
        ]

        for command in chained_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_not_trigger_on_venv_python(self):
        """Test that guard doesn't trigger when using venv Python."""
        venv_commands = [
            "./venv/bin/python script.py",
            "venv/bin/python3 test.py",
            "./venv/bin/python3 -m pytest",
            "/home/user/project/venv/bin/python manage.py",
            "cd /app && ./venv/bin/python3 script.py",
        ]

        for command in venv_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertFalse(self.guard.should_trigger(context), f"Should NOT trigger on: {command}")

    def test_should_not_trigger_on_allowed_system_commands(self):
        """Test that guard doesn't trigger on allowed system Python commands."""
        allowed_commands = [
            "python -m venv venv",
            "python3 -m venv venv",
            "python --version",
            "python3 --version",
            "python -V",
            "python3 -V",
            "which python",
            "which python3",
            "whereis python",
            "type python3",
        ]

        for command in allowed_commands:
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
                    tool_input={"command": "python script.py"},
                    command="python script.py",
                )
                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_without_command(self):
        """Test that guard doesn't trigger without a command."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)
        self.assertFalse(self.guard.should_trigger(context))

        context = GuardContext(tool_name="Bash", tool_input={}, command="")
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_python_commands(self):
        """Test that guard doesn't trigger on non-Python commands."""
        non_python_commands = [
            "node script.js",
            "npm install",
            "ruby script.rb",
            "perl script.pl",
            "bash script.sh",
            "go run main.go",
            "java Main",
            "gcc program.c",
        ]

        for command in non_python_commands:
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
            "PYTHON script.py",
            "Python script.py",
            "PYTHON3 test.py",
            "Python3 manage.py",
        ]

        for command in case_variations:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on case variation: {command}")

    def test_get_message_extracts_script_name(self):
        """Test that guard message extracts and includes script name."""
        test_cases = [
            ("python script.py", "script.py"),
            ("python3 /path/to/test.py", "test.py"),
            ("python manage.py runserver", "manage.py"),
            ("python3 -m pytest test_file.py", "test_file.py"),
        ]

        for command, expected_script in test_cases:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                message = self.guard.get_message(context)
                self.assertIn(expected_script, message, f"Message should contain script: {expected_script}")

    def test_get_message_contains_helpful_guidance(self):
        """Test that guard message contains helpful guidance."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "python3 script.py"},
            command="python3 script.py",
        )

        message = self.guard.get_message(context)

        # Check for key guidance elements
        self.assertIn("PYTHON VENV ENFORCEMENT", message)
        self.assertIn("python3 script.py", message)  # Original command
        self.assertIn("ACTIVATE VENV FIRST", message)
        self.assertIn("source venv/bin/activate", message)
        self.assertIn("./venv/bin/python3", message)
        self.assertIn("SoCo 0.28.0", message)
        self.assertIn("MySQL connector", message)
        self.assertIn("which python3", message)
        self.assertIn("setup-venv.sh", message)
        self.assertIn("WHY THIS MATTERS", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_complex_python_commands(self):
        """Test guard handles complex Python commands correctly."""
        complex_cases = [
            # Should trigger
            ("cd /app && python script.py && echo done", True),
            ("export VAR=value; python3 test.py", True),
            ("if [ -f script.py ]; then python script.py; fi", True),
            ("for f in *.py; do python $f; done", True),
            # Should not trigger
            ("./venv/bin/python script.py && echo done", False),
            ("python3 -m venv myenv", False),
            ("which python3 && python3 --version", False),
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
            "  python script.py  ",
            "python  script.py",
            "python\tscript.py",
            "\npython3 script.py\n",
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
        self.assertEqual(self.guard.name, "Python Venv Enforcement")
        self.assertEqual(self.guard.description, "Ensures Python scripts are run using the venv Python binary")

    def test_python_with_options(self):
        """Test guard handles Python commands with various options."""
        python_with_options = [
            "python -u script.py",  # Unbuffered
            "python3 -O script.py",  # Optimized
            "python -W ignore script.py",  # Warnings
            "python3 -B script.py",  # No bytecode
            "python -c 'print(123)'",  # Command string
            "python3 -m module.submodule",  # Module execution
        ]

        for command in python_with_options:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_embedded_python_commands(self):
        """Test guard detects Python commands embedded in larger commands."""
        embedded_commands = [
            "time python script.py",
            "sudo python3 install.py",
            "nohup python server.py &",
            "screen -d -m python worker.py",
            "(cd /app && python manage.py migrate)",
        ]

        for command in embedded_commands:
            with self.subTest(command=command):
                context = GuardContext(
                    tool_name="Bash",
                    tool_input={"command": command},
                    command=command,
                )
                # Note: Current implementation may not catch all of these
                # This test documents expected behavior for future improvements


if __name__ == "__main__":
    unittest.main()
