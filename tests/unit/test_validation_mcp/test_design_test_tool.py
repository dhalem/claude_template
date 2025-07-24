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
Unit tests for design_test MCP tool functionality.
Tests Gemini AI integration for test design validation.
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


class TestDesignTestTool:
    """Test design_test MCP tool functionality."""

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

    def test_design_test_tool_exists(self):
        """Test that design_test tool is registered."""
        tools = self.server.list_tools()
        design_tool = next((t for t in tools if t["name"] == "design_test"), None)

        assert design_tool is not None
        assert design_tool["name"] == "design_test"
        assert "description" in design_tool
        assert "Validate test design" in design_tool["description"]

    def test_design_test_tool_schema(self):
        """Test design_test tool has correct input schema."""
        tools = self.server.list_tools()
        design_tool = next((t for t in tools if t["name"] == "design_test"), None)

        schema = design_tool["inputSchema"]
        assert schema["type"] == "object"

        required_fields = ["test_content", "test_file_path", "requirements"]
        for field in required_fields:
            assert field in schema["properties"]
            assert field in schema["required"]

    def test_design_test_basic_functionality(self):
        """Test design_test tool basic call functionality."""
        test_params = {
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

        # This should work (not raise NotImplementedError anymore)
        result = self.server.call_tool("design_test", test_params)

        # Verify response structure
        assert isinstance(result, dict)
        assert "validation_result" in result
        assert "test_fingerprint" in result
        assert "design_token" in result
        assert "gemini_analysis" in result
        assert "recommendations" in result

    def test_design_test_validation_result_structure(self):
        """Test that design_test returns proper validation result structure."""
        test_params = {
            "test_content": "def test_simple(): assert True",
            "test_file_path": "test_simple.py",
            "requirements": "Simple test to verify basic functionality"
        }

        result = self.server.call_tool("design_test", test_params)

        # Check validation result details
        assert result["validation_result"] in ["approved", "rejected", "needs_revision"]
        assert isinstance(result["test_fingerprint"], str)
        assert len(result["test_fingerprint"]) > 0
        assert isinstance(result["design_token"], str)
        assert len(result["design_token"]) > 0
        assert isinstance(result["gemini_analysis"], str)
        assert len(result["gemini_analysis"]) > 0
        assert isinstance(result["recommendations"], list)

    def test_design_test_database_integration(self):
        """Test that design_test stores validation results in database."""
        test_params = {
            "test_content": "def test_database_integration(): pass",
            "test_file_path": "test_db_integration.py",
            "requirements": "Test database integration functionality"
        }

        result = self.server.call_tool("design_test", test_params)
        fingerprint = result["test_fingerprint"]

        # Verify data was stored in database
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT test_fingerprint, current_stage, gemini_analysis, test_file_path
                FROM test_validations WHERE test_fingerprint = ?
            """, (fingerprint,))
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == fingerprint
            assert row[1] == "design"
            assert row[2] is not None  # gemini_analysis stored
            assert row[3] == test_params["test_file_path"]

    def test_design_test_token_generation(self):
        """Test that design_test generates valid tokens for next stage."""
        test_params = {
            "test_content": "def test_token_generation(): pass",
            "test_file_path": "test_tokens.py",
            "requirements": "Test token generation functionality"
        }

        result = self.server.call_tool("design_test", test_params)
        token = result["design_token"]
        fingerprint = result["test_fingerprint"]

        # Verify token is valid
        assert self.server.token_manager.validate_token(token, fingerprint, "design")

        # Verify token contains correct information
        decoded = self.server.token_manager.decode_token(token)
        assert decoded["fingerprint"] == fingerprint
        assert decoded["stage"] == "design"

    def test_design_test_gemini_analysis_quality(self):
        """Test that design_test produces meaningful Gemini analysis."""
        test_params = {
            "test_content": """
def test_user_authentication():
    '''Test user authentication with valid credentials.'''
    user = User(username="testuser", password="password123")
    login_result = authenticate_user(user.username, user.password)
    assert login_result.success is True
    assert login_result.user_id == user.id
    assert login_result.session_token is not None
""",
            "test_file_path": "test_authentication.py",
            "requirements": "Users should be able to authenticate with username and password. Successful authentication should return session token and user ID."
        }

        result = self.server.call_tool("design_test", test_params)
        analysis = result["gemini_analysis"]

        # Analysis should be comprehensive
        assert len(analysis) > 100  # Non-trivial analysis

        # Should mention key test elements
        analysis_lower = analysis.lower()
        assert any(keyword in analysis_lower for keyword in [
            "authentication", "user", "test", "assert", "password"
        ])

    def test_design_test_requirements_alignment(self):
        """Test that design_test validates alignment with requirements."""
        # Test with well-aligned test
        good_params = {
            "test_content": """
def test_user_profile_creation():
    '''Test user profile creation with required fields.'''
    profile_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'bio': 'Software developer'
    }
    profile = create_user_profile(profile_data)
    assert profile.first_name == 'John'
    assert profile.last_name == 'Doe'
    assert profile.bio == 'Software developer'
    assert profile.created_at is not None
