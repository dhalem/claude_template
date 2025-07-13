"""Unit tests for base guard functionality."""

import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext, GuardResult  # noqa: E402


class TestGuardContext(unittest.TestCase):
    """Test cases for GuardContext."""

    def test_from_claude_input_bash(self):
        """Test creating context from Claude input for Bash commands."""
        input_json = {"tool_name": "Bash", "tool_input": {"command": "git commit -m test --no-verify"}}

        context = GuardContext.from_claude_input(input_json)

        self.assertEqual(context.tool_name, "Bash")
        self.assertEqual(context.command, "git commit -m test --no-verify")
        self.assertEqual(context.tool_input, {"command": "git commit -m test --no-verify"})
        self.assertEqual(context.raw_input, input_json)

    def test_from_claude_input_edit(self):
        """Test creating context from Claude input for Edit commands."""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py", "old_string": "old", "new_string": "new"},
        }

        context = GuardContext.from_claude_input(input_json)

        self.assertEqual(context.tool_name, "Edit")
        self.assertEqual(context.file_path, "test.py")
        self.assertEqual(context.new_string, "new")
        self.assertIsNone(context.command)

    def test_from_claude_input_write(self):
        """Test creating context from Claude input for Write commands."""
        input_json = {"tool_name": "Write", "tool_input": {"file_path": "test.py", "content": 'print("hello")'}}

        context = GuardContext.from_claude_input(input_json)

        self.assertEqual(context.tool_name, "Write")
        self.assertEqual(context.file_path, "test.py")
        self.assertEqual(context.content, 'print("hello")')

    def test_from_claude_input_multiedit(self):
        """Test creating context from Claude input for MultiEdit commands."""
        input_json = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": "test.py",
                "edits": [{"old_string": "old1", "new_string": "new1"}, {"old_string": "old2", "new_string": "new2"}],
            },
        }

        context = GuardContext.from_claude_input(input_json)

        self.assertEqual(context.tool_name, "MultiEdit")
        self.assertEqual(context.file_path, "test.py")
        self.assertEqual(context.new_string, "new1\nnew2")

    def test_from_claude_input_empty(self):
        """Test creating context from minimal Claude input."""
        input_json = {"tool_name": "Unknown", "tool_input": {}}

        context = GuardContext.from_claude_input(input_json)

        self.assertEqual(context.tool_name, "Unknown")
        self.assertIsNone(context.command)
        self.assertIsNone(context.file_path)


class TestGuardResult(unittest.TestCase):
    """Test cases for GuardResult."""

    def test_exit_code_blocking(self):
        """Test that blocking results have exit code 2."""
        result = GuardResult(should_block=True, message="Test message")

        self.assertTrue(result.should_block)
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.message, "Test message")

    def test_exit_code_allowing(self):
        """Test that allowing results have exit code 0."""
        result = GuardResult(should_block=False)

        self.assertFalse(result.should_block)
        self.assertEqual(result.exit_code, 0)


class ConcreteGuard(BaseGuard):
    """Concrete guard for testing base functionality."""

    def __init__(
        self,
        should_trigger_result=True,
        default_action=GuardAction.BLOCK,
        message_result="ConcreteGuard triggered",
        name="ConcreteGuard",
        description="Test guard",
    ):
        super().__init__(name, description)
        self._should_trigger_result = should_trigger_result
        self._default_action = default_action
        self._message_result = message_result

    def should_trigger(self, context):
        return self._should_trigger_result

    def get_message(self, context):
        if self._message_result is None:
            return None
        return f"{self._message_result} for {context.tool_name}"

    def get_default_action(self):
        return self._default_action


class MockGuard(BaseGuard):
    """Mock guard for testing base functionality (backward compatibility)."""

    def __init__(self, should_trigger=True, default_action=GuardAction.BLOCK):
        super().__init__("Mock Guard", "Test guard")
        self._should_trigger = should_trigger
        self._default_action = default_action

    def should_trigger(self, context):
        return self._should_trigger

    def get_message(self, context):
        return f"Mock guard triggered for {context.tool_name}"

    def get_default_action(self):
        return self._default_action


