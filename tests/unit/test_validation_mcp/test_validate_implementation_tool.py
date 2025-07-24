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
Unit tests for validate_implementation MCP tool functionality.
Tests implementation validation against approved designs using Gemini AI.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.mcp.server import TestValidationMCPServer
from indexing.test_validation.utils.config import ValidationConfig


class TestValidateImplementationTool:
    """Test validate_implementation MCP tool functionality."""

    def setup_method(self):
        """Setup test environment for each test."""
        # Create temporary database file
        tmp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = tmp_file.name
        tmp_file.close()

        # Create configuration
        self.config = ValidationConfig()
        self.config.set("database_path", self.db_path)
        self.config.set("gemini_model", "gemini-2.5-flash")
        self.config.set("validation_stages", ["design", "implementation", "breaking", "approval"])

        # Set required environment variable for testing
        os.environ['GEMINI_API_KEY'] = 'test_api_key_for_integration_testing'

        # Create server
        self.server = TestValidationMCPServer(config=self.config)

    def teardown_method(self):
        """Cleanup test environment after each test."""
        if hasattr(self, 'db_path') and os.path.exists(self.db_path):
            os.unlink(self.db_path)

        # Clean up environment variable
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    def _create_approved_design(self):
        """Helper to create an approved design for testing."""
        # First run design_test to get approved design and token
        design_params = {
            "test_content": """
def test_user_registration():
    '''Test user registration with valid data.'''
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'secure_password'
    }
    user = create_user(user_data)
    assert user.id is not None
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.is_active is True
""",
            "test_file_path": "test_user_registration.py",
            "requirements": "User should be able to register with valid username, email, and password. System should create active user account and assign unique ID."
        }

        design_result = self.server.call_tool("design_test", design_params)
        return design_result["test_fingerprint"], design_result["design_token"]

    def test_validate_implementation_tool_exists(self):
        """Test that validate_implementation tool is registered."""
        tools = self.server.list_tools()
        impl_tool = next((t for t in tools if t["name"] == "validate_implementation"), None)

        assert impl_tool is not None
        assert impl_tool["name"] == "validate_implementation"
        assert "description" in impl_tool
        assert "implementation" in impl_tool["description"].lower()

    def test_validate_implementation_tool_schema(self):
        """Test validate_implementation tool has correct input schema."""
        tools = self.server.list_tools()
        impl_tool = next((t for t in tools if t["name"] == "validate_implementation"), None)

        schema = impl_tool["inputSchema"]
        assert schema["type"] == "object"

        required_fields = ["test_fingerprint", "implementation_code", "design_token"]
        for field in required_fields:
            assert field in schema["properties"]
            assert field in schema["required"]

    def test_validate_implementation_basic_functionality(self):
        """Test validate_implementation tool basic call functionality."""
        fingerprint, design_token = self._create_approved_design()

        impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": """
def test_user_registration():
    '''Test user registration with valid data.'''
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'secure_password'
    }
    user = create_user(user_data)
    assert user.id is not None
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.is_active is True

def create_user(user_data):
    # Implementation of user creation
    return User(id=1, username=user_data['username'],
                email=user_data['email'], is_active=True)

class User:
    def __init__(self, id, username, email, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active
""",
            "design_token": design_token
        }

        # This should work (not raise NotImplementedError anymore)
        result = self.server.call_tool("validate_implementation", impl_params)

        # Verify response structure
        assert isinstance(result, dict)
        assert "validation_result" in result
        assert "implementation_token" in result
        assert "gemini_analysis" in result
        assert "design_comparison" in result
        assert "recommendations" in result

    def test_validate_implementation_token_validation(self):
        """Test that validate_implementation validates design tokens properly."""
        fingerprint, design_token = self._create_approved_design()

        # Test with valid token
        valid_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": "def test_valid(): pass",
            "design_token": design_token
        }

        result = self.server.call_tool("validate_implementation", valid_params)
        assert "validation_result" in result

        # Test with invalid token
        invalid_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": "def test_invalid(): pass",
            "design_token": "invalid_token_123"
        }

        with pytest.raises(ValueError, match="Invalid or expired design token"):
            self.server.call_tool("validate_implementation", invalid_params)

    def test_validate_implementation_database_integration(self):
        """Test that validate_implementation stores results in database."""
        fingerprint, design_token = self._create_approved_design()

        impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": "def test_db_integration(): pass",
            "design_token": design_token
        }

        result = self.server.call_tool("validate_implementation", impl_params)

        # Verify data was updated in database
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT current_stage, status, updated_at
                FROM test_validations WHERE test_fingerprint = ?
            """, (fingerprint,))
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "implementation"  # Stage updated
            assert row[2] is not None  # updated_at set

    def test_validate_implementation_token_generation(self):
        """Test that validate_implementation generates valid tokens for next stage."""
        fingerprint, design_token = self._create_approved_design()

        impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": "def test_token_gen(): pass",
            "design_token": design_token
        }

        result = self.server.call_tool("validate_implementation", impl_params)
        impl_token = result["implementation_token"]

        # Verify token is valid for breaking behavior stage
        assert self.server.token_manager.validate_token(impl_token, fingerprint, "implementation")

        # Verify token contains correct information
        decoded = self.server.token_manager.decode_token(impl_token)
        assert decoded["fingerprint"] == fingerprint
        assert decoded["stage"] == "implementation"

    def test_validate_implementation_design_comparison(self):
        """Test that validate_implementation compares against original design."""
        fingerprint, design_token = self._create_approved_design()

        # Test with implementation that matches design well
        good_impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": """
