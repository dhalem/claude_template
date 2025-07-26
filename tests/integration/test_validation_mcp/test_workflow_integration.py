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
End-to-end workflow integration tests for Test Validation MCP system.
Tests complete validation workflows from test creation to approval.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.database.manager import DatabaseManager
from indexing.test_validation.utils.config import ValidationConfig
from indexing.test_validation.utils.fingerprinting import TestFingerprinter
from indexing.test_validation.utils.tokens import ValidationTokenManager


class TestValidationWorkflow:
    """Test complete validation workflows and end-to-end scenarios."""

    def setup_method(self):
        """Setup test environment for each test."""
        import tempfile

        # Create temporary database file
        tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp_file.name
        tmp_file.close()

        # Create configuration
        self.config = ValidationConfig()
        self.config.set("validation_stages", ["design", "implementation", "breaking", "approval"])
        self.config.set("token_expiry_hours", 24)
        self.config.set("max_validation_attempts", 3)

        # Create components
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.create_tables()
        self.fingerprinter = TestFingerprinter(cache_enabled=True)
        self.token_manager = ValidationTokenManager(default_expiry_hours=self.config.get("token_expiry_hours"))

    def teardown_method(self):
        """Cleanup test environment after each test."""
        import os

        # Cleanup temporary database file
        if hasattr(self, "db_path") and os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_complete_validation_lifecycle(self):
        """Test complete test validation lifecycle from design to approval."""
        # Step 1: Test design phase
        test_content = """
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

def test_user_registration_invalid_email():
    '''Test user registration fails with invalid email.'''
    user_data = {
        'username': 'testuser',
        'email': 'invalid_email',
        'password': 'secure_password'
    }

    with raises(ValidationError):
        create_user(user_data)

def create_user(user_data):
    # Simulate user creation
    if '@' not in user_data['email']:
        raise ValidationError('Invalid email format')
    return User(
        id=1,
        username=user_data['username'],
        email=user_data['email'],
        is_active=True
    )

class User:
    def __init__(self, id, username, email, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active

class ValidationError(Exception):
    pass

def raises(exception_type):
    class RaisesContext:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
            return issubclass(exc_type, exception_type)
    return RaisesContext()
"""
        test_file = "test_user_registration.py"

        # Generate fingerprint and store initial validation record
        fingerprint = self.fingerprinter.generate_fingerprint(test_content, test_file)
        metadata = self.fingerprinter.extract_metadata(test_content, test_file)

        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO test_validations
                (test_fingerprint, file_path, validation_stage, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (fingerprint, test_file, "design", datetime.now().isoformat(), str(metadata)),
            )
            conn.commit()

        # Step 2: Design validation passes
        design_token = self.token_manager.generate_token(fingerprint, "design")
        assert self.token_manager.validate_token(design_token, fingerprint, "design")

        # Record design validation
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO validation_history
                (test_fingerprint, stage, status, validated_at, validator_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (fingerprint, "design", "passed", datetime.now().isoformat(), "design_validator"),
            )

            # Move to implementation stage
            cursor.execute(
                """
                UPDATE test_validations
                SET validation_stage = ?, updated_at = ?
                WHERE test_fingerprint = ?
            """,
                ("implementation", datetime.now().isoformat(), fingerprint),
            )
            conn.commit()

        # Step 3: Implementation validation
        impl_token = self.token_manager.generate_token(fingerprint, "implementation")
        assert self.token_manager.validate_token(impl_token, fingerprint, "implementation")

        # Simulate implementation validation passing
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO validation_history
                (test_fingerprint, stage, status, validated_at, validator_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (fingerprint, "implementation", "passed", datetime.now().isoformat(), "impl_validator"),
            )

            # Move to breaking behavior stage
            cursor.execute(
                """
                UPDATE test_validations
                SET validation_stage = ?, updated_at = ?
                WHERE test_fingerprint = ?
            """,
                ("breaking", datetime.now().isoformat(), fingerprint),
            )
            conn.commit()

        # Step 4: Breaking behavior validation
        breaking_token = self.token_manager.generate_token(fingerprint, "breaking")
        assert self.token_manager.validate_token(breaking_token, fingerprint, "breaking")

        # Simulate breaking behavior validation passing
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO validation_history
                (test_fingerprint, stage, status, validated_at, validator_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (fingerprint, "breaking", "passed", datetime.now().isoformat(), "breaking_validator"),
            )

            # Move to approval stage
            cursor.execute(
                """
                UPDATE test_validations
                SET validation_stage = ?, updated_at = ?
                WHERE test_fingerprint = ?
            """,
                ("approval", datetime.now().isoformat(), fingerprint),
            )
            conn.commit()

        # Step 5: Final approval
        approval_token = self.token_manager.generate_token(fingerprint, "approval")
        assert self.token_manager.validate_token(approval_token, fingerprint, "approval")

        # Store approval token
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO approval_tokens (test_fingerprint, token, approved_by, approved_at, stage, issued_timestamp, expires_timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    fingerprint,
                    approval_token,
                    "final_approver",
                    datetime.now().isoformat(),
                    "approval",
                    datetime.now().isoformat(),
                    (datetime.now() + timedelta(days=7)).isoformat(),
                    "VALID",
                ),
            )

            # Mark validation as completed
            cursor.execute(
                """
                INSERT INTO validation_history
                (test_fingerprint, stage, status, validated_at, validator_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (fingerprint, "approval", "approved", datetime.now().isoformat(), "final_approver"),
            )

            cursor.execute(
                """
                UPDATE test_validations
                SET validation_stage = ?, updated_at = ?
                WHERE test_fingerprint = ?
            """,
                ("completed", datetime.now().isoformat(), fingerprint),
            )
            conn.commit()

        # Verify complete workflow
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()

            # Check final state
            cursor.execute(
                """
                SELECT validation_stage, file_path FROM test_validations
                WHERE test_fingerprint = ?
            """,
                (fingerprint,),
            )
            result = cursor.fetchone()
            assert result[0] == "completed"
            assert result[1] == test_file

            # Verify all validation history
            cursor.execute(
                """
                SELECT stage, status FROM validation_history
                WHERE test_fingerprint = ? ORDER BY validated_at
            """,
                (fingerprint,),
            )
            history = cursor.fetchall()

            expected_history = [
                ("design", "passed"),
                ("implementation", "passed"),
                ("breaking", "passed"),
                ("approval", "approved"),
            ]

            assert len(history) == 4
            for i, (stage, result) in enumerate(expected_history):
                assert history[i][0] == stage
                assert history[i][1] == result

    def test_validation_failure_and_retry(self):
        """Test validation failure handling and retry mechanism."""
        test_content = "def test_failing(): assert False"
        test_file = "test_failing.py"
        fingerprint = self.fingerprinter.generate_fingerprint(test_content, test_file)

        # Store initial validation record
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO test_validations
                (test_fingerprint, file_path, validation_stage, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (fingerprint, test_file, "design", datetime.now().isoformat()),
            )
            conn.commit()

        # Simulate multiple validation failures
        max_attempts = self.config.get("max_validation_attempts")

        for attempt in range(max_attempts):
            # Generate token for attempt
            token = self.token_manager.generate_token(fingerprint, "design")

            # Record failure
            with self.db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO validation_history
                    (test_fingerprint, stage, status, validated_at, validator_id, attempt_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (fingerprint, "design", "failed", datetime.now().isoformat(), f"validator_{attempt}", attempt + 1),
                )
                conn.commit()

        # After max attempts, validation should be marked as failed
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE test_validations
                SET validation_stage = ?, updated_at = ?
                WHERE test_fingerprint = ?
            """,
                ("failed", datetime.now().isoformat(), fingerprint),
            )
            conn.commit()

        # Verify failure state
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT validation_stage FROM test_validations WHERE test_fingerprint = ?
            """,
                (fingerprint,),
            )
            assert cursor.fetchone()[0] == "failed"

            # Verify attempt count
            cursor.execute(
                """
                SELECT COUNT(*) FROM validation_history
                WHERE test_fingerprint = ? AND stage = 'design'
            """,
                (fingerprint,),
            )
            assert cursor.fetchone()[0] == max_attempts

    def test_concurrent_validation_workflows(self):
        """Test multiple validation workflows running concurrently."""
        import threading

        test_files = [
            ("test_auth.py", "def test_authentication(): pass"),
            ("test_users.py", "def test_user_crud(): pass"),
            ("test_products.py", "def test_product_management(): pass"),
            ("test_orders.py", "def test_order_processing(): pass"),
            ("test_payments.py", "def test_payment_flow(): pass"),
        ]

        results = {}
        errors = []

        def workflow_thread(test_file, test_content, thread_id):
            """Run a complete validation workflow in a separate thread."""
            try:
                # Each thread has its own instances but shares database
                fingerprinter = TestFingerprinter()
                token_manager = ValidationTokenManager()

                fingerprint = fingerprinter.generate_fingerprint(test_content, test_file)

                # Store initial validation
                with self.db_manager.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO test_validations
                        (test_fingerprint, file_path, validation_stage, created_at)
                        VALUES (?, ?, ?, ?)
                    """,
                        (fingerprint, test_file, "design", datetime.now().isoformat()),
                    )
                    conn.commit()

                # Process through all stages
                stages = ["design", "implementation", "breaking", "approval"]
                for i, stage in enumerate(stages):
                    # Generate and validate token
                    token = token_manager.generate_token(fingerprint, stage)
                    is_valid = token_manager.validate_token(token, fingerprint, stage)

                    if not is_valid:
                        raise Exception(f"Token validation failed for {stage}")

                    # Record validation
                    with self.db_manager.get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO validation_history
                            (test_fingerprint, stage, status, validated_at, validator_id)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (fingerprint, stage, "passed", datetime.now().isoformat(), f"thread_{thread_id}"),
                        )

                        # Update to next stage or completion
                        next_stage = stages[i + 1] if i < len(stages) - 1 else "completed"
                        cursor.execute(
                            """
                            UPDATE test_validations
                            SET validation_stage = ?, updated_at = ?
                            WHERE test_fingerprint = ?
                        """,
                            (next_stage, datetime.now().isoformat(), fingerprint),
                        )
                        conn.commit()

                results[thread_id] = {"test_file": test_file, "fingerprint": fingerprint, "status": "completed"}

            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")

        # Start all workflows concurrently
        threads = []
        for i, (test_file, test_content) in enumerate(test_files):
            thread = threading.Thread(target=workflow_thread, args=(test_file, test_content, i))
            threads.append(thread)
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Concurrent workflow errors: {errors}"
        assert len(results) == len(test_files), "Not all workflows completed"

        # Verify database state
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()

            # All validations should be completed
            cursor.execute(
                """
                SELECT COUNT(*) FROM test_validations WHERE validation_stage = 'completed'
            """,
            )
            completed_count = cursor.fetchone()[0]
            assert completed_count == len(test_files)

            # Should have 4 validation history entries per test
            cursor.execute("SELECT COUNT(*) FROM validation_history")
            history_count = cursor.fetchone()[0]
            assert history_count == len(test_files) * 4

    def test_token_lifecycle_across_stages(self):
        """Test token lifecycle management across validation stages."""
        test_content = "def test_token_lifecycle(): pass"
        test_file = "test_tokens.py"
        fingerprint = self.fingerprinter.generate_fingerprint(test_content, test_file)

        # Create database record
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO test_validations
                (test_fingerprint, file_path, validation_stage, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (fingerprint, test_file, "design", datetime.now().isoformat()),
            )
            conn.commit()

        tokens = {}
        stages = ["design", "implementation", "breaking", "approval"]

        # Generate tokens for each stage
        for stage in stages:
            token = self.token_manager.generate_token(fingerprint, stage)
            tokens[stage] = token

            # Verify token is valid for its stage
            assert self.token_manager.validate_token(token, fingerprint, stage)

            # Verify token is invalid for other stages
            for other_stage in stages:
                if other_stage != stage:
                    assert not self.token_manager.validate_token(token, fingerprint, other_stage)

        # Test token usage and revocation
        design_token = tokens["design"]

        # Mark token as used
        self.token_manager.mark_used(design_token, "design_validation", "validator_1")

        # Used token should no longer be valid
        assert not self.token_manager.validate_token(design_token, fingerprint, "design")

        # Usage info should be available
        usage_info = self.token_manager.get_usage_info(design_token)
        assert usage_info["used"] is True
        assert usage_info["action"] == "design_validation"
        assert usage_info["user"] == "validator_1"

        # Test token revocation
        impl_token = tokens["implementation"]
        self.token_manager.revoke_token(impl_token)

        # Revoked token should not be valid
        assert not self.token_manager.validate_token(impl_token, fingerprint, "implementation")
        assert self.token_manager.is_revoked(impl_token)

    def test_configuration_driven_workflow(self):
        """Test workflow behavior driven by configuration changes."""
        # Create custom configuration
        custom_config = ValidationConfig()
        custom_config.set("validation_stages", ["design", "implementation", "approval"])  # Skip breaking
        custom_config.set("token_expiry_hours", 1)  # Short expiry
        custom_config.set("max_validation_attempts", 2)  # Fewer attempts

        # Create components with custom config
        token_manager = ValidationTokenManager(default_expiry_hours=custom_config.get("token_expiry_hours"))

        test_content = "def test_config_driven(): pass"
        test_file = "test_config.py"
        fingerprint = self.fingerprinter.generate_fingerprint(test_content, test_file)

        # Store with custom stages
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO test_validations
                (test_fingerprint, file_path, validation_stage, created_at, validation_stages)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    fingerprint,
                    test_file,
                    "design",
                    datetime.now().isoformat(),
                    json.dumps(custom_config.get("validation_stages")),
                ),
            )
            conn.commit()

        # Test workflow with custom stages
        stages = custom_config.get("validation_stages")
        for stage in stages:
            token = token_manager.generate_token(fingerprint, stage)

            # Verify token expiry matches configuration
            expiry_time = token_manager.get_expiry_time(token)
            expected_expiry = datetime.now() + timedelta(hours=1)
            time_diff = abs((expiry_time - expected_expiry).total_seconds())
            assert time_diff < 60, f"Token expiry should match config for {stage}"

            # Validate and record
            assert token_manager.validate_token(token, fingerprint, stage)

            with self.db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO validation_history
                    (test_fingerprint, stage, status, validated_at, validator_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (fingerprint, stage, "passed", datetime.now().isoformat(), "config_validator"),
                )
                conn.commit()

        # Verify only configured stages were used
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT stage FROM validation_history WHERE test_fingerprint = ?
            """,
                (fingerprint,),
            )
            used_stages = [row[0] for row in cursor.fetchall()]

            assert set(used_stages) == set(stages)
            assert "breaking" not in used_stages  # Should be skipped

    def test_metadata_driven_validation_routing(self):
        """Test how metadata affects validation routing and requirements."""
        # Test with different types of tests requiring different validation
        test_scenarios = [
            {
                "content": """