class TestBaseGuard(unittest.TestCase):
    """Test cases for BaseGuard."""

    def test_check_not_triggered(self):
        """Test guard that doesn't trigger."""
        guard = MockGuard(should_trigger=False)
        context = GuardContext(tool_name="Test", tool_input={})

        result = guard.check(context, is_interactive=False)

        self.assertFalse(result.should_block)
        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(result.message)

    def test_check_triggered_non_interactive_block(self):
        """Test guard triggers in non-interactive mode with block default."""
        guard = MockGuard(should_trigger=True, default_action=GuardAction.BLOCK)
        context = GuardContext(tool_name="Test", tool_input={})

        result = guard.check(context, is_interactive=False)

        self.assertTrue(result.should_block)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Mock guard triggered", result.message)
        self.assertIn("safety-first policy", result.message)

    def test_check_triggered_non_interactive_allow(self):
        """Test guard triggers in non-interactive mode with allow default."""
        guard = MockGuard(should_trigger=True, default_action=GuardAction.ALLOW)
        context = GuardContext(tool_name="Test", tool_input={})

        result = guard.check(context, is_interactive=False)

        self.assertFalse(result.should_block)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Mock guard triggered", result.message)
        self.assertIn("Allowing by default", result.message)


class TestGuardContextEdgeCases(unittest.TestCase):
    """Test edge cases for GuardContext."""

    def test_guard_context_with_missing_fields(self):
        """Test GuardContext with various missing fields."""
        # Test with minimal fields
        context = GuardContext(
            tool_name="Bash",
            tool_input={},
        )

        self.assertEqual(context.tool_name, "Bash")
        self.assertEqual(context.tool_input, {})
        self.assertIsNone(context.command)
        self.assertIsNone(context.file_path)
        self.assertIsNone(context.content)
        self.assertIsNone(context.new_string)

    def test_guard_context_with_all_fields(self):
        """Test GuardContext with all fields populated."""
        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={"file_path": "test.py", "edits": [{"old_string": "old", "new_string": "new"}]},
            command="test command",
            file_path="test.py",
            content="test content",
            new_string="new content",
        )

        self.assertEqual(context.tool_name, "MultiEdit")
        self.assertEqual(context.file_path, "test.py")
        self.assertEqual(context.command, "test command")
        self.assertEqual(context.content, "test content")
        self.assertEqual(context.new_string, "new content")
        self.assertIn("edits", context.tool_input)

    def test_guard_result_blocking_behavior(self):
        """Test GuardResult blocking and exit code logic."""
        # Test blocking result
        blocking_result = GuardResult(should_block=True, message="This should block")

        self.assertTrue(blocking_result.should_block)
        self.assertEqual(blocking_result.exit_code, 2)
        self.assertEqual(blocking_result.message, "This should block")

        # Test allowing result
        allowing_result = GuardResult(should_block=False, message="This should allow")

        self.assertFalse(allowing_result.should_block)
        self.assertEqual(allowing_result.exit_code, 0)
        self.assertEqual(allowing_result.message, "This should allow")

    def test_guard_result_with_empty_message(self):
        """Test GuardResult with empty or None message."""
        result_empty = GuardResult(should_block=True, message="")

        result_none = GuardResult(should_block=True, message=None)

        self.assertEqual(result_empty.message, "")
        self.assertIsNone(result_none.message)
        # Both should still have correct exit codes
        self.assertEqual(result_empty.exit_code, 2)
        self.assertEqual(result_none.exit_code, 2)

    def test_guard_context_from_claude_input_edge_cases(self):
        """Test GuardContext.from_claude_input with edge cases."""
        # Test with None values
        input_with_nones = {"tool_name": "Write", "tool_input": {"file_path": None, "content": None}}

        context = GuardContext.from_claude_input(input_with_nones)
        self.assertEqual(context.tool_name, "Write")
        self.assertIsNone(context.file_path)
        self.assertIsNone(context.content)

        # Test with missing tool_input
        input_no_tool_input = {"tool_name": "Test"}
        context = GuardContext.from_claude_input(input_no_tool_input)
        self.assertEqual(context.tool_name, "Test")
        self.assertEqual(context.tool_input, {})

        # Test with empty multiedit edits
        input_empty_edits = {"tool_name": "MultiEdit", "tool_input": {"file_path": "test.py", "edits": []}}

        context = GuardContext.from_claude_input(input_empty_edits)
        self.assertEqual(context.tool_name, "MultiEdit")
        self.assertEqual(context.file_path, "test.py")
        self.assertEqual(context.new_string, "")


