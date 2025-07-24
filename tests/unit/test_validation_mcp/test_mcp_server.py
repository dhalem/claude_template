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
Unit tests for Test Validation MCP Server.
Tests MCP server initialization, tool registration, and protocol compliance.
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.database.manager import DatabaseManager
from indexing.test_validation.mcp.server import TestValidationMCPServer
from indexing.test_validation.utils.config import ValidationConfig


class TestMCPServerInitialization:
    """Test MCP server initialization and basic functionality."""

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

    def teardown_method(self):
        """Cleanup test environment after each test."""
        if hasattr(self, 'db_path') and os.path.exists(self.db_path):
            os.unlink(self.db_path)

        # Clean up environment variable
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    def test_server_initialization_with_config(self):
        """Test that MCP server initializes properly with configuration."""
        # This test will fail until we implement the server
        server = TestValidationMCPServer(config=self.config)

        assert server is not None
        assert server.config == self.config
        assert server.db_manager is not None
        assert isinstance(server.db_manager, DatabaseManager)

    def test_server_initialization_with_database_path(self):
        """Test server initialization with direct database path."""
        server = TestValidationMCPServer(database_path=self.db_path)

        assert server is not None
        assert server.db_path == self.db_path
        assert server.db_manager is not None

    def test_server_initialization_requires_config_or_path(self):
        """Test that server initialization requires either config or database path."""
        with pytest.raises(ValueError, match="Either config or database_path must be provided"):
            TestValidationMCPServer()

    def test_server_has_required_mcp_tools(self):
        """Test that server registers all required MCP tools."""
        server = TestValidationMCPServer(config=self.config)

        # Server should have these tools registered
        expected_tools = [
            "design_test",
            "validate_implementation",
            "verify_breaking_behavior",
            "approve_test"
        ]

        tools = server.list_tools()
        tool_names = [tool["name"] for tool in tools]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_server_tool_descriptions(self):
        """Test that all tools have proper descriptions and schemas."""
        server = TestValidationMCPServer(config=self.config)
        tools = server.list_tools()

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert len(tool["description"]) > 10  # Non-trivial description
            assert "properties" in tool["inputSchema"]

    def test_server_mcp_protocol_compliance(self):
        """Test that server implements MCP protocol correctly."""
        server = TestValidationMCPServer(config=self.config)

        # Test initialize method exists and returns proper format
        assert hasattr(server, "initialize")
        assert hasattr(server, "list_tools")
        assert hasattr(server, "call_tool")

        # Test protocol version
        assert hasattr(server, "PROTOCOL_VERSION")
        assert server.PROTOCOL_VERSION == "2024-11-05"

    def test_server_database_integration(self):
        """Test that server properly integrates with database layer."""
        server = TestValidationMCPServer(config=self.config)

        # Database should be created and accessible
        with server.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["test_validations", "validation_history", "api_usage", "approval_tokens"]
            for table in expected_tables:
                assert table in tables

    def test_server_gemini_client_initialization(self):
        """Test that server initializes Gemini client properly."""
        server = TestValidationMCPServer(config=self.config)

        assert hasattr(server, "gemini_client")
        assert server.gemini_client is not None

    def test_server_missing_gemini_api_key_handling(self):
        """Test proper handling when GEMINI_API_KEY is missing."""
        # Remove the API key temporarily
        del os.environ['GEMINI_API_KEY']

        with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
            TestValidationMCPServer(config=self.config)

    def test_server_logging_configuration(self):
        """Test that server configures logging properly."""
        server = TestValidationMCPServer(config=self.config)

        assert hasattr(server, "logger")
        assert server.logger.name == "test_validation_mcp_server"

    def test_server_shutdown_cleanup(self):
        """Test that server cleans up resources on shutdown."""
        server = TestValidationMCPServer(config=self.config)

        # Should have shutdown method
        assert hasattr(server, "shutdown")

        # Call shutdown and verify cleanup
        server.shutdown()

        # Verify resources are cleaned up
        assert server.db_manager._active_connections == 0


