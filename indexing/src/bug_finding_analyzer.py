# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Bug finding analyzer using shared BaseCodeAnalyzer foundation.

This module implements the find_bugs tool using the shared component
architecture, demonstrating the code reuse and consistency benefits
of the BaseCodeAnalyzer pattern for bug detection and analysis.
"""

import logging
from typing import Dict, List, Optional, Tuple

from base_code_analyzer import AnalysisResult, BaseCodeAnalyzer
from bug_formatter import BugFormatter

logger = logging.getLogger(__name__)


class BugFindingAnalyzer(BaseCodeAnalyzer):
    """Bug finding analyzer that identifies potential bugs and security vulnerabilities.

    This analyzer focuses on finding bugs, security vulnerabilities, memory issues,
    logic errors, performance problems, and other code correctness issues.
    """

    def __init__(self, default_model: str = "gemini-2.5-pro", usage_tracker=None):
        """Initialize the bug finding analyzer with centralized usage tracking.

        Args:
            default_model: Default Gemini model to use for bug finding
            usage_tracker: Optional centralized usage tracker for multi-tool monitoring
        """
        super().__init__(default_model, usage_tracker)
        self.bug_formatter = BugFormatter()

    def get_tool_info(self) -> Tuple[str, str, Dict]:
        """Get tool-specific information for find_bugs.

        Returns:
            Tuple of (tool_name, description, additional_schema)
        """
        tool_name = "find_bugs"
        description = "Find potential bugs, security vulnerabilities, and correctness issues in code using AI analysis"

        # Bug-specific additional schema parameters
        additional_schema = {
            "properties": {
                "severity_filter": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "description": "Optional: Only report bugs of specified severity levels",
                },
                "bug_categories": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["security", "memory", "logic", "performance", "concurrency", "api_usage"],
                    },
                    "description": "Optional: Specific categories of bugs to look for",
                },
                "include_suggestions": {
                    "type": "boolean",
                    "description": "Optional: Include fix suggestions for found bugs (default: true)",
                },
            }
        }

        return tool_name, description, additional_schema

    def format_analysis_prompt(
        self, files: Dict[str, str], file_tree: str, focus_areas: List[str], claude_md_path: Optional[str], **kwargs
    ) -> str:
        """Format the bug finding prompt for Gemini.

        Args:
            files: Dictionary of file paths to contents
            file_tree: String representation of file structure
            focus_areas: Optional specific areas to focus on
            claude_md_path: Optional path to CLAUDE.md file
            **kwargs: Additional tool-specific parameters

        Returns:
            Formatted bug finding prompt string for Gemini
        """
        # Extract bug-specific parameters from kwargs
        bug_categories = kwargs.get("bug_categories", [])
        severity_filter = kwargs.get("severity_filter")
        include_suggestions = kwargs.get("include_suggestions", True)

        return self.bug_formatter.format_bug_finding_request(
            files=files,
            file_tree=file_tree,
            bug_categories=bug_categories,
            focus_areas=focus_areas,
            claude_md_path=claude_md_path,
            include_suggestions=include_suggestions,
            severity_filter=severity_filter,
        )

    def format_analysis_response(self, result: AnalysisResult) -> str:
        """Format the final bug finding response.

        Args:
            result: AnalysisResult containing bug analysis content and metadata

        Returns:
            Formatted response string for the user
        """
        # Parse the response content to extract bug findings and create summary
        bug_findings, summary_stats = self._parse_bug_findings(result.content)

        # Build comprehensive bug report with metadata
        response = f"""# Bug Analysis Report

## Summary
- **Directory**: {result.directory}
- **Model**: {result.model}
- **Files Analyzed**: {result.collection_stats['files_collected']}
- **Total Size**: {result.collection_stats['total_size']:,} bytes
- **Focus Areas**: {', '.join(result.focus_areas) if result.focus_areas else 'All categories'}

## Bug Findings Summary
- **Total Bugs Found**: {summary_stats['total_bugs']}
- **Critical**: {summary_stats.get('critical', 0)}
- **High**: {summary_stats.get('high', 0)}
- **Medium**: {summary_stats.get('medium', 0)}
- **Low**: {summary_stats.get('low', 0)}
- **Categories Found**: {', '.join(summary_stats.get('categories', []))}
- **Files with Bugs**: {summary_stats.get('files_with_bugs', 0)}

## Usage Statistics
- **Total Tokens**: {result.usage_stats['total_tokens']:,}
- **Input Tokens**: {result.usage_stats['input_tokens']:,}
- **Output Tokens**: {result.usage_stats['output_tokens']:,}
- **Estimated Cost**: ${result.usage_stats['estimated_cost']:.6f}

---

## Detailed Bug Analysis

{result.content}

---

