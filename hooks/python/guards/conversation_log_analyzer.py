"""Conversation log analyzer for Claude Code sessions.

Analyzes recent conversation logs from Claude Code projects to detect patterns
in the conversation history that might indicate problematic interactions.

REMINDER: Update HOOKS.md when modifying this guard!
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ConversationEntry:
    """Single conversation turn from Claude Code logs."""

    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    tool_calls: Optional[List[Dict]] = None


@dataclass
class ConversationAnalysis:
    """Analysis result for conversation log patterns."""

    patterns_detected: List[str]
    confidence_scores: Dict[str, float]
    should_alert: bool
    alert_message: str
    reasoning: str
    recent_entries_analyzed: int


class ConversationLogReader:
    """Reads and parses Claude Code conversation logs."""

    def __init__(self, working_directory: str):
        self.working_directory = Path(working_directory)
        self.claude_dir = Path.home() / ".claude"
        self.project_name = self._derive_project_name()
        self.log_pattern = f"projects/{self.project_name}/*.jsonl"

    def _derive_project_name(self) -> str:
        """Derive Claude project name from working directory.

        Based on user's observation that project name is a simple transformation
        of the working directory name.
        """
        # Convert absolute path to relative-style name
        # /home/dhalem/github/sptodial_one/spotidal -> -home-dhalem-github-sptodial-one-spotidal
        path_str = str(self.working_directory)
        # Replace slashes and underscores with dashes
        project_name = path_str.replace('/', '-').replace('_', '-')
        # Keep the leading dash - it's part of the Claude project naming convention

        return project_name

    def find_log_files(self) -> List[Path]:
        """Find conversation log files for this project."""
        projects_dir = self.claude_dir / "projects"
        if not projects_dir.exists():
            logger.warning("Claude projects directory not found: %s", projects_dir)
            return []

        # Look for project directory with our derived name
        project_dir = projects_dir / self.project_name
        if not project_dir.exists():
            # Try to find project directory with similar name
            logger.warning("Exact project directory not found: %s", project_dir)
            logger.info("Available projects: %s", [d.name for d in projects_dir.iterdir() if d.is_dir()])
            return []

        # Find .jsonl files in the project directory
        log_files = list(project_dir.glob("*.jsonl"))
        logger.info("Found %d log files for workspace %s (project %s)",
                    len(log_files), self.working_directory, self.project_name)
        return log_files

    def read_recent_entries(self, max_entries: int = 50, hours_back: int = 24) -> List[ConversationEntry]:
        """Read recent conversation entries from log files."""
        log_files = self.find_log_files()
        if not log_files:
            return []

        # Sort by modification time, newest first
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        from datetime import timezone
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        entries = []

        for log_file in log_files:
            try:
                file_entries = self._parse_log_file(log_file, cutoff_time)
                entries.extend(file_entries)

                if len(entries) >= max_entries:
                    break

            except Exception as e:
                logger.error("Failed to parse log file %s: %s", log_file, e)
                continue

        # Sort by timestamp, newest first
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:max_entries]

    def _parse_log_file(self, log_file: Path, cutoff_time: datetime) -> List[ConversationEntry]:
        """Parse a single JSONL log file efficiently by reading from the end."""
        entries = []

        try:
            # Read the file in reverse to get recent entries efficiently
            lines = self._tail_lines(log_file, max_lines=100)  # Read up to 100 lines from end

            for line in reversed(lines):  # Process from newest to oldest
                line = line.strip()
                if not line:
                    continue

                try:
                    entry_data = json.loads(line)
                    entry = self._parse_entry(entry_data)

                    if entry and entry.timestamp >= cutoff_time:
                        entries.append(entry)
                    elif entry and entry.timestamp < cutoff_time:
                        # Since we're reading in reverse chronological order,
                        # we can stop once we hit entries older than cutoff
                        break

                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON in %s: %s", log_file, e)
                    continue

        except Exception as e:
            logger.error("Failed to read log file %s: %s", log_file, e)

        return entries

    def _tail_lines(self, file_path: Path, max_lines: int = 100) -> List[str]:
        """Efficiently read the last N lines from a file."""
        try:
            with open(file_path, 'rb') as f:
                # Go to end of file
                f.seek(0, 2)
                file_size = f.tell()

                # Read in chunks from the end
                lines = []
                chunk_size = 8192
                pos = file_size

                while pos > 0 and len(lines) < max_lines:
                    # Calculate chunk start position
                    chunk_start = max(0, pos - chunk_size)
                    chunk_len = pos - chunk_start

                    # Read chunk
                    f.seek(chunk_start)
                    chunk = f.read(chunk_len).decode('utf-8', errors='ignore')

                    # Split into lines and prepend to our list
                    chunk_lines = chunk.split('\n')
                    if pos < file_size:  # Not the first chunk
                        # The first line might be partial, combine with previous
                        if lines:
                            lines[0] = chunk_lines[-1] + lines[0]
                            chunk_lines = chunk_lines[:-1]

                    lines = chunk_lines + lines
                    pos = chunk_start

                # Remove empty lines and return last max_lines
                lines = [line for line in lines if line.strip()]
                return lines[-max_lines:] if len(lines) > max_lines else lines

        except Exception as e:
            logger.error("Failed to tail file %s: %s", file_path, e)
            return []

    def _parse_entry(self, entry_data: Dict) -> Optional[ConversationEntry]:
        """Parse a single conversation entry from JSON data."""
        try:
            # Extract timestamp
            timestamp_str = entry_data.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Fallback to current time if no timestamp
                timestamp = datetime.now()

            # Claude logs use 'type' instead of 'role'
            entry_type = entry_data.get('type', 'unknown')

            # Map entry type to role
            if entry_type in ['user', 'assistant']:
                role = entry_type
            else:
                # Skip non-conversation entries
                return None

            # Handle different message formats
            message = entry_data.get('message', '')
            content = ""
            tool_calls = []

            if entry_type == 'user':
                # User messages can be simple strings or dicts
                if isinstance(message, str):
                    content = message
                elif isinstance(message, dict):
                    # Extract actual user content from API format
                    if 'content' in message:
                        # Handle user messages with content field
                        user_content = message.get('content', '')
                        if isinstance(user_content, str):
                            content = user_content
                        elif isinstance(user_content, list):
                            # Handle tool results from user
                            for item in user_content:
                                if isinstance(item, dict):
                                    if item.get('type') == 'tool_result':
                                        # This is a tool result response
                                        tool_content = item.get('content', '')
                                        if len(tool_content) > 200:
                                            content = f"[Tool result: {tool_content[:200]}...]"
                                        else:
                                            content = f"[Tool result: {tool_content}]"
                                    else:
                                        # Other content types
                                        content = str(item.get('content', ''))
                        else:
                            content = str(user_content)
                    else:
                        # Fallback for other formats
                        content = message.get('text', message.get('message', str(message)))

            elif entry_type == 'assistant':
                # Assistant messages are complex dicts with Claude API response
                if isinstance(message, dict) and 'content' in message:
                    content_items = message.get('content', [])
                    text_parts = []

                    # Parse content items
                    for item in content_items:
                        if isinstance(item, dict):
                            if item.get('type') == 'text':
                                # Text content
                                text_parts.append(item.get('text', ''))
                            elif item.get('type') == 'tool_use':
                                # Tool invocation
                                tool_name = item.get('name', '')
                                tool_input = item.get('input', {})
                                tool_calls.append({
                                    'name': tool_name,
                                    'parameters': tool_input
                                })
                                # Add a text representation
                                if tool_name:
                                    text_parts.append(f"[Invoking {tool_name}]")

                    # Combine text parts
                    content = ' '.join(text_parts).strip()

                elif isinstance(message, str):
                    content = message

            # If we have no content but have tool calls, create a description
            if not content and tool_calls:
                tool_names = [tc['name'] for tc in tool_calls]
                content = f"[Using tools: {', '.join(tool_names)}]"

            return ConversationEntry(
                timestamp=timestamp,
                role=role,
                content=content,
                tool_calls=tool_calls
            )

        except Exception as e:
            logger.warning("Failed to parse conversation entry: %s", e)
            return None


class ConversationPatternAnalyzer:
    """Analyzes conversation patterns using LLM for intelligent pattern detection."""

    def __init__(self, llm_provider=None):
        """Initialize with optional LLM provider.

        Args:
            llm_provider: LLMProvider instance for AI-powered analysis
        """
        self.llm_provider = llm_provider

        # Configurable content limits
        self.user_content_limit = int(os.getenv("CONVERSATION_LOG_USER_CONTENT_LIMIT", "2000"))
        self.assistant_content_limit = int(os.getenv("CONVERSATION_LOG_ASSISTANT_CONTENT_LIMIT", "2000"))
        self.command_limit = int(os.getenv("CONVERSATION_LOG_COMMAND_LIMIT", "2000"))
        self.params_limit = int(os.getenv("CONVERSATION_LOG_PARAMS_LIMIT", "1000"))

    def analyze_conversation(self, entries: List[ConversationEntry]) -> ConversationAnalysis:
        """Analyze conversation entries for problematic patterns using LLM."""
        if not entries:
            return ConversationAnalysis(
                patterns_detected=[],
                confidence_scores={},
                should_alert=False,
                alert_message="",
                reasoning="No conversation entries to analyze",
                recent_entries_analyzed=0
            )

        # If no LLM provider, return minimal analysis
        if not self.llm_provider:
            return ConversationAnalysis(
                patterns_detected=["LLM Analysis Unavailable"],
                confidence_scores={"LLM Analysis Unavailable": 1.0},
                should_alert=False,
                alert_message="LLM analysis not configured. Please set up LLM provider.",
                reasoning="LLM provider not available for conversation analysis",
                recent_entries_analyzed=len(entries)
            )

        try:
            # Prepare conversation context for LLM
            conversation_context = self._prepare_conversation_context(entries)
            logger.debug("Prepared conversation context for LLM analysis: %s", conversation_context[:1000])

            # Get LLM analysis
            logger.debug("Sending conversation context to LLM for analysis...")
            llm_result = self._get_llm_analysis(conversation_context)
            logger.debug("LLM analysis result: patterns=%s, should_block=%s", llm_result.patterns_detected, llm_result.should_block)

            # Convert LLM result to ConversationAnalysis
            return self._process_llm_result(llm_result, len(entries))

        except Exception as e:
            logger.error("LLM conversation analysis failed: %s", e, exc_info=True)
            return ConversationAnalysis(
                patterns_detected=["Analysis Error"],
                confidence_scores={"Analysis Error": 1.0},
                should_alert=True,
                alert_message=f"❌ LLM analysis failed: {str(e)}",
                reasoning=f"LLM analysis encountered error: {str(e)}",
                recent_entries_analyzed=len(entries)
            )

    def _prepare_conversation_context(self, entries: List[ConversationEntry]) -> str:
        """Prepare conversation entries for LLM analysis."""
        context_parts = []

        # Sort entries by timestamp (oldest first for chronological context)
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)

        for entry in sorted_entries:
            timestamp_str = entry.timestamp.strftime("%H:%M:%S")

            # Format entry based on role
            if entry.role == "user":
                context_parts.append(f"[{timestamp_str}] USER: {entry.content[:self.user_content_limit]}")
            else:  # assistant
                if entry.tool_calls:
                    for tool_call in entry.tool_calls:
                        tool_name = tool_call.get('name', 'Unknown')
                        params = tool_call.get('parameters', {})
                        if tool_name == 'Bash':
                            command = params.get('command', '')
                            context_parts.append(f"[{timestamp_str}] ASSISTANT (Bash): {command[:self.command_limit]}")
                        else:
                            context_parts.append(f"[{timestamp_str}] ASSISTANT ({tool_name}): {json.dumps(params)[:self.params_limit]}")
                else:
                    context_parts.append(f"[{timestamp_str}] ASSISTANT: {entry.content[:self.assistant_content_limit]}")

        return "\n".join(context_parts)

    def _get_llm_analysis(self, conversation_context: str):
        """Get LLM analysis of conversation patterns."""
        # Shorter, more concise prompt to avoid token limits
        analysis_prompt = f"""Analyze this Claude Code log for dangerous patterns:

