"""Unit tests for file operation guards."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.file_guards import HookInstallationGuard, MockCodeGuard, PreCommitConfigGuard  # noqa: E402


class TestMockCodeGuard(unittest.TestCase):
    """Test cases for MockCodeGuard."""

    def setUp(self):
        self.guard = MockCodeGuard()

    def test_should_trigger_on_unittest_mock(self):
        """Test that guard triggers on unittest.mock imports."""
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "test.py", "content": "import unittest.mock\nfrom unittest.mock import patch"},
            content="import unittest.mock\nfrom unittest.mock import patch",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_mock_patch_decorator(self):
        """Test that guard triggers on @mock.patch decorators."""
        context = GuardContext(
            tool_name="Edit",
            tool_input={"file_path": "test.py", "new_string": "@mock.patch('requests.get')\ndef test_api():\n    pass"},
            new_string="@mock.patch('requests.get')\ndef test_api():\n    pass",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_magic_mock(self):
        """Test that guard triggers on MagicMock usage."""
        context = GuardContext(
            tool_name="Write",
            tool_input={
                "file_path": "test.py",
                "content": "from unittest.mock import MagicMock\nmock_obj = MagicMock()",
            },
            content="from unittest.mock import MagicMock\nmock_obj = MagicMock()",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_simulation_comment(self):
        """Test that guard triggers on SIMULATION: comments."""
        context = GuardContext(
            tool_name="Write",
            tool_input={
                "file_path": "test.py",
                "content": "# SIMULATION: Mock database response\nreturn {'status': 'ok'}",
            },
            content="# SIMULATION: Mock database response\nreturn {'status': 'ok'}",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_multiedit_with_mocks(self):
        """Test that guard triggers on MultiEdit with mock patterns."""
        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={
                "file_path": "test.py",
                "edits": [
                    {"old_string": "old1", "new_string": "@mock.patch('service')"},
                    {"old_string": "old2", "new_string": "new2"},
                ],
            },
            new_string="@mock.patch('service')\nnew2",  # Combined from edits
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_real_code(self):
        """Test that guard doesn't trigger on real code without mocks."""
        context = GuardContext(
            tool_name="Write",
            tool_input={
                "file_path": "test.py",
                "content": "import requests\n\ndef get_data():\n    return requests.get('http://api.com')",
            },
            content="import requests\n\ndef get_data():\n    return requests.get('http://api.com')",
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_file_operations(self):
        """Test that guard doesn't trigger on non-file operations."""
        context = GuardContext(tool_name="Bash", tool_input={"command": "python test.py"}, command="python test.py")

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_empty_content(self):
        """Test that guard doesn't trigger on empty content."""
        context = GuardContext(tool_name="Write", tool_input={"file_path": "test.py"}, content=None, new_string=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_lists_patterns(self):
        """Test that error message lists detected patterns."""
        context = GuardContext(
            tool_name="Write",
            tool_input={
                "file_path": "test.py",
                "content": "import unittest.mock\n@mock.patch('service')\ndef test():\n    pass",
            },
            content="import unittest.mock\n@mock.patch('service')\ndef test():\n    pass",
        )

        message = self.guard.get_message(context)

        self.assertIn("Detected patterns:", message)
        self.assertIn("unittest\\.mock", message)
        self.assertIn("@mock\\.patch", message)
        self.assertIn("MOCKS AND SIMULATIONS ARE STRICTLY FORBIDDEN", message)
        self.assertIn("Mocks lie. Real tests reveal truth", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)


class TestPreCommitConfigGuard(unittest.TestCase):
    """Test cases for PreCommitConfigGuard."""

    def setUp(self):
        self.guard = PreCommitConfigGuard()

    def test_should_trigger_on_precommit_config_edit(self):
        """Test that guard triggers on .pre-commit-config.yaml edits."""
        test_files = [".pre-commit-config.yaml", "/path/to/.pre-commit-config.yaml", "project/.pre-commit-config.yaml"]

        for file_path in test_files:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Edit", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {file_path}")

    def test_should_trigger_on_write_to_precommit_config(self):
        """Test that guard triggers on writing to pre-commit config."""
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": ".pre-commit-config.yaml", "content": "repos:\n  - repo: local"},
            file_path=".pre-commit-config.yaml",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_multiedit_precommit_config(self):
        """Test that guard triggers on MultiEdit of pre-commit config."""
        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={"file_path": ".pre-commit-config.yaml", "edits": [{"old_string": "old", "new_string": "new"}]},
            file_path=".pre-commit-config.yaml",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_other_yaml_files(self):
        """Test that guard doesn't trigger on other YAML files."""
        test_files = ["docker-compose.yaml", "config.yml", ".github/workflows/ci.yaml", "data.yaml"]

        for file_path in test_files:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Edit", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertFalse(self.guard.should_trigger(context), f"Should not trigger on: {file_path}")

    def test_should_not_trigger_on_non_file_operations(self):
        """Test that guard doesn't trigger on non-file operations."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "pre-commit run --all-files"}, command="pre-commit run --all-files"
        )

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_no_file_path(self):
        """Test that guard doesn't trigger when no file path."""
        context = GuardContext(tool_name="Edit", tool_input={"old_string": "old", "new_string": "new"}, file_path=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_explains_rule(self):
        """Test that error message explains the rule violation."""
        context = GuardContext(
            tool_name="Edit", tool_input={"file_path": ".pre-commit-config.yaml"}, file_path=".pre-commit-config.yaml"
        )

        message = self.guard.get_message(context)

        self.assertIn(".pre-commit-config.yaml", message)
        self.assertIn("PRE-COMMIT HOOKS MAY NEVER BE DISABLED", message)
        self.assertIn("FORBIDDEN PRACTICES", message)
        self.assertIn("explicit written permission", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)


class TestHookInstallationGuard(unittest.TestCase):
    """Test cases for HookInstallationGuard."""

    def setUp(self):
        self.guard = HookInstallationGuard()

    def test_should_trigger_on_claude_directory_edit(self):
        """Test that guard triggers on .claude directory file operations."""
        test_paths = ["/home/user/.claude/settings.json", "~/.claude/adaptive-guard.sh", "/path/.claude/hooks.sh"]

        for file_path in test_paths:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Edit", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {file_path}")

    def test_should_trigger_on_write_to_claude_directory(self):
        """Test that guard triggers on writing to .claude directory."""
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/home/user/.claude/new-hook.sh", "content": "#!/bin/bash\necho 'test'"},
            file_path="/home/user/.claude/new-hook.sh",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_bash_cp_to_claude(self):
        """Test that guard triggers on bash cp commands to .claude directory."""
        test_commands = [
            "cp adaptive-guard.sh ~/.claude/",
            "cp settings.json /home/user/.claude/settings.json",
            "sudo cp hook.sh ~/.claude/",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_not_trigger_on_other_directories(self):
        """Test that guard doesn't trigger on other directories."""
        test_paths = ["/home/user/project/config.json", "~/.bashrc", "/etc/hosts", "./local-settings.json"]

        for file_path in test_paths:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Edit", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertFalse(self.guard.should_trigger(context), f"Should not trigger on: {file_path}")

    def test_should_not_trigger_on_non_cp_bash_commands(self):
        """Test that guard doesn't trigger on non-cp bash commands."""
        test_commands = [
            "ls ~/.claude/",
            "cat ~/.claude/settings.json",
            "chmod +x ~/.claude/hook.sh",
            "cd ~/.claude && ls",
        ]

        for command in test_commands:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                # Should not trigger because these aren't copy operations
                result = self.guard.should_trigger(context)
                if "cp" not in command and ".claude/" not in command:
                    self.assertFalse(result, f"Should not trigger on: {command}")

    def test_get_message_explains_workflow(self):
        """Test that error message explains correct workflow."""
        context = GuardContext(
            tool_name="Edit", tool_input={"file_path": "~/.claude/settings.json"}, file_path="~/.claude/settings.json"
        )

        message = self.guard.get_message(context)

        self.assertIn("~/.claude/settings.json", message)
        self.assertIn("CORRECT WORKFLOW", message)
        self.assertIn("./install-hooks.sh", message)
        self.assertIn("timestamped backups", message)
        self.assertIn("/home/dhalem/github/sptodial_one/spotidal/hooks/", message)

    def test_get_message_for_bash_copy(self):
        """Test error message for bash copy commands."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "cp hook.sh ~/.claude/"}, command="cp hook.sh ~/.claude/"
        )

        message = self.guard.get_message(context)

        self.assertIn("cp hook.sh ~/.claude/", message)
        self.assertIn("install script", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)


if __name__ == "__main__":
    unittest.main()