*Generated by Bug Finding MCP Server using {result.model}*
"""

        return response

    def _parse_bug_findings(self, content: str) -> Tuple[List[Dict], Dict]:
        """Parse bug findings from AI response content.

        First attempts to extract and parse JSON format from markdown code blocks.
        Falls back to text parsing if JSON extraction fails.

        Args:
            content: Raw AI response content

        Returns:
            Tuple of (bug_findings_list, summary_statistics)
        """
        import json
        import re

        # First, try to extract JSON from markdown code blocks
        json_pattern = r"```json\s*\n(.*?)\n```"
        json_matches = re.findall(json_pattern, content, re.DOTALL)

        if json_matches:
            try:
                # Parse the first JSON block found
                json_data = json.loads(json_matches[0])

                # Extract bugs and summary from JSON
                bug_findings = json_data.get("bugs", [])
                summary_json = json_data.get("summary", {})

                # Build summary stats from JSON
                summary_stats = {
                    "total_bugs": summary_json.get("total_bugs", len(bug_findings)),
                    "critical": summary_json.get("by_severity", {}).get("critical", 0),
                    "high": summary_json.get("by_severity", {}).get("high", 0),
                    "medium": summary_json.get("by_severity", {}).get("medium", 0),
                    "low": summary_json.get("by_severity", {}).get("low", 0),
                    "categories": list(
                        set(bug.get("category", "unknown") for bug in bug_findings if bug.get("category"))
                    ),
                    "files_with_bugs": len(
                        set(
                            bug.get("location", {}).get("file", "")
                            if isinstance(bug.get("location"), dict)
                            else bug.get("location", "").split(":")[0]
                            for bug in bug_findings
                            if bug.get("location")
                        )
                    ),
                }

                # Normalize bug format for consistency
                normalized_bugs = []
                for bug in bug_findings:
                    # Handle location as either dict or string
                    location = bug.get("location", "Unknown")
                    if isinstance(location, dict):
                        location_str = f"{location.get('file', 'Unknown')}:{location.get('line', '?')}"
                    else:
                        location_str = location

                    normalized_bug = {
                        "bug_id": bug.get("bug_id", "BUG-???"),
                        "category": bug.get("category", "unknown"),
                        "severity": bug.get("severity", "unknown"),
                        "title": bug.get("title", "Unknown"),
                        "location": location_str,
                        "description": bug.get("description", ""),
                        "confidence": bug.get("confidence", 0),
                        "code_snippet": bug.get("code_snippet", ""),
                        "fix_suggestion": bug.get("fix_suggestion", ""),
                    }
                    normalized_bugs.append(normalized_bug)

                logger.info(f"Successfully parsed {len(normalized_bugs)} bugs from JSON format")
                return normalized_bugs, summary_stats

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse JSON response, falling back to text parsing: {e}")
                # Fall through to text parsing

        # Fallback: Text-based parsing (original implementation)
        logger.info("Using text-based parsing for bug findings")

        # Initialize summary statistics
        summary_stats = {
            "total_bugs": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "categories": set(),
            "files_with_bugs": set(),
        }

        bug_findings = []

        # Simple parsing logic - look for bug patterns
        lines = content.split("\n")
        current_bug = None

        for line in lines:
            line = line.strip()

            # Look for bug ID patterns (e.g., "**BUG-001**" or "BUG-001")
            if line.startswith("**BUG-") or line.startswith("BUG-"):
                if current_bug:
                    bug_findings.append(current_bug)
                    self._update_summary_stats(current_bug, summary_stats)

                # Start new bug
                bug_id = line.replace("**", "").replace("*", "").split()[0]
                current_bug = {
                    "bug_id": bug_id,
                    "category": "unknown",
                    "severity": "unknown",
                    "title": "Unknown",
                    "location": "Unknown",
                    "description": "",
                    "confidence": 0,
                    "code_snippet": "",
                    "fix_suggestion": "",
                }

            # Parse bug details
            elif current_bug and ":" in line:
                if line.lower().startswith("- **category**:") or line.lower().startswith("**category**:"):
                    current_bug["category"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("- **severity**:") or line.lower().startswith("**severity**:"):
                    current_bug["severity"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("- **title**:") or line.lower().startswith("**title**:"):
                    current_bug["title"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("- **location**:") or line.lower().startswith("**location**:"):
                    current_bug["location"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("- **confidence**:") or line.lower().startswith("**confidence**:"):
                    confidence_str = line.split(":", 1)[1].strip().replace("%", "")
                    try:
                        current_bug["confidence"] = int(confidence_str)
                    except ValueError:
                        current_bug["confidence"] = 0
                elif line.lower().startswith("- **code**:") or line.lower().startswith("**code snippet**:"):
                    current_bug["code_snippet"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("- **fix**:") or line.lower().startswith("**fix suggestion**:"):
                    current_bug["fix_suggestion"] = line.split(":", 1)[1].strip()

        # Don't forget the last bug
        if current_bug:
            bug_findings.append(current_bug)
            self._update_summary_stats(current_bug, summary_stats)

        # Convert sets to lists for JSON serialization
        summary_stats["categories"] = list(summary_stats["categories"])
        summary_stats["files_with_bugs"] = len(summary_stats["files_with_bugs"])

        return bug_findings, summary_stats

    def _update_summary_stats(self, bug: Dict, stats: Dict):
        """Update summary statistics with a bug finding.

        Args:
            bug: Bug finding dictionary
            stats: Summary statistics dictionary to update
        """
        stats["total_bugs"] += 1

        # Count by severity
        severity = bug.get("severity", "").lower()
        if severity in stats:
            stats[severity] += 1

        # Track categories
        category = bug.get("category", "").lower()
        if category and category != "unknown":
            stats["categories"].add(category)

        # Track files with bugs
        location = bug.get("location", "")
        if location and ":" in location:
            file_path = location.split(":")[0]
            if file_path:
                stats["files_with_bugs"].add(file_path)
