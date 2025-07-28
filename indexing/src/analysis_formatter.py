# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Analysis formatter for flexible code analysis MCP server.

Formats files and context with custom prompts for Gemini analysis.
"""

from typing import Dict, Optional

from base_formatter import BaseFormatter


class AnalysisFormatter(BaseFormatter):
    """Formats code files with custom prompts for flexible Gemini analysis."""

    def format_analysis_request(
        self, files: Dict[str, str], custom_prompt: str, file_tree: Optional[str] = None
    ) -> str:
        """Format a custom analysis request for Gemini.

        Args:
            files: Dictionary of file paths to contents
            custom_prompt: Custom analysis prompt from user
            file_tree: Optional pre-generated file tree

        Returns:
            Formatted prompt for Gemini with custom analysis instructions
        """
        # Use base formatter to get formatted components
        context = self.format_base_context(files, file_tree)

        # Build complete analysis prompt with custom instructions
        return self._build_analysis_prompt(
            claude_md=context["claude_md"],
            file_tree=context["file_tree"],
            code_files=context["code_files"],
            custom_prompt=custom_prompt,
        )

    def _build_analysis_prompt(self, claude_md: str, file_tree: str, code_files: str, custom_prompt: str) -> str:
        """Build the complete analysis prompt with custom instructions.

        Args:
            claude_md: CLAUDE.md content
            file_tree: Formatted file tree
            code_files: Formatted code files
            custom_prompt: Custom analysis instructions

        Returns:
            Complete formatted prompt for Gemini
        """
        return f"""You are an expert code analyst. Please analyze the following codebase according to the custom instructions provided.

**Project Context:**
{claude_md}

**Codebase Structure:**
{file_tree}

**Code Files:**
{code_files}

**Custom Analysis Instructions:**
{custom_prompt}

Please provide a detailed analysis based on the custom instructions above. Focus on the specific aspects requested and provide actionable insights."""

    def format_simple_analysis(self, content: str, prompt: str) -> str:
        """Format a simple analysis request for single content with custom prompt.

        Args:
            content: The code content to analyze
            prompt: Custom analysis prompt

        Returns:
            Formatted prompt for Gemini
        """
        return f"""You are an expert code analyst. Please analyze the following code according to the instructions provided.

**Code to Analyze:**
```
{content}
```

**Analysis Instructions:**
{prompt}

Please provide a detailed analysis based on the instructions above."""
