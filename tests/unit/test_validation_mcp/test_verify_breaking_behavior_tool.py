# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Unit tests for verify_breaking_behavior MCP tool functionality.
Tests validation that tests properly break when expected conditions are not met.
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


class TestVerifyBreakingBehaviorTool:
    """Test verify_breaking_behavior MCP tool functionality."""

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

    def _create_approved_implementation(self):
        """Helper to create an approved implementation for testing."""
        # First run design_test to get approved design and token
        design_params = {
            "test_content": """
def test_user_authentication():
    '''Test user authentication with valid credentials.'''
    user = User(username="testuser", password="password123")
    login_result = authenticate_user(user.username, user.password)
    assert login_result.success is True
    assert login_result.user_id == user.id
    assert login_result.session_token is not None
""",
            "test_file_path": "test_user_authentication.py",
            "requirements": "Users should be able to authenticate with username and password. Successful authentication should return session token and user ID."
        }

        design_result = self.server.call_tool("design_test", design_params)
        fingerprint = design_result["test_fingerprint"]
        design_token = design_result["design_token"]

        # Then run validate_implementation to get implementation token
        impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": """
def test_user_authentication():
    '''Test user authentication with valid credentials.'''
    user = User(username="testuser", password="password123")
    login_result = authenticate_user(user.username, user.password)
    assert login_result.success is True
    assert login_result.user_id == user.id
    assert login_result.session_token is not None

def authenticate_user(username, password):
    # Implementation of authentication
    return LoginResult(success=True, user_id=1, session_token="token123")

class User:
    def __init__(self, username, password):
        self.id = 1
        self.username = username
        self.password = password

class LoginResult:
    def __init__(self, success, user_id, session_token):
        self.success = success
        self.user_id = user_id
        self.session_token = session_token
