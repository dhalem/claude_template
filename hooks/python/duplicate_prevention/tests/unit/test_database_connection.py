# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for database connection functionality

TDD RED Phase: These tests define the expected behavior of database connection
before implementation. They should fail initially and pass once implementation
is complete.

REAL INTEGRATION TESTING - NO MOCKS
These tests use real Qdrant database connections to ensure actual functionality.

Test Coverage:
- Database connection establishment
- Connection validation
- Error handling for connection failures
- Connection cleanup and resource management
"""

import os
import sys
import time

import pytest

# Add duplicate_prevention to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from duplicate_prevention.database import DatabaseConnector, get_health_status


class TestDatabaseConnection:
    """Test suite for DatabaseConnector connection functionality

    Uses real Qdrant database connections - no mocks allowed.
    Tests will fail in RED phase until database is installed and implementation complete.
    """

    def test_database_connector_initialization(self):
        """Test DatabaseConnector can be initialized with default parameters"""
        connector = DatabaseConnector()
        assert connector is not None
        assert hasattr(connector, "connect")
        assert hasattr(connector, "health_check")
        assert hasattr(connector, "close")

    def test_database_connector_initialization_with_custom_params(self):
        """Test DatabaseConnector accepts custom host, port, and timeout"""
        connector = DatabaseConnector(host="test-host", port=9999, timeout=60)
        assert connector is not None
        # These assertions will need implementation details during GREEN phase

    def test_connect_returns_boolean(self):
        """Test connect method returns boolean indicating success/failure"""
        connector = DatabaseConnector()

        # This should return a boolean (True for success, False for failure)
        result = connector.connect()
        assert isinstance(result, bool)

    @pytest.mark.integration
    def test_connect_to_real_database_success(self):
        """Test connect method returns True when real Qdrant database is available"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # This test will connect to real Qdrant database
        result = connector.connect()
        assert result is True  # Should succeed since Qdrant is running

    @pytest.mark.integration
    def test_connect_to_unreachable_database_failure(self):
        """Test connect method returns False when database is unreachable"""
        # Test with definitely unreachable host
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=2)

        # This test tries real connection to unreachable host
        result = connector.connect()
        assert result is False

    @pytest.mark.integration
    def test_connect_with_invalid_port_failure(self):
        """Test connect method returns False with invalid port"""
        # Use invalid port on localhost
        connector = DatabaseConnector(host="localhost", port=9999, timeout=2)

        # Real connection attempt to invalid port should fail
        result = connector.connect()
        assert result is False

    def test_connect_respects_timeout(self):
        """Test connect method respects timeout parameter"""
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        # Real connection with very short timeout should fail quickly
        start_time = time.time()
        result = connector.connect()
        end_time = time.time()
        assert result is False
        assert (end_time - start_time) <= 2  # Should timeout in ~1 second

    def test_multiple_connections_safe(self):
        """Test multiple connect calls work correctly"""
        connector = DatabaseConnector()

        # Should be able to call connect multiple times safely
        first_result = connector.connect()
        second_result = connector.connect()
        # Results should be consistent
        assert first_result == second_result
        assert isinstance(first_result, bool)
        assert isinstance(second_result, bool)

    def test_close_connection_no_errors(self):
        """Test close method works without errors"""
        connector = DatabaseConnector()

        # close() should work even if never connected
        # Should not raise exceptions (already implemented as pass)
        try:
            connector.close()
            # This should pass even in RED phase since close() doesn't raise
        except Exception as e:
            pytest.fail(f"close() should not raise exceptions: {e}")


