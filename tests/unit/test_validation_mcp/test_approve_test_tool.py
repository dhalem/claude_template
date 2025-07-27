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
Unit tests for approve_test MCP tool functionality.
Tests final approval of validated test, generates approval token for use.
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


class TestApproveTestTool:
    """Test approve_test MCP tool functionality."""

    def setup_method(self):
        """Setup test environment for each test."""
        # Create temporary database file
        tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp_file.name
        tmp_file.close()

        # Create configuration
        self.config = ValidationConfig()
        self.config.set("database_path", self.db_path)
        self.config.set("gemini_model", "gemini-2.5-flash")
        self.config.set("validation_stages", ["design", "implementation", "breaking", "approval"])

        # Set required environment variable for testing
        os.environ["GEMINI_API_KEY"] = "test_api_key_for_integration_testing"

        # Create server
        self.server = TestValidationMCPServer(config=self.config)

    def teardown_method(self):
        """Cleanup test environment after each test."""
        if hasattr(self, "db_path") and os.path.exists(self.db_path):
            os.unlink(self.db_path)

        # Clean up environment variable
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]

    def _create_approved_breaking_behavior(self):
        """Helper to create an approved breaking behavior validation for testing."""
        # First run design_test to get approved design and token
        design_params = {
            "test_content": """
def test_final_approval():
    '''Test final approval workflow.'''
    result = process_data({"key": "value", "status": "active"})
    assert result.success is True
    assert result.data["key"] == "value"
    assert result.data["status"] == "active"
    assert result.timestamp is not None
""",
            "test_file_path": "test_final_approval.py",
            "requirements": "System should process data with key-value pairs and status. Processing should return success with original data and timestamp.",
        }

        design_result = self.server.call_tool("design_test", design_params)
        fingerprint = design_result["test_fingerprint"]
        design_token = design_result["design_token"]

        # Then run validate_implementation to get implementation token
        impl_params = {
            "test_fingerprint": fingerprint,
            "implementation_code": """
def test_final_approval():
    '''Test final approval workflow.'''
    result = process_data({"key": "value", "status": "active"})
    assert result.success is True
    assert result.data["key"] == "value"
    assert result.data["status"] == "active"
    assert result.timestamp is not None

def process_data(data):
    # Implementation of data processing
    import time
    return ProcessResult(success=True, data=data, timestamp=time.time())

class ProcessResult:
    def __init__(self, success, data, timestamp):
        self.success = success
        self.data = data
        self.timestamp = timestamp
""",
            "design_token": design_token,
        }

        impl_result = self.server.call_tool("validate_implementation", impl_params)
        implementation_token = impl_result["implementation_token"]

        # Finally run verify_breaking_behavior to get breaking token
        breaking_params = {
            "test_fingerprint": fingerprint,
            "breaking_scenarios": [
                "Processing should fail when data is None or empty",
                "Processing should fail when required keys are missing",
                "Processing should fail when data format is invalid",
            ],
            "implementation_token": implementation_token,
        }

        breaking_result = self.server.call_tool("verify_breaking_behavior", breaking_params)
        return fingerprint, breaking_result["breaking_token"]

    def test_approve_test_tool_exists(self):
        """Test that approve_test tool is registered."""
        tools = self.server.list_tools()
        approve_tool = next((t for t in tools if t["name"] == "approve_test"), None)

        assert approve_tool is not None
        assert approve_tool["name"] == "approve_test"
        assert "description" in approve_tool
        assert any(word in approve_tool["description"].lower() for word in ["approval", "approve"])

    def test_approve_test_tool_schema(self):
        """Test approve_test tool has correct input schema."""
        tools = self.server.list_tools()
        approve_tool = next((t for t in tools if t["name"] == "approve_test"), None)

        schema = approve_tool["inputSchema"]
        assert schema["type"] == "object"

        required_fields = ["test_fingerprint", "approval_notes", "breaking_token"]
        for field in required_fields:
            assert field in schema["properties"]
            assert field in schema["required"]

    def test_approve_test_basic_functionality(self):
        """Test approve_test tool basic call functionality."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Test has been thoroughly validated through all stages. Ready for production use.",
            "breaking_token": breaking_token,
        }

        # This should work (not raise NotImplementedError anymore)
        result = self.server.call_tool("approve_test", approve_params)

        # Verify response structure
        assert isinstance(result, dict)
        assert "approval_result" in result
        assert "approval_token" in result
        assert "approval_summary" in result
        assert "final_recommendations" in result
        assert "validation_complete" in result

    def test_approve_test_token_validation(self):
        """Test that approve_test validates breaking tokens properly."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        # Test with valid token
        valid_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Approved after thorough validation",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", valid_params)
        assert "approval_result" in result

        # Test with invalid token
        invalid_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Attempted approval with invalid token",
            "breaking_token": "invalid_token_123",
        }

        with pytest.raises(ValueError, match="Invalid or expired breaking token"):
            self.server.call_tool("approve_test", invalid_params)

    def test_approve_test_database_integration(self):
        """Test that approve_test stores results in database."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Final approval granted after comprehensive validation",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", approve_params)

        # Verify data was updated in database
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT validation_stage, status, updated_at, approval_token
                FROM test_validations WHERE test_fingerprint = ?
            """,
                (fingerprint,),
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "approval"  # Stage updated
            assert row[1] == "APPROVED"  # Status should be APPROVED for final approval
            assert row[2] is not None  # updated_at set
            assert row[3] is not None  # approval_token set

    def test_approve_test_approval_token_generation(self):
        """Test that approve_test generates valid approval tokens."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Test approved for production deployment",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", approve_params)
        approval_token = result["approval_token"]

        # Verify token is valid for approval stage
        assert self.server.token_manager.validate_token(approval_token, fingerprint, "approval")

        # Verify token contains correct information
        decoded = self.server.token_manager.decode_token(approval_token)
        assert decoded["fingerprint"] == fingerprint
        assert decoded["stage"] == "approval"

    def test_approve_test_approval_summary(self):
        """Test that approve_test provides comprehensive approval summary."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Comprehensive validation completed successfully. Test demonstrates proper functionality and failure handling.",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", approve_params)

        # Should provide comprehensive summary
        summary = result["approval_summary"]
        assert len(summary) > 100  # Non-trivial summary

        # Should mention key concepts
        summary_lower = summary.lower()
        assert any(keyword in summary_lower for keyword in ["approval", "validation", "complete", "test", "stage"])

    def test_approve_test_validation_complete_flag(self):
        """Test that approve_test sets validation_complete flag correctly."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "All validation stages completed successfully",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", approve_params)

        # Should indicate validation is complete
        assert result["validation_complete"] is True
        assert result["approval_result"] == "approved"

    def test_approve_test_edge_cases(self):
        """Test approve_test handles edge cases properly."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        # Test with empty approval notes
        with pytest.raises(ValueError, match="approval_notes cannot be empty"):
            self.server.call_tool(
                "approve_test",
                {"test_fingerprint": fingerprint, "approval_notes": "", "breaking_token": breaking_token},
            )

        # Test with missing fingerprint
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.server.call_tool(
                "approve_test", {"approval_notes": "Some approval notes", "breaking_token": breaking_token}
            )

        # Test with missing breaking token
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.server.call_tool(
                "approve_test", {"test_fingerprint": fingerprint, "approval_notes": "Some approval notes"}
            )

    def test_approve_test_fingerprint_mismatch(self):
        """Test approve_test with mismatched fingerprints."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        # Test with wrong fingerprint for the token
        wrong_fingerprint = "wrong_fingerprint_12345"

        with pytest.raises(ValueError, match="Token fingerprint mismatch"):
            self.server.call_tool(
                "approve_test",
                {
                    "test_fingerprint": wrong_fingerprint,
                    "approval_notes": "Attempted approval with mismatched fingerprint",
                    "breaking_token": breaking_token,
                },
            )

    def test_approve_test_approval_notes_quality(self):
        """Test approve_test validates approval notes quality."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        # Test with comprehensive approval notes
        good_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Test has been thoroughly validated through all four stages: design validation confirmed requirements alignment, implementation validation verified code quality and adherence to design, breaking behavior validation confirmed proper failure handling, and all scenarios demonstrate robust test coverage. Approved for production use.",
            "breaking_token": breaking_token,
        }

        good_result = self.server.call_tool("approve_test", good_params)
        assert good_result["approval_result"] == "approved"

        # Test with minimal approval notes
        minimal_params = {"test_fingerprint": fingerprint, "approval_notes": "OK", "breaking_token": breaking_token}

        minimal_result = self.server.call_tool("approve_test", minimal_params)
        # Should still approve but may have recommendations
        assert minimal_result["approval_result"] == "approved"
        assert len(minimal_result["final_recommendations"]) >= 0

    def test_approve_test_database_approval_tokens_table(self):
        """Test that approve_test stores approval tokens in approval_tokens table."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Final approval with token tracking",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", approve_params)
        approval_token = result["approval_token"]

        # Verify approval token was stored in approval_tokens table
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT test_fingerprint, approval_token, approved_by, stage, status
                FROM approval_tokens WHERE test_fingerprint = ?
            """,
                (fingerprint,),
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == fingerprint
            assert row[1] == approval_token
            assert row[2] == "gemini_ai"  # approved_by
            assert row[3] == "approval"  # stage
            assert row[4] == "VALID"  # status

    def test_approve_test_concurrent_access(self):
        """Test approve_test handles concurrent calls safely."""
        import threading

        # Prepare breaking behaviors sequentially to avoid race conditions
        breaking_data = []
        for i in range(3):
            fingerprint, breaking_token = self._create_approved_breaking_behavior()
            breaking_data.append((fingerprint, breaking_token))

        results = []
        errors = []

        def worker_approve(worker_id):
            try:
                fingerprint, breaking_token = breaking_data[worker_id]

                # Only run the approval concurrently
                approve_params = {
                    "test_fingerprint": fingerprint,
                    "approval_notes": f"Concurrent approval for worker {worker_id} - comprehensive validation completed successfully through all stages",
                    "breaking_token": breaking_token,
                }

                result = self.server.call_tool("approve_test", approve_params)
                results.append(result)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Start concurrent approve_test calls
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_approve, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 3

        # All should be approved
        for result in results:
            assert result["approval_result"] == "approved"
            assert result["validation_complete"] is True

    def test_approve_test_cost_tracking(self):
        """Test that approve_test tracks API usage costs."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        # Check initial API usage count
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage WHERE operation = 'approve_test'")
            initial_count = cursor.fetchone()[0]

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Final approval with cost tracking validation",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", approve_params)

        # Should have recorded API usage
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_usage WHERE operation = 'approve_test'")
            final_count = cursor.fetchone()[0]

            assert final_count > initial_count

    def test_approve_test_comprehensive_workflow(self):
        """Test approve_test completes the comprehensive validation workflow."""
        fingerprint, breaking_token = self._create_approved_breaking_behavior()

        approve_params = {
            "test_fingerprint": fingerprint,
            "approval_notes": "Comprehensive workflow validation: Design phase validated requirements alignment and test structure. Implementation phase confirmed code quality and design adherence. Breaking behavior phase verified proper failure handling and edge case coverage. All validation stages completed successfully. Test demonstrates robust functionality and comprehensive coverage. Approved for production deployment with confidence.",
            "breaking_token": breaking_token,
        }

        result = self.server.call_tool("approve_test", approve_params)

        # Verify complete workflow results
        assert result["approval_result"] == "approved"
        assert result["validation_complete"] is True
        assert len(result["approval_summary"]) > 200  # Comprehensive summary
        assert len(result["final_recommendations"]) >= 0  # May have final recommendations

        # Verify complete database state
        with self.server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()

            # Check main validation record
            cursor.execute(
                """
                SELECT validation_stage, status, approval_token
                FROM test_validations WHERE test_fingerprint = ?
            """,
                (fingerprint,),
            )
            validation_row = cursor.fetchone()

            assert validation_row[0] == "approval"  # Final stage
            assert validation_row[1] == "APPROVED"  # Final status
            assert validation_row[2] is not None  # Approval token generated

            # Check validation history shows all stages
            cursor.execute(
                """
                SELECT stage FROM validation_history
                WHERE test_fingerprint = ? ORDER BY validated_at
            """,
                (fingerprint,),
            )
            history_stages = [row[0] for row in cursor.fetchall()]

            expected_stages = ["design", "implementation", "breaking", "approval"]
            assert all(stage in history_stages for stage in expected_stages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
