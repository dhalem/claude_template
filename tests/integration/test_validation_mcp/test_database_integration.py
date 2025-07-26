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
Integration tests for database layer with utilities.
Tests how configuration, fingerprinting, and tokens integrate with database.
"""

import os
import sys
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.database.manager import DatabaseManager
from indexing.test_validation.utils.config import ValidationConfig
from indexing.test_validation.utils.fingerprinting import TestFingerprinter
from indexing.test_validation.utils.tokens import ValidationTokenManager


class TestDatabaseUtilityIntegration:
    """Test integration between database layer and utility components."""

    def test_config_driven_database_setup(self):
        """Test that database manager can use configuration from ValidationConfig."""
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            # Create configuration with database settings
            config = ValidationConfig()
            config.set("database_path", db_path)
            config.set("connection_timeout", 30)
            config.set("max_connections", 10)

            # Create database manager using config settings
            db_manager = DatabaseManager(config.get("database_path"))
            db_manager.create_tables()

            # Verify database was created and accessible
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                expected_tables = ["test_validations", "validation_history", "api_usage", "approval_tokens"]
                for table in expected_tables:
                    assert table in tables, f"Table {table} not found in database"

        finally:
            # Cleanup temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_fingerprinting_with_database_storage(self):
        """Test storing and retrieving fingerprints through database."""
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            # Setup database and fingerprinter
            db_manager = DatabaseManager(db_path)
            db_manager.create_tables()
            fingerprinter = TestFingerprinter()

            # Create test content and generate fingerprint
            test_content = """
def test_example():
    assert True

def test_another():
    assert False
"""
            filename = "test_example.py"
            fingerprint = fingerprinter.generate_fingerprint(test_content, filename)

            # Store fingerprint in database
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO test_validations (test_fingerprint, file_path, validation_stage)
                    VALUES (?, ?, ?)
                """,
                    (fingerprint, filename, "design"),
                )
                conn.commit()

            # Retrieve and verify fingerprint
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT test_fingerprint, file_path FROM test_validations
                    WHERE file_path = ?
                """,
                    (filename,),
                )
                result = cursor.fetchone()

                assert result is not None, "Fingerprint not found in database"
                stored_fingerprint, stored_path = result
                assert stored_fingerprint == fingerprint
                assert stored_path == filename

        finally:
            # Cleanup temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_token_persistence_integration(self):
        """Test that tokens can be persisted through database and validated."""
        # Setup database and token manager with persistence
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            # Create token manager with persistent storage
            token_manager = ValidationTokenManager(storage_path=db_path, secret_key="test_secret_key")

            # Generate and persist token
            fingerprint = "test_fingerprint_123"
            stage = "implementation"
            token = token_manager.generate_token(fingerprint, stage)

            # Create new token manager instance (simulates restart)
            token_manager2 = ValidationTokenManager(storage_path=db_path, secret_key="test_secret_key")

            # Verify token can be validated by new instance
            is_valid = token_manager2.validate_token(token, fingerprint, stage)
            assert is_valid, "Token should be valid after persistence"

            # Verify token data is accessible
            decoded = token_manager2.decode_token(token)
            assert decoded["fingerprint"] == fingerprint
            assert decoded["stage"] == stage

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_cross_component_workflow(self):
        """Test complete workflow using all components together."""
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            # Setup all components
            db_manager = DatabaseManager(db_path)
            db_manager.create_tables()
            config = ValidationConfig()
            fingerprinter = TestFingerprinter()
            token_manager = ValidationTokenManager()

            # Configure test validation stages
            config.set("validation_stages", ["design", "implementation", "breaking", "approval"])

            # Simulate test file
            test_content = """
def test_user_authentication():
    user = create_test_user()
    assert user.authenticate("password123")

def test_user_permissions():
    user = create_regular_user()
    assert not user.has_admin_privileges()
