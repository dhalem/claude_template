"""Tests for conversation log analyzer."""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guards.conversation_log_analyzer import (
    ConversationEntry,
    ConversationLogAnalyzer,
    ConversationLogReader,
    ConversationPatternAnalyzer,
)


class TestConversationLogReader(unittest.TestCase):
    """Test ConversationLogReader functionality."""

    def test_derive_project_name(self):
        """Test project name derivation from working directory."""
        reader = ConversationLogReader("/home/user/project/subdir")
        expected = "-home-user-project-subdir"
        self.assertEqual(reader.project_name, expected)

    def test_derive_project_name_complex_path(self):
        """Test project name derivation with complex path."""
        reader = ConversationLogReader("/home/dhalem/github/sptodial_one/spotidal")
        expected = "-home-dhalem-github-sptodial-one-spotidal"
        self.assertEqual(reader.project_name, expected)

    def test_parse_entry_valid(self):
        """Test parsing valid conversation entry."""
        reader = ConversationLogReader("/test/path")

        # Claude log format with actual structure
        entry_data = {
            "timestamp": "2025-01-01T12:00:00Z",
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Hello, I can help you with that."},
                    {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}
                ]
            }
        }

        entry = reader._parse_entry(entry_data)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.role, "assistant")
        self.assertIn("Hello, I can help you with that.", entry.content)
        self.assertEqual(len(entry.tool_calls), 1)
        self.assertEqual(entry.tool_calls[0]['name'], 'Bash')

    def test_parse_entry_minimal(self):
        """Test parsing minimal conversation entry."""
        reader = ConversationLogReader("/test/path")

        # Claude log format uses 'type' and 'message'
        entry_data = {
            "type": "user",
            "message": "Help me with git"
        }

        entry = reader._parse_entry(entry_data)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.role, "user")
        self.assertEqual(entry.content, "Help me with git")
        self.assertEqual(entry.tool_calls, [])


class TestConversationPatternAnalyzer(unittest.TestCase):
    """Test ConversationPatternAnalyzer functionality."""

    def test_analyze_conversation_without_llm(self):
        """Test conversation analysis when LLM is not available."""
        analyzer = ConversationPatternAnalyzer(llm_provider=None)

        from datetime import timezone
        entries = [
            ConversationEntry(
                timestamp=datetime.now(timezone.utc),
                role="assistant",
                content="I'll delete the branch: git branch -D feature-branch",
                tool_calls=[{"name": "Bash", "parameters": {"command": "git branch -D feature-branch"}}]
            )
        ]

        analysis = analyzer.analyze_conversation(entries)

        self.assertEqual(analysis.patterns_detected, ["LLM Analysis Unavailable"])
        self.assertFalse(analysis.should_alert)
        self.assertIn("LLM analysis not configured", analysis.alert_message)

    @patch('guards.meta_cognitive_guard.LLMProvider')
    def test_analyze_conversation_with_llm(self, mock_llm_provider_class):
        """Test conversation analysis with LLM available."""
        # Create mock LLM provider
        mock_llm_provider = mock_llm_provider_class.return_value

        # Create mock analysis result
        from guards.meta_cognitive_guard import PatternAnalysis
        mock_result = PatternAnalysis(
            patterns_detected=["Work Loss Risk", "False Success Claims"],
            confidence_scores={"Work Loss Risk": 0.85, "False Success Claims": 0.70},
            should_block=True,
            intervention_message="Stop and verify git status before proceeding",
            reasoning="Detected destructive git operations following unverified claims"
        )
        mock_llm_provider.analyze_patterns.return_value = mock_result

        analyzer = ConversationPatternAnalyzer(llm_provider=mock_llm_provider)

        from datetime import timezone
        entries = [
            ConversationEntry(
                timestamp=datetime.now(timezone.utc),
                role="assistant",
                content="Everything up-to-date. I'll delete the branch: git branch -D feature-branch",
                tool_calls=[{"name": "Bash", "parameters": {"command": "git branch -D feature-branch"}}]
            )
        ]

        analysis = analyzer.analyze_conversation(entries)

        self.assertEqual(analysis.patterns_detected, ["Work Loss Risk", "False Success Claims"])
        self.assertTrue(analysis.should_alert)
        self.assertIn("Work Loss Risk", analysis.alert_message)
        self.assertIn("LLM CONVERSATION ANALYSIS", analysis.alert_message)

    def test_analyze_conversation_empty(self):
        """Test analyzing empty conversation."""
        analyzer = ConversationPatternAnalyzer()

        analysis = analyzer.analyze_conversation([])

        self.assertEqual(analysis.patterns_detected, [])
        self.assertEqual(analysis.confidence_scores, {})
        self.assertFalse(analysis.should_alert)
        self.assertEqual(analysis.recent_entries_analyzed, 0)


class TestConversationLogAnalyzer(unittest.TestCase):
    """Test full ConversationLogAnalyzer integration."""

    def setUp(self):
        """Set up test with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.working_dir = Path(self.temp_dir) / "test-project"
        self.working_dir.mkdir()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('guards.conversation_log_analyzer.Path.home')
    def test_analyze_with_no_logs(self, mock_home):
        """Test analysis when no log files exist."""
        mock_home.return_value = Path(self.temp_dir)

        analyzer = ConversationLogAnalyzer(str(self.working_dir))
        analysis = analyzer.analyze_recent_conversation()

        self.assertEqual(analysis.patterns_detected, [])
        self.assertFalse(analysis.should_alert)
        self.assertEqual(analysis.recent_entries_analyzed, 0)

    @patch('guards.conversation_log_analyzer.Path.home')
    def test_analyze_with_mock_logs(self, mock_home):
        """Test analysis with mock log files."""
        # Set up mock Claude directory structure
        claude_dir = Path(self.temp_dir) / ".claude"
        projects_dir = claude_dir / "projects"
        # Use the actual derived project name that would be generated
        derived_name = str(self.working_dir).replace('/', '-').replace('_', '-')
        project_dir = projects_dir / derived_name
        project_dir.mkdir(parents=True)

        mock_home.return_value = Path(self.temp_dir)

        # Create mock log file
        log_file = project_dir / "conversation.jsonl"
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        log_entries = [
            {
                "timestamp": now_utc.isoformat(),
                "type": "assistant",
                "message": "Everything up-to-date. I'll run git branch -D to delete the old branch.",
                "tool_calls": [{"name": "Bash", "parameters": {"command": "git branch -D old-branch"}}]
            },
            {
                "timestamp": (now_utc - timedelta(minutes=5)).isoformat(),
                "type": "user",
                "message": "Please help me merge this branch"
            }
        ]

        with open(log_file, 'w') as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + '\n')

        analyzer = ConversationLogAnalyzer(str(self.working_dir))
        analysis = analyzer.analyze_recent_conversation()

        # Should detect patterns in the mock conversation
        self.assertTrue(len(analysis.patterns_detected) > 0)
        self.assertTrue(analysis.recent_entries_analyzed > 0)


if __name__ == '__main__':
    unittest.main()