def test_user_registration():
    '''Test user registration with valid data - enhanced implementation.'''
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'secure_password'
    }
    user = create_user(user_data)
    assert user.id is not None
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.is_active is True
    # Additional validation
    assert len(user.username) > 0
    assert '@' in user.email

def create_user(user_data):
    return User(id=1, username=user_data['username'],
                email=user_data['email'], is_active=True)

class User:
    def __init__(self, id, username, email, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active
""",
            "design_token": design_token
        }

        good_result = self.server.call_tool("validate_implementation", good_impl_params)

        # Should likely be approved due to good implementation
        assert good_result["validation_result"] in ["approved", "needs_revision"]
        assert "design_comparison" in good_result
        assert len(good_result["gemini_analysis"]) > 50

    def test_validate_implementation_poor_alignment(self):
        """Test validate_implementation with implementation that doesn't match design."""
        fingerprint, design_token = self._create_approved_design()

        # Test with implementation that diverges from design
        bad_impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": """
def test_completely_different():
    '''This test does something completely different.'''
    x = 1 + 1
    assert x == 2
""",
            "design_token": design_token
        }

        bad_result = self.server.call_tool("validate_implementation", bad_impl_params)

        # Should likely be rejected due to poor alignment
        assert bad_result["validation_result"] in ["rejected", "needs_revision"]
        assert "recommendations" in bad_result
        assert len(bad_result["recommendations"]) > 0

    def test_validate_implementation_edge_cases(self):
        """Test validate_implementation handles edge cases properly."""
        fingerprint, design_token = self._create_approved_design()

        # Test with empty implementation code
        with pytest.raises(ValueError, match="implementation_code cannot be empty"):
            self.server.call_tool("validate_implementation", {
                "test_fingerprint": fingerprint,
                "implementation_code": "",
                "design_token": design_token
            })

        # Test with invalid Python syntax
        with pytest.raises(ValueError, match="Invalid Python syntax"):
            self.server.call_tool("validate_implementation", {
                "test_fingerprint": fingerprint,
                "implementation_code": "def invalid_syntax( pass",
                "design_token": design_token
            })

        # Test with missing fingerprint
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.server.call_tool("validate_implementation", {
                "implementation_code": "def test(): pass",
                "design_token": design_token
            })

    def test_validate_implementation_fingerprint_mismatch(self):
        """Test validate_implementation with mismatched fingerprints."""
        fingerprint, design_token = self._create_approved_design()

        # Test with wrong fingerprint for the token
        wrong_fingerprint = "wrong_fingerprint_12345"

        with pytest.raises(ValueError, match="Token fingerprint mismatch"):
            self.server.call_tool("validate_implementation", {
                "test_fingerprint": wrong_fingerprint,
                "implementation_code": "def test_mismatch(): pass",
                "design_token": design_token
            })

    def test_validate_implementation_concurrent_access(self):
        """Test validate_implementation handles concurrent calls safely."""
        import threading

        # Create multiple approved designs
        designs = []
        for i in range(3):
            fingerprint, token = self._create_approved_design()
            designs.append((fingerprint, token))

        results = []
        errors = []

        def worker_impl(worker_id):
            try:
                fingerprint, token = designs[worker_id]
                impl_params = {
                    "test_fingerprint": fingerprint,
                    "implementation_code": f"def test_concurrent_{worker_id}(): assert True",
                    "design_token": token
                }
                result = self.server.call_tool("validate_implementation", impl_params)
                results.append(result)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Start concurrent validate_implementation calls
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_impl, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 3

    def test_validate_implementation_cost_tracking(self):
        """Test that validate_implementation tracks API usage costs."""
        fingerprint, design_token = self._create_approved_design()

        # Check initial API usage count
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage WHERE operation = 'validate_implementation'")
            initial_count = cursor.fetchone()[0]

        impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": "def test_cost_tracking(): pass",
            "design_token": design_token
        }

        result = self.server.call_tool("validate_implementation", impl_params)

        # Should have recorded API usage
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage WHERE operation = 'validate_implementation'")
            final_count = cursor.fetchone()[0]

            assert final_count > initial_count

    def test_validate_implementation_metadata_analysis(self):
        """Test that validate_implementation analyzes implementation metadata."""
        fingerprint, design_token = self._create_approved_design()

        impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": """
import pytest
from unittest import TestCase

class TestUserRegistration(TestCase):
    '''Comprehensive user registration test suite.'''

    @pytest.mark.integration
    def test_user_registration_with_validation(self):
        '''Test user registration with comprehensive validation.'''
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'secure_password'
        }
        user = create_user(user_data)

        # Core assertions
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_active is True

        # Enhanced validation
        assert isinstance(user.id, int)
        assert len(user.username) >= 3
        assert '@' in user.email and '.' in user.email

    def test_user_registration_edge_cases(self):
        '''Test edge cases for user registration.'''
        # Test minimum username length
        min_user_data = {'username': 'ab', 'email': 'ab@c.d', 'password': 'pass'}
        with pytest.raises(ValidationError):
            create_user(min_user_data)

def create_user(user_data):
    if len(user_data['username']) < 3:
        raise ValidationError("Username too short")
    return User(id=generate_id(), **user_data, is_active=True)

class User:
    def __init__(self, id, username, email, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active

class ValidationError(Exception):
    pass

def generate_id():
    return 1
""",
            "design_token": design_token
        }

        result = self.server.call_tool("validate_implementation", impl_params)

        # Should analyze enhanced implementation features
        analysis = result["gemini_analysis"].lower()
        assert any(keyword in analysis for keyword in [
            "class", "method", "validation", "edge case", "import"
        ]), "Analysis should mention implementation enhancements"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
