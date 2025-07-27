# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER missing mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Base code analyzer for shared MCP analysis functionality.

This module provides the common foundation for all code analysis tools,
implementing the shared workflow, parameter validation, and result formatting
that enables 70%+ code reuse between different analysis types.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from file_collector import FileCollector
from gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class AnalysisResult:
    """Container for analysis results with metadata."""

    def __init__(
        self,
        content: str,
        usage_stats: Dict,
        collection_stats: Dict,
        directory: str,
        model: str,
        focus_areas: List[str],
    ):
        self.content = content
        self.usage_stats = usage_stats
        self.collection_stats = collection_stats
        self.directory = directory
        self.model = model
        self.focus_areas = focus_areas


class BaseCodeAnalyzer(ABC):
    """Abstract base class for all code analysis tools.

    Provides the common workflow orchestration, parameter validation,
    and result formatting that is shared across all analysis types.

    Subclasses need only implement:
    - get_tool_info(): Return tool name and description
    - format_analysis_prompt(): Create analysis-specific prompt
    - format_analysis_response(): Format final response
    """

    def __init__(self, default_model: str = "gemini-2.5-pro", usage_tracker=None):
        """Initialize the base analyzer with centralized usage tracking.

        Args:
            default_model: Default Gemini model to use for analysis
            usage_tracker: Optional centralized usage tracker for multi-tool monitoring
        """
        self.default_model = default_model
        self.usage_tracker = usage_tracker
        self.file_collector = FileCollector()

    @abstractmethod
    def get_tool_info(self) -> Tuple[str, str, Dict]:
        """Get tool-specific information.

        Returns:
            Tuple of (tool_name, description, additional_schema)
            additional_schema can add tool-specific parameters to the base schema
        """
        pass

    @abstractmethod
    def format_analysis_prompt(
        self, files: Dict[str, str], file_tree: str, focus_areas: List[str], claude_md_path: Optional[str], **kwargs
    ) -> str:
        """Format the analysis prompt for the AI.

        Args:
            files: Dictionary of file paths to contents
            file_tree: String representation of file structure
            focus_areas: Optional specific areas to focus on
            claude_md_path: Optional path to CLAUDE.md file
            **kwargs: Additional tool-specific parameters

        Returns:
            Formatted prompt string for AI analysis
        """
        pass

    @abstractmethod
    def format_analysis_response(self, result: AnalysisResult) -> str:
        """Format the final analysis response.

        Args:
            result: AnalysisResult containing content and metadata

        Returns:
            Formatted response string for the user
        """
        pass

    def get_base_schema(self) -> Dict:
        """Get the base parameter schema shared by all analysis tools.

        Returns:
            Base JSON schema for tool parameters
        """
        return {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Absolute path to the directory to analyze"},
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Specific areas to focus on (e.g., 'security', 'performance')",
                },
                "model": {
                    "type": "string",
                    "description": f"Optional: Gemini model to use (default: {self.default_model})",
                    "enum": ["gemini-1.5-flash", "gemini-2.5-pro"],
                },
                "max_file_size": {
                    "type": "number",
                    "description": "Optional: Maximum file size in bytes (default: 1048576)",
                },
            },
            "required": ["directory"],
        }

    def get_complete_tool_schema(self) -> Dict:
        """Get the complete tool schema with base + tool-specific parameters.

        Returns:
            Complete JSON schema for this analysis tool
        """
        base_schema = self.get_base_schema()
        tool_name, description, additional_schema = self.get_tool_info()

        # Merge additional schema properties into base schema
        if additional_schema.get("properties"):
            base_schema["properties"].update(additional_schema["properties"])

        # Add any additional required fields
        if additional_schema.get("required"):
            base_schema["required"].extend(additional_schema["required"])

        return base_schema

    def validate_parameters(self, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate analysis parameters.

        Args:
            arguments: Dictionary of tool arguments

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required directory parameter
        directory = arguments.get("directory")
        if not directory:
            return False, "Error: directory parameter is required"

        # Validate directory exists and is a directory
        directory_path = Path(directory).resolve()
        if not directory_path.exists():
            return False, f"Error: Directory '{directory}' does not exist"

        if not directory_path.is_dir():
            return False, f"Error: '{directory}' is not a directory"

        # Validate model if provided
        model = arguments.get("model", self.default_model)
        valid_models = ["gemini-1.5-flash", "gemini-2.5-pro"]
        if model not in valid_models:
            return False, f"Error: Invalid model '{model}'. Must be one of: {valid_models}"

        # Validate max_file_size if provided
        max_file_size = arguments.get("max_file_size")
        if max_file_size is not None:
            if not isinstance(max_file_size, (int, float)) or max_file_size <= 0:
                return False, "Error: max_file_size must be a positive number"

        return True, None

    def collect_files(self, directory: str, max_file_size: int) -> Tuple[Dict[str, str], str]:
        """Collect files from directory for analysis.

        Args:
            directory: Directory path to collect from
            max_file_size: Maximum file size in bytes

        Returns:
            Tuple of (files_dict, file_tree_string)

        Raises:
            ValueError: If no files found or collection fails
        """
        logger.info(f"Collecting files from: {directory}")

        # Set file size limit
        self.file_collector.max_file_size = max_file_size

        # Collect files
        files = self.file_collector.collect_files(directory)

        if not files:
            raise ValueError("No files found to analyze")

        # Generate file tree
        file_tree = self.file_collector.get_file_tree()

        logger.info(f"Collected {len(files)} files for analysis")
        return files, file_tree

    def perform_analysis(self, prompt: str, model: str, task_type: str = "review") -> Tuple[str, Dict]:
        """Perform AI analysis using Gemini with task-aware tracking.

        Args:
            prompt: Formatted analysis prompt
            model: Gemini model to use
            task_type: Type of analysis task for tracking (e.g., 'review', 'bug_finding')

        Returns:
            Tuple of (analysis_text, usage_stats)
        """
        logger.info(f"Starting {task_type} analysis with {model}")

        # Initialize Gemini client with usage tracker
        gemini_client = GeminiClient(model=model, usage_tracker=self.usage_tracker)

        # Get analysis from Gemini using task-aware method
        analysis_text = gemini_client.analyze_code(prompt, task_type=task_type)

        # Get usage statistics
        usage_stats = gemini_client.get_usage_report()

        logger.info(
            f"Analysis completed. Task: {task_type}, Tokens: {usage_stats['total_tokens']}, "
            f"Cost: ${usage_stats['estimated_cost']:.6f}"
        )

        return analysis_text, usage_stats

    def analyze(self, arguments: Dict[str, Any]) -> AnalysisResult:
        """Perform complete analysis workflow.

        This is the main orchestration method that coordinates all steps
        of the analysis process using the template method pattern.

        Args:
            arguments: Dictionary of tool arguments

        Returns:
            AnalysisResult with content and metadata

        Raises:
            ValueError: If parameters are invalid or analysis fails
        """
        # Step 1: Validate parameters
        is_valid, error_message = self.validate_parameters(arguments)
        if not is_valid:
            raise ValueError(error_message)

        # Step 2: Extract and prepare parameters
        directory = arguments.get("directory")
        directory_path = Path(directory).resolve()
        focus_areas = arguments.get("focus_areas", [])
        model = arguments.get("model", self.default_model)
        max_file_size = arguments.get("max_file_size", 1048576)  # 1MB default

        logger.info(f"Starting analysis for: {directory}")

        # Step 3: Collect files
        files, file_tree = self.collect_files(str(directory_path), max_file_size)

        # Step 4: Prepare CLAUDE.md path
        claude_md_path = directory_path / "CLAUDE.md"
        claude_md_path = str(claude_md_path) if claude_md_path.exists() else None

        # Step 5: Format analysis prompt (tool-specific)
        # Pass all arguments to allow tool-specific parameters
        analysis_prompt = self.format_analysis_prompt(
            files=files,
            file_tree=file_tree,
            focus_areas=focus_areas,
            claude_md_path=claude_md_path,
            **arguments,  # Pass all arguments for tool-specific use
        )

        # Step 6: Determine task type from tool info
        tool_name, _, _ = self.get_tool_info()
        # Extract task type from tool name (e.g., "review_code" -> "review", "find_bugs" -> "bug_finding")
        if "review" in tool_name:
            task_type = "review"
        elif "bug" in tool_name:
            task_type = "bug_finding"
        else:
            task_type = "analysis"  # Generic fallback

        # Step 7: Perform AI analysis with task-aware tracking
        analysis_text, usage_stats = self.perform_analysis(analysis_prompt, model, task_type)

        # Step 8: Get collection statistics
        collection_stats = self.file_collector.get_collection_summary()

        # Step 9: Create result object
        result = AnalysisResult(
            content=analysis_text,
            usage_stats=usage_stats,
            collection_stats=collection_stats,
            directory=directory,
            model=model,
            focus_areas=focus_areas,
        )

        return result

    def analyze_and_format(self, arguments: Dict[str, Any]) -> str:
        """Perform analysis and return formatted response.

        This is the main entry point for MCP tool handlers.

        Args:
            arguments: Dictionary of tool arguments

        Returns:
            Formatted response string ready for user display
        """
        try:
            # Perform analysis
            result = self.analyze(arguments)

            # Format response (tool-specific)
            formatted_response = self.format_analysis_response(result)

            return formatted_response

        except Exception as e:
            # Log error with full context
            import traceback

            error_details = traceback.format_exc()
            logger.error(f"Error in analysis: {e}")
            logger.error(f"Full traceback: {error_details}")

            # Return user-friendly error
            return f"Error: {str(e)}\n\nFull error details:\n{error_details}"
