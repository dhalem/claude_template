"""Conversation Log Analysis Guard for Claude Code sessions.

Analyzes conversation logs for patterns and sends findings to external LLM for review.
Integrates with the meta-cognitive guard system while focusing on conversation history.

REMINDER: Update HOOKS.md when modifying this guard!
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402
from guards.meta_cognitive_guard import LLMProvider  # noqa: E402

# Set up logging to same file as meta-cognitive guard
log_path = Path.home() / ".claude" / "conversation_log.log"
log_path.parent.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_path, mode='a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)


class ConversationLogGuard(BaseGuard):
    """Guard that analyzes conversation logs for problematic patterns."""

    def __init__(self):
        super().__init__(
            name="Conversation Log Analysis",
            description="Analyzes conversation history for patterns indicating confusion, errors, or work loss"
        )

        # Configuration from environment
        self.enabled = os.getenv("CONVERSATION_LOG_ANALYSIS_ENABLED", "true").lower() == "true"
        self.max_entries = int(os.getenv("CONVERSATION_LOG_MAX_ENTRIES", "2"))
        self.hours_back = int(os.getenv("CONVERSATION_LOG_HOURS_BACK", "24"))

        # Initialize analysis state
        self._current_analysis = None

        # Initialize LLM for conversation analysis (required - this is the primary method)
        self.llm_provider = None
        if self.enabled:
            try:
                provider = os.getenv("CONVERSATION_LOG_LLM_PROVIDER", "google")
                version = os.getenv("CONVERSATION_LOG_LLM_VERSION", "1.5-flash")
                self.llm_provider = LLMProvider(provider, version)
                logger.info("✅ Conversation log LLM provider initialized: %s %s", provider, version)
            except Exception as e:
                logger.error("❌ Conversation log LLM initialization failed: %s", e)
                logger.error("❌ LLM analysis is required for conversation log guard. Please configure LLM provider.")

        # Note: log_analyzer will be created per-request for workspace-specific analysis

    def should_trigger(self, context: GuardContext) -> bool:
        """Determine if this guard should analyze conversation logs."""
        if not self.enabled:
            logger.info("ConversationLog Analysis | Analysis: Skipped | Reason: Guard disabled")
            return False

        # Get working directory (consistent with get_message method)
        workspace = context.tool_input.get('working_directory', os.getcwd())
        is_test = self._is_test_context(context, workspace)
        test_marker = " | Test: Yes" if is_test else ""

        # Only trigger on Bash commands or file operations that might be risky
        if context.tool_name in ["Bash", "Edit", "Write", "MultiEdit"]:
            # Check if this looks like a potentially risky operation
            content = context.content or context.new_string or ""
            command = getattr(context, 'command', '') or content

            risky_patterns = [
                'git',
                'rm',
                'delete',
                'remove',
                'docker',
                'branch',
                'reset',
                'checkout'
            ]

            if any(pattern in command.lower() for pattern in risky_patterns):
                logger.info("ConversationLog Analysis | Workspace: %s | Trigger: Yes | Reason: Risky operation detected | Command: %s%s",
                            workspace, command[:100], test_marker)
                return True

        logger.info("ConversationLog Analysis | Workspace: %s | Trigger: No | Tool: %s%s", workspace, context.tool_name, test_marker)
        return False

    def _is_test_context(self, context: GuardContext, workspace: str) -> bool:
        """Detect if this is a test invocation."""
        # Check various indicators of test context
        indicators = [
            # Direct test script invocation
            'test_conversation_log' in str(context.tool_input.get('command', '')),
            'debug_conversation_log' in str(context.tool_input.get('command', '')),
            'debug_token_limits' in str(context.tool_input.get('command', '')),

            # Test workspace patterns
            '/test/' in workspace,
            workspace.endswith('_test'),

            # Common test commands
            'pytest' in str(context.tool_input.get('command', '')),
            'python3 test' in str(context.tool_input.get('command', '')),

            # Environment variable
            os.getenv('CONVERSATION_LOG_TEST_MODE', '').lower() == 'true'
        ]

        return any(indicators)

    def get_message(self, context: GuardContext) -> Optional[str]:
        """Analyze conversation logs using LLM and generate warning if patterns detected."""
        if not self.enabled:
            return None

        try:
            # Get working directory from current context (fallback to current pwd)
            working_directory = context.tool_input.get('working_directory', os.getcwd())

            # Create analyzer for the current workspace
            from guards.conversation_log_analyzer import ConversationLogAnalyzer
            analyzer = ConversationLogAnalyzer(working_directory, self.llm_provider)

            # Analyze conversation logs using LLM
            analysis = analyzer.analyze_recent_conversation(
                max_entries=self.max_entries,
                hours_back=self.hours_back
            )

            # Log the analysis
            workspace = working_directory
            is_test = self._is_test_context(context, workspace)
            test_marker = " | Test: Yes" if is_test else ""

            logger.critical(
                "ConversationLog Analysis | Workspace: %s | Entries: %d | Patterns: %s | Alert: %s | LLM: %s%s",
                workspace,
                analysis.recent_entries_analyzed,
                analysis.patterns_detected,
                analysis.should_alert,
                "Available" if self.llm_provider else "Unavailable",
                test_marker
            )

            # Store the analysis result for get_default_action
            self._current_analysis = analysis

            # Return alert message if patterns detected
            if analysis.should_alert:
                return analysis.alert_message

            return None

        except Exception as e:
            logger.error("Conversation log analysis failed: %s", e, exc_info=True)
            return f"⚠️ Failed to analyze conversation logs: {str(e)}"

    def get_default_action(self) -> GuardAction:
        """Return default action for non-interactive mode."""
        if not self.enabled:
            return GuardAction.ALLOW

        # Block only when we have alerts for actual conversation patterns (not technical issues)
        # Technical patterns like "Analysis Error", "Token Limit Exceeded", "LLM Analysis Unavailable" should not block
        if hasattr(self, '_current_analysis') and self._current_analysis and self._current_analysis.should_alert:
            # Define technical error patterns that should not block operations
            technical_patterns = {
                "Analysis Error",
                "Token Limit Exceeded",
                "LLM Analysis Unavailable"
            }

            # Check if all detected patterns are technical issues
            detected_patterns = set(self._current_analysis.patterns_detected)
            if detected_patterns and not detected_patterns.issubset(technical_patterns):
                # We have real conversation patterns, block to show the warning
                return GuardAction.BLOCK

        return GuardAction.ALLOW
