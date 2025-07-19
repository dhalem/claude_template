#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Comprehensive tests for the GeminiClient class.

Tests API key handling, request formatting, response parsing, usage tracking,
and error conditions without making real API calls.
"""

import os

# Add paths for imports
import sys
import unittest
from unittest.mock import Mock, PropertyMock, patch

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from gemini_client import GeminiClient


class TestGeminiClient(unittest.TestCase):
    """Test the GeminiClient class functionality."""

    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.api_key_patcher = patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
        self.api_key_patcher.start()

        # Mock the google.generativeai module
        self.genai_patcher = patch('gemini_client.genai')
        self.mock_genai = self.genai_patcher.start()

        # Mock the GenerativeModel
        self.mock_model = Mock()
        self.mock_genai.GenerativeModel.return_value = self.mock_model

    def tearDown(self):
        """Clean up test environment."""
        self.api_key_patcher.stop()
        self.genai_patcher.stop()

    def test_initialization_with_default_model(self):
        """Test GeminiClient initialization with default model."""
        client = GeminiClient()

        self.assertEqual(client.model_name, "gemini-1.5-flash")
        self.mock_genai.configure.assert_called_once_with(api_key='test-api-key')
        self.mock_genai.GenerativeModel.assert_called_once_with("gemini-1.5-flash")
        self.assertEqual(client.total_tokens, 0)
        self.assertEqual(client.input_tokens, 0)
        self.assertEqual(client.output_tokens, 0)
        self.assertEqual(client.call_count, 0)

    def test_initialization_with_custom_model(self):
        """Test GeminiClient initialization with custom model."""
        client = GeminiClient(model="gemini-2.5-pro")

        self.assertEqual(client.model_name, "gemini-2.5-pro")
        self.mock_genai.GenerativeModel.assert_called_once_with("gemini-2.5-pro")

    def test_initialization_no_api_key(self):
        """Test GeminiClient initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as cm:
                GeminiClient()
            self.assertIn("GEMINI_API_KEY", str(cm.exception))

    def test_initialization_with_google_api_key(self):
        """Test GeminiClient accepts GOOGLE_API_KEY as fallback."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'google-test-key'}, clear=True):
            client = GeminiClient()
            self.mock_genai.configure.assert_called_once_with(api_key='google-test-key')

    def test_review_code_success(self):
        """Test successful code review."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = "This code looks good!"
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.total_token_count = 150

        self.mock_model.generate_content.return_value = mock_response

        client = GeminiClient()
        result = client.review_code("def hello(): pass")

        # Verify result
        self.assertEqual(result, "This code looks good!")

        # Verify API call
        self.mock_model.generate_content.assert_called_once()
        args, kwargs = self.mock_model.generate_content.call_args
        self.assertEqual(args[0], "def hello(): pass")
        self.assertIn('generation_config', kwargs)

        # Verify generation config (since it's mocked, check the call was made)
        self.assertIsNotNone(kwargs['generation_config'])

        # Verify usage tracking
        self.assertEqual(client.total_tokens, 150)
        self.assertEqual(client.input_tokens, 100)
        self.assertEqual(client.output_tokens, 50)
        self.assertEqual(client.call_count, 1)

    def test_review_code_blocked_response(self):
        """Test handling of blocked response from Gemini."""
        # Setup mock response that raises ValueError on .text access
        mock_response = Mock()
        # Configure text property to raise ValueError when accessed
        type(mock_response).text = PropertyMock(side_effect=ValueError("Response blocked"))
        mock_response.prompt_feedback = "Content violates policy"
        mock_response.candidates = []

        # Mock usage metadata with proper return values to avoid TypeError
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 0
        mock_response.usage_metadata.total_token_count = 100

        self.mock_model.generate_content.return_value = mock_response

        client = GeminiClient()
        with self.assertRaises(ValueError) as cm:
            client.review_code("malicious code")

        self.assertIn("No text content in Gemini response", str(cm.exception))

    def test_review_code_api_exception(self):
        """Test handling of API exceptions."""
        self.mock_model.generate_content.side_effect = Exception("API Error")

        client = GeminiClient()
        with self.assertRaises(Exception):
            client.review_code("def hello(): pass")

    def test_update_usage_with_metadata(self):
        """Test usage tracking with complete metadata."""
        mock_response = Mock()
        mock_response.text = "Review result"
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 200
        mock_response.usage_metadata.candidates_token_count = 100
        mock_response.usage_metadata.total_token_count = 300

        self.mock_model.generate_content.return_value = mock_response

        client = GeminiClient()
        client.review_code("code to review")

        self.assertEqual(client.input_tokens, 200)
        self.assertEqual(client.output_tokens, 100)
        self.assertEqual(client.total_tokens, 300)
        self.assertEqual(client.call_count, 1)

    def test_update_usage_no_metadata(self):
        """Test usage tracking when metadata is missing."""
        mock_response = Mock()
        mock_response.text = "Review result"
        mock_response.usage_metadata = None

        self.mock_model.generate_content.return_value = mock_response

        client = GeminiClient()
        client.review_code("code to review")

        # Should still increment call count but no token tracking
        self.assertEqual(client.input_tokens, 0)
        self.assertEqual(client.output_tokens, 0)
        self.assertEqual(client.total_tokens, 0)
        self.assertEqual(client.call_count, 1)

    def test_update_usage_incomplete_metadata(self):
        """Test usage tracking with incomplete metadata."""
        mock_response = Mock()
        mock_response.text = "Review result"
        mock_response.usage_metadata = Mock()
        # Only some attributes present
        mock_response.usage_metadata.prompt_token_count = 150
        # Missing candidates_token_count and total_token_count - set up mock to return None
        del mock_response.usage_metadata.candidates_token_count
        del mock_response.usage_metadata.total_token_count

        self.mock_model.generate_content.return_value = mock_response

        client = GeminiClient()
        client.review_code("code to review")

        self.assertEqual(client.input_tokens, 150)
        self.assertEqual(client.output_tokens, 0)  # Default when missing
        self.assertEqual(client.total_tokens, 0)   # Default when missing
        self.assertEqual(client.call_count, 1)

    def test_get_usage_report_flash_model(self):
        """Test usage report for flash model."""
        client = GeminiClient(model="gemini-1.5-flash")
        client.total_tokens = 10000
        client.input_tokens = 6000
        client.output_tokens = 4000
        client.call_count = 5

        report = client.get_usage_report()

        expected_cost = (10000 / 1000) * 0.000125  # flash pricing

        self.assertEqual(report["model"], "gemini-1.5-flash")
        self.assertEqual(report["total_tokens"], 10000)
        self.assertEqual(report["input_tokens"], 6000)
        self.assertEqual(report["output_tokens"], 4000)
        self.assertEqual(report["call_count"], 5)
        self.assertEqual(report["estimated_cost"], round(expected_cost, 6))

    def test_get_usage_report_pro_model(self):
        """Test usage report for pro model."""
        client = GeminiClient(model="gemini-2.5-pro")
        client.total_tokens = 5000
        client.input_tokens = 3000
        client.output_tokens = 2000
        client.call_count = 2

        report = client.get_usage_report()

        expected_cost = (5000 / 1000) * 0.0025  # pro pricing

        self.assertEqual(report["model"], "gemini-2.5-pro")
        self.assertEqual(report["total_tokens"], 5000)
        self.assertEqual(report["input_tokens"], 3000)
        self.assertEqual(report["output_tokens"], 2000)
        self.assertEqual(report["call_count"], 2)
        self.assertEqual(report["estimated_cost"], round(expected_cost, 6))

    def test_get_usage_report_unknown_model(self):
        """Test usage report defaults to pro pricing for unknown models."""
        client = GeminiClient(model="gemini-unknown")
        client.total_tokens = 2000

        report = client.get_usage_report()

        expected_cost = (2000 / 1000) * 0.0025  # pro pricing as default
        self.assertEqual(report["estimated_cost"], round(expected_cost, 6))

    def test_multiple_api_calls_accumulate_usage(self):
        """Test that multiple API calls accumulate usage correctly."""
        # Setup mock responses
        responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.text = f"Review {i+1}"
            mock_response.usage_metadata = Mock()
            mock_response.usage_metadata.prompt_token_count = 100 * (i + 1)
            mock_response.usage_metadata.candidates_token_count = 50 * (i + 1)
            mock_response.usage_metadata.total_token_count = 150 * (i + 1)
            responses.append(mock_response)

        self.mock_model.generate_content.side_effect = responses

        client = GeminiClient()

        # Make multiple calls
        for i in range(3):
            result = client.review_code(f"code {i+1}")
            self.assertEqual(result, f"Review {i+1}")

        # Verify accumulated usage
        self.assertEqual(client.input_tokens, 100 + 200 + 300)   # 600
        self.assertEqual(client.output_tokens, 50 + 100 + 150)   # 300
        self.assertEqual(client.total_tokens, 150 + 300 + 450)   # 900
        self.assertEqual(client.call_count, 3)

    def test_extract_text_from_response_success(self):
        """Test successful text extraction from response."""
        mock_response = Mock()
        mock_response.text = "Extracted text content"

        client = GeminiClient()
        result = client._extract_text_from_response(mock_response)

        self.assertEqual(result, "Extracted text content")

    def test_extract_text_from_response_blocked(self):
        """Test text extraction from blocked response."""
        mock_response = Mock()
        # Configure text property to raise ValueError when accessed
        type(mock_response).text = PropertyMock(side_effect=ValueError("Content blocked"))
        mock_response.prompt_feedback = "Safety filter triggered"
        mock_response.candidates = ["candidate1", "candidate2"]

        client = GeminiClient()
        with self.assertRaises(ValueError) as cm:
            client._extract_text_from_response(mock_response)

        self.assertIn("No text content in Gemini response", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
