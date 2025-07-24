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
Unit tests for database schema creation following TDD RED phase.
These tests should FAIL initially as the implementation doesn't exist yet.
"""

import os
import sqlite3

# Import DatabaseManager - now it should work in GREEN phase
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.database.manager import DatabaseManager


class TestDatabaseSchema:
    """Test database schema creation and structure."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_database_creation(self, temp_db_path):
        """Test database and tables are created correctly."""
        # This should fail - DatabaseManager doesn't exist yet
        assert DatabaseManager is not None, "DatabaseManager not implemented yet"

        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Verify database file exists
        assert os.path.exists(temp_db_path), "Database file should be created"

        # Verify we can connect
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check sqlite_master for tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            'test_validations',
            'validation_history',
            'api_usage',
            'approval_tokens'
        }

        assert expected_tables.issubset(tables), f"Missing tables. Found: {tables}"
        conn.close()

    def test_test_validations_table_structure(self, temp_db_path):
        """Test test_validations table has correct schema."""
        # This should fail initially
        assert DatabaseManager is not None, "DatabaseManager not implemented yet"

        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Get table schema
        cursor.execute("PRAGMA table_info(test_validations)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'test_fingerprint': 'TEXT',
            'test_name': 'TEXT',
            'test_file_path': 'TEXT',
            'current_stage': 'TEXT',
            'status': 'TEXT',
            'gemini_analysis': 'TEXT',
            'validation_timestamp': 'DATETIME',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME',
            'approval_token': 'TEXT',
            'cost_cents': 'INTEGER',
            'user_value_statement': 'TEXT',
            'expiration_timestamp': 'DATETIME',
            'metadata': 'TEXT',
            'validation_stages': 'TEXT',
            'implementation_code': 'TEXT',
            'implementation_analysis': 'TEXT',
            'breaking_scenarios': 'TEXT',
            'breaking_analysis': 'TEXT',
            'approval_notes': 'TEXT'
        }

        for col, dtype in expected_columns.items():
            assert col in columns, f"Column {col} missing from test_validations"
            assert columns[col] == dtype, f"Column {col} has wrong type: {columns[col]}"

        conn.close()

    def test_validation_history_table_structure(self, temp_db_path):
        """Test validation_history table has correct schema."""
        # This should fail initially
        assert DatabaseManager is not None, "DatabaseManager not implemented yet"

        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(validation_history)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'test_fingerprint': 'TEXT',
            'stage': 'TEXT',
            'attempt_number': 'INTEGER',
            'validation_result': 'TEXT',
            'validated_at': 'DATETIME',
            'validator_id': 'TEXT',
            'feedback': 'TEXT',
            'timestamp': 'DATETIME'
        }

        for col, dtype in expected_columns.items():
            assert col in columns, f"Column {col} missing from validation_history"
            assert columns[col] == dtype, f"Column {col} has wrong type: {columns[col]}"

        conn.close()

    def test_api_usage_table_structure(self, temp_db_path):
        """Test api_usage table has correct schema."""
        # This should fail initially
        assert DatabaseManager is not None, "DatabaseManager not implemented yet"

        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(api_usage)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'timestamp': 'DATETIME',
            'service': 'TEXT',
            'operation': 'TEXT',
            'input_tokens': 'INTEGER',
            'output_tokens': 'INTEGER',
            'cost_cents': 'INTEGER'
            # daily_total_cents removed - will be calculated on the fly
        }

        for col, dtype in expected_columns.items():
            assert col in columns, f"Column {col} missing from api_usage"
            assert columns[col] == dtype, f"Column {col} has wrong type: {columns[col]}"

        conn.close()

    def test_approval_tokens_table_structure(self, temp_db_path):
        """Test approval_tokens table has correct schema."""
        # This should fail initially
        assert DatabaseManager is not None, "DatabaseManager not implemented yet"

        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(approval_tokens)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'test_fingerprint': 'TEXT',
            'approval_token': 'TEXT',
            'approved_by': 'TEXT',
            'approved_at': 'DATETIME',
            'stage': 'TEXT',
            'issued_timestamp': 'DATETIME',
            'expires_timestamp': 'DATETIME',
            'used_timestamp': 'DATETIME',
            'status': 'TEXT'
        }

        for col, dtype in expected_columns.items():
            assert col in columns, f"Column {col} missing from approval_tokens"
            assert columns[col] == dtype, f"Column {col} has wrong type: {columns[col]}"

        conn.close()

    def test_database_constraints(self, temp_db_path):
        """Test database constraints are properly set."""
        # This should fail initially
        assert DatabaseManager is not None, "DatabaseManager not implemented yet"

        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Test UNIQUE constraint on test_fingerprint
        cursor.execute("""
            INSERT INTO test_validations (test_fingerprint, test_name, test_file_path, current_stage, status, validation_timestamp)
            VALUES ('test_fp_123', 'test_example', '/path/to/test.py', 'design', 'PENDING', datetime('now'))
        """)
        conn.commit()

        # This should raise IntegrityError due to UNIQUE constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO test_validations (test_fingerprint, test_name, test_file_path, current_stage, status, validation_timestamp)
                VALUES ('test_fp_123', 'test_example2', '/path/to/test2.py', 'design', 'PENDING', datetime('now'))
            """)

        # Test PRIMARY KEY on approval_tokens
        cursor.execute("""
            INSERT INTO approval_tokens (approval_token, test_fingerprint, approved_by, approved_at, stage, issued_timestamp, expires_timestamp, status)
            VALUES ('token_123', 'test_fp_123', 'test_user', datetime('now'), 'design', datetime('now'), datetime('now', '+7 days'), 'VALID')
        """)
        conn.commit()

        # This should raise IntegrityError due to PRIMARY KEY
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO approval_tokens (approval_token, test_fingerprint, approved_by, approved_at, stage, issued_timestamp, expires_timestamp, status)
                VALUES ('token_123', 'test_fp_456', 'test_user', datetime('now'), 'implementation', datetime('now'), datetime('now', '+7 days'), 'VALID')
            """)

        conn.close()

    def test_foreign_key_constraints(self, temp_db_path):
        """Test foreign key constraints between tables."""
        # This should fail initially
        assert DatabaseManager is not None, "DatabaseManager not implemented yet"

        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        conn = sqlite3.connect(temp_db_path)
        # Enable foreign key enforcement
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Try to insert validation_history without matching test_fingerprint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO validation_history (test_fingerprint, stage, attempt_number, validation_result, feedback, timestamp)
                VALUES ('non_existent_fp', 'design', 1, 'REJECTED', 'Test feedback', datetime('now'))
            """)

        conn.close()


if __name__ == "__main__":
    # Run tests - these should all FAIL in RED phase
    pytest.main([__file__, "-v"])