class TestDatabaseHealthCheck:
    """Test suite for database health check functionality"""

    @pytest.mark.integration
    def test_health_check_returns_dict(self):
        """Test health_check method returns dictionary with status information"""
        connector = DatabaseConnector()

        # Should return dict with health status from real database
        result = connector.health_check()
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.integration
    def test_health_check_with_running_database(self):
        """Test health_check returns healthy status when database is running"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Real health check against running Qdrant database
        result = connector.health_check()
        assert result["status"] == "ok"
        assert "message" in result  # Our implementation returns message

    @pytest.mark.integration
    def test_health_check_with_unreachable_database(self):
        """Test health_check handles unreachable database gracefully"""
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=2)

        # Real health check against unreachable database
        # Should not crash, should return error status
        result = connector.health_check()
        assert isinstance(result, dict)
        assert result.get("status") == "error"


class TestHealthStatusFunction:
    """Test suite for standalone health status function"""

    @pytest.mark.integration
    def test_get_health_status_returns_dict(self):
        """Test get_health_status returns dictionary with health information"""
        # This test uses real connection to check database health
        result = get_health_status()
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.integration
    def test_get_health_status_with_custom_host_port(self):
        """Test get_health_status accepts custom host and port"""
        # Should work with custom parameters against real database
        result = get_health_status(host="localhost", port=6333)
        assert isinstance(result, dict)
        assert result["status"] == "ok"

    @pytest.mark.integration
    def test_get_health_status_handles_connection_errors(self):
        """Test get_health_status handles unreachable database gracefully"""
        # Real connection attempt to unreachable host
        # Should not crash when database is unreachable
        result = get_health_status(host="192.0.2.1", port=6333)
        assert isinstance(result, dict)
        assert result.get("status") == "error"


class TestDatabaseConnectorConfiguration:
    """Test suite for DatabaseConnector configuration handling"""

    def test_default_configuration_values(self):
        """Test DatabaseConnector uses sensible default values"""
        connector = DatabaseConnector()

        # Should use localhost:6333 by default (standard Qdrant port)
        # Should have reasonable timeout (30 seconds)
        assert connector is not None
        assert connector.host == "localhost"
        assert connector.port == 6333
        assert connector.timeout == 30
        assert connector.protocol == "http"

    def test_configuration_override(self):
        """Test DatabaseConnector accepts configuration overrides"""
        custom_host = "my-qdrant-server.com"
        custom_port = 7777
        custom_timeout = 45

        connector = DatabaseConnector(host=custom_host, port=custom_port, timeout=custom_timeout)

        assert connector is not None
        assert connector.host == custom_host
        assert connector.port == custom_port
        assert connector.timeout == custom_timeout

    def test_https_protocol_and_api_key_configuration(self):
        """Test DatabaseConnector accepts HTTPS protocol and API key"""
        connector = DatabaseConnector(protocol="https", api_key="test-api-key-123")

        assert connector is not None
        assert connector.protocol == "https"
        assert connector.api_key == "test-api-key-123"
        assert connector.base_url == "https://localhost:6333"

    def test_invalid_protocol_raises_error(self):
        """Test DatabaseConnector raises ValueError for invalid protocol"""
        with pytest.raises(ValueError, match="Invalid protocol 'ftp'. Must be 'http' or 'https'"):
            DatabaseConnector(protocol="ftp")


class TestStrictErrorHandling:
    """Test suite for strict error handling methods that raise exceptions"""

    @pytest.mark.integration
    def test_connect_strict_success(self):
        """Test connect_strict succeeds with running database"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Should not raise any exceptions with running database
        try:
            connector.connect_strict()
        except Exception as e:
            pytest.fail(f"connect_strict should not raise exceptions with running database: {e}")

    @pytest.mark.integration
    def test_connect_strict_timeout_raises_exception(self):
        """Test connect_strict raises DatabaseTimeoutError on timeout"""
        from duplicate_prevention.database import DatabaseTimeoutError

        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises(DatabaseTimeoutError):
            connector.connect_strict()

    @pytest.mark.integration
    def test_connect_strict_connection_error_raises_exception(self):
        """Test connect_strict raises DatabaseError on HTTP error (port 9999 returns 404)"""
        from duplicate_prevention.database import DatabaseError

        connector = DatabaseConnector(host="localhost", port=9999, timeout=2)

        with pytest.raises(DatabaseError):
            connector.connect_strict()

    @pytest.mark.integration
    def test_health_check_strict_success(self):
        """Test health_check_strict succeeds with running database"""
        connector = DatabaseConnector(host="localhost", port=6333)

        result = connector.health_check_strict()
        assert isinstance(result, dict)
        assert result["status"] == "ok"

    @pytest.mark.integration
    def test_health_check_strict_timeout_raises_exception(self):
        """Test health_check_strict raises DatabaseTimeoutError on timeout"""
        from duplicate_prevention.database import DatabaseTimeoutError

        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises(DatabaseTimeoutError):
            connector.health_check_strict()

    @pytest.mark.integration
    def test_health_check_strict_connection_error_raises_exception(self):
        """Test health_check_strict raises DatabaseError on HTTP error (port 9999 returns 404)"""
        from duplicate_prevention.database import DatabaseError

        connector = DatabaseConnector(host="localhost", port=9999, timeout=2)

        with pytest.raises(DatabaseError):
            connector.health_check_strict()


# TDD RED Phase Notes:
# - All tests should currently FAIL with NotImplementedError
# - @pytest.mark.integration marks tests that need real database
# - Tests define exact expected behavior for implementation
# - No mocks used - all tests use real connections
# - GREEN phase will implement just enough to make these tests pass
# - Database installation happens in GREEN phase task a11-green-1
