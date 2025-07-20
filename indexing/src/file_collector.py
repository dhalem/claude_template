# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""File collector for code review MCP server.

Recursively scans directories for source and documentation files,
respecting gitignore patterns and handling encoding gracefully.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FileCollector:
    """Collects source and documentation files for code review."""

    # File extensions to include
    SOURCE_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.rs', '.go', '.java',
        '.c', '.cpp', '.h', '.hpp', '.sh', '.bash'
    }

    CONFIG_EXTENSIONS = {
        '.json', '.yaml', '.yml', '.toml', '.ini'
    }

    DOC_EXTENSIONS = {
        '.md', '.rst', '.txt'
    }

    # Directories to exclude (shared with code_indexer.py)
    EXCLUDED_DIRS = {
        '.git', 'node_modules', 'venv', '.venv', '__pycache__',
        'dist', 'build', 'target', '.pytest_cache', '.mypy_cache'
    }

    # Files to always include (case insensitive)
    ALWAYS_INCLUDE = {
        'claude.md', 'readme.md', 'pyproject.toml', 'package.json', 'cargo.toml'
    }

    def __init__(self, max_file_size: int = 1024 * 1024):  # 1MB default
        self.max_file_size = max_file_size
        self.collected_files: Dict[str, str] = {}
        self.skipped_files: List[str] = []
        self.total_size = 0
        self.base_directory: Optional[Path] = None

    def collect_files(self, directory: str) -> Dict[str, str]:
        """Collect all relevant files from directory.

        Args:
            directory: Absolute path to directory to scan

        Returns:
            Dictionary mapping file paths to file contents
        """
        directory_path = Path(directory)

        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Reset state
        self.collected_files = {}
        self.skipped_files = []
        self.total_size = 0
        self.base_directory = directory_path

        # Load .gitignore patterns
        gitignore_patterns = self._load_gitignore(directory_path)

        # Recursively collect files
        self._collect_recursive(directory_path, gitignore_patterns)

        logger.info(f"Collected {len(self.collected_files)} files, "
                    f"skipped {len(self.skipped_files)}, "
                    f"total size: {self.total_size:,} bytes")

        return self.collected_files

    def _collect_recursive(self, path: Path, gitignore_patterns: List[str]) -> None:
        """Recursively collect files from directory."""
        try:
            for item in path.iterdir():
                if item.is_dir():
                    # Skip excluded directories
                    if item.name in self.EXCLUDED_DIRS:
                        logger.debug(f"Skipping excluded directory: {item}")
                        continue

                    # Check gitignore
                    if self._matches_gitignore(item, gitignore_patterns):
                        logger.debug(f"Skipping gitignored directory: {item}")
                        continue

                    # Recurse into subdirectory
                    self._collect_recursive(item, gitignore_patterns)

                elif item.is_file():
                    self._process_file(item, gitignore_patterns)

        except PermissionError:
            logger.warning(f"Permission denied accessing: {path}")
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")

    def _process_file(self, file_path: Path, gitignore_patterns: List[str]) -> None:
        """Process a single file."""
        # Check if file should be included
        if not self._should_include_file(file_path):
            return

        # Check gitignore
        if self._matches_gitignore(file_path, gitignore_patterns):
            logger.debug(f"Skipping gitignored file: {file_path}")
            return

        # Check file size
        try:
            if file_path.stat().st_size > self.max_file_size:
                self.skipped_files.append(f"{file_path} (too large)")
                logger.debug(f"Skipping large file: {file_path}")
                return
        except OSError:
            logger.warning(f"Could not stat file: {file_path}")
            return

        # Read file content
        content = self._read_file_safely(file_path)
        if content is not None:
            # Calculate relative path from the base directory being scanned
            relative_path = str(file_path.relative_to(self.base_directory))
            self.collected_files[relative_path] = content
            self.total_size += len(content)
            logger.debug(f"Collected file: {relative_path}")
        else:
            self.skipped_files.append(f"{file_path} (read error)")

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included based on extension and name."""
        # Always include certain files
        if file_path.name.lower() in self.ALWAYS_INCLUDE:
            return True

        # Check extension
        extension = file_path.suffix.lower()
        return (extension in self.SOURCE_EXTENSIONS or
                extension in self.CONFIG_EXTENSIONS or
                extension in self.DOC_EXTENSIONS)

    def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding detection."""
        encodings = ['utf-8', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    content = f.read()

                # Check if this looks like a binary file
                if self._is_binary_content(content):
                    logger.debug(f"Skipping binary file: {file_path}")
                    return None

                return content

            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                return None

        logger.warning(f"Could not decode file: {file_path}")
        return None

    def _is_binary_content(self, content: str) -> bool:
        """Check if content appears to be binary."""
        # Check for null bytes
        if '\x00' in content:
            return True

        # Check for high ratio of non-printable characters
        if len(content) > 0:
            printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
            ratio = printable_chars / len(content)
            return ratio < 0.7  # Less than 70% printable = probably binary

        return False

    def _load_gitignore(self, directory: Path) -> List[str]:
        """Load gitignore patterns from .gitignore file."""
        gitignore_path = directory / '.gitignore'
        patterns = []

        if gitignore_path.exists():
            try:
                with open(gitignore_path, encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)

                logger.debug(f"Loaded {len(patterns)} gitignore patterns")
            except Exception as e:
                logger.warning(f"Error reading .gitignore: {e}")

        return patterns

    def _matches_gitignore(self, path: Path, patterns: List[str]) -> bool:
        """Check if path matches any gitignore pattern."""
        path_str = str(path)

        return any(self._match_pattern(path_str, pattern) for pattern in patterns)

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Simple gitignore pattern matching."""
        # Handle negation patterns
        if pattern.startswith('!'):
            return False  # Simplified - don't handle negation for now

        # Convert gitignore pattern to regex
        # Escape special regex chars except * and ?
        regex_pattern = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')

        # Handle directory patterns
        if pattern.endswith('/'):
            # Directory patterns should match the directory and anything inside it
            regex_pattern = regex_pattern[:-1] + '(/.*)?$'
        else:
            # For file/directory patterns, match at path boundaries (end of string or followed by /)
            regex_pattern = regex_pattern + '(/|$)'

        # Handle absolute patterns
        if pattern.startswith('/'):
            regex_pattern = '^' + regex_pattern[1:]
        else:
            regex_pattern = '(^|/)' + regex_pattern

        try:
            return bool(re.search(regex_pattern, path))
        except re.error:
            logger.warning(f"Invalid gitignore pattern: {pattern}")
            return False

    def get_file_tree(self) -> str:
        """Generate a tree view of collected files."""
        if not self.collected_files:
            return "No files collected"

        files = sorted(self.collected_files.keys())
        tree_lines = []

        for file_path in files:
            # Simple tree representation
            depth = file_path.count(os.sep)
            indent = "  " * depth
            filename = os.path.basename(file_path)
            tree_lines.append(f"{indent}{filename}")

        return "\n".join(tree_lines)

    def get_collection_summary(self) -> Dict:
        """Get summary of collection results."""
        return {
            "files_collected": len(self.collected_files),
            "files_skipped": len(self.skipped_files),
            "total_size": self.total_size,
            "skipped_files": self.skipped_files
        }
