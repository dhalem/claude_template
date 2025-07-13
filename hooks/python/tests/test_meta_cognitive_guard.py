"""Tests for MetaCognitiveGuard pattern detection."""

import os
import sys
import unittest
from unittest.mock import patch

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext
from guards.meta_cognitive_guard import (
    GeminiClient,
    LLMProvider,
    MetaCognitiveGuard,
    PatternAnalysis,
)


class TestPatternAnalysis(unittest.TestCase):
    """Test PatternAnalysis data structure."""

    def test_pattern_analysis_creation(self):
        """Test PatternAnalysis can be created with proper fields."""
        analysis = PatternAnalysis(
            patterns_detected=["infrastructure_blame", "theory_lock_in"],
            confidence_scores={"infrastructure_blame": 0.85, "theory_lock_in": 0.70},
            should_block=True,
            intervention_message="Test your theory instead of explaining it",
            reasoning="Multiple patterns detected with high confidence",
        )

        self.assertEqual(analysis.patterns_detected, ["infrastructure_blame", "theory_lock_in"])
        self.assertEqual(analysis.confidence_scores["infrastructure_blame"], 0.85)
        self.assertTrue(analysis.should_block)
        self.assertIn("Test your theory", analysis.intervention_message)


class TestLLMProvider(unittest.TestCase):
    """Test LLMProvider model resolution and initialization."""

    def test_model_name_resolution_google(self):
        """Test Google model name resolution."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):  # pragma: allowlist secret
            provider = LLMProvider("google", "2.0-flash-exp")
            self.assertEqual(provider.model_name, "gemini-2.0-flash-thinking-exp")

    def test_model_name_resolution_anthropic(self):
        """Test Anthropic model name resolution."""
        # Test model name resolution without initializing client
        provider = LLMProvider.__new__(LLMProvider)
        provider.provider = "anthropic"
        provider.version = "sonnet"
        model_name = provider._resolve_model_name()
        self.assertEqual(model_name, "claude-3-5-sonnet-20241022")

    def test_model_name_resolution_openai(self):
        """Test OpenAI model name resolution."""
        # Test model name resolution without initializing client
        provider = LLMProvider.__new__(LLMProvider)
        provider.provider = "openai"
        provider.version = "4o-mini"
        model_name = provider._resolve_model_name()
        self.assertEqual(model_name, "gpt-4o-mini")

    def test_model_name_resolution_local(self):
        """Test Local model name resolution."""
        # Test model name resolution without initializing client
        provider = LLMProvider.__new__(LLMProvider)
        provider.provider = "local"
        provider.version = "llama-3.1-8b"
        model_name = provider._resolve_model_name()
        self.assertEqual(model_name, "llama3.1:8b")

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        provider = LLMProvider.__new__(LLMProvider)
        provider.provider = "unsupported"
        provider.version = "version"
        with self.assertRaises(ValueError) as context:
            provider._resolve_model_name()
        self.assertIn("Unsupported version", str(context.exception))

    def test_unsupported_version_raises_error(self):
        """Test that unsupported version raises ValueError."""
        provider = LLMProvider.__new__(LLMProvider)
        provider.provider = "google"
        provider.version = "unsupported-version"
        with self.assertRaises(ValueError) as context:
            provider._resolve_model_name()
        self.assertIn("Unsupported version", str(context.exception))


class TestGeminiClient(unittest.TestCase):
    """Test GeminiClient functionality."""

    def setUp(self):
        """Set up test environment."""
        self.api_key = "test_api_key"  # pragma: allowlist secret
        self.model = "gemini-2.0-flash-experimental"

    def test_gemini_client_initialization(self):
        """Test GeminiClient initialization with API key."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)
            self.assertEqual(client.model, self.model)
            self.assertEqual(client.api_key, self.api_key)

    def test_gemini_client_no_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                GeminiClient(self.model)
            self.assertIn("GOOGLE_API_KEY", str(context.exception))

    def test_build_analysis_prompt(self):
        """Test analysis prompt construction."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)
            content = "This is a test response with theory explanations."
            prompt = client._build_analysis_prompt(content)

            self.assertIn("RESPONSE TO ANALYZE:", prompt)
            self.assertIn(content, prompt)
            self.assertIn("Infrastructure Blame", prompt)
            self.assertIn("Theory Lock-in", prompt)
            self.assertIn("Rabbit Holes", prompt)
            self.assertIn("Excuse Making", prompt)
            self.assertIn("RETURN ONLY THE JSON OBJECT, NOTHING ELSE", prompt)

    def test_call_gemini_api_success(self):
        """Test successful Gemini API call structure parsing."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)

            # Test parsing logic with valid response structure
            valid_response = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"patterns_detected": ["Theory Lock-in"], "confidence_scores": {"Theory Lock-in": 0.8}, "should_block": false, "intervention_message": "Test instead of explain", "reasoning": "Theoretical explanations without testing"}'
                                }
                            ]
                        }
                    }
                ]
            }

            # Test parsing directly
            analysis = client._parse_response(valid_response)
            self.assertEqual(analysis.patterns_detected, ["Theory Lock-in"])
            self.assertEqual(analysis.confidence_scores["Theory Lock-in"], 0.8)
            self.assertFalse(analysis.should_block)

    def test_call_gemini_api_failure(self):
        """Test Gemini API call failure handling."""
        # Skip if no real API key
        if not os.getenv("GOOGLE_API_KEY"):
            self.skipTest("No API key available for real test")

        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)

            # Test with invalid prompt that should cause API error
            with self.assertRaises(RuntimeError) as context:
                # Empty prompt should cause API error
                client._call_gemini_api("")

            self.assertIn("Gemini API error", str(context.exception))

    def test_parse_response_success(self):
        """Test successful response parsing."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)

            gemini_response = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"patterns_detected": ["infrastructure_blame"], "confidence_scores": {"infrastructure_blame": 0.9}, "should_block": true, "intervention_message": "Check recent changes", "reasoning": "Blaming infrastructure without evidence"}'
                                }
                            ]
                        }
                    }
                ]
            }

            analysis = client._parse_response(gemini_response)

            self.assertEqual(analysis.patterns_detected, ["Infrastructure Blame"])
            self.assertEqual(analysis.confidence_scores["Infrastructure Blame"], 0.9)
            self.assertTrue(analysis.should_block)
            self.assertIn("Check recent changes", analysis.intervention_message)

    def test_parse_response_invalid_json_fallback(self):
        """Test that invalid JSON raises an error."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)

            gemini_response = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Invalid JSON response from LLM"
                                }
                            ]
                        }
                    }
                ]
            }

            # Should raise error for invalid JSON
            with self.assertRaises(ValueError, msg="Failed to parse Gemini response"):
                client._parse_response(gemini_response)

    def test_heuristic_analysis_infrastructure_blame(self):
        self.skipTest("Heuristic methods removed")
        return
        """Test heuristic detection of infrastructure blame."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)

            content = "The network connection is failing and the container restart didn't work."
            analysis = client._heuristic_analysis(content)

            self.assertIn("infrastructure_blame", analysis.patterns_detected)
            self.assertGreater(analysis.confidence_scores["infrastructure_blame"], 0.5)

    def test_heuristic_analysis_theory_lock_in(self):
        self.skipTest("Heuristic methods removed")
        return
        """Test heuristic detection of theory lock-in."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": self.api_key}):
            client = GeminiClient(self.model)

            content = "This should be working because the code is supposed to handle this case properly and it ought to work according to the specification." * 10  # Make it longer to trigger detection
            analysis = client._heuristic_analysis(content)

            # The theory lock-in detection requires length > 300 and missing "test"
            if len(content) > 300 and "test" not in content.lower():
                self.assertIn("theory_lock_in", analysis.patterns_detected)
                self.assertGreater(analysis.confidence_scores["theory_lock_in"], 0.5)

    def test_heuristic_analysis_rabbit_holes(self):
        """Test heuristic detection of rabbit holes."""
        self.skipTest("Heuristic methods removed")
        return

    def test_heuristic_analysis_excuse_making(self):
        """Test heuristic detection of excuse making."""
        self.skipTest("Heuristic methods removed")
        return

    def test_should_block_heuristic_multiple_patterns(self):
        """Test heuristic blocking logic for multiple patterns."""
        self.skipTest("Heuristic methods removed")
        return

    def test_should_block_heuristic_high_risk_patterns(self):
        """Test heuristic blocking logic for high-risk patterns."""
        self.skipTest("Heuristic methods removed")
        return

    def test_generate_intervention_message(self):
        """Test intervention message generation."""
        self.skipTest("Heuristic methods removed")
        return