class TestBaseGuardEdgeCases(unittest.TestCase):
    """Test edge cases for BaseGuard implementations."""

    @patch("builtins.input", return_value="y")
    def test_concrete_guard_interactive_with_allow_default(self, mock_input):
        """Test concrete guard with ALLOW default in interactive mode."""
        guard = ConcreteGuard(default_action=GuardAction.ALLOW)

        context = GuardContext(tool_name="Test", tool_input={"test": "data"})

        # In interactive mode with ALLOW default, should allow
        result = guard.check(context, is_interactive=True)
        self.assertFalse(result.should_block)
        self.assertEqual(result.exit_code, 0)
        # Should show the guard's custom message
        self.assertIn("ConcreteGuard triggered", result.message)

    def test_concrete_guard_non_interactive_with_allow_default(self):
        """Test concrete guard with ALLOW default in non-interactive mode."""
        guard = ConcreteGuard(default_action=GuardAction.ALLOW)

        context = GuardContext(tool_name="Test", tool_input={"test": "data"})

        # In non-interactive mode, should still allow for ALLOW guards
        result = guard.check(context, is_interactive=False)
        self.assertFalse(result.should_block)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("ConcreteGuard triggered", result.message)

    @patch("builtins.input", return_value="n")
    def test_concrete_guard_interactive_with_block_default(self, mock_input):
        """Test concrete guard with BLOCK default in interactive mode."""
        guard = ConcreteGuard(default_action=GuardAction.BLOCK)

        context = GuardContext(tool_name="Test", tool_input={"test": "data"})

        # In interactive mode with BLOCK default, still blocks
        result = guard.check(context, is_interactive=True)
        self.assertTrue(result.should_block)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("ConcreteGuard triggered", result.message)

    def test_concrete_guard_when_not_triggered(self):
        """Test concrete guard when should_trigger returns False."""
        guard = ConcreteGuard(should_trigger_result=False)

        context = GuardContext(tool_name="Test", tool_input={"test": "data"})

        # Should not block when guard doesn't trigger
        result = guard.check(context, is_interactive=False)
        self.assertFalse(result.should_block)
        self.assertEqual(result.exit_code, 0)
        # Message should be None when not triggered
        self.assertIsNone(result.message)

    def test_guard_with_none_message(self):
        """Test guard that returns None as message."""
        guard = ConcreteGuard(message_result=None)

        context = GuardContext(tool_name="Test", tool_input={"test": "data"})

        result = guard.check(context, is_interactive=False)
        # Should handle None message gracefully
        self.assertIsNone(result.message)
        self.assertTrue(result.should_block)  # Still blocks
        self.assertEqual(result.exit_code, 2)

    def test_guard_with_empty_name_and_description(self):
        """Test guard with empty name and description."""
        guard = ConcreteGuard(name="", description="")

        self.assertEqual(guard.name, "")
        self.assertEqual(guard.description, "")

        # Should still function normally
        context = GuardContext(tool_name="Test", tool_input={})
        result = guard.check(context)
        self.assertTrue(result.should_block)

    def test_guard_with_long_name_and_description(self):
        """Test guard with very long name and description."""
        long_name = "A" * 1000
        long_description = "B" * 10000

        guard = ConcreteGuard(name=long_name, description=long_description)

        self.assertEqual(guard.name, long_name)
        self.assertEqual(guard.description, long_description)

        # Should still function normally
        context = GuardContext(tool_name="Test", tool_input={})
        result = guard.check(context)
        self.assertTrue(result.should_block)

    def test_guard_check_with_large_context(self):
        """Test guard check with very large context data."""
        guard = ConcreteGuard()

        # Create large tool input
        large_content = "X" * 100000  # 100KB of data
        large_tool_input = {
            "file_path": "test.py",
            "content": large_content,
            "extra_data": {f"key{i}": f"value{i}" for i in range(1000)},
        }

        context = GuardContext(tool_name="Write", tool_input=large_tool_input, content=large_content)

        # Should handle large context without issues
        result = guard.check(context)
        self.assertTrue(result.should_block)
        self.assertIn("ConcreteGuard triggered", result.message)

    def test_guard_check_performance(self):
        """Test guard performance with repeated checks."""
        guard = ConcreteGuard()

        context = GuardContext(tool_name="Test", tool_input={"test": "data"})

        # Run many checks to test performance
        for _i in range(1000):
            result = guard.check(context)
            self.assertTrue(result.should_block)
            self.assertEqual(result.exit_code, 2)

    def test_guard_with_unicode_content(self):
        """Test guard with unicode content in various fields."""
        unicode_content = "Hello 世界 🌍 Testing émojis and ñoñó characters"

        guard = ConcreteGuard(message_result=unicode_content)

        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": f"test_{unicode_content}.py", "content": unicode_content},
            content=unicode_content,
        )

        result = guard.check(context)
        self.assertTrue(result.should_block)
        self.assertIn(unicode_content, result.message)


if __name__ == "__main__":
    unittest.main()