LOG:
{conversation_context}

DETECT:
1. Work Loss Risk - destructive commands (git branch -D, rm -rf)
2. False Success - AI claims success but commands failed
3. Confusion - repeated errors or contradictions
4. Danger Sequence - risky commands after failures

JSON response only:
{{"patterns_detected": ["pattern names"], "confidence_scores": {{"pattern": 0.8}}, "should_block": false, "intervention_message": "advice", "reasoning": "why"}}"""

        logger.debug("Analysis prompt length: %d chars (~%d tokens)", len(analysis_prompt), len(analysis_prompt) // 4)
        return self.llm_provider.analyze_patterns(analysis_prompt)

    def _process_llm_result(self, llm_result, entries_count: int) -> ConversationAnalysis:
        """Process LLM analysis result into ConversationAnalysis."""
        patterns_detected = llm_result.patterns_detected
        confidence_scores = llm_result.confidence_scores
        should_alert = llm_result.should_block or len(patterns_detected) >= 2

        # Generate comprehensive alert message
        alert_message = self._format_llm_alert(llm_result) if should_alert else ""

        return ConversationAnalysis(
            patterns_detected=patterns_detected,
            confidence_scores=confidence_scores,
            should_alert=should_alert,
            alert_message=alert_message,
            reasoning=llm_result.reasoning,
            recent_entries_analyzed=entries_count
        )

    def _format_llm_alert(self, llm_result) -> str:
        """Format LLM analysis into user-friendly alert message."""
        message_parts = [
            "🧠 LLM CONVERSATION ANALYSIS",
            "",
            f"🔍 RISK ASSESSMENT: {self._get_risk_level(llm_result.confidence_scores)}",
            llm_result.reasoning,
            "",
            "📊 DETECTED PATTERNS:"
        ]

        for pattern in llm_result.patterns_detected:
            confidence = llm_result.confidence_scores.get(pattern, 0)
            message_parts.append(f"   - {pattern}: {confidence*100:.0f}% confidence")

        message_parts.extend([
            "",
            "✅ LLM RECOMMENDATIONS:",
            llm_result.intervention_message,
            "",
            "⚠️  CRITICAL: Review conversation history before proceeding"
        ])

        return "\n".join(message_parts)

    def _get_risk_level(self, confidence_scores: Dict[str, float]) -> str:
        """Determine risk level from confidence scores."""
        max_score = max(confidence_scores.values()) if confidence_scores else 0

        if max_score >= 0.8:
            return "HIGH - Immediate Action Required"
        elif max_score >= 0.6:
            return "MEDIUM - Caution Advised"
        elif max_score >= 0.4:
            return "LOW - Monitor Situation"
        else:
            return "MINIMAL - No Immediate Concern"


class ConversationLogAnalyzer:
    """Main interface for conversation log analysis."""

    def __init__(self, working_directory: str, llm_provider=None):
        self.log_reader = ConversationLogReader(working_directory)
        self.pattern_analyzer = ConversationPatternAnalyzer(llm_provider)

    def analyze_recent_conversation(self, max_entries: int = 5, hours_back: int = 24) -> ConversationAnalysis:
        """Analyze recent conversation for problematic patterns."""
        try:
            # Read recent conversation entries
            entries = self.log_reader.read_recent_entries(max_entries, hours_back)

            # Analyze for patterns
            analysis = self.pattern_analyzer.analyze_conversation(entries)

            logger.info(
                "Conversation analysis complete: workspace=%s, %d entries, %d patterns detected",
                self.log_reader.working_directory,
                len(entries),
                len(analysis.patterns_detected)
            )

            return analysis

        except Exception as e:
            logger.error("Conversation log analysis failed: %s", e, exc_info=True)
            return ConversationAnalysis(
                patterns_detected=["Analysis Error"],
                confidence_scores={"Analysis Error": 1.0},
                should_alert=True,
                alert_message=f"❌ Failed to analyze conversation logs: {str(e)}",
                reasoning=f"Analysis failed with error: {str(e)}",
                recent_entries_analyzed=0
            )