class TestMetaCognitiveGuard(unittest.TestCase):
    """Test MetaCognitiveGuard functionality."""

    def setUp(self):
        """Set up test environment."""
        self.api_key = "test_api_key"  # pragma: allowlist secret

    def test_meta_cognitive_guard_initialization_enabled(self):
        """Test MetaCognitiveGuard initialization when enabled."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "2.0-flash-exp"
        }):
            guard = MetaCognitiveGuard()
            self.assertTrue(guard.enabled)
            self.assertEqual(guard.name, "Meta-Cognitive Pattern Detection")

    def test_meta_cognitive_guard_initialization_disabled(self):
        """Test MetaCognitiveGuard initialization when disabled."""
        with patch.dict(os.environ, {
            "META_COGNITIVE_ANALYSIS_ENABLED": "false"
        }):
            guard = MetaCognitiveGuard()
            self.assertFalse(guard.enabled)

    def test_meta_cognitive_guard_initialization_llm_failure(self):
        """Test MetaCognitiveGuard initialization when LLM setup fails."""
        with patch.dict(os.environ, {
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "invalid_provider"
        }):
            guard = MetaCognitiveGuard()
            self.assertFalse(guard.enabled)

    def test_should_trigger_long_content(self):
        """Test that guard triggers for long content."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }):
            guard = MetaCognitiveGuard()
            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="This is a very long content that should trigger the meta-cognitive guard analysis because it exceeds the minimum length threshold for pattern detection." * 3
            )
            self.assertTrue(guard.should_trigger(context))

    def test_should_trigger_short_content(self):
        """Test that guard doesn't trigger for short content."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }):
            guard = MetaCognitiveGuard()
            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="Short content"
            )
            self.assertFalse(guard.should_trigger(context))

    def test_should_trigger_disabled_guard(self):
        """Test that disabled guard doesn't trigger."""
        with patch.dict(os.environ, {
            "META_COGNITIVE_ANALYSIS_ENABLED": "false"
        }):
            guard = MetaCognitiveGuard()
            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="This is a very long content that should trigger the meta-cognitive guard analysis because it exceeds the minimum length threshold for pattern detection." * 3
            )
            self.assertFalse(guard.should_trigger(context))

    def test_get_message_no_patterns(self):
        """Test get_message when no patterns are detected."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }):
            guard = MetaCognitiveGuard()

            # Skip test if no real API key available
            if not os.getenv("GOOGLE_API_KEY"):
                self.skipTest("No API key available for real test")

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="Normal content without problematic patterns"
            )

            message = guard.get_message(context)
            self.assertIsNone(message)

    def test_get_message_with_patterns(self):
        """Test get_message when patterns are detected."""
        # Skip if no real API key available
        real_api_key = os.getenv("GOOGLE_API_KEY")
        if not real_api_key:
            self.skipTest("No real API key available")

        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": real_api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }):
            guard = MetaCognitiveGuard()

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="""The network connection is failing and I can't connect to the database.
                The containers are not starting properly and the file system seems corrupted.
                This is definitely an infrastructure problem not related to any code changes."""
            )

            message = guard.get_message(context)
            # With real API, we expect some patterns detected or None if no patterns
            # We can't assert specific patterns since real API may vary
            if message:
                self.assertIn("META-COGNITIVE PATTERN ALERT", message)

    def test_get_message_llm_failure(self):
        """Test get_message when LLM analysis fails."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }):
            guard = MetaCognitiveGuard()

            # Skip test if no real API key available
            if not os.getenv("GOOGLE_API_KEY"):
                self.skipTest("No API key available for real test")

            context = GuardContext(
                tool_name="Edit",
                tool_input={},
                content="Content that would cause LLM failure"
            )

            message = guard.get_message(context)
            self.assertIsNone(message)

    def test_get_default_action_enabled(self):
        """Test get_default_action when guard is enabled."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }):
            guard = MetaCognitiveGuard()
            action = guard.get_default_action()
            self.assertEqual(action, GuardAction.ALLOW)

    def test_get_default_action_disabled(self):
        """Test get_default_action when guard is disabled."""
        with patch.dict(os.environ, {
            "META_COGNITIVE_ANALYSIS_ENABLED": "false"
        }):
            guard = MetaCognitiveGuard()
            action = guard.get_default_action()
            self.assertEqual(action, GuardAction.ALLOW)

    def test_format_intervention_message(self):
        """Test formatting of intervention message."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": self.api_key,
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }):
            guard = MetaCognitiveGuard()

            analysis = PatternAnalysis(
                patterns_detected=["infrastructure_blame", "theory_lock_in"],
                confidence_scores={"infrastructure_blame": 0.9, "theory_lock_in": 0.7},
                should_block=True,
                intervention_message="Check recent changes; Test your theory",
                reasoning="Multiple problematic patterns detected"
            )

            message = guard._format_intervention_message(analysis)

            self.assertIn("🧠 META-COGNITIVE PATTERN ALERT", message)
            self.assertIn("infrastructure_blame, theory_lock_in", message)
            self.assertIn("90%", message)
            self.assertIn("70%", message)
            self.assertIn("Check recent changes; Test your theory", message)
            self.assertIn("What did I change in the last 10 minutes?", message)


