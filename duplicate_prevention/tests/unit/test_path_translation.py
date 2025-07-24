# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for path translation logic in duplicate prevention system."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from duplicate_prevention.workspace_detector import WorkspaceDetector
from hooks.python.guards.duplicate_prevention_guard import DuplicatePreventionGuard


class TestPathTranslation:
    """Test path translation between Docker and local filesystems using real components."""

    def setup_method(self):
        """Create a temporary workspace for testing."""
        self.temp_dir = tempfile.mkdtemp(prefix="test_duplicate_prevention_")
        self.original_cwd = os.getcwd()

        # Create a git repo structure
        git_dir = Path(self.temp_dir) / ".git"
        git_dir.mkdir()

        # Create some test directories
        (Path(self.temp_dir) / "src" / "utils").mkdir(parents=True)
        (Path(self.temp_dir) / "lib").mkdir(parents=True)

        # Change to temp directory
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary workspace."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_relative_to_absolute_conversion_real(self):
        """Test converting relative paths to absolute paths with real components."""
        guard = DuplicatePreventionGuard()

        # Create a test file
        test_file = Path(self.temp_dir) / "src" / "utils" / "helper.py"
        test_file.write_text("def helper(): pass")

        # Test relative path conversion
        relative_path = "src/utils/helper.py"
        absolute_path = guard._convert_to_absolute_path(relative_path)

        # Should convert to absolute path based on workspace
        assert Path(absolute_path).is_absolute()
        assert absolute_path.endswith("src/utils/helper.py")
        assert Path(absolute_path).exists()

    def test_absolute_path_unchanged_real(self):
        """Test that absolute paths are returned unchanged."""
        guard = DuplicatePreventionGuard()

        # Create an absolute path
        absolute_path = str(Path(self.temp_dir) / "src" / "main.py")
        result = guard._convert_to_absolute_path(absolute_path)

        assert result == absolute_path
        assert result.startswith("/")

    def test_workspace_detection_real(self):
        """Test workspace detection with real filesystem."""
        detector = WorkspaceDetector()

        # Get workspace info from our temp directory
        workspace_info = detector.get_workspace_info()

        assert workspace_info["workspace_root"] == self.temp_dir
        assert workspace_info["is_workspace_detected"] is True
        assert workspace_info["collection_name"].endswith("_duplicate_prevention")

    def test_path_normalization_real(self):
        """Test path normalization with real filesystem operations."""
        guard = DuplicatePreventionGuard()

        # Create a real file
        test_file = Path(self.temp_dir) / "src" / "test.py"
        test_file.write_text("# test file")

        # Test with different path representations
        paths = [
            "src/test.py",
            "./src/test.py",
            "src//test.py",
        ]

        results = []
        for path in paths:
            result = guard._convert_to_absolute_path(path)
            results.append(result)
            # Verify the file actually exists at the converted path
            assert Path(result).exists()

        # All should resolve to the same path
        assert len(set(results)) == 1

    def test_empty_path_handling_real(self):
        """Test handling of empty paths with real guard."""
        guard = DuplicatePreventionGuard()

        # Test empty string
        result = guard._convert_to_absolute_path("")
        assert result == ""

    def test_nonexistent_path_handling(self):
        """Test handling of paths that don't exist."""
        guard = DuplicatePreventionGuard()

        # Path that doesn't exist
        nonexistent = "this/does/not/exist.py"
        result = guard._convert_to_absolute_path(nonexistent)

        # Should still convert to absolute even if doesn't exist
        assert Path(result).is_absolute()
        assert result.endswith("this/does/not/exist.py")


class TestWorkspaceDetection:
    """Test workspace detection functionality."""

    def test_workspace_detection_with_git(self):
        """Test workspace detection finds git root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create git structure
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()

            # Create nested directory
            nested = Path(temp_dir) / "src" / "deep" / "nested"
            nested.mkdir(parents=True)

            # Change to nested directory
            original_cwd = os.getcwd()
            try:
                os.chdir(nested)

                detector = WorkspaceDetector()
                info = detector.get_workspace_info()

                assert info["workspace_root"] == temp_dir
                assert Path(info["workspace_root"]) / ".git" in Path(temp_dir).rglob(".git")
            finally:
                os.chdir(original_cwd)

    def test_workspace_detection_without_git(self):
        """Test workspace detection falls back when no indicators found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # No git directory or other indicators
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                detector = WorkspaceDetector()
                info = detector.get_workspace_info()

                # Should not detect workspace
                assert info["workspace_root"] is None
                assert info["is_workspace_detected"] is False
                # Should fall back to global collection
                assert info["collection_name"] == "code_similarity_search"
            finally:
                os.chdir(original_cwd)

    def test_workspace_name_environment_override(self):
        """Test WORKSPACE_NAME environment variable override."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a git directory so workspace is detected
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()

            original_cwd = os.getcwd()
            original_env = os.environ.get("WORKSPACE_NAME")

            try:
                os.chdir(temp_dir)
                os.environ["WORKSPACE_NAME"] = "custom_workspace"

                detector = WorkspaceDetector()
                info = detector.get_workspace_info()

                # Workspace name is derived from collection name
                assert info["collection_name"] == "custom_workspace_duplicate_prevention"
                assert info["is_workspace_detected"] is True
                assert info["workspace_root"] == temp_dir
            finally:
                os.chdir(original_cwd)
                if original_env is None:
                    os.environ.pop("WORKSPACE_NAME", None)
                else:
                    os.environ["WORKSPACE_NAME"] = original_env
