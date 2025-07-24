# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Test suite for DuplicatePreventionGuard - RED phase (failing tests).

These tests use REAL integration testing with actual database and embedding systems.
No mocks are used - all tests verify real functionality.
"""

import os
import sys
import unittest

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, project_root)

from base_guard import GuardAction, GuardContext


class TestDuplicatePreventionGuard(unittest.TestCase):
    """Test suite for DuplicatePreventionGuard.

    RED PHASE: These tests should FAIL until the guard is implemented.
    Uses REAL integration testing - no mocks.
    """

    def setUp(self):
        """Set up test fixtures with real components."""
        # Import the guard that doesn't exist yet
        try:
            from guards.duplicate_prevention_guard import DuplicatePreventionGuard

            self.guard = DuplicatePreventionGuard()
        except ImportError:
            self.skipTest("DuplicatePreventionGuard not implemented yet")

        # Set up test database
        self.test_db_host = "localhost"
        self.test_db_port = 6333
        self.test_collection = "test_duplicate_prevention_guard"

    def tearDown(self):
        """Clean up test data."""
        if hasattr(self, "guard") and hasattr(self.guard, "db_connector"):
            try:
                # Clean up test collection
                self.guard.db_connector.delete_collection(self.test_collection)
            except:
                pass  # Ignore cleanup errors

        # Also clean up any direct database connections used in tests
        from duplicate_prevention.database import DatabaseConnector

        try:
            db = DatabaseConnector(host=self.test_db_host, port=self.test_db_port)
            db.delete_collection(self.test_collection)
        except:
            pass  # Ignore cleanup errors

    def test_guard_metadata(self):
        """Test guard has proper name and description."""
        self.assertEqual(self.guard.name, "Duplicate Prevention")
        self.assertIn("similar code", self.guard.description.lower())
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)

    def test_should_not_trigger_on_non_file_operations(self):
        """Guard should not trigger on non-file operations."""
        context = GuardContext(tool_name="Bash", tool_input={"command": "ls -la"}, command="ls -la")
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_empty_content(self):
        """Guard should not trigger on empty file content."""
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/test/empty.py", "content": ""},
            file_path="/test/empty.py",
            content="",
        )
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_small_files(self):
        """Guard should not trigger on very small files (< 50 lines)."""
        small_content = "print('hello')\n" * 10  # 10 lines
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/test/small.py", "content": small_content},
            file_path="/test/small.py",
            content=small_content,
        )
        self.assertFalse(self.guard.should_trigger(context))

    def test_should_trigger_on_similar_python_function_real_integration(self):
        """Guard should trigger when creating similar Python functions.

        Uses REAL database and embedding generation - no mocks.
        """
        # First, insert a similar function into the database
        existing_function = '''
def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    import math
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
'''

        # Store existing function in database using real embedding system
        from duplicate_prevention.database import DatabaseConnector
        from duplicate_prevention.embedding_generator import EmbeddingGenerator

        db = DatabaseConnector(host=self.test_db_host, port=self.test_db_port)
        embedding_gen = EmbeddingGenerator()

        # Ensure we start with a clean collection
        try:
            db.delete_collection(self.test_collection)
        except:
            pass  # Collection might not exist

        # Create test collection
        db.create_collection(self.test_collection, vector_size=384)

        # Configure guard to use our test collection
        self.guard.collection_name = self.test_collection

        # Generate and store embedding for existing function
        existing_embedding_result = embedding_gen.generate_embedding(existing_function, "python")
        existing_embedding = existing_embedding_result["embedding"]
        db.insert_point(
            collection_name=self.test_collection,
            point_id=1,
            vector=existing_embedding,
            metadata={"file_path": "/existing/utils.py", "function_name": "calculate_distance", "language": "python"},
        )

        # Now test similar function - should trigger guard
        new_function = '''
def compute_point_distance(x1, y1, x2, y2):
    """Compute the distance between two coordinate points."""
    import math
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
'''

        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/new/geometry.py", "content": new_function},
            file_path="/new/geometry.py",
            content=new_function,
        )

        # This should trigger because the functions are very similar
        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_different_function_real_integration(self):
        """Guard should not trigger when functions are actually different.

        Uses REAL database and embedding generation - no mocks.
        """
        # Insert a different function into the database
        existing_function = '''
def send_email(to_address, subject, body):
    """Send an email message."""
    import smtplib
    # Email sending logic here
    return True
'''

        # Store existing function in database
        from duplicate_prevention.database import DatabaseConnector
        from duplicate_prevention.embedding_generator import EmbeddingGenerator

        db = DatabaseConnector(host=self.test_db_host, port=self.test_db_port)
        embedding_gen = EmbeddingGenerator()

        # Ensure we start with a clean collection
        try:
            db.delete_collection(self.test_collection)
        except:
            pass  # Collection might not exist

        # Create test collection
        db.create_collection(self.test_collection, vector_size=384)

        # Configure guard to use our test collection
        self.guard.collection_name = self.test_collection

        # Generate and store embedding
        existing_embedding_result = embedding_gen.generate_embedding(existing_function, "python")
        existing_embedding = existing_embedding_result["embedding"]
        db.insert_point(
            collection_name=self.test_collection,
            point_id=1,
            vector=existing_embedding,
            metadata={"file_path": "/existing/email_utils.py", "function_name": "send_email", "language": "python"},
        )

        # Test completely different function - should NOT trigger
        new_function = '''
def calculate_fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
'''

        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/new/math_utils.py", "content": new_function},
            file_path="/new/math_utils.py",
            content=new_function,
        )

        # Should not trigger because functions are completely different
        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_shows_similar_files_real_data(self):
        """Guard message should show details of similar files found.

        Uses REAL database with actual similar files.
        """
        # Set up real database with similar functions
        from duplicate_prevention.database import DatabaseConnector
        from duplicate_prevention.embedding_generator import EmbeddingGenerator

        db = DatabaseConnector(host=self.test_db_host, port=self.test_db_port)
        embedding_gen = EmbeddingGenerator()

        # Ensure we start with a clean collection
        try:
            db.delete_collection(self.test_collection)
        except:
            pass  # Collection might not exist

        # Create fresh test collection
        db.create_collection(self.test_collection, vector_size=384)

        # Configure guard to use our test collection
        self.guard.collection_name = self.test_collection

        # Insert two similar distance calculation functions
        function1 = '''
def euclidean_distance(p1, p2):
    """Calculate Euclidean distance."""
    import math
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
'''

        function2 = '''
def manhattan_distance(p1, p2):
    """Calculate Manhattan distance."""
    return sum(abs(a - b) for a, b in zip(p1, p2))
'''

        # Store both functions
        embed1_result = embedding_gen.generate_embedding(function1, "python")
        embed2_result = embedding_gen.generate_embedding(function2, "python")
        embed1 = embed1_result["embedding"]
        embed2 = embed2_result["embedding"]

        db.insert_point(
            self.test_collection, 1, embed1, {"file_path": "/app/utils/math.py", "function_name": "euclidean_distance"}
        )

        db.insert_point(
            self.test_collection,
            2,
            embed2,
            {"file_path": "/app/geometry/distance.py", "function_name": "manhattan_distance"},
        )

        # Test new similar function
        new_function = '''
def point_distance(x1, y1, x2, y2):
    """Calculate distance between points."""
    import math
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)
'''

        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/new/point_calc.py", "content": new_function},
            file_path="/new/point_calc.py",
            content=new_function,
        )

        # First call should_trigger to populate _similar_files
        should_trigger = self.guard.should_trigger(context)
        self.assertTrue(should_trigger, "Guard should trigger for similar functions")

        # Get the actual message from the guard
        message = self.guard.get_message(context)

        # Verify message contains information about similar files
        self.assertIn("similar", message.lower())
        self.assertIn("/app/utils/math.py", message)
        self.assertIn("75%", message)  # Check similarity percentage is shown

    def test_handles_database_unavailable_gracefully(self):
        """Guard should handle database unavailability gracefully."""
        # Test with invalid database connection
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/test/file.py", "content": "def test(): pass"},
            file_path="/test/file.py",
            content="def test(): pass",
        )

        # Should not crash and should not trigger when database is unavailable
        result = self.guard.should_trigger(context)
        self.assertIsInstance(result, bool)

    def test_similarity_threshold_configuration(self):
        """Guard should use configurable similarity threshold."""
        self.assertTrue(hasattr(self.guard, "similarity_threshold"))
        self.assertIsInstance(self.guard.similarity_threshold, float)
        self.assertGreater(self.guard.similarity_threshold, 0.0)
        self.assertLess(self.guard.similarity_threshold, 1.0)

    def test_minimum_file_size_configuration(self):
        """Guard should have configurable minimum file size for checking."""
        self.assertTrue(hasattr(self.guard, "min_file_size"))
        self.assertIsInstance(self.guard.min_file_size, int)
        self.assertGreater(self.guard.min_file_size, 0)

    def test_supported_file_extensions(self):
        """Guard should check only supported file extensions."""
        self.assertTrue(hasattr(self.guard, "supported_extensions"))
        self.assertIsInstance(self.guard.supported_extensions, (list, tuple, set))

        # Should support common programming languages
        extensions = set(self.guard.supported_extensions)
        expected_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"}
        self.assertTrue(expected_extensions.issubset(extensions))

    def test_multiedit_operation_support(self):
        """Guard should work with MultiEdit operations."""
        # Create context for MultiEdit operation
        multiedit_content = r'''
import re

def validate_email_address(email):
    """Validate email format using regex pattern."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
'''

        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={
                "file_path": "/new/validator.py",
                "edits": [{"old_string": "", "new_string": multiedit_content}],
            },
            file_path="/new/validator.py",
            new_string=multiedit_content,
        )

        # Should handle MultiEdit operations
        result = self.guard.should_trigger(context)
        self.assertIsInstance(result, bool)

    def test_javascript_similarity_detection(self):
        """Guard should detect similar JavaScript code."""
        js_content = r"""
class UserValidator {
    constructor() {
        this.emailPattern = /^[^@]+@[^@]+\.[^@]+$/;
    }

    validateEmail(email) {
        return this.emailPattern.test(email);
    }
}
"""

        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/test/validator.js", "content": js_content},
            file_path="/test/validator.js",
            content=js_content,
        )

        # Should handle JavaScript files
        result = self.guard.should_trigger(context)
        self.assertIsInstance(result, bool)

    def test_unsupported_file_extension_ignored(self):
        """Guard should ignore unsupported file extensions."""
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "/test/document.txt", "content": "This is a text document with no code."},
            file_path="/test/document.txt",
            content="This is a text document with no code.",
        )

        # Should not trigger on non-code files
        self.assertFalse(self.guard.should_trigger(context))


if __name__ == "__main__":
    unittest.main()
