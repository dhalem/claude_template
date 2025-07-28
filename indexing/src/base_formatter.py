# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Base formatter for code analysis MCP server.

Provides common functionality for formatting files and context for Gemini analysis.
Extracted from ReviewFormatter to support multiple analysis types.
"""

import os
from pathlib import Path
from typing import Dict, Optional


class BaseFormatter:
    """Base class for formatting code files and context for Gemini analysis."""

    def __init__(self):
        self.file_tree = ""
        self.code_files = ""

    def _format_file_tree(self, file_tree: str) -> str:
        """Format file tree for display.

        Args:
            file_tree: String representation of file structure

        Returns:
            Formatted file tree with code block syntax
        """
        return f"""```
{file_tree}
```"""

    def _format_code_files(self, files: Dict[str, str]) -> str:
        """Format code files for analysis.

        Args:
            files: Dictionary of file paths to contents

        Returns:
            Formatted string with all files and syntax highlighting
        """
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
        """Get language identifier for syntax highlighting.

        Args:
            extension: File extension (e.g., '.py', '.js')

        Returns:
            Language identifier for markdown syntax highlighting
        """
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".sh": "bash",
            ".bash": "bash",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".md": "markdown",
            ".rst": "rst",
            ".txt": "text",
        }

        return language_map.get(extension, "text")

    def _generate_file_tree_from_files(self, files: Dict[str, str]) -> str:
        """Generate a tree view from file dictionary.

        Args:
            files: Dictionary of file paths to contents

        Returns:
            Tree representation of the files
        """
        if not files:
            return "No files provided"

        file_paths = sorted(files.keys())
        tree_lines = []

        for file_path in file_paths:
            # Simple tree representation
            depth = file_path.count(os.sep)
            indent = "  " * depth
            filename = os.path.basename(file_path)
            tree_lines.append(f"{indent}{filename}")

        return "\n".join(tree_lines)

    def _load_claude_md_from_files(self, files: Dict[str, str]) -> str:
        """Load CLAUDE.md content from files dictionary.

        Args:
            files: Dictionary of file paths to contents

        Returns:
            CLAUDE.md content or default message if not found
        """
        # Try to find CLAUDE.md in files
        for file_path, content in files.items():
            if file_path.lower().endswith("claude.md") or file_path.lower() == "claude.md":
                return content

        # If no CLAUDE.md found, return default message
        return "No CLAUDE.md file found in the provided files."

    def format_base_context(self, files: Dict[str, str], file_tree: Optional[str] = None) -> Dict[str, str]:
        """Format basic context components that can be used by subclasses.

        Args:
            files: Dictionary of file paths to contents
            file_tree: Optional pre-generated file tree

        Returns:
            Dictionary with formatted components: 'claude_md', 'file_tree', 'code_files'
        """
        # Load CLAUDE.md content
        claude_md_content = self._load_claude_md_from_files(files)

        # Generate or use provided file tree
        if file_tree is None:
            file_tree = self._generate_file_tree_from_files(files)

        # Format file tree and code files
        formatted_file_tree = self._format_file_tree(file_tree)
        formatted_code_files = self._format_code_files(files)

        return {"claude_md": claude_md_content, "file_tree": formatted_file_tree, "code_files": formatted_code_files}