class TestMCPServerToolRegistration:
    """Test MCP tool registration and schema validation."""

    def setup_method(self):
        """Setup test environment."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = tmp_file.name
        tmp_file.close()

        self.config = ValidationConfig()
        self.config.set("database_path", self.db_path)

        # Set required environment variable
        os.environ['GEMINI_API_KEY'] = 'test_api_key_for_integration_testing'

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    def test_design_test_tool_registration(self):
        """Test design_test tool is properly registered."""
        server = TestValidationMCPServer(config=self.config)
        tools = server.list_tools()

        design_tool = next((t for t in tools if t["name"] == "design_test"), None)
        assert design_tool is not None

        # Verify schema
        schema = design_tool["inputSchema"]
        assert "test_content" in schema["properties"]
        assert "test_file_path" in schema["properties"]
        assert "requirements" in schema["properties"]

    def test_validate_implementation_tool_registration(self):
        """Test validate_implementation tool is properly registered."""
        server = TestValidationMCPServer(config=self.config)
        tools = server.list_tools()

        validate_tool = next((t for t in tools if t["name"] == "validate_implementation"), None)
        assert validate_tool is not None

        schema = validate_tool["inputSchema"]
        assert "test_fingerprint" in schema["properties"]
        assert "implementation_code" in schema["properties"]
        assert "design_token" in schema["properties"]

    def test_verify_breaking_behavior_tool_registration(self):
        """Test verify_breaking_behavior tool is properly registered."""
        server = TestValidationMCPServer(config=self.config)
        tools = server.list_tools()

        breaking_tool = next((t for t in tools if t["name"] == "verify_breaking_behavior"), None)
        assert breaking_tool is not None

        schema = breaking_tool["inputSchema"]
        assert "test_fingerprint" in schema["properties"]
        assert "breaking_scenarios" in schema["properties"]
        assert "implementation_token" in schema["properties"]

    def test_approve_test_tool_registration(self):
        """Test approve_test tool is properly registered."""
        server = TestValidationMCPServer(config=self.config)
        tools = server.list_tools()

        approve_tool = next((t for t in tools if t["name"] == "approve_test"), None)
        assert approve_tool is not None

        schema = approve_tool["inputSchema"]
        assert "test_fingerprint" in schema["properties"]
        assert "approval_notes" in schema["properties"]
        assert "breaking_token" in schema["properties"]


class TestMCPServerProtocolCompliance:
    """Test MCP protocol compliance and communication."""

    def setup_method(self):
        """Setup test environment."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = tmp_file.name
        tmp_file.close()

        self.config = ValidationConfig()
        self.config.set("database_path", self.db_path)

        # Set required environment variable
        os.environ['GEMINI_API_KEY'] = 'test_api_key_for_integration_testing'

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    def test_mcp_initialize_response(self):
        """Test MCP initialize method returns proper response."""
        server = TestValidationMCPServer(config=self.config)

        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }

        response = server.initialize(init_params)

        assert "protocolVersion" in response
        assert response["protocolVersion"] == "2024-11-05"
        assert "capabilities" in response
        assert "serverInfo" in response
        assert response["serverInfo"]["name"] == "test-validation-mcp"

    def test_mcp_list_tools_response_format(self):
        """Test list_tools returns proper MCP format."""
        server = TestValidationMCPServer(config=self.config)
        tools = server.list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert "type" in tool["inputSchema"]
            assert tool["inputSchema"]["type"] == "object"

    def test_mcp_call_tool_error_handling(self):
        """Test call_tool method handles errors properly."""
        server = TestValidationMCPServer(config=self.config)

        # Test calling non-existent tool
        with pytest.raises(ValueError, match="Unknown tool"):
            server.call_tool("nonexistent_tool", {})

    def test_mcp_call_tool_validation(self):
        """Test call_tool validates input parameters."""
        server = TestValidationMCPServer(config=self.config)

        # Test calling tool with missing required parameters
        with pytest.raises(ValueError, match="Missing required parameter"):
            server.call_tool("design_test", {})  # Missing test_content

    def test_server_handles_concurrent_requests(self):
        """Test server can handle concurrent tool calls."""
        server = TestValidationMCPServer(config=self.config)
        results = []
        errors = []

        def make_tool_call(thread_id):
            try:
                # Test concurrent access to server capabilities
                tools = server.list_tools()
                results.append(f"thread_{thread_id}_success")
                time.sleep(0.1)  # Simulate processing time
            except Exception as e:
                errors.append(f"thread_{thread_id}: {str(e)}")

        # Start multiple concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_tool_call, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should handle concurrent requests without errors
        assert len(errors) == 0
        assert len(results) == 5

    def test_server_tool_call_with_real_parameters(self):
        """Test calling tools with real parameters to verify interface."""
        server = TestValidationMCPServer(config=self.config)

        # Test that tools are now implemented and work correctly
        test_params = {
            "test_content": "def test_example(): assert True",
            "test_file_path": "test_example.py",
            "requirements": "Test should verify basic functionality"
        }

        # Should succeed now that the tool is implemented
        result = server.call_tool("design_test", test_params)

        # Verify we get expected response structure
        assert isinstance(result, dict)
        assert "validation_result" in result
        assert "test_fingerprint" in result
        assert "design_token" in result


