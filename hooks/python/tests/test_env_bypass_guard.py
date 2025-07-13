"""Tests for EnvBypassGuard.

REMINDER: Update HOOKS.md when adding new tests!
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardContext  # noqa: E402
from guards.env_bypass_guard import EnvBypassGuard  # noqa: E402


class TestEnvBypassGuard(unittest.TestCase):
    """Test cases for EnvBypassGuard."""

    def setUp(self):
        """Set up test fixtures."""
        self.guard = EnvBypassGuard()

    def create_context(self, command, tool_name="Bash"):
        """Helper to create GuardContext."""
        return GuardContext(tool_name=tool_name, tool_input={"command": command}, command=command)

    def test_non_bash_tool_not_triggered(self):
        """Should not trigger for non-Bash tools."""
        context = self.create_context("export SKIP_GUARDS=1", tool_name="Task")
        result = self.guard.check(context)
        self.assertFalse(result.should_block)

    def test_empty_command_not_triggered(self):
        """Should not trigger for empty commands."""
        context = self.create_context("")
        result = self.guard.check(context)
        self.assertFalse(result.should_block)

    def test_export_bypass_variables_triggers(self):
        """Should trigger for export commands with bypass variables."""
        bypass_commands = [
            "export CLAUDE_SKIP_GUARDS=1",
            "export CLAUDE_DISABLE_GUARDS=true",
            "export CLAUDE_BYPASS_GUARDS=yes",
            "export SKIP_GUARDS=1",
            "export DISABLE_GUARDS=1",
            "export BYPASS_GUARDS=1",
            "export NO_GUARDS=1",
            "export GUARD_SKIP=1",
            "export GUARD_DISABLE=1",
            "export TEST_SKIP=1",
            "export SKIP_TESTS=1",
            "export BYPASS_TESTS=1",
            "export DISABLE_TESTS=1",
            "export NO_TESTS=1",
            "export FORCE_PASS=1",
            "export ALWAYS_PASS=1",
            "export IGNORE_FAILURES=1",
        ]

        for cmd in bypass_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertTrue(result.should_block)
                self.assertIn("ENVIRONMENT BYPASS ATTEMPT DETECTED", result.message)

    def test_case_insensitive_detection(self):
        """Should detect bypass attempts regardless of case."""
        case_variations = [
            "EXPORT CLAUDE_SKIP_GUARDS=1",
            "Export Claude_Skip_Guards=1",
            "export claude_skip_guards=1",
            "EXPORT SKIP_GUARDS=1",
        ]

        for cmd in case_variations:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertTrue(result.should_block)

    def test_set_command_triggers(self):
        """Should trigger for set commands (alternative to export)."""
        commands = [
            "set CLAUDE_SKIP_GUARDS=1",
            "set DISABLE_GUARDS=true",
        ]

        for cmd in commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertTrue(result.should_block)

    def test_env_command_triggers(self):
        """Should trigger for env command with bypass variables."""
        commands = [
            "env CLAUDE_SKIP_GUARDS=1 python test.py",
            "env SKIP_TESTS=1 ./run_tests.sh",
            "env BYPASS_GUARDS=true some_command",
        ]

        for cmd in commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertTrue(result.should_block)

    def test_normal_exports_not_triggered(self):
        """Should not trigger for normal environment variables."""
        safe_commands = [
            "export PATH=/usr/local/bin:$PATH",
            "export PYTHONPATH=/home/user/project",
            "export DATABASE_URL=postgres://localhost",
            "export API_KEY=secret123",
            "export CLAUDE_API_KEY=key123",  # Not a bypass pattern
            "export TEST_MODE=1",  # TEST alone is OK if not TEST_SKIP
        ]

        for cmd in safe_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertFalse(result.should_block)

    def test_other_bash_commands_not_triggered(self):
        """Should not trigger for non-export commands."""
        other_commands = [
            "echo $CLAUDE_SKIP_GUARDS",
            "if [ -n \"$SKIP_GUARDS\" ]; then echo 'set'; fi",
            "unset CLAUDE_SKIP_GUARDS",
            "printenv SKIP_GUARDS",
        ]

        for cmd in other_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertFalse(result.should_block)

    def test_message_includes_security_info(self):
        """Should include security violation info in message."""
        context = self.create_context("export CLAUDE_SKIP_GUARDS=1")
        result = self.guard.check(context)

        self.assertIn("SECURITY VIOLATION", result.message)
        self.assertIn("Guards exist to prevent production issues", result.message)
        self.assertIn("Fix the underlying issue", result.message)
        self.assertIn("SECURITY POLICY", result.message)

    def test_complex_commands_with_bypass_vars(self):
        """Should detect bypass vars in complex commands."""
        complex_commands = [
            "cd /tmp && export CLAUDE_SKIP_GUARDS=1 && python test.py",
            "export PATH=$PATH:/usr/local/bin && export SKIP_TESTS=1",
            "source ~/.bashrc; export BYPASS_GUARDS=true",
        ]

        for cmd in complex_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertTrue(result.should_block)

    def test_guard_metadata(self):
        """Should have correct metadata."""
        self.assertEqual(self.guard.name, "Environment Variable Bypass Prevention")
        self.assertIn("blocks attempts to set environment variables", self.guard.description.lower())

    def test_direct_env_syntax_triggers(self):
        """Should trigger for direct VAR=value command syntax."""
        direct_commands = [
            "SKIP=true git commit -m 'test'",
            "SKIP_TESTS=1 pytest",
            "CLAUDE_SKIP_GUARDS=yes ./run_tests.sh",
            "BYPASS_GUARDS=1 make test",
            "DISABLE_TESTS=true npm test",
            "FORCE_PASS=1 cargo test",
            "SKIP_GUARDS=yes git push",
            "NO_TESTS=1 python manage.py test",
        ]

        for cmd in direct_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertTrue(result.should_block, f"Should block: {cmd}")

    def test_direct_syntax_with_multiple_vars(self):
        """Should detect bypass vars in multi-var direct syntax."""
        multi_var_commands = [
            "DEBUG=1 SKIP_TESTS=1 python test.py",
            "VERBOSE=true CLAUDE_SKIP_GUARDS=1 ./script.sh",
            "LOG_LEVEL=debug BYPASS_GUARDS=yes make build",
        ]

        for cmd in multi_var_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertTrue(result.should_block)

    def test_direct_syntax_normal_vars_not_triggered(self):
        """Should not trigger for normal vars in direct syntax."""
        safe_direct_commands = [
            "DEBUG=1 python test.py",
            "VERBOSE=true ./script.sh",
            "API_KEY=secret node app.js",
            "DATABASE_URL=postgres://localhost psql",
            "TEST_MODE=1 npm start",  # TEST alone is OK
        ]

        for cmd in safe_direct_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                result = self.guard.check(context)
                self.assertFalse(result.should_block, f"Should not block: {cmd}")


if __name__ == "__main__":
    unittest.main()
