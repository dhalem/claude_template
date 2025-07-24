# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Duplicate Prevention Guard - prevents creation of similar code.

This guard uses the embedding generation system to detect when new code
is similar to existing code in the repository and warns the user.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, project_root)

from base_guard import BaseGuard, GuardAction, GuardContext


class DuplicatePreventionGuard(BaseGuard):
    """Guard that prevents creation of duplicate/similar code.

    Uses real embedding generation and vector similarity search to detect
    when new code is similar to existing code in the repository.
    """

    def __init__(self):
        super().__init__(
            name="Duplicate Prevention",
            description="Prevents creation of similar code by detecting semantic duplicates using AI embeddings",
        )

        # Configuration
        self.similarity_threshold = 0.70  # 70% similarity threshold
        self.min_file_size = 5  # Minimum lines to check
        self.supported_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".jsx", ".tsx"}

        # Database configuration
        self.db_host = "localhost"
        self.db_port = 6333
        # Note: collection_name is now dynamically determined per workspace
        self._workspace_detector = None

        # Lazy loading for components
        self._db_connector = None
        self._embedding_generator = None

    def get_default_action(self) -> GuardAction:
        """Default action is to block - prevent duplicate code creation by default."""
        return GuardAction.BLOCK

    @property
    def db_connector(self):
        """Lazy load database connector."""
        if self._db_connector is None:
            try:
                from duplicate_prevention.database import DatabaseConnector

                self._db_connector = DatabaseConnector(host=self.db_host, port=self.db_port)
            except Exception:
                self._db_connector = None
        return self._db_connector

    @property
    def embedding_generator(self):
        """Lazy load embedding generator."""
        if self._embedding_generator is None:
            try:
                from duplicate_prevention.embedding_generator import EmbeddingGenerator

                self._embedding_generator = EmbeddingGenerator()
            except Exception:
                self._embedding_generator = None
        return self._embedding_generator

    @property
    def workspace_detector(self):
        """Lazy load workspace detector."""
        if self._workspace_detector is None:
            try:
                from duplicate_prevention.workspace_detector import workspace_detector

                self._workspace_detector = workspace_detector
            except Exception:
                self._workspace_detector = None
        return self._workspace_detector

    def get_workspace_collection_name(self) -> str:
        """Get the collection name for the current workspace.

        Returns:
            Workspace-specific collection name or fallback to global collection
        """
        # Allow test override of collection name
        if hasattr(self, "collection_name") and self.collection_name:
            return self.collection_name

        if self.workspace_detector:
            workspace_info = self.workspace_detector.get_workspace_info()
            return workspace_info["collection_name"]
        else:
            # Fallback to original global collection if workspace detection fails
            return "code_similarity_search"

    def _convert_to_absolute_path(self, file_path: str) -> str:
        """Convert a relative path to absolute path using workspace root.

        Args:
            file_path: The file path (relative or absolute)

        Returns:
            Absolute path to the file
        """
        if not file_path or file_path.startswith("/"):
            return file_path

        # Get workspace root from workspace detector
        if self.workspace_detector:
            try:
                workspace_info = self.workspace_detector.get_workspace_info()
                workspace_root = workspace_info.get("workspace_root")
                if workspace_root:
                    return str(Path(workspace_root) / file_path)
            except Exception:
                # Fall through to return original path
                pass

        return file_path

    def should_trigger(self, context: GuardContext) -> bool:
        """Check if this guard should trigger on the given context.

        Args:
            context: The guard context containing tool and file information

        Returns:
            True if the guard should trigger (similar code detected)
        """
        # Only trigger on file operations
        if context.tool_name not in ["Write", "Edit", "MultiEdit"]:
            return False

        # Get file path and content
        file_path = context.file_path
        if not file_path:
            return False

        # Check if file extension is supported
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_extensions:
            return False

        # Get content to check
        content = self._extract_content(context)
        if not content or not content.strip():
            return False

        # Check if content is large enough to analyze
        line_count = len(content.split("\n"))
        if line_count < self.min_file_size:
            return False

        # Check for similarity with existing code
        return self._check_similarity(content, file_path)

    def _extract_content(self, context: GuardContext) -> str:
        """Extract content from context for similarity checking."""
        content = ""

        if context.content:
            content += context.content

        if context.new_string:
            content += "\n" + context.new_string

        # Handle MultiEdit
        if context.tool_name == "MultiEdit" and context.tool_input:
            edits = context.tool_input.get("edits", [])
            for edit in edits:
                new_str = edit.get("new_string", "")
                if new_str:
                    content += "\n" + new_str

        return content

    def _check_similarity(self, content: str, file_path: str) -> bool:
        """Check if content is similar to existing code.

        Args:
            content: The code content to check
            file_path: Path of the file being created/edited

        Returns:
            True if similar code is found above threshold
        """
        try:
            # Ensure components are available
            if not self.db_connector or not self.embedding_generator:
                return False

            # Get workspace-specific collection name (moved this up)
            collection_name = self.get_workspace_collection_name()

            # Ensure collection exists
            if not self.db_connector.collection_exists(collection_name):
                # Create collection if it doesn't exist
                self.db_connector.create_collection(collection_name, vector_size=384)
                # Continue to store the first vector for future comparisons

            # Generate embedding for the new content
            # Detect language from file extension
            file_ext = Path(file_path).suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".jsx": "javascript",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
                ".go": "go",
                ".rs": "rust",
            }
            language = language_map.get(file_ext, "unknown")

            # Generate embedding
            embedding_result = self.embedding_generator.generate_embedding(content, language)
            if not embedding_result or "embedding" not in embedding_result:
                return False

            embedding = embedding_result["embedding"]
            if not embedding or not isinstance(embedding, list):
                return False

            # Search for similar vectors in workspace-specific collection
            similar_results = self.db_connector.search_similar_vectors(
                collection_name=collection_name, query_vector=embedding, limit=5  # Get top 5 similar results
            )

            # similar_results can be empty list if collection is empty - this is OK
            # Continue to check for similarity and store vector

            # Check if any result exceeds similarity threshold
            self._similar_files = []
            for result in similar_results:
                similarity_score = result.get("score", 0.0)
                if similarity_score >= self.similarity_threshold:
                    result_metadata = result.get("metadata", {})
                    result_file_path = result_metadata.get("file_path", "")

                    # Skip if this is the same file being edited
                    # Convert stored relative path to absolute for comparison
                    from pathlib import Path as PathLib

                    if not result_file_path.startswith("/"):
                        # Get workspace root from workspace detector
                        from duplicate_prevention.workspace_detector import workspace_detector

                        workspace_info = workspace_detector.get_workspace_info()
                        workspace_root = workspace_info["workspace_root"]
                        result_file_path = str(PathLib(workspace_root) / result_file_path)

                    # Now compare absolute paths
                    if result_file_path == file_path:
                        continue

                    self._similar_files.append({"score": similarity_score, "metadata": result_metadata})

            # If duplicates found, return True to trigger warning
            if len(self._similar_files) > 0:
                return True

            # No duplicates found - store this code for future comparisons
            try:
                # Generate unique point ID based on file path and content hash
                import hashlib

                content_hash = hashlib.md5(content.encode()).hexdigest()
                point_id = abs(hash(f"{file_path}:{content_hash}")) % (2**31)

                # Create metadata for the stored vector
                metadata = {
                    "file_path": file_path,
                    "language": language,
                    "content_hash": content_hash,
                    "line_count": len(content.split("\n")),
                    "created_at": str(time.time()),
                }

                # Store the vector for future comparisons
                success = self.db_connector.insert_point(
                    collection_name=collection_name, point_id=point_id, vector=embedding, metadata=metadata
                )

                if success:
                    print(f"Debug: Stored vector for {file_path} in {collection_name}")
                else:
                    print(f"Warning: Failed to store vector for {file_path}")

            except Exception as store_error:
                print(f"Warning: Failed to store vector: {store_error}")

            return False

        except Exception as e:
            # Fail gracefully - don't block on errors
            print(f"Warning: Duplicate prevention check failed: {e}")
            return False

    def get_message(self, context: GuardContext) -> str:
        """Get the message to display when the guard triggers.

        Args:
            context: The guard context

        Returns:
            Detailed message about similar files found
        """
        if not hasattr(self, "_similar_files") or not self._similar_files:
            return "🔍 DUPLICATE DETECTION: Similar code detected, but details unavailable."

        # Sort by similarity score (highest first)
        similar_files = sorted(self._similar_files, key=lambda x: x["score"], reverse=True)

        message_parts = ["🚨 DUPLICATE CODE BLOCKED: Similar code already exists!", "", "📍 DUPLICATE LOCATIONS FOUND:"]

        for i, similar in enumerate(similar_files[:3], 1):  # Show top 3
            score = similar["score"]
            metadata = similar["metadata"]
            file_path = metadata.get("file_path", "Unknown file")

            # Convert relative path to absolute local path
            # The metadata stores relative paths, but we need to show absolute paths to the user
            if not file_path.startswith("/"):
                # Get workspace root from workspace detector
                from duplicate_prevention.workspace_detector import workspace_detector

                workspace_info = workspace_detector.get_workspace_info()
                workspace_root = workspace_info["workspace_root"]
                file_path = str(Path(workspace_root) / file_path)

            percentage = int(score * 100)
            message_parts.append(f"  {i}. {percentage}% similar code in: {file_path}")
            message_parts.append(f"     Similarity score: {score:.3f}")

        message_parts.extend(
            [
                "",
                "❌ WHY THIS IS BLOCKED:",
                "  Creating duplicate code leads to maintenance issues, bugs, and inconsistency.",
                "  The existing code should be reused or refactored instead.",
                "",
                "✅ RECOMMENDED ACTIONS:",
                "  1. Edit the existing similar file to add your functionality",
                "  2. Extract common code into a shared utility function",
                "  3. Refactor both implementations to use shared components",
                "",
                "🔓 TO OVERRIDE THIS BLOCK:",
                "  If you believe this is genuinely different functionality:",
                "  1. Ask for an override code from the human operator",
                "  2. Re-run with: HOOK_OVERRIDE_CODE=<code> <your command>",
                "",
                "💡 SIMILARITY GUIDE:",
                "  • 90%+ = Almost identical - definitely reuse existing",
                "  • 80-90% = Very similar - strong refactoring candidate",
                "  • 75-80% = Similar patterns - consider shared utilities",
            ]
        )

        return "\n".join(message_parts)