""",
            "design_token": design_token
        }

        impl_result = self.server.call_tool("validate_implementation", impl_params)
        return fingerprint, impl_result["implementation_token"]

    def test_verify_breaking_behavior_tool_exists(self):
        """Test that verify_breaking_behavior tool is registered."""
        tools = self.server.list_tools()
        breaking_tool = next((t for t in tools if t["name"] == "verify_breaking_behavior"), None)

        assert breaking_tool is not None
        assert breaking_tool["name"] == "verify_breaking_behavior"
        assert "description" in breaking_tool
        assert any(word in breaking_tool["description"].lower() for word in ["breaking", "breaks"])

    def test_verify_breaking_behavior_tool_schema(self):
        """Test verify_breaking_behavior tool has correct input schema."""
        tools = self.server.list_tools()
        breaking_tool = next((t for t in tools if t["name"] == "verify_breaking_behavior"), None)

        schema = breaking_tool["inputSchema"]
        assert schema["type"] == "object"

        required_fields = ["test_fingerprint", "breaking_scenarios", "implementation_token"]
        for field in required_fields:
            assert field in schema["properties"]
            assert field in schema["required"]

        # Check breaking_scenarios is array type
        assert schema["properties"]["breaking_scenarios"]["type"] == "array"

    def test_verify_breaking_behavior_basic_functionality(self):
        """Test verify_breaking_behavior tool basic call functionality."""
        fingerprint, implementation_token = self._create_approved_implementation()

        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": [
                "Invalid username should cause authentication to fail",
                "Empty password should cause authentication to fail",
                "Non-existent user should cause authentication to fail"
            ],
            "implementation_token": implementation_token
        }

        # This should work (not raise NotImplementedError anymore)
        result = self.server.call_tool("verify_breaking_behavior", breaking_params)

        # Verify response structure
        assert isinstance(result, dict)
        assert "validation_result" in result
        assert "breaking_token" in result
        assert "breaking_analysis" in result
        assert "scenario_results" in result
        assert "recommendations" in result

    def test_verify_breaking_behavior_token_validation(self):
        """Test that verify_breaking_behavior validates implementation tokens properly."""
        fingerprint, implementation_token = self._create_approved_implementation()

        # Test with valid token
        valid_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": ["Test should fail with invalid data"],
            "implementation_token": implementation_token
        }

        result = self.server.call_tool("verify_breaking_behavior", valid_params)
        assert "validation_result" in result

        # Test with invalid token
        invalid_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": ["Test should fail with invalid data"],
            "implementation_token": "invalid_token_123"
        }

        with pytest.raises(ValueError, match="Invalid or expired implementation token"):
            self.server.call_tool("verify_breaking_behavior", invalid_params)

    def test_verify_breaking_behavior_database_integration(self):
        """Test that verify_breaking_behavior stores results in database."""
        fingerprint, implementation_token = self._create_approved_implementation()

        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": ["Authentication should fail with wrong password"],
            "implementation_token": implementation_token
        }

        result = self.server.call_tool("verify_breaking_behavior", breaking_params)

        # Verify data was updated in database
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT current_stage, status, updated_at
                FROM test_validations WHERE test_fingerprint = ?
            """, (fingerprint,))
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "breaking"  # Stage updated
            assert row[2] is not None  # updated_at set

    def test_verify_breaking_behavior_token_generation(self):
        """Test that verify_breaking_behavior generates valid tokens for next stage."""
        fingerprint, implementation_token = self._create_approved_implementation()

        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": ["Test should fail when authentication method returns error"],
            "implementation_token": implementation_token
        }

        result = self.server.call_tool("verify_breaking_behavior", breaking_params)
        breaking_token = result["breaking_token"]

        # Verify token is valid for approval stage
        assert self.server.token_manager.validate_token(breaking_token, fingerprint, "breaking")

        # Verify token contains correct information
        decoded = self.server.token_manager.decode_token(breaking_token)
        assert decoded["fingerprint"] == fingerprint
        assert decoded["stage"] == "breaking"

    def test_verify_breaking_behavior_scenario_analysis(self):
        """Test that verify_breaking_behavior analyzes breaking scenarios properly."""
        fingerprint, implementation_token = self._create_approved_implementation()

        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": [
                "Authentication should fail when username is empty",
                "Authentication should fail when password is None",
                "Authentication should fail when user does not exist in database",
                "Authentication should return error for disabled user accounts"
            ],
            "implementation_token": implementation_token
        }

        result = self.server.call_tool("verify_breaking_behavior", breaking_params)

        # Should analyze each scenario
        assert "scenario_results" in result
        scenario_results = result["scenario_results"]
        assert isinstance(scenario_results, list)
        assert len(scenario_results) == 4  # One for each scenario

        # Each scenario should have analysis
        for scenario_result in scenario_results:
            assert "scenario" in scenario_result
            assert "analysis" in scenario_result
            assert "expected_failure" in scenario_result

    def test_verify_breaking_behavior_gemini_analysis_quality(self):
        """Test that verify_breaking_behavior produces meaningful analysis."""
        fingerprint, implementation_token = self._create_approved_implementation()

        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": [
                "Authentication should fail with invalid credentials",
                "Login attempt should be rejected for locked accounts"
            ],
            "implementation_token": implementation_token
        }

        result = self.server.call_tool("verify_breaking_behavior", breaking_params)
        analysis = result["breaking_analysis"]

        # Analysis should be comprehensive
        assert len(analysis) > 100  # Non-trivial analysis

        # Should mention key concepts
        analysis_lower = analysis.lower()
        assert any(keyword in analysis_lower for keyword in [
            "breaking", "failure", "scenario", "test", "authentication"
        ])

    def test_verify_breaking_behavior_edge_cases(self):
        """Test verify_breaking_behavior handles edge cases properly."""
        fingerprint, implementation_token = self._create_approved_implementation()

        # Test with empty breaking scenarios
        with pytest.raises(ValueError, match="breaking_scenarios cannot be empty"):
            self.server.call_tool("verify_breaking_behavior", {
                "test_fingerprint": fingerprint,
                "breaking_scenarios": [],
                "implementation_token": implementation_token
            })

        # Test with missing fingerprint
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.server.call_tool("verify_breaking_behavior", {
                "breaking_scenarios": ["Some scenario"],
                "implementation_token": implementation_token
            })

        # Test with missing implementation token
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.server.call_tool("verify_breaking_behavior", {
                "test_fingerprint": fingerprint,
                "breaking_scenarios": ["Some scenario"]
            })

    def test_verify_breaking_behavior_fingerprint_mismatch(self):
        """Test verify_breaking_behavior with mismatched fingerprints."""
        fingerprint, implementation_token = self._create_approved_implementation()

        # Test with wrong fingerprint for the token
        wrong_fingerprint = "wrong_fingerprint_12345"

        with pytest.raises(ValueError, match="Token fingerprint mismatch"):
            self.server.call_tool("verify_breaking_behavior", {
                "test_fingerprint": wrong_fingerprint,
                "breaking_scenarios": ["Test should fail"],
                "implementation_token": implementation_token
            })

    def test_verify_breaking_behavior_scenario_validation(self):
        """Test verify_breaking_behavior validates scenario quality."""
        fingerprint, implementation_token = self._create_approved_implementation()

        # Test with good scenarios
        good_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": [
                "Authentication should fail when username contains SQL injection",
                "Login should be rejected when account is temporarily locked",
                "Password validation should fail for weak passwords"
            ],
            "implementation_token": implementation_token
        }

        good_result = self.server.call_tool("verify_breaking_behavior", good_params)
        assert good_result["validation_result"] in ["approved", "needs_revision"]

        # Test with vague scenarios
        vague_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": [
                "Test should fail",
                "Something bad happens",
                "Error occurs"
            ],
            "implementation_token": implementation_token
        }

        vague_result = self.server.call_tool("verify_breaking_behavior", vague_params)
        # Should likely suggest revision due to vague scenarios
        assert len(vague_result["recommendations"]) > 0

    def test_verify_breaking_behavior_concurrent_access(self):
        """Test verify_breaking_behavior handles concurrent calls safely."""
        import threading

        results = []
        errors = []

        def worker_breaking(worker_id):
            try:
                # Create unique implementation for each worker to avoid conflicts
                design_params = {
                    "test_content": f"""
def test_concurrent_authentication_{worker_id}():
    '''Test concurrent authentication scenario {worker_id}.'''
    user = User(username="testuser{worker_id}", password="password123")
    login_result = authenticate_user(user.username, user.password)
    assert login_result.success is True
    assert login_result.user_id == user.id
    assert login_result.session_token is not None
""",
                    "test_file_path": f"test_concurrent_authentication_{worker_id}.py",
                    "requirements": f"Worker {worker_id}: Users should be able to authenticate with username and password. Successful authentication should return session token and user ID."
                }

                design_result = self.server.call_tool("design_test", design_params)
                fingerprint = design_result["test_fingerprint"]
                design_token = design_result["design_token"]

                # Then run validate_implementation
                impl_params = {
                    "test_fingerprint": fingerprint,
                    "implementation_code": f"""
def test_concurrent_authentication_{worker_id}():
    '''Test concurrent authentication scenario {worker_id}.'''
    user = User(username="testuser{worker_id}", password="password123")
    login_result = authenticate_user(user.username, user.password)
    assert login_result.success is True
    assert login_result.user_id == user.id
    assert login_result.session_token is not None

def authenticate_user(username, password):
    return LoginResult(success=True, user_id={worker_id + 1}, session_token="token{worker_id}")

class User:
    def __init__(self, username, password):
        self.id = {worker_id + 1}
        self.username = username
        self.password = password

class LoginResult:
    def __init__(self, success, user_id, session_token):
        self.success = success
        self.user_id = user_id
        self.session_token = session_token
""",
                    "design_token": design_token
                }

                impl_result = self.server.call_tool("validate_implementation", impl_params)
                implementation_token = impl_result["implementation_token"]

                # Now test breaking behavior
                breaking_params = {
                    "test_fingerprint": fingerprint,
                    "breaking_scenarios": [f"Authentication should fail in concurrent scenario {worker_id}"],
                    "implementation_token": implementation_token
                }
                result = self.server.call_tool("verify_breaking_behavior", breaking_params)
                results.append(result)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Start concurrent verify_breaking_behavior calls
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_breaking, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 3

    def test_verify_breaking_behavior_cost_tracking(self):
        """Test that verify_breaking_behavior tracks API usage costs."""
        fingerprint, implementation_token = self._create_approved_implementation()

        # Check initial API usage count
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage WHERE operation = 'verify_breaking_behavior'")
            initial_count = cursor.fetchone()[0]

        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": ["Authentication should fail with invalid token"],
            "implementation_token": implementation_token
        }

        result = self.server.call_tool("verify_breaking_behavior", breaking_params)

        # Should have recorded API usage
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage WHERE operation = 'verify_breaking_behavior'")
            final_count = cursor.fetchone()[0]

            assert final_count > initial_count

    def test_verify_breaking_behavior_comprehensive_scenarios(self):
        """Test verify_breaking_behavior with comprehensive breaking scenarios."""
        fingerprint, implementation_token = self._create_approved_implementation()

        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": [
                "Authentication should fail when username is null or empty",
                "Authentication should fail when password is null or empty",
                "Authentication should fail when user account is disabled",
                "Authentication should fail when user account is locked due to failed attempts",
                "Authentication should fail when provided credentials don't match database records",
                "Authentication should fail when database connection is unavailable",
                "Authentication should handle concurrent login attempts gracefully",
                "Authentication should prevent SQL injection in username field"
            ],
            "implementation_token": implementation_token
        }

        result = self.server.call_tool("verify_breaking_behavior", breaking_params)

        # Should handle comprehensive scenario list
        assert result["validation_result"] in ["approved", "rejected", "needs_revision"]
        assert len(result["scenario_results"]) == 8
        assert len(result["breaking_analysis"]) > 200  # Comprehensive analysis

        # Each scenario should be individually analyzed
        for scenario_result in result["scenario_results"]:
            assert len(scenario_result["analysis"]) > 10
            assert scenario_result["expected_failure"] in [True, False]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