class TestMCPServerErrorHandling:
    """Test MCP server error handling and edge cases."""

    def setup_method(self):
        """Setup test environment."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = tmp_file.name
        tmp_file.close()

        self.config = ValidationConfig()
        self.config.set("database_path", self.db_path)

        os.environ['GEMINI_API_KEY'] = 'test_api_key_for_integration_testing'

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    def test_server_invalid_database_path_handling(self):
        """Test server handles invalid database paths gracefully."""
        invalid_config = ValidationConfig()
        invalid_config.set("database_path", "/invalid/path/that/does/not/exist.db")

        # Should raise appropriate error for invalid database path
        with pytest.raises((ValueError, OSError, PermissionError)):
            TestValidationMCPServer(config=invalid_config)

    def test_server_corrupted_database_handling(self):
        """Test server handles corrupted database files."""
        # Create a corrupted database file
        with open(self.db_path, 'w') as f:
            f.write("This is not a valid SQLite database")

        # Should handle corrupted database gracefully
        with pytest.raises((ValueError, Exception)):
            TestValidationMCPServer(database_path=self.db_path)

    def test_server_configuration_validation(self):
        """Test server validates configuration parameters."""
        invalid_config = ValidationConfig()
        invalid_config.set("database_path", "")  # Empty path
        invalid_config.set("gemini_model", "invalid-model")  # Invalid model

        with pytest.raises(ValueError):
            TestValidationMCPServer(config=invalid_config)

    def test_server_thread_safety_under_load(self):
        """Test server thread safety under concurrent load."""
        server = TestValidationMCPServer(config=self.config)

        results = []
        errors = []

        def stress_test_worker(worker_id):
            """Worker that performs multiple operations concurrently."""
            try:
                for i in range(10):
                    # Multiple operations per worker
                    tools = server.list_tools()
                    assert len(tools) > 0

                    # Access database through server
                    with server.db_manager.get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM test_validations")
                        cursor.fetchone()

                    time.sleep(0.01)  # Small delay to create contention

                results.append(f"worker_{worker_id}_completed")

            except Exception as e:
                errors.append(f"worker_{worker_id}: {str(e)}")

        # Start multiple concurrent workers
        threads = []
        for i in range(10):
            thread = threading.Thread(target=stress_test_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout

        # Verify no errors and all workers completed
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10, f"Not all workers completed: {results}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
