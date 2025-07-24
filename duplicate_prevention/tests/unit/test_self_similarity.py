# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for self-similarity detection in duplicate prevention system."""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from duplicate_prevention.database import DatabaseConnector
from duplicate_prevention.embedding_generator import EmbeddingGenerator

# Import guard components - add hooks/python to path
hooks_path = project_root / "hooks" / "python"
sys.path.insert(0, str(hooks_path))

from base_guard import GuardContext
from guards.duplicate_prevention_guard import DuplicatePreventionGuard


class TestSelfSimilarityDetection:
    """Test that the guard allows edits to the same file."""

    def setup_method(self):
        """Set up test environment."""
        self.db = DatabaseConnector()
        self.embedding_gen = EmbeddingGenerator()
        self.guard = DuplicatePreventionGuard()

        # Create a unique test collection
        self.test_collection = f"test_self_similarity_{int(time.time() * 1000)}"

        # Ensure collection exists
        if not self.db.collection_exists(self.test_collection):
            self.db.create_collection(self.test_collection, vector_size=384)

    def teardown_method(self):
        """Clean up test collection."""
        try:
            self.db.delete_collection(self.test_collection)
        except Exception:
            pass

    def test_same_file_not_blocked(self):
        """Test that editing the same file is not blocked."""
        # Create test file content
        test_code = """
def calculate_sum(a, b):
    '''Calculate sum of two numbers.'''
    return a + b
"""

        # Store the code in our test collection
        embedding_result = self.embedding_gen.generate_embedding(test_code, "python")
        embedding = embedding_result["embedding"]

        # Store with a test file path - use absolute path for consistency
        test_file = "/home/user/project/math_utils.py"
        metadata = {
            "file_path": test_file,  # Store absolute path for simpler comparison
            "language": "python",
            "content_hash": "test_hash",
        }

        point_id = abs(hash(test_file)) % (2**31)
        self.db.insert_point(
            collection_name=self.test_collection, point_id=point_id, vector=embedding, metadata=metadata
        )

        # Now simulate editing the same file
        # The guard should detect it's the same file and not block
        context = GuardContext(
            tool_name="Edit",
            tool_input={"file_path": test_file, "content": test_code},
            file_path=test_file,
            content=test_code,  # Same content
        )

        # Override the collection name for testing
        original_get_collection = self.guard.get_workspace_collection_name
        self.guard.get_workspace_collection_name = lambda: self.test_collection

        try:
            # Check if guard triggers
            should_trigger = self.guard.should_trigger(context)

            # Guard should NOT trigger for editing same file
            assert should_trigger is False
        finally:
            # Restore original method
            self.guard.get_workspace_collection_name = original_get_collection

    def test_same_filename_different_directory_blocked(self):
        """Test that same filename in different directory IS blocked."""
        # Create test file content
        test_code = """
def calculate_sum(a, b):
    '''Calculate sum of two numbers.'''
    return a + b
"""

        # Store the code in our test collection
        embedding_result = self.embedding_gen.generate_embedding(test_code, "python")
        embedding = embedding_result["embedding"]

        # Store with original file path
        original_file = "/home/user/project1/utils.py"
        metadata = {"file_path": original_file, "language": "python", "content_hash": "test_hash"}  # Use absolute path

        point_id = abs(hash(original_file)) % (2**31)
        self.db.insert_point(
            collection_name=self.test_collection, point_id=point_id, vector=embedding, metadata=metadata
        )

        # Now try to create same code in different directory
        new_file = "/home/user/project2/utils.py"
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": new_file, "content": test_code},
            file_path=new_file,
            content=test_code,
        )

        # Override the collection name for testing
        original_get_collection = self.guard.get_workspace_collection_name
        self.guard.get_workspace_collection_name = lambda: self.test_collection

        try:
            # Check if guard triggers
            should_trigger = self.guard.should_trigger(context)

            # Guard SHOULD trigger - this is duplicate code in different location
            assert should_trigger is True

            # Verify the error message mentions the original file
            message = self.guard.get_message(context)
            assert "/home/user/project1/utils.py" in message or "Similar code already exists" in message
        finally:
            # Restore original method
            self.guard.get_workspace_collection_name = original_get_collection

    def test_edit_existing_file_allowed(self):
        """Test that editing an existing file with modifications is allowed."""
        # Original code
        original_code = """
def process_data(data):
    '''Process input data.'''
    return data.upper()
"""

        # Store the original code
        embedding_result = self.embedding_gen.generate_embedding(original_code, "python")
        embedding = embedding_result["embedding"]

        test_file = "/home/user/project/processor.py"
        metadata = {"file_path": test_file, "language": "python", "content_hash": "original_hash"}

        point_id = abs(hash(test_file)) % (2**31)
        self.db.insert_point(
            collection_name=self.test_collection, point_id=point_id, vector=embedding, metadata=metadata
        )

        # Modified code (added logging)
        modified_code = """
def process_data(data):
    '''Process input data.'''
    print(f"Processing: {data}")
    return data.upper()
"""

        # Try to edit the same file
        context = GuardContext(
            tool_name="Edit",
            tool_input={"file_path": test_file, "content": modified_code},
            file_path=test_file,
            content=modified_code,
        )

        # Override the collection name for testing
        original_get_collection = self.guard.get_workspace_collection_name
        self.guard.get_workspace_collection_name = lambda: self.test_collection

        try:
            # Check if guard triggers
            should_trigger = self.guard.should_trigger(context)

            # Guard should NOT block editing same file
            assert should_trigger is False
        finally:
            # Restore original method
            self.guard.get_workspace_collection_name = original_get_collection

    def test_relative_vs_absolute_path_comparison(self):
        """Test that relative and absolute paths to same file are recognized."""
        test_code = """
class DataProcessor:
    def __init__(self):
        self.data = []
"""

        # Store with relative path
        embedding_result = self.embedding_gen.generate_embedding(test_code, "python")
        embedding = embedding_result["embedding"]

        metadata = {"file_path": "src/processor.py", "language": "python", "content_hash": "test_hash"}  # Relative path

        point_id = 12345
        self.db.insert_point(
            collection_name=self.test_collection, point_id=point_id, vector=embedding, metadata=metadata
        )

        # Now edit with absolute path
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create git directory for workspace detection
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()

            # Create the src directory
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()

            # Absolute path to the file
            absolute_file = src_dir / "processor.py"
            absolute_file.write_text(test_code)

            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                context = GuardContext(
                    tool_name="Edit",
                    tool_input={"file_path": str(absolute_file), "content": test_code},
                    file_path=str(absolute_file),
                    content=test_code,
                )

                # Override the collection name for testing
                original_get_collection = self.guard.get_workspace_collection_name
                self.guard.get_workspace_collection_name = lambda: self.test_collection

                try:
                    # Check if guard triggers
                    should_trigger = self.guard.should_trigger(context)

                    # Should NOT trigger - same file
                    assert should_trigger is False
                finally:
                    # Restore original method
                    self.guard.get_workspace_collection_name = original_get_collection
            finally:
                os.chdir(original_cwd)

    def test_high_similarity_but_different_file_blocked(self):
        """Test that very similar code in different file is still blocked."""
        # Original code
        original_code = """
def validate_email(email):
    '''Validate email address format.'''
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
"""

        # Store original
        embedding_result = self.embedding_gen.generate_embedding(original_code, "python")
        embedding = embedding_result["embedding"]

        original_file = "/home/user/project/validators/email.py"
        metadata = {"file_path": original_file, "language": "python", "content_hash": "original_hash"}

        point_id = abs(hash(original_file)) % (2**31)
        self.db.insert_point(
            collection_name=self.test_collection, point_id=point_id, vector=embedding, metadata=metadata
        )

        # Very similar code (just changed variable name)
        similar_code = """
def validate_email(addr):
    '''Validate email address format.'''
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, addr) is not None
"""

        # Try to create in different file
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/home/user/project/utils/email_checker.py", "content": similar_code},
            file_path="/home/user/project/utils/email_checker.py",
            content=similar_code,
        )

        # Override the collection name for testing
        original_get_collection = self.guard.get_workspace_collection_name
        self.guard.get_workspace_collection_name = lambda: self.test_collection

        try:
            # Check if guard triggers
            should_trigger = self.guard.should_trigger(context)

            # Should trigger - this is duplicate code
            assert should_trigger is True
        finally:
            # Restore original method
            self.guard.get_workspace_collection_name = original_get_collection