class TestEnvironmentVariables(unittest.TestCase):
    """Test environment variable configuration."""

    def test_default_provider_and_version(self):
        """Test default provider and version configuration."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": "test_key",  # pragma: allowlist secret
            "META_COGNITIVE_ANALYSIS_ENABLED": "true"
        }, clear=True):
            guard = MetaCognitiveGuard()
            self.assertTrue(guard.enabled)
            # Default should be Google with 2.0-flash-exp
            self.assertEqual(guard.llm_provider.provider, "google")
            self.assertEqual(guard.llm_provider.version, "2.0-flash-exp")

    def test_custom_provider_and_version(self):
        """Test custom provider and version configuration."""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": "test_key",  # pragma: allowlist secret
            "META_COGNITIVE_ANALYSIS_ENABLED": "true",
            "META_COGNITIVE_LLM_PROVIDER": "google",
            "META_COGNITIVE_LLM_VERSION": "1.5-flash"
        }):
            guard = MetaCognitiveGuard()
            self.assertTrue(guard.enabled)
            self.assertEqual(guard.llm_provider.provider, "google")
            self.assertEqual(guard.llm_provider.version, "1.5-flash")

    def test_fallback_to_heuristics_enabled(self):
        """Test fallback to heuristics when enabled."""
        self.skipTest("Heuristic methods removed")
        return

    def test_fallback_to_heuristics_disabled(self):
        """Test fallback to heuristics when disabled."""
        self.skipTest("Heuristic methods removed")
        return


if __name__ == "__main__":
    unittest.main()
