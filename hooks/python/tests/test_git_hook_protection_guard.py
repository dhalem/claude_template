"""Tests for Git Hook Protection Guard."""


from base_guard import GuardContext
from guards.git_hook_protection_guard import GitHookProtectionGuard


class TestGitHookProtectionGuard:
    """Test cases for Git Hook Protection Guard."""

    def setup_method(self):
        """Set up test fixtures."""
        self.guard = GitHookProtectionGuard()

    def test_should_not_trigger_on_non_bash_tools(self):
        """Should not trigger for non-Bash tools."""
        context = GuardContext(
            tool_name="Edit",
            tool_input={"file_path": "test.py"}
        )
        assert not self.guard.should_trigger(context)

    def test_should_trigger_on_direct_hook_manipulation(self):
        """Should trigger when directly manipulating .git/hooks."""
        dangerous_commands = [
            "mv .git/hooks/pre-commit .git/hooks/pre-commit.bak",
            "rm .git/hooks/pre-commit",
            "chmod -x .git/hooks/pre-commit",
            "echo '' > .git/hooks/pre-commit",
            "touch .git/hooks/fake-hook",
        ]

        for command in dangerous_commands:
            context = GuardContext(
                tool_name="Bash",
                tool_input={"command": command}
            )
            assert self.guard.should_trigger(context), f"Should trigger for: {command}"

    def test_should_trigger_on_pre_commit_uninstall(self):
        """Should trigger when uninstalling pre-commit."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "pre-commit uninstall"}
        )
        assert self.guard.should_trigger(context)

    def test_should_trigger_on_no_verify_flag(self):
        """Should trigger on --no-verify flag."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "git commit --no-verify -m 'bypassing hooks'"}
        )
        assert self.guard.should_trigger(context)

    def test_should_trigger_on_skip_environment_variable(self):
        """Should trigger when setting SKIP environment variable."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "SKIP=flake8 git commit -m 'test'"}
        )
        assert self.guard.should_trigger(context)

    def test_should_trigger_on_git_config_hooks_disable(self):
        """Should trigger when disabling hooks via git config."""
        dangerous_commands = [
            "git config core.hooksPath none",
            "git config hooks.allownonascii false",
            "git config core.hooksPath /dev/null",
        ]

        for command in dangerous_commands:
            context = GuardContext(
                tool_name="Bash",
                tool_input={"command": command}
            )
            assert self.guard.should_trigger(context), f"Should trigger for: {command}"

    def test_should_not_trigger_on_safe_git_commands(self):
        """Should not trigger on safe git commands."""
        safe_commands = [
            "git status",
            "git log",
            "git diff",
            "git commit -m 'normal commit'",
            "git push origin main",
            "ls .git/",
            "cat .git/config",
        ]

        for command in safe_commands:
            context = GuardContext(
                tool_name="Bash",
                tool_input={"command": command}
            )
            assert not self.guard.should_trigger(context), f"Should not trigger for: {command}"

    def test_get_message_includes_command(self):
        """Should include attempted command in message."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled"}
        )
        message = self.guard.get_message(context)
        assert "mv .git/hooks/pre-commit" in message
        assert "SECURITY VIOLATION" in message

    def test_default_action_is_block(self):
        """Should always block hook modifications."""
        assert self.guard.get_default_action().value == "block"

    def test_case_insensitive_pattern_matching(self):
        """Should match patterns case-insensitively."""
        commands = [
            "MV .git/hooks/pre-commit backup",
            "RM .GIT/HOOKS/pre-commit",
            "CHMOD +x .Git/Hooks/pre-commit",
        ]

        for command in commands:
            context = GuardContext(
                tool_name="Bash",
                tool_input={"command": command}
            )
            assert self.guard.should_trigger(context), f"Should trigger for: {command}"
