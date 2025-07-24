# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Test fingerprinting utility for unique test identification.
Provides content-based fingerprinting with AST analysis and metadata extraction.
"""

import ast
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Optional


class TestFingerprinter:
    """Generates unique fingerprints for test files and functions."""

    def __init__(self, cache_enabled: bool = False):
        """Initialize the fingerprinter with optional caching.

        Args:
            cache_enabled: Whether to enable fingerprint caching
        """
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, str] = {}
        self._cache_stats = {"hits": 0, "misses": 0}

    def generate_fingerprint(self, content: str, filename: str, method: str = "content") -> str:
        """Generate a fingerprint for test content.

        Args:
            content: The test file content
            filename: Name of the test file
            method: Fingerprinting method ("content" or "ast")

        Returns:
            SHA-256 hex fingerprint string
        """
        # Check cache first
        cache_key = f"{method}:{filename}:{hash(content)}"
        if self.cache_enabled and cache_key in self._cache:
            self._cache_stats["hits"] += 1
            return self._cache[cache_key]

        self._cache_stats["misses"] += 1

        if method == "ast":
            fingerprint = self._generate_ast_fingerprint(content, filename)
        else:
            fingerprint = self._generate_content_fingerprint(content, filename)

        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = fingerprint

        return fingerprint

    def _generate_content_fingerprint(self, content: str, filename: str) -> str:
        """Generate fingerprint based on normalized content."""
        # Normalize whitespace
        normalized_content = self._normalize_whitespace(content)

        # Include filename to prevent collisions
        combined = f"{filename}:{normalized_content}"

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()

    def _generate_ast_fingerprint(self, content: str, filename: str) -> str:
        """Generate fingerprint based on AST (ignoring comments)."""
        try:
            # Parse content to AST
            tree = ast.parse(content)

            # Convert AST to normalized string representation
            ast_str = ast.dump(tree, annotate_fields=False, include_attributes=False)

            # Include filename
            combined = f"{filename}:{ast_str}"

            # Generate SHA-256 hash
            hash_obj = hashlib.sha256(combined.encode('utf-8'))
            return hash_obj.hexdigest()
        except SyntaxError:
            # Fall back to content-based if AST parsing fails
            return self._generate_content_fingerprint(content, filename)

    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in content."""
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in content.splitlines()]

        # Remove empty lines
        lines = [line for line in lines if line]

        # Join with consistent spacing
        return '\n'.join(lines)

    def generate_from_file(self, file_path: str) -> str:
        """Generate fingerprint directly from file path.

        Args:
            file_path: Path to the test file

        Returns:
            SHA-256 hex fingerprint string
        """
        path = Path(file_path)
        content = path.read_text(encoding='utf-8')
        filename = path.name

        return self.generate_fingerprint(content, filename)

    def generate_function_fingerprint(self, content: str, function_name: str, filename: str) -> str:
        """Generate fingerprint for a specific function within a file.

        Args:
            content: The test file content
            function_name: Name of the function to fingerprint
            filename: Name of the test file

        Returns:
            SHA-256 hex fingerprint string
        """
        try:
            # Parse content to AST
            tree = ast.parse(content)

            # Find the specific function
            function_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    function_node = node
                    break

            if function_node is None:
                raise ValueError(f"Function '{function_name}' not found in content")

            # Convert function AST to string
            function_ast_str = ast.dump(function_node, annotate_fields=False, include_attributes=False)

            # Include filename and function name
            combined = f"{filename}:{function_name}:{function_ast_str}"

            # Generate SHA-256 hash
            hash_obj = hashlib.sha256(combined.encode('utf-8'))
            return hash_obj.hexdigest()

        except SyntaxError:
            # Fall back to content-based search
            return self._extract_function_content_fingerprint(content, function_name, filename)

    def _extract_function_content_fingerprint(self, content: str, function_name: str, filename: str) -> str:
        """Extract function content using regex and generate fingerprint."""
        # Simple regex to find function definition
        pattern = rf'def\s+{re.escape(function_name)}\s*\([^)]*\):.*?(?=def\s+|\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            raise ValueError(f"Function '{function_name}' not found in content")

        function_content = match.group(0)
        normalized_content = self._normalize_whitespace(function_content)

        # Include filename and function name
        combined = f"{filename}:{function_name}:{normalized_content}"

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()

    def has_changed(self, fingerprint1: str, fingerprint2: str) -> bool:
        """Check if two fingerprints indicate a change.

        Args:
            fingerprint1: First fingerprint
            fingerprint2: Second fingerprint

        Returns:
            True if fingerprints are different (indicating change)
        """
        return fingerprint1 != fingerprint2

    def extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract metadata from test file content.

        Args:
            content: The test file content
            filename: Name of the test file

        Returns:
            Dictionary containing extracted metadata
        """
        try:
            # Parse content to AST
            tree = ast.parse(content)

            metadata = {
                "functions": [],
                "classes": [],
                "imports": [],
                "decorators": []
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip methods inside classes for function list
                    if not any(isinstance(parent, ast.ClassDef)
                             for parent in ast.walk(tree)
                             if any(n == node for n in ast.walk(parent))):
                        metadata["functions"].append(node.name)

                    # Extract decorators from this function
                    for decorator in node.decorator_list:
                        decorator_name = self._extract_decorator_name(decorator)
                        if decorator_name and decorator_name not in metadata["decorators"]:
                            metadata["decorators"].append(decorator_name)

                elif isinstance(node, ast.ClassDef):
                    metadata["classes"].append(node.name)

                    # Extract decorators from methods in this class
                    for class_node in node.body:
                        if isinstance(class_node, ast.FunctionDef):
                            for decorator in class_node.decorator_list:
                                decorator_name = self._extract_decorator_name(decorator)
                                if decorator_name and decorator_name not in metadata["decorators"]:
                                    metadata["decorators"].append(decorator_name)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        metadata["imports"].append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        metadata["imports"].append(node.module)

            return metadata

        except SyntaxError:
            # Return empty metadata if parsing fails
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "decorators": []
            }

    def _extract_decorator_name(self, decorator) -> Optional[str]:
        """Extract decorator name from AST node.

        Args:
            decorator: AST decorator node

        Returns:
            String representation of decorator name or None
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            # Handle nested attributes like pytest.mark.slow
            parts = []
            node = decorator
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
                return '.'.join(reversed(parts))
        elif isinstance(decorator, ast.Call):
            # Handle decorator calls like @pytest.mark.slow()
            return self._extract_decorator_name(decorator.func)

        return None

    def get_cache_stats(self) -> Dict[str, int]:
        """Get caching statistics.

        Returns:
            Dictionary with cache hit and miss counts
        """
        return self._cache_stats.copy()