""",
            "test_file_path": "test_profile_creation.py",
            "requirements": "Users should be able to create profiles with first name, last name, and bio. Profile should have creation timestamp."
        }

        good_result = self.server.call_tool("design_test", good_params)

        # Should likely be approved due to good alignment
        assert good_result["validation_result"] in ["approved", "needs_revision"]

        # Test with poorly aligned test
        bad_params = {
            "test_content": "def test_random(): assert 1 + 1 == 2",
            "test_file_path": "test_random.py",
            "requirements": "Users should be able to upload and manage profile photos with resize functionality."
        }

        bad_result = self.server.call_tool("design_test", bad_params)

        # Should likely be rejected due to poor alignment
        assert bad_result["validation_result"] in ["rejected", "needs_revision"]

    def test_design_test_edge_cases(self):
        """Test design_test handles edge cases properly."""
        # Test with empty test content
        with pytest.raises(ValueError, match="test_content cannot be empty"):
            self.server.call_tool("design_test", {
                "test_content": "",
                "test_file_path": "test_empty.py",
                "requirements": "Some requirements"
            })

        # Test with invalid Python syntax
        with pytest.raises(ValueError, match="Invalid Python syntax"):
            self.server.call_tool("design_test", {
                "test_content": "def test_invalid( pass",
                "test_file_path": "test_invalid.py",
                "requirements": "Some requirements"
            })

        # Test with missing requirements
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.server.call_tool("design_test", {
                "test_content": "def test_no_req(): pass",
                "test_file_path": "test_no_req.py"
                # Missing requirements
            })

    def test_design_test_duplicate_handling(self):
        """Test that design_test handles duplicate test submissions."""
        test_params = {
            "test_content": "def test_duplicate_handling(): pass",
            "test_file_path": "test_duplicates.py",
            "requirements": "Test duplicate handling"
        }

        # First submission
        result1 = self.server.call_tool("design_test", test_params)
        fingerprint1 = result1["test_fingerprint"]

        # Second submission with same content
        result2 = self.server.call_tool("design_test", test_params)
        fingerprint2 = result2["test_fingerprint"]

        # Should generate same fingerprint but new token
        assert fingerprint1 == fingerprint2
        assert result1["design_token"] != result2["design_token"]

        # Should update database record, not create duplicate
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test_validations WHERE test_fingerprint = ?", (fingerprint1,))
            count = cursor.fetchone()[0]
            assert count == 1  # Only one record despite two submissions

    def test_design_test_concurrent_access(self):
        """Test design_test handles concurrent tool calls safely."""
        import threading

        results = []
        errors = []

        def worker_test(worker_id):
            try:
                test_params = {
                    "test_content": f"def test_concurrent_{worker_id}(): pass",
                    "test_file_path": f"test_concurrent_{worker_id}.py",
                    "requirements": f"Test concurrent access worker {worker_id}"
                }
                result = self.server.call_tool("design_test", test_params)
                results.append(result)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Start multiple concurrent design_test calls
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_test, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 5

        # All should have unique fingerprints (different test content)
        fingerprints = [r["test_fingerprint"] for r in results]
        assert len(set(fingerprints)) == 5

    def test_design_test_cost_tracking(self):
        """Test that design_test tracks API usage costs."""
        test_params = {
            "test_content": "def test_cost_tracking(): pass",
            "test_file_path": "test_costs.py",
            "requirements": "Test cost tracking functionality"
        }

        # Check initial API usage count
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage")
            initial_count = cursor.fetchone()[0]

        result = self.server.call_tool("design_test", test_params)

        # Should have recorded API usage
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage")
            final_count = cursor.fetchone()[0]

            assert final_count > initial_count

            # Check usage details
            cursor.execute("""
                SELECT service, operation, input_tokens, output_tokens, cost_cents
                FROM api_usage ORDER BY timestamp DESC LIMIT 1
            """)
            usage = cursor.fetchone()

            assert usage[0] == "gemini"  # service
            assert usage[1] == "design_test"  # operation
            assert usage[2] > 0  # input_tokens
            assert usage[3] > 0  # output_tokens
            assert usage[4] >= 0  # cost_cents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