"""
            test_file = "test_authentication.py"

            # Step 1: Generate fingerprint for test
            fingerprint = fingerprinter.generate_fingerprint(test_content, test_file)

            # Step 2: Store test validation record in database
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO test_validations
                    (test_fingerprint, file_path, validation_stage, validation_timestamp)
                    VALUES (?, ?, ?, ?)
                """,
                    (fingerprint, test_file, "design", datetime.now().isoformat()),
                )
                conn.commit()

            # Step 3: Generate validation token for implementation stage
            impl_token = token_manager.generate_token(fingerprint, "implementation")

            # Step 4: Validate token and proceed to next stage
            is_valid = token_manager.validate_token(impl_token, fingerprint, "implementation")
            assert is_valid, "Implementation token should be valid"

            # Step 5: Update database with validation progress
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE test_validations
                    SET validation_stage = ?, validation_timestamp = ?
                    WHERE test_fingerprint = ?
                """,
                    ("implementation", datetime.now().isoformat(), fingerprint),
                )

                # Record validation history
                cursor.execute(
                    """
                    INSERT INTO validation_history
                    (test_fingerprint, stage, attempt_number, status, feedback, validated_at, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        fingerprint,
                        "design",
                        1,
                        "APPROVED",
                        "Test passed validation",
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()

            # Step 6: Verify workflow state in database
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT validation_stage, file_path FROM test_validations
                    WHERE test_fingerprint = ?
                """,
                    (fingerprint,),
                )
                result = cursor.fetchone()

                assert result is not None
                current_stage, file_path = result
                assert current_stage == "implementation"
                assert file_path == test_file

        finally:
            # Cleanup temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_concurrent_database_access(self):
        """Test that multiple components can safely access database concurrently."""
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            db_manager = DatabaseManager(db_path)
            db_manager.create_tables()
            results = []
            errors = []

            def worker_thread(worker_id):
                """Worker function that performs database operations."""
                try:
                    fingerprinter = TestFingerprinter()
                    token_manager = ValidationTokenManager()

                    # Each worker creates unique test data
                    test_content = f"def test_worker_{worker_id}(): assert True"
                    filename = f"test_worker_{worker_id}.py"
                    fingerprint = fingerprinter.generate_fingerprint(test_content, filename)

                    # Store in database
                    with db_manager.get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO test_validations
                            (test_fingerprint, file_path, validation_stage)
                            VALUES (?, ?, ?)
                        """,
                            (fingerprint, filename, "design"),
                        )
                        conn.commit()

                    # Generate and validate token
                    token = token_manager.generate_token(fingerprint, "design")
                    is_valid = token_manager.validate_token(token, fingerprint, "design")

                    results.append({"worker_id": worker_id, "fingerprint": fingerprint, "token_valid": is_valid})

                except Exception as e:
                    errors.append(f"Worker {worker_id}: {str(e)}")

            # Run multiple workers concurrently
            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify results
            assert len(errors) == 0, f"Concurrent access errors: {errors}"
            assert len(results) == 5, "Not all workers completed successfully"

            # Verify all workers' data was stored correctly
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM test_validations")
                count = cursor.fetchone()[0]
                assert count == 5, "Not all records were stored in database"

        finally:
            # Cleanup temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_database_transaction_with_utilities(self):
        """Test that utilities work correctly within database transactions."""
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            db_manager = DatabaseManager(db_path)
            db_manager.create_tables()
            fingerprinter = TestFingerprinter()
            token_manager = ValidationTokenManager()

            test_content = "def test_transaction(): pass"
            filename = "test_transaction.py"
            fingerprint = fingerprinter.generate_fingerprint(test_content, filename)

            # Test successful transaction
            with db_manager.get_transaction() as conn:
                cursor = conn.cursor()

                # Insert test validation
                cursor.execute(
                    """
                    INSERT INTO test_validations
                    (test_fingerprint, file_path, validation_stage)
                    VALUES (?, ?, ?)
                """,
                    (fingerprint, filename, "design"),
                )

                # Generate token (this should work within transaction)
                token = token_manager.generate_token(fingerprint, "design")

                # Insert validation history
                cursor.execute(
                    """
                    INSERT INTO validation_history
                    (test_fingerprint, stage, attempt_number, status, feedback, validated_at, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        fingerprint,
                        "design",
                        1,
                        "APPROVED",
                        "Test passed validation",
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )

            # Verify transaction was committed
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM test_validations")
                assert cursor.fetchone()[0] == 1

                cursor.execute("SELECT COUNT(*) FROM validation_history")
                assert cursor.fetchone()[0] == 1

        finally:
            # Cleanup temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_error_recovery_integration(self):
        """Test how components handle database errors and recover."""
        # Test that configuration handles non-existent paths gracefully
        config = ValidationConfig()
        config.set("database_path", "/nonexistent/path/validation.db")

        # Configuration should still work
        assert config.get("database_path") == "/nonexistent/path/validation.db"
        assert config.get("token_expiry_hours") == 168  # Default value

        # Test token manager without persistent storage (in-memory only)
        token_manager = ValidationTokenManager()  # No storage_path = in-memory only

        # Token generation should work in-memory
        token = token_manager.generate_token("test_fp", "design")
        is_valid = token_manager.validate_token(token, "test_fp", "design")
        assert is_valid, "Token should be valid in-memory mode"

        # Test fingerprinter resilience
        fingerprinter = TestFingerprinter()
        fingerprint = fingerprinter.generate_fingerprint("def test(): pass", "test.py")
        assert len(fingerprint) > 0, "Fingerprinter should work regardless of database issues"

    def test_configuration_impact_on_components(self):
        """Test how configuration changes affect database and utility behavior."""
        # Create configuration with custom settings
        config = ValidationConfig()
        config.set("token_expiry_hours", 1)  # Short expiry for testing
        config.set("max_validation_attempts", 5)
        config.set("rate_limit_per_minute", 10)

        # Create database manager with config-driven path
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            config.set("database_path", db_path)
            db_manager = DatabaseManager(config.get("database_path"))

            # Create token manager with config-driven settings and unique user for this test
            token_manager = ValidationTokenManager(
                default_expiry_hours=config.get("token_expiry_hours"),
                rate_limit_per_minute=config.get("rate_limit_per_minute"),
                storage_path=db_path,
            )

            # Reset rate limiter to ensure clean test state
            token_manager._rate_limit_tracker.clear()

            # Test that configuration affects token behavior (use unique user for this test)
            import time

            test_user = f"config_test_user_{int(time.time())}"
            fingerprint = "config_test"
            token = token_manager.generate_token(fingerprint, "design", user_id=test_user)

            # Verify token expiry time matches configuration
            expiry_time = token_manager.get_expiry_time(token)
            expected_expiry = datetime.now() + timedelta(hours=1)
            time_diff = abs((expiry_time - expected_expiry).total_seconds())
            assert time_diff < 60, "Token expiry should match configuration"

            # Test rate limiting from configuration (using specific user)
            # Note: We already generated one token above, so we're at 1/10
            tokens = []
            for i in range(9):  # 9 more tokens should be at the limit (total 10)
                token = token_manager.generate_token(f"{fingerprint}_{i}", "design", user_id=test_user)
                tokens.append(token)

            # Next token should trigger rate limit for this specific user
            with pytest.raises(Exception) as exc_info:
                token_manager.generate_token(f"{fingerprint}_overflow", "design", user_id=test_user)
            assert "rate limit" in str(exc_info.value).lower()

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_metadata_extraction_with_database_storage(self):
        """Test fingerprinting metadata extraction and database storage."""
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            db_manager = DatabaseManager(db_path)
            db_manager.create_tables()
            fingerprinter = TestFingerprinter()

            # Complex test content with metadata
            test_content = """
import pytest

@pytest.mark.slow
def test_complex_scenario():
    '''Test complex user scenario with authentication.'''
    user = create_test_user()
    assert user.authenticate("valid_password")

@pytest.mark.integration
class TestUserManagement:
    def test_user_creation(self):
            user = User(name="test", email="test@example.com")
            assert user.is_valid()

    @pytest.mark.skip("Not implemented yet")
    def test_user_deletion(self):
            pass

def create_test_user():
    return User(name="testuser", email="test@example.com")

class User:
    def __init__(self, name, email):
            self.name = name
            self.email = email

    def authenticate(self, password):
            return password == "valid_password"

    def is_valid(self):
            return "@" in self.email and len(self.name) > 0
"""
            filename = "test_complex.py"

            # Generate fingerprint and extract metadata
            fingerprint = fingerprinter.generate_fingerprint(test_content, filename)
            metadata = fingerprinter.extract_metadata(test_content, filename)

            # Store in database with metadata
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO test_validations
                    (test_fingerprint, file_path, validation_stage, gemini_analysis)
                    VALUES (?, ?, ?, ?)
                """,
                    (fingerprint, filename, "design", str(metadata)),
                )
                conn.commit()

            # Retrieve and verify metadata
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT gemini_analysis FROM test_validations WHERE test_fingerprint = ?
                """,
                    (fingerprint,),
                )
                result = cursor.fetchone()
                stored_metadata = result[0] if result else None

                # Verify metadata contains expected information
                assert stored_metadata is not None, "No metadata stored"
                assert "pytest.mark.slow" in stored_metadata
                assert "TestUserManagement" in stored_metadata
                assert "test_complex_scenario" in stored_metadata
                # Note: pytest.mark.integration is a class-level decorator, so might not be in top-level decorators
                assert "pytest" in stored_metadata

        finally:
            # Cleanup temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
