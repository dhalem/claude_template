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
Unit tests for database connection management following TDD RED phase.
These tests should FAIL initially as the implementation doesn't exist yet.
"""

import os
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.database.manager import DatabaseManager


class TestDatabaseConnectionManagement:
    """Test database connection management, transactions, and cleanup."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_connection_context_manager_closes_on_success(self, temp_db_path):
        """Test that connections are properly closed after successful operations."""
        # This should fail - we need to verify connection closure
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Use the context manager
        conn_ref = None
        cursor_ref = None
        with db_manager.get_db_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            # Keep references to test after context
            conn_ref = conn
            cursor_ref = cursor

        # After exiting context, operations should fail
        # sqlite3 doesn't have .closed attribute, so we test by trying operations
        with pytest.raises(sqlite3.ProgrammingError):
            cursor_ref.execute("SELECT 1")  # Should fail - connection closed

    def test_connection_context_manager_closes_on_error(self, temp_db_path):
        """Test that connections are properly closed even when errors occur."""
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        cursor_ref = None
        # Force an error inside the context
        with pytest.raises(RuntimeError):
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor_ref = cursor
                # Do some work
                cursor.execute("SELECT 1")
                # Raise an error
                raise RuntimeError("Test error")

        # Connection should still be closed despite the error
        # We verify by checking that cursor operations fail
        with pytest.raises(sqlite3.ProgrammingError):
            cursor_ref.execute("SELECT 1")

    def test_transaction_rollback_on_error(self, temp_db_path):
        """Test that transactions are rolled back on errors."""
        # This should fail - we need transaction management
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Insert a test record
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                    current_stage, status, validation_timestamp)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, ('fp_test_1', 'test1', '/test1.py', 'design', 'PENDING'))
            conn.commit()

        # Try to insert another record but fail midway
        try:
            with db_manager.get_transaction() as conn:  # New method we need
                cursor = conn.cursor()
                # First insert - should work
                cursor.execute("""
                    INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                        current_stage, status, validation_timestamp)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, ('fp_test_2', 'test2', '/test2.py', 'design', 'PENDING'))

                # Force an error
                raise RuntimeError("Simulated error")
        except RuntimeError:
            pass  # Expected

        # Verify the second insert was rolled back
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test_validations WHERE test_fingerprint = ?", ('fp_test_2',))
            count = cursor.fetchone()[0]
            assert count == 0, "Transaction should have been rolled back"

    def test_connection_thread_safety(self, temp_db_path):
        """Test that connections are thread-safe and isolated."""
        # This should fail - we need thread-safe connection handling
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        results = []
        errors = []

        def worker(thread_id):
            """Worker function for thread testing."""
            try:
                with db_manager.get_db_connection() as conn:
                    cursor = conn.cursor()
                    # Each thread inserts its own record
                    cursor.execute("""
                        INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                            current_stage, status, validation_timestamp)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (f'fp_thread_{thread_id}', f'test_{thread_id}',
                          f'/test_{thread_id}.py', 'design', 'PENDING'))
                    conn.commit()

                    # Simulate some work
                    time.sleep(0.01)

                    # Verify our insert
                    cursor.execute("SELECT COUNT(*) FROM test_validations WHERE test_fingerprint = ?",
                                 (f'fp_thread_{thread_id}',))
                    count = cursor.fetchone()[0]
                    results.append((thread_id, count))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Run multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify no errors and all inserts succeeded
        assert len(errors) == 0, f"Thread errors occurred: {errors}"
        assert len(results) == 10, "All threads should complete"
        for thread_id, count in results:
            assert count == 1, f"Thread {thread_id} insert verification failed"

    def test_connection_pool_size_limit(self, temp_db_path):
        """Test that connection pool has appropriate size limits."""
        # This should fail - we need connection pooling
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Get pool stats (method doesn't exist yet)
        initial_stats = db_manager.get_pool_stats()
        assert initial_stats['active_connections'] == 0
        assert initial_stats['max_connections'] > 0

        # Open multiple connections
        contexts = []
        connections = []
        for i in range(5):
            ctx = db_manager.get_db_connection()
            conn = ctx.__enter__()
            contexts.append(ctx)
            connections.append(conn)

        # Check pool stats
        stats = db_manager.get_pool_stats()
        assert stats['active_connections'] == 5

        # Clean up
        for ctx in contexts:
            ctx.__exit__(None, None, None)

        # Verify connections returned to pool
        final_stats = db_manager.get_pool_stats()
        assert final_stats['active_connections'] == 0

    def test_connection_timeout_handling(self, temp_db_path):
        """Test that connections handle timeouts appropriately."""
        # This should fail - we need timeout handling
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Test with a short timeout
        with db_manager.get_db_connection(timeout=0.1) as conn:  # 100ms timeout
            cursor = conn.cursor()
            # This should work quickly
            cursor.execute("SELECT 1")

            # Verify timeout is set properly
            # SQLite uses busy_timeout in milliseconds
            cursor.execute("PRAGMA busy_timeout")
            timeout = cursor.fetchone()[0]
            assert timeout == 100, f"Expected timeout 100ms, got {timeout}ms"

    def test_connection_recovery_after_database_lock(self, temp_db_path):
        """Test that connection manager can recover from database locks."""
        # This should fail - we need lock recovery
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Simulate a database lock by holding a write transaction
        lock_conn = sqlite3.connect(temp_db_path)
        lock_conn.execute("BEGIN EXCLUSIVE")
        lock_cursor = lock_conn.cursor()
        lock_cursor.execute("""
            INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                current_stage, status, validation_timestamp)
            VALUES ('fp_lock', 'lock_test', '/lock.py', 'design', 'PENDING', datetime('now'))
        """)
        # Don't commit - hold the lock

        # Try to get a connection with timeout
        start_time = time.time()
        with pytest.raises(sqlite3.OperationalError):  # Should timeout
            with db_manager.get_db_connection(timeout=0.5) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                        current_stage, status, validation_timestamp)
                    VALUES ('fp_timeout', 'timeout_test', '/timeout.py', 'design', 'PENDING', datetime('now'))
                """)
                conn.commit()

        # Verify we didn't wait forever
        elapsed = time.time() - start_time
        assert elapsed < 1.0, "Should have timed out quickly"

        # Clean up
        lock_conn.rollback()
        lock_conn.close()

    def test_connection_provides_row_factory(self, temp_db_path):
        """Test that connections can provide dict-like row access."""
        # This should fail - we need row factory support
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Insert test data
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                    current_stage, status, validation_timestamp)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, ('fp_dict_test', 'dict_test', '/dict.py', 'design', 'PENDING'))
            conn.commit()

        # Get connection with row factory
        with db_manager.get_db_connection(row_factory='dict') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_validations WHERE test_fingerprint = ?", ('fp_dict_test',))
            row = cursor.fetchone()

            # Should be able to access as dict
            assert isinstance(row, dict) or hasattr(row, '__getitem__')
            assert row['test_fingerprint'] == 'fp_dict_test'
            assert row['test_name'] == 'dict_test'
            assert row['status'] == 'PENDING'

    def test_get_transaction_auto_rollback(self, temp_db_path):
        """Test that get_transaction automatically rolls back on exceptions."""
        # This should fail - we need get_transaction method
        db_manager = DatabaseManager(temp_db_path)
        db_manager.create_tables()

        # Insert initial data
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                    current_stage, status, validation_timestamp)
                VALUES ('fp_base', 'base_test', '/base.py', 'design', 'PENDING', datetime('now'))
            """)
            conn.commit()

        # Use get_transaction - should auto-rollback on exception
        with pytest.raises(ValueError):
            with db_manager.get_transaction() as conn:
                cursor = conn.cursor()
                # Update existing record
                cursor.execute("""
                    UPDATE test_validations
                    SET status = 'APPROVED'
                    WHERE test_fingerprint = 'fp_base'
                """)

                # Insert new record
                cursor.execute("""
                    INSERT INTO test_validations (test_fingerprint, test_name, test_file_path,
                        current_stage, status, validation_timestamp)
                    VALUES ('fp_trans', 'trans_test', '/trans.py', 'design', 'PENDING', datetime('now'))
                """)

                # Raise error before commit
                raise ValueError("Simulated error")

        # Verify both operations were rolled back
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            # Check original record unchanged
            cursor.execute("SELECT status FROM test_validations WHERE test_fingerprint = 'fp_base'")
            status = cursor.fetchone()[0]
            assert status == 'PENDING', "Update should have been rolled back"

            # Check new record not inserted
            cursor.execute("SELECT COUNT(*) FROM test_validations WHERE test_fingerprint = 'fp_trans'")
            count = cursor.fetchone()[0]
            assert count == 0, "Insert should have been rolled back"


if __name__ == "__main__":
    # Run tests - these should all FAIL in RED phase
    pytest.main([__file__, "-v"])
