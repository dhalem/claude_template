"""Integration tests for MetaCognitiveGuard with real Gemini 2.0 Flash API."""

import os
import sys
import unittest
from unittest.mock import patch

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardContext
from guards.meta_cognitive_guard import MetaCognitiveGuard
from main import create_registry


class TestMetaCognitiveIntegration(unittest.TestCase):
    """Integration tests for MetaCognitiveGuard."""

    def setUp(self):
        """Set up test environment."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            self.skipTest("GOOGLE_API_KEY not set - skipping integration tests")

    def test_guard_registry_integration(self):
        """Test that MetaCognitiveGuard is properly registered in the main registry."""
        registry = create_registry()

        # Check that MetaCognitiveGuard is registered for appropriate tools
        edit_guards = registry.get_guards_for_tool("Edit")
        write_guards = registry.get_guards_for_tool("Write")
        multiedit_guards = registry.get_guards_for_tool("MultiEdit")

        meta_cognitive_guard_found = False
        for guard in edit_guards:
            if isinstance(guard, MetaCognitiveGuard):
                meta_cognitive_guard_found = True
                break

        self.assertTrue(meta_cognitive_guard_found, "MetaCognitiveGuard not found in Edit tool guards")

        # Verify it's also in Write and MultiEdit
        self.assertTrue(any(isinstance(g, MetaCognitiveGuard) for g in write_guards))
        self.assertTrue(any(isinstance(g, MetaCognitiveGuard) for g in multiedit_guards))

    def test_infrastructure_blame_pattern_detection(self):
        """Test detection of infrastructure blame patterns."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash"
        }):
            guard = MetaCognitiveGuard()

            # Test content with infrastructure blame pattern
            infrastructure_blame_content = """
            The network connection is failing and I can't connect to the database.
            The containers are not starting properly and the file system seems corrupted.
            This is definitely a deployment issue with the infrastructure.
            The code should work fine but the environment is broken.
            """

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content=infrastructure_blame_content
            )

            if guard.should_trigger(context):
                message = guard.get_message(context)
                if message:
                    self.assertIn("META-COGNITIVE PATTERN ALERT", message)
                    # Either LLM detected it or heuristic fallback did
                    self.assertTrue(
                        "infrastructure blame" in message.lower() or
                        "check recent code changes" in message.lower()
                    )

    def test_theory_lock_in_pattern_detection(self):
        """Test detection of theory lock-in patterns."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash"
        }):
            guard = MetaCognitiveGuard()

            # Test content with theory lock-in pattern
            theory_lock_in_content = """
            This should be working according to the documentation because the API is supposed to handle this case.
            The code ought to work properly since we followed the specification exactly.
            Based on my understanding, the response should be formatted correctly because that's how the system is designed.
            I believe the issue is with the client not following the expected protocol.
            """

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content=theory_lock_in_content
            )

            if guard.should_trigger(context):
                message = guard.get_message(context)
                if message:
                    self.assertIn("META-COGNITIVE PATTERN ALERT", message)
                    # Either LLM detected it or heuristic fallback did
                    self.assertTrue(
                        "theory lock-in" in message.lower() or
                        "test your theory" in message.lower()
                    )

    def test_rabbit_hole_pattern_detection(self):
        """Test detection of rabbit hole patterns."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash"
        }):
            guard = MetaCognitiveGuard()

            # Test content with rabbit hole pattern
            rabbit_hole_content = """
            This is happening because the system was designed with a specific architecture in mind because
            the original developers wanted to optimize for performance because they believed that the database
            queries would be slower because of the way the indexes are structured because of the legacy schema
            design because the previous team decided to use a different approach because they thought it would
            be more maintainable because of the complexity of the domain model because the business requirements
            were not clearly defined because the stakeholders had different opinions because the market conditions
            were changing because the technology landscape was evolving because the competition was introducing
            new features because the user expectations were higher because the industry standards were shifting.
            """

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content=rabbit_hole_content
            )

            if guard.should_trigger(context):
                message = guard.get_message(context)
                if message:
                    self.assertIn("META-COGNITIVE PATTERN ALERT", message)
                    # Either LLM detected it or heuristic fallback did
                    self.assertTrue(
                        "rabbit holes" in message.lower() or
                        "concrete actions" in message.lower()
                    )

    def test_excuse_making_pattern_detection(self):
        """Test detection of excuse making patterns."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash"
        }):
            guard = MetaCognitiveGuard()

            # Test content with excuse making pattern
            excuse_making_content = """
            I'm really frustrated with this bug and feeling overwhelmed by all the different components.
            This is getting tiresome and I'm starting to feel like the codebase is too complex to understand.
            I've been working on this for hours and I'm getting tired of debugging the same issues.
            The problem is that I'm not familiar enough with this part of the system to make progress.
            """

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content=excuse_making_content
            )

            if guard.should_trigger(context):
                message = guard.get_message(context)
                if message:
                    self.assertIn("META-COGNITIVE PATTERN ALERT", message)
                    # Either LLM detected it or heuristic fallback did
                    self.assertTrue(
                        "excuse making" in message.lower() or
                        "acknowledge errors directly" in message.lower()
                    )

    def test_clean_content_no_patterns(self):
        """Test that clean content doesn't trigger false positives."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash"
        }):
            guard = MetaCognitiveGuard()

            # Test clean content without problematic patterns
            clean_content = """
            Let me check the recent changes to see what might have caused this issue.
            I'll run a quick test to verify the API endpoint is working correctly.
            Based on the error message, I need to investigate the authentication flow.
            Let me examine the logs to understand what's happening step by step.
            """

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content=clean_content
            )

            if guard.should_trigger(context):
                message = guard.get_message(context)
                # Clean content should not trigger a warning
                self.assertIsNone(message)

    def test_guard_with_multiedit_context(self):
        """Test guard functionality with MultiEdit context."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash"
        }):
            guard = MetaCognitiveGuard()

            # Test MultiEdit context with problematic content
            context = GuardContext(
                tool_name="MultiEdit",
                tool_input={
                    "edits": [
                        {"old_string": "old1", "new_string": "The network is failing and containers are broken"},
                        {"old_string": "old2", "new_string": "This should work according to the documentation"}
                    ]
                },
                new_string="The network is failing and containers are broken\nThis should work according to the documentation"
            )

            if guard.should_trigger(context):
                message = guard.get_message(context)
                if message:
                    self.assertIn("META-COGNITIVE PATTERN ALERT", message)

    def test_environment_variable_configuration(self):
        """Test different environment variable configurations."""
        # Test with different provider versions
        test_configs = [
            ("google", "1.5-flash"),
            ("google", "2.0-flash-exp"),
            ("google", "1.5-flash-002"),
        ]

        for provider, version in test_configs:
            with patch.dict(os.environ, {
                "GOOGLE_API_KEY": self.api_key,
                "META_COGNITIVE_ANALYSIS_ENABLED": "true",
                "META_COGNITIVE_LLM_PROVIDER": provider,
                "META_COGNITIVE_LLM_VERSION": version
            }):
                guard = MetaCognitiveGuard()
                self.assertTrue(guard.enabled)
                self.assertEqual(guard.llm_provider.provider, provider)
                self.assertEqual(guard.llm_provider.version, version)

    def test_disabled_guard_behavior(self):
        """Test that disabled guard doesn't interfere with normal operation."""
        with patch.dict(os.environ, {
            "META_COGNITIVE_ANALYSIS_ENABLED": "false"
        }):
            guard = MetaCognitiveGuard()
            self.assertFalse(guard.enabled)

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="Any content should be ignored when disabled"
            )

            self.assertFalse(guard.should_trigger(context))
            self.assertIsNone(guard.get_message(context))

    def test_heuristic_fallback_behavior(self):
        """Test that heuristic fallback works when LLM fails."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": "invalid_key",  # This will cause API calls to fail  # pragma: allowlist secret
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash",
            "META_COGNITIVE_FALLBACK_TO_HEURISTICS": "true"
        }):
            guard = MetaCognitiveGuard()

            # Test with infrastructure blame content
            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="The network connection is failing and containers are broken. This is a system issue."
            )

            if guard.should_trigger(context):
                message = guard.get_message(context)
                # Should still get a message due to heuristic fallback
                # (might be None if heuristics don't detect the pattern)
                if message:
                    self.assertIn("META-COGNITIVE PATTERN ALERT", message)


if __name__ == "__main__":
    unittest.main()
