# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Review formatter for code review MCP server.

Formats collected files and context into review prompts for Gemini.
"""

from pathlib import Path
from typing import Dict, List, Optional


class ReviewFormatter:
    """Formats code files and context for review by Gemini."""

    def __init__(self):
        self.claude_md_content = ""
        self.file_tree = ""
        self.code_files = ""

    def format_review_request(
        self,
        files: Dict[str, str],
        file_tree: str,
        focus_areas: Optional[List[str]] = None,
        claude_md_path: Optional[str] = None
    ) -> str:
        """Format a complete review request for Gemini.

        Args:
            files: Dictionary of file paths to contents
            file_tree: String representation of file structure
            focus_areas: Optional specific areas to focus on
            claude_md_path: Optional path to CLAUDE.md file

        Returns:
            Formatted prompt for Gemini
        """
        # Load CLAUDE.md content if available
        self._load_claude_md(claude_md_path, files)

        # Format file tree
        self.file_tree = self._format_file_tree(file_tree)

        # Format code files
        self.code_files = self._format_code_files(files)

        # Build focus areas prompt
        focus_areas_prompt = self._build_focus_areas_prompt(focus_areas)

        # Build complete prompt
        return self._build_review_prompt(focus_areas_prompt)

    def _load_claude_md(self, claude_md_path: Optional[str], files: Dict[str, str]) -> None:
        """Load CLAUDE.md content from path or files."""
        self.claude_md_content = ""

        # Try provided path first
        if claude_md_path:
            try:
                with open(claude_md_path, encoding='utf-8') as f:
                    self.claude_md_content = f.read()
                    return
            except Exception:
                pass  # Fall back to files dict

        # Try to find CLAUDE.md in files
        for file_path, content in files.items():
            if file_path.lower().endswith('claude.md'):
                self.claude_md_content = content
                break

        # If no CLAUDE.md found, use a default message
        if not self.claude_md_content:
            self.claude_md_content = "No CLAUDE.md file found in the project."

    def _format_file_tree(self, file_tree: str) -> str:
        """Format file tree for display."""
        return f"""```
{file_tree}
```"""

    def _format_code_files(self, files: Dict[str, str]) -> str:
        """Format code files for review."""
        formatted_files = []

        for file_path, content in files.items():
            # Determine file type for syntax highlighting
            file_ext = Path(file_path).suffix.lower()
            language = self._get_language_from_extension(file_ext)

            formatted_file = f"""## File: {file_path}

```{language}
{content}
```"""
            formatted_files.append(formatted_file)

        return "\n\n".join(formatted_files)

    def _get_language_from_extension(self, extension: str) -> str:
        """Get language identifier for syntax highlighting."""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.sh': 'bash',
            '.bash': 'bash',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.md': 'markdown',
            '.rst': 'rst',
            '.txt': 'text'
        }

        return language_map.get(extension, 'text')

    def _build_focus_areas_prompt(self, focus_areas: Optional[List[str]]) -> str:
        """Build focus areas section of prompt."""
        if not focus_areas:
            return ""

        focus_list = "\n".join(f"- {area}" for area in focus_areas)
        return f"""
**SPECIAL FOCUS AREAS:**
Please pay particular attention to these areas:
{focus_list}
"""

    def _build_review_prompt(self, focus_areas_prompt: str) -> str:
        """Build the complete review prompt."""
        return f"""You are an expert code reviewer. Please review the following codebase comprehensively.

**Project Context:**
{self.claude_md_content}

**Codebase Structure:**
{self.file_tree}

**Code Files:**
{self.code_files}

Please provide a detailed review covering:
1. **Architecture & Design**: Overall structure, patterns, and design decisions
2. **Code Quality**: Readability, maintainability, and adherence to best practices
3. **Security**: Potential vulnerabilities or security concerns
4. **Performance**: Bottlenecks or optimization opportunities
5. **Error Handling**: Robustness, error recovery, and edge case handling
6. **Testing**: Test coverage and quality
7. **Documentation**: Completeness and clarity
8. **Dependencies**: Appropriateness and security of external dependencies

{focus_areas_prompt}

**Format your review as follows:**
- **Executive Summary** (2-3 paragraphs)
- **Strengths** (bullet points)
- **Areas for Improvement** (organized by severity: Critical, Major, Minor)
- **Specific Recommendations** (actionable items)
- **Code Examples** (where applicable)

Focus on providing actionable feedback that will help improve the code quality, security, and maintainability."""

    def format_simple_review(self, content: str) -> str:
        """Format a simple review request for testing."""
        return f"""You are an expert code reviewer. Please review the following code:

```
{content}
```

Provide a brief review focusing on:
- Code quality and best practices
- Potential issues or improvements
- Security considerations

Keep the review concise but thorough."""