@pytest.mark.integration
def test_database_integration():
    with database_connection() as conn:
        assert conn.is_connected()
""",
                "file": "test_db_integration.py",
                "expected_requirements": ["design", "implementation", "breaking", "approval"],
            },
            {
                "content": """
@pytest.mark.unit
def test_simple_function():
    result = add(2, 3)
    assert result == 5
""",
                "file": "test_unit_simple.py",
                "expected_requirements": ["design", "implementation"],
            },
            {
                "content": """
@pytest.mark.performance
def test_performance_benchmark():
    start_time = time.time()
    process_large_dataset()
    duration = time.time() - start_time
    assert duration < 5.0
""",
                "file": "test_performance.py",
                "expected_requirements": ["design", "implementation", "breaking", "approval"],
            },
        ]

        for scenario in test_scenarios:
            fingerprint = self.fingerprinter.generate_fingerprint(scenario["content"], scenario["file"])
            metadata = self.fingerprinter.extract_metadata(scenario["content"], scenario["file"])

            # Determine validation requirements based on metadata
            requirements = self._determine_validation_requirements(metadata)

            # Store with requirements
            with self.db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO test_validations
                    (test_fingerprint, file_path, validation_stage, created_at,
                     metadata, validation_stages)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        fingerprint,
                        scenario["file"],
                        "design",
                        datetime.now().isoformat(),
                        str(metadata),
                        json.dumps(requirements),
                    ),
                )
                conn.commit()

            # Verify requirements match expectations
            assert requirements == scenario["expected_requirements"]

            # Process through required stages
            for stage in requirements:
                token = self.token_manager.generate_token(fingerprint, stage)
                assert self.token_manager.validate_token(token, fingerprint, stage)

    def _determine_validation_requirements(self, metadata):
        """Determine validation requirements based on test metadata."""
        decorators = metadata.get("decorators", [])

        # Integration and performance tests need full validation
        if any("integration" in d or "performance" in d for d in decorators):
            return ["design", "implementation", "breaking", "approval"]

        # Unit tests need minimal validation
        if any("unit" in d for d in decorators):
            return ["design", "implementation"]

        # Default full validation
        return ["design", "implementation", "breaking", "approval"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
