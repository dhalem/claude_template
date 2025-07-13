"""Meta-cognitive pattern detection guard for Claude responses.

Analyzes Claude's responses for counterproductive reasoning patterns like
infrastructure blame, theory lock-in, rabbit holes, and excuse making.
Uses secondary LLM analysis for sophisticated pattern detection.

REMINDER: Update HOOKS.md when modifying this guard!
"""

import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402
from guards.pattern_normalizer import normalize_confidence_scores, normalize_patterns  # noqa: E402

# Set up logging to persistent file
log_path = Path.home() / ".claude" / "meta_cognitive.log"
log_path.parent.mkdir(exist_ok=True)

# Configure file handler separately to ensure INFO level
file_handler = logging.FileHandler(log_path, mode='a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Get logger and add handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)


@dataclass
class PatternAnalysis:
    """Result of LLM pattern analysis."""

    patterns_detected: List[str]
    confidence_scores: Dict[str, float]
    should_block: bool
    intervention_message: str
    reasoning: str


class LLMProvider:
    """Configurable LLM provider with separate provider and version selection."""

    def __init__(self, provider: str, version: str):
        self.provider = provider
        self.version = version
        self.model_name = self._resolve_model_name()
        self.client = self._initialize_client()

    def _resolve_model_name(self) -> str:
        """Convert provider + version to actual model name."""
        provider_versions = {
            "anthropic": {
                "haiku": "claude-3-5-haiku-20241022",
                "sonnet": "claude-3-5-sonnet-20241022",
                "opus": "claude-3-opus-20240229"
            },
            "openai": {
                "4o-mini": "gpt-4o-mini",
                "4o": "gpt-4o",
                "3.5-turbo": "gpt-3.5-turbo"
            },
            "google": {
                "1.5-flash": "gemini-1.5-flash",
                "1.5-flash-8b": "gemini-1.5-flash-8b",
                "2.0-flash-exp": "gemini-2.0-flash-thinking-exp",
                "1.5-flash-002": "gemini-1.5-flash-002",
                "1.5-pro": "gemini-1.5-pro"
            },
            "local": {
                "llama-3.1-8b": "llama3.1:8b",
                "llama-3.1-70b": "llama3.1:70b",
                "codellama": "codellama:latest"
            }
        }

        provider_map = provider_versions.get(self.provider, {})
        model_name = provider_map.get(self.version)

        if not model_name:
            raise ValueError(f"Unsupported version '{self.version}' for provider '{self.provider}'")

        return model_name

    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider == "google":
            return GeminiClient(model=self.model_name)
        elif self.provider == "anthropic":
            return ClaudeClient(model=self.model_name)
        elif self.provider == "openai":
            return OpenAIClient(model=self.model_name)
        elif self.provider == "local":
            return LocalClient(model=self.model_name)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def analyze_patterns(self, content: str) -> PatternAnalysis:
        """Analyze content for problematic reasoning patterns."""
        result = self.client.analyze_patterns(content)

        # Get raw response if available
        raw_response = getattr(self.client, '_last_response', None)
        raw_response_str = json.dumps(raw_response, indent=2) if raw_response else "No raw response available"

        # Detect test context
        is_test = self._is_test_content(content)
        test_marker = " | Test: Yes" if is_test else ""

        # Log every analysis attempt with raw response
        logger.critical(
            "MetaCognitive Analysis | Provider: %s | Model: %s | LLM Called: Yes | Patterns: %s | Scores: %s | Block: %s | Message: %s | Content: %s | Raw Response: %s%s",
            self.provider,
            self.model_name,
            result.patterns_detected,
            result.confidence_scores,
            result.should_block,
            result.intervention_message[:100] + "..." if result.intervention_message and len(result.intervention_message) > 100 else (result.intervention_message or ""),
            content[:200] + "..." if len(content) > 200 else content,
            raw_response_str[:500] + "..." if len(raw_response_str) > 500 else raw_response_str,
            test_marker
        )

        return result

    def _is_test_content(self, content: str) -> bool:
        """Detect if this is test content."""
        test_indicators = [
            'test_conversation_log',
            'debug_conversation_log',
            'debug_token_limits',
            'pytest',
            'unittest',
            'test_meta_cognitive',
            'TEST_MODE',
            'dummy test',
            'example test'
        ]
        return any(indicator in content.lower() for indicator in test_indicators)


class GeminiClient:
    """Google Gemini API client for pattern analysis."""

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        # Gemini API endpoint
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def analyze_patterns(self, content: str) -> PatternAnalysis:
        """Send content to Gemini for pattern analysis."""
        try:
            analysis_prompt = self._build_analysis_prompt(content)
            response = self._call_gemini_api(analysis_prompt)
            result = self._parse_response(response)

            # Log complete response info in parent's analyze_patterns
            self._last_response = response
            return result
        except Exception as e:
            logger.error("GeminiClient.analyze_patterns failed: %s", e, exc_info=True)
            raise

    def _build_analysis_prompt(self, content: str) -> str:
        """Build the analysis prompt for Gemini."""
        return f"""Analyze this AI assistant response for counterproductive reasoning patterns:

RESPONSE TO ANALYZE:
{content}

CONTEXT: The AI is helping debug a technical problem during development session.

DETECT THESE PATTERNS:
1. Infrastructure Blame: Blaming network/containers/systems when code changes more likely
2. Theory Lock-in: Defending explanations instead of testing empirically
3. Rabbit Holes: Long explanations without concrete testing actions
4. Excuse Making: Creating emotional narratives vs acknowledging errors

CRITICAL: Only flag if pattern is clearly present and harmful to problem-solving.

RESPONSE INSTRUCTIONS:
1. Analyze the text for the 4 patterns listed above
2. Return ONLY a JSON object with NO other text
3. Use these EXACT pattern names in your response:
   - "Infrastructure Blame" (not "infrastructure_blame")
   - "Theory Lock-in" (not "theory_lock_in")
   - "Rabbit Holes" (not "rabbit_holes")
   - "Excuse Making" (not "excuse_making")

EXAMPLE RESPONSE:
{{
    "patterns_detected": ["Infrastructure Blame", "Theory Lock-in"],
    "confidence_scores": {{"Infrastructure Blame": 0.85, "Theory Lock-in": 0.72}},
    "should_block": false,
    "intervention_message": "Check recent code changes before blaming infrastructure; Test your theory instead of explaining",
    "reasoning": "The response blames infrastructure without checking recent changes"
}}

RETURN ONLY THE JSON OBJECT, NOTHING ELSE."""

    def _call_gemini_api(self, prompt: str) -> Dict:
        """Make API call to Gemini."""
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "candidateCount": 1,
                "maxOutputTokens": 500
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        logger.debug("Sending request to Gemini API with prompt length: %d", len(prompt))
        logger.debug("Request payload: %s", json.dumps(payload, indent=2))

        response = requests.post(
            f"{self.endpoint}?key={self.api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )

        logger.debug("Gemini API response status: %d", response.status_code)

        if response.status_code != 200:
            error_msg = f"Gemini API error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        response_data = response.json()
        logger.debug("Gemini API response data: %s", json.dumps(response_data, indent=2))
        return response_data

    def _parse_response(self, response: Dict) -> PatternAnalysis:
        """Parse Gemini API response into PatternAnalysis."""
        try:
            logger.debug("Parsing Gemini response with keys: %s", list(response.keys()))

            # Extract text from Gemini response format
            candidates = response.get("candidates", [])
            logger.debug("Found %d candidates in response", len(candidates))
            if not candidates:
                logger.error("No candidates in Gemini response. Full response: %s", json.dumps(response, indent=2))
                raise ValueError("No candidates in Gemini response")

            candidate = candidates[0]
            logger.debug("First candidate keys: %s", list(candidate.keys()))
            content = candidate.get("content", {})
            logger.debug("Content keys: %s", list(content.keys()))

            parts = content.get("parts", [])
            logger.debug("Found %d parts in content", len(parts))
            if not parts:
                # Check if this is a MAX_TOKENS issue
                finish_reason = candidate.get("finishReason", "")
                if finish_reason == "MAX_TOKENS":
                    logger.warning("Gemini response hit MAX_TOKENS limit. Input may be too long.")
                    # Return a safe fallback result for MAX_TOKENS
                    return PatternAnalysis(
                        patterns_detected=["Token Limit Exceeded"],
                        confidence_scores={"Token Limit Exceeded": 1.0},
                        should_block=False,
                        intervention_message="Analysis incomplete due to input size. Consider reviewing conversation manually.",
                        reasoning="Gemini API hit token limit while analyzing conversation"
                    )
                else:
                    logger.error("No parts in Gemini response. Candidate: %s", json.dumps(candidate, indent=2))
                    raise ValueError("No parts in Gemini response")

            part = parts[0]
            logger.debug("First part keys: %s", list(part.keys()))
            text = part.get("text", "")
            logger.debug("Extracted text length: %d", len(text))
            if not text:
                logger.error("No text in Gemini response part. Part: %s", json.dumps(part, indent=2))
                raise ValueError("No text in Gemini response")

            # Extract JSON from the response text
            logger.debug("Searching for JSON in text: %s", text[:500])
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in Gemini response text: %s", text)
                raise ValueError("No JSON found in Gemini response")

            json_text = json_match.group()
            logger.debug("Extracted JSON text: %s", json_text)

            try:
                analysis_data = json.loads(json_text)
                logger.debug("Successfully parsed JSON: %s", analysis_data)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON: %s. Text was: %s", e, json_text)
                raise ValueError(f"Invalid JSON in Gemini response: {e}")

            return PatternAnalysis(
                patterns_detected=normalize_patterns(analysis_data.get("patterns_detected", [])),
                confidence_scores=normalize_confidence_scores(analysis_data.get("confidence_scores", {})),
                should_block=analysis_data.get("should_block", False),
                intervention_message=analysis_data.get("intervention_message", ""),
                reasoning=analysis_data.get("reasoning", "")
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse Gemini response: {e}")


class ClaudeClient:
    """Anthropic Claude API client for pattern analysis."""

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.endpoint = "https://api.anthropic.com/v1/messages"

    def analyze_patterns(self, content: str) -> PatternAnalysis:
        """Send content to Claude for pattern analysis."""
        try:
            analysis_prompt = self._build_analysis_prompt(content)
            response = self._call_claude_api(analysis_prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error("ClaudeClient.analyze_patterns failed: %s", e, exc_info=True)
            raise

    def _build_analysis_prompt(self, content: str) -> str:
        """Build the analysis prompt for Claude."""
        return f"""Analyze this AI assistant response for counterproductive reasoning patterns:

RESPONSE TO ANALYZE:
{content}

CONTEXT: The AI is helping debug a technical problem during development session.

DETECT THESE PATTERNS:
1. Infrastructure Blame: Blaming network/containers/systems when code changes more likely
2. Theory Lock-in: Defending explanations instead of testing empirically
3. Rabbit Holes: Long explanations without concrete testing actions
4. Excuse Making: Creating emotional narratives vs acknowledging errors

CRITICAL: Only flag if pattern is clearly present and harmful to problem-solving.

RESPONSE INSTRUCTIONS:
1. Analyze the text for the 4 patterns listed above
2. Return ONLY a JSON object with NO other text
3. Use these EXACT pattern names in your response:
   - "Infrastructure Blame" (not "infrastructure_blame")
   - "Theory Lock-in" (not "theory_lock_in")
   - "Rabbit Holes" (not "rabbit_holes")
   - "Excuse Making" (not "excuse_making")

EXAMPLE RESPONSE:
{{
    "patterns_detected": ["Infrastructure Blame", "Theory Lock-in"],
    "confidence_scores": {{"Infrastructure Blame": 0.85, "Theory Lock-in": 0.72}},
    "should_block": false,
    "intervention_message": "Check recent code changes before blaming infrastructure; Test your theory instead of explaining",
    "reasoning": "The response blames infrastructure without checking recent changes"
}}

RETURN ONLY THE JSON OBJECT, NOTHING ELSE."""

    def _call_claude_api(self, prompt: str) -> Dict:
        """Make API call to Claude."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            error_msg = f"Claude API error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return response.json()

    def _parse_response(self, response: Dict) -> PatternAnalysis:
        """Parse Claude API response into PatternAnalysis."""
        try:
            # Extract text from Claude response format
            content = response.get("content", [])
            if not content:
                raise ValueError("No content in Claude response")

            text = content[0].get("text", "")
            if not text:
                raise ValueError("No text in Claude response")

            # Extract JSON from the response text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in Claude response")

            analysis_data = json.loads(json_match.group())

            return PatternAnalysis(
                patterns_detected=normalize_patterns(analysis_data.get("patterns_detected", [])),
                confidence_scores=normalize_confidence_scores(analysis_data.get("confidence_scores", {})),
                should_block=analysis_data.get("should_block", False),
                intervention_message=analysis_data.get("intervention_message", ""),
                reasoning=analysis_data.get("reasoning", "")
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse Claude response: {e}")


class OpenAIClient:
    """OpenAI API client for pattern analysis."""

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def analyze_patterns(self, content: str) -> PatternAnalysis:
        """Send content to OpenAI for pattern analysis."""
        try:
            analysis_prompt = self._build_analysis_prompt(content)
            response = self._call_openai_api(analysis_prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error("OpenAIClient.analyze_patterns failed: %s", e, exc_info=True)
            raise

    def _build_analysis_prompt(self, content: str) -> str:
        """Build the analysis prompt for OpenAI."""
        return f"""Analyze this AI assistant response for counterproductive reasoning patterns:

RESPONSE TO ANALYZE:
{content}

CONTEXT: The AI is helping debug a technical problem during development session.

DETECT THESE PATTERNS:
1. Infrastructure Blame: Blaming network/containers/systems when code changes more likely
2. Theory Lock-in: Defending explanations instead of testing empirically
3. Rabbit Holes: Long explanations without concrete testing actions
4. Excuse Making: Creating emotional narratives vs acknowledging errors

CRITICAL: Only flag if pattern is clearly present and harmful to problem-solving.

RESPONSE INSTRUCTIONS:
1. Analyze the text for the 4 patterns listed above
2. Return ONLY a JSON object with NO other text
3. Use these EXACT pattern names in your response:
   - "Infrastructure Blame" (not "infrastructure_blame")
   - "Theory Lock-in" (not "theory_lock_in")
   - "Rabbit Holes" (not "rabbit_holes")
   - "Excuse Making" (not "excuse_making")

EXAMPLE RESPONSE:
{{
    "patterns_detected": ["Infrastructure Blame", "Theory Lock-in"],
    "confidence_scores": {{"Infrastructure Blame": 0.85, "Theory Lock-in": 0.72}},
    "should_block": false,
    "intervention_message": "Check recent code changes before blaming infrastructure; Test your theory instead of explaining",
    "reasoning": "The response blames infrastructure without checking recent changes"
}}

RETURN ONLY THE JSON OBJECT, NOTHING ELSE."""

    def _call_openai_api(self, prompt: str) -> Dict:
        """Make API call to OpenAI."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing AI assistant responses for problematic reasoning patterns. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            error_msg = f"OpenAI API error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return response.json()

    def _parse_response(self, response: Dict) -> PatternAnalysis:
        """Parse OpenAI API response into PatternAnalysis."""
        try:
            # Extract content from OpenAI response format
            choices = response.get("choices", [])
            if not choices:
                raise ValueError("No choices in OpenAI response")

            message = choices[0].get("message", {})
            content = message.get("content", "")
            if not content:
                raise ValueError("No content in OpenAI response")

            # Parse JSON directly (OpenAI returns valid JSON with json_object mode)
            analysis_data = json.loads(content)

            return PatternAnalysis(
                patterns_detected=analysis_data.get("patterns_detected", []),
                confidence_scores=analysis_data.get("confidence_scores", {}),
                should_block=analysis_data.get("should_block", False),
                intervention_message=analysis_data.get("intervention_message", ""),
                reasoning=analysis_data.get("reasoning", "")
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse OpenAI response: {e}")


class LocalClient:
    """Local Ollama client for pattern analysis."""

    def __init__(self, model: str):
        self.model = model
        self.endpoint = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        # Test connection to Ollama
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            if response.status_code != 200:
                error_msg = f"Cannot connect to Ollama at {self.endpoint}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama is not running or not accessible at {self.endpoint}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def analyze_patterns(self, content: str) -> PatternAnalysis:
        """Send content to Ollama for pattern analysis."""
        try:
            analysis_prompt = self._build_analysis_prompt(content)
            response = self._call_ollama_api(analysis_prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error("LocalClient.analyze_patterns failed: %s", e, exc_info=True)
            raise

    def _build_analysis_prompt(self, content: str) -> str:
        """Build the analysis prompt for Ollama."""
        return f"""Analyze this AI assistant response for counterproductive reasoning patterns:

RESPONSE TO ANALYZE:
{content}

CONTEXT: The AI is helping debug a technical problem during development session.

DETECT THESE PATTERNS:
1. Infrastructure Blame: Blaming network/containers/systems when code changes more likely
2. Theory Lock-in: Defending explanations instead of testing empirically
3. Rabbit Holes: Long explanations without concrete testing actions
4. Excuse Making: Creating emotional narratives vs acknowledging errors

CRITICAL: Only flag if pattern is clearly present and harmful to problem-solving.

RESPONSE FORMAT (JSON only, no other text):
{{
    "patterns_detected": ["pattern1", "pattern2"],
    "confidence_scores": {{"pattern1": 0.85, "pattern2": 0.72}},
    "should_block": true/false,
    "intervention_message": "specific actionable guidance",
    "reasoning": "why this is problematic"
}}

Focus on: Is the AI testing concrete possibilities or explaining theories? Are they blaming infrastructure or checking recent changes?"""

    def _call_ollama_api(self, prompt: str) -> Dict:
        """Make API call to Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": 0.1,
            "stream": False,
            "format": "json"
        }

        response = requests.post(
            f"{self.endpoint}/api/generate",
            json=payload,
            timeout=60  # Ollama can be slower
        )

        if response.status_code != 200:
            error_msg = f"Ollama API error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return response.json()

    def _parse_response(self, response: Dict) -> PatternAnalysis:
        """Parse Ollama API response into PatternAnalysis."""
        try:
            # Extract response from Ollama format
            text = response.get("response", "")
            if not text:
                raise ValueError("No response in Ollama output")

            # Parse JSON directly
            analysis_data = json.loads(text)

            return PatternAnalysis(
                patterns_detected=analysis_data.get("patterns_detected", []),
                confidence_scores=analysis_data.get("confidence_scores", {}),
                should_block=analysis_data.get("should_block", False),
                intervention_message=analysis_data.get("intervention_message", ""),
                reasoning=analysis_data.get("reasoning", "")
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse Ollama response: {e}")


class MetaCognitiveGuard(BaseGuard):
    """Detects counterproductive reasoning patterns in Claude responses."""

    def __init__(self):
        super().__init__(
            name="Meta-Cognitive Pattern Detection",
            description="Detects infrastructure blame, theory lock-in, rabbit holes, and excuse making"
        )

        # Initialize LLM provider from environment variables
        provider = os.getenv("META_COGNITIVE_LLM_PROVIDER", "google")
        version = os.getenv("META_COGNITIVE_LLM_VERSION", "2.0-flash-exp")

        self.enabled = os.getenv("META_COGNITIVE_ANALYSIS_ENABLED", "true").lower() == "true"

        if self.enabled:
            try:
                self.llm_provider = LLMProvider(provider, version)
                # Only log if there's a problem - normal startup should be silent
            except Exception as e:
                # Disable if LLM setup fails
                self.enabled = False
                logger.error("❌ Meta-cognitive analysis disabled due to LLM setup error: %s", e, exc_info=True)

    def should_trigger(self, context: GuardContext) -> bool:
        """Determine if this guard should analyze the context."""
        if not self.enabled:
            logger.critical("MetaCognitive Analysis | LLM Called: No | Reason: Guard disabled")
            return False

        # Get content to analyze
        content = context.content or context.new_string or ""
        content_len = len(content) if content else 0

        # Only analyze responses, not user commands
        # In the hook system, we'd need to identify when this is a Claude response
        # For now, analyze any content that looks like a response
        if content_len > 100:
            return True

        # Detect test context
        is_test = self._is_test_guard_context(context)
        test_marker = " | Test: Yes" if is_test else ""

        # Log when we skip due to short content
        logger.critical(
            "MetaCognitive Analysis | LLM Called: No | Reason: Content too short (%d chars) | Content: %s%s",
            content_len,
            content[:50] + "..." if content_len > 50 else content,
            test_marker
        )
        return False

    def _is_test_guard_context(self, context: GuardContext) -> bool:
        """Detect if this is a test context from guard context."""
        # Check command for test indicators
        command = str(context.tool_input.get('command', ''))
        content = context.content or context.new_string or ""

        test_indicators = [
            'test_',
            'debug_',
            'pytest',
            '/test/',
            '_test'
        ]

        return (any(indicator in command.lower() for indicator in test_indicators) or
                any(indicator in content.lower() for indicator in test_indicators) or
                os.getenv('META_COGNITIVE_TEST_MODE', '').lower() == 'true')

    def get_message(self, context: GuardContext) -> str:
        """Analyze content and generate intervention message."""
        if not self.enabled:
            return None

        # Get content to analyze
        content = context.content or context.new_string or ""
        if not content:
            return None

        try:
            # Perform LLM analysis
            analysis = self.llm_provider.analyze_patterns(content)

            if not analysis.patterns_detected:
                return None

            # Generate intervention message
            return self._format_intervention_message(analysis)

        except Exception as e:
            # Don't block on LLM failures, but always log errors
            logger.error("Meta-cognitive analysis failed: %s", e, exc_info=True)
            return None

    def _format_intervention_message(self, analysis: PatternAnalysis) -> str:
        """Format the intervention message for display."""
        confidence_str = ", ".join([
            f"{pattern}: {score:.0%}"
            for pattern, score in analysis.confidence_scores.items()
        ])

        return f"""🧠 META-COGNITIVE PATTERN ALERT

🚨 DETECTED PATTERNS: {', '.join(analysis.patterns_detected)}
📊 CONFIDENCE LEVELS: {confidence_str}

❌ PROBLEM: {analysis.reasoning}

✅ SUGGESTED ACTION: {analysis.intervention_message}

🎯 ALTERNATIVE APPROACH:
1. What did I change in the last 10 minutes?
2. What's the simplest test I can run right now?
3. Am I explaining or investigating?

💡 REMEMBER: Test first, theorize later. Recent changes are more likely than infrastructure failures."""

    def get_default_action(self) -> GuardAction:
        """Return default action for non-interactive mode."""
        if not self.enabled:
            return GuardAction.ALLOW

        # For now, just warn rather than block
        # Can be made configurable later
        return GuardAction.ALLOW
