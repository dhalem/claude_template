# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Workspace detection utility for duplicate prevention system.

Mirrors the workspace detection pattern from code search indexer but uses
common workspace indicators instead of .code_index.db files.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional


class WorkspaceDetector:
    """Detects workspace boundaries for duplicate prevention collections.

    Uses the same search pattern as code search indexer but looks for
    common workspace indicators to identify project boundaries.
    """

    # Workspace indicators in priority order
    WORKSPACE_INDICATORS = [
        ".git",  # Git repository (highest priority)
        "package.json",  # Node.js project
        "pyproject.toml",  # Modern Python project
        "setup.py",  # Python project
        "Cargo.toml",  # Rust project
        "pom.xml",  # Java Maven project
        "build.gradle",  # Java Gradle project
        "go.mod",  # Go module
        "composer.json",  # PHP project
        "Gemfile",  # Ruby project
        ".code_index.db",  # Code search database (fallback)
    ]

    def __init__(self):
        """Initialize workspace detector."""
        pass

    def find_workspace_root(self, start_path: Optional[str] = None) -> Optional[str]:
        """Find workspace root directory using code search pattern.

        Args:
            start_path: Optional starting path (defaults to current working directory)

        Returns:
            Absolute path to workspace root, or None if not found
        """
        if start_path:
            current = Path(start_path).resolve()
        else:
            current = Path.cwd().resolve()

        # Search current directory and parent directories up to 3 levels
        # This mirrors the exact pattern from code_searcher.py
        search_paths = [current]

        # Add parent directories up to 3 levels
        parent = current
        for _ in range(3):
            parent = parent.parent
            search_paths.append(parent)

        # Also check home directory and Docker path like code search
        search_paths.extend(
            [
                Path.home(),
                Path("/app"),  # Docker container path
            ]
        )

        # Search for workspace indicators in priority order
        for workspace_path in search_paths:
            if not workspace_path.exists():
                continue

            for indicator in self.WORKSPACE_INDICATORS:
                indicator_path = workspace_path / indicator
                if indicator_path.exists():
                    return str(workspace_path.resolve())

        # No workspace found
        return None

    def get_workspace_collection_name(self, workspace_root: Optional[str] = None) -> str:
        """Generate Qdrant collection name for workspace.

        Args:
            workspace_root: Optional workspace root path

        Returns:
            Sanitized collection name for the workspace
        """
        if not workspace_root:
            workspace_root = self.find_workspace_root()

        if not workspace_root:
            # Fallback to global collection if no workspace detected
            return "code_similarity_search"

        # Generate stable collection name from workspace path
        workspace_path = Path(workspace_root).resolve()

        # Check for environment variable override (useful for Docker)
        workspace_name = os.getenv("WORKSPACE_NAME")
        if not workspace_name:
            workspace_name = workspace_path.name

        # Sanitize name for Qdrant collection requirements
        # Collection names must be alphanumeric with underscores/hyphens
        sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "_", workspace_name)
        sanitized_name = re.sub(r"_+", "_", sanitized_name)  # Collapse multiple underscores
        sanitized_name = sanitized_name.strip("_")  # Remove leading/trailing underscores

        # Ensure name is not empty
        if not sanitized_name:
            sanitized_name = "workspace"

        # Add suffix to ensure uniqueness and indicate purpose
        collection_name = f"{sanitized_name}_duplicate_prevention"

        # Handle potential naming conflicts by adding hash suffix if needed
        if len(collection_name) > 60:  # Qdrant has collection name length limits
            # Create short hash of full path for uniqueness
            path_hash = hashlib.md5(str(workspace_path).encode()).hexdigest()[:8]
            collection_name = f"{sanitized_name[:40]}_dp_{path_hash}"

        return collection_name

    def get_workspace_info(self, start_path: Optional[str] = None) -> dict:
        """Get complete workspace information.

        Args:
            start_path: Optional starting path

        Returns:
            Dictionary with workspace root, collection name, and metadata
        """
        workspace_root = self.find_workspace_root(start_path)
        collection_name = self.get_workspace_collection_name(workspace_root)

        return {
            "workspace_root": workspace_root,
            "collection_name": collection_name,
            "detected_indicators": self._get_detected_indicators(workspace_root) if workspace_root else [],
            "is_workspace_detected": workspace_root is not None,
        }

    def _get_detected_indicators(self, workspace_root: str) -> list:
        """Get list of workspace indicators found in the workspace root.

        Args:
            workspace_root: Workspace root directory

        Returns:
            List of indicator files/directories found
        """
        detected = []
        workspace_path = Path(workspace_root)

        for indicator in self.WORKSPACE_INDICATORS:
            if (workspace_path / indicator).exists():
                detected.append(indicator)

        return detected


# Singleton instance for easy access
workspace_detector = WorkspaceDetector()
