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
Database management module for Test Validation MCP.
Handles database creation, schema management, and connections.
"""

import logging
import sqlite3
import threading
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Table name constants to avoid magic strings
TABLE_TEST_VALIDATIONS = "test_validations"
TABLE_VALIDATION_HISTORY = "validation_history"
TABLE_API_USAGE = "api_usage"
TABLE_APPROVAL_TOKENS = "approval_tokens"

# Valid status values for constraints
VALID_STATUSES = ["PENDING", "APPROVED", "REJECTED", "EXPIRED"]
VALID_STAGES = ["design", "implementation", "breaking", "approval"]


class DatabaseManager:
    """Manages database connections and schema for test validation system."""

    def __init__(self, db_path: str):
        """Initialize database manager with specified database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._active_connections = 0
        self._max_connections = 10
        self._lock = threading.Lock()  # Thread-safe connection counter

    @contextmanager
    def get_db_connection(self, timeout=None, row_factory=None):
        """Get a database connection with automatic resource management.

        Args:
            timeout: Optional timeout in seconds (converted to milliseconds for SQLite)
            row_factory: Optional row factory ('dict' for dict-like rows)

        Yields:
            sqlite3.Connection: Database connection with foreign keys enabled

        Raises:
            sqlite3.Error: If database connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")

            # Set timeout if specified
            if timeout is not None:
                # SQLite uses milliseconds for busy_timeout
                timeout_ms = int(timeout * 1000)
                conn.execute(f"PRAGMA busy_timeout = {timeout_ms}")

            # Set row factory if specified
            if row_factory == 'dict':
                conn.row_factory = sqlite3.Row

            with self._lock:
                self._active_connections += 1
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
            with self._lock:
                self._active_connections -= 1

    def create_tables(self):
        """Create all required database tables with proper schema.

        Creates the following tables:
        - test_validations: Main validation records
        - validation_history: Track validation attempts
        - api_usage: Track API usage and costs
        - approval_tokens: Track validation tokens

        Raises:
            sqlite3.Error: If table creation fails
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                # Create test_validations table with enhanced constraints
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {TABLE_TEST_VALIDATIONS} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_fingerprint TEXT UNIQUE NOT NULL,
                        test_name TEXT,
                        test_file_path TEXT NOT NULL,
                        current_stage TEXT NOT NULL CHECK (current_stage IN ('design', 'implementation', 'breaking', 'approval', 'completed', 'failed')),
                        status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
                        gemini_analysis TEXT,
                        validation_timestamp DATETIME,
                        created_at DATETIME,
                        updated_at DATETIME,
                        approval_token TEXT UNIQUE,
                        cost_cents INTEGER DEFAULT 0,
                        user_value_statement TEXT,
                        expiration_timestamp DATETIME,
                        metadata TEXT,
                        validation_stages TEXT
                    )
                ''')

                # Create validation_history table with foreign key
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {TABLE_VALIDATION_HISTORY} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_fingerprint TEXT NOT NULL,
                        stage TEXT NOT NULL CHECK (stage IN ('design', 'implementation', 'breaking', 'approval')),
                        attempt_number INTEGER,
                        validation_result TEXT NOT NULL,
                        validated_at DATETIME NOT NULL,
                        validator_id TEXT,
                        feedback TEXT,
                        timestamp DATETIME,
                        FOREIGN KEY (test_fingerprint) REFERENCES {TABLE_TEST_VALIDATIONS}(test_fingerprint)
                    )
                ''')

                # Create index on foreign key for performance
                cursor.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_validation_history_fingerprint
                    ON {TABLE_VALIDATION_HISTORY} (test_fingerprint)
                ''')

                # Create api_usage table (without daily_total_cents - will be calculated)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {TABLE_API_USAGE} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        service TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        input_tokens INTEGER,
                        output_tokens INTEGER,
                        cost_cents INTEGER
                    )
                ''')

                # Create approval_tokens table
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {TABLE_APPROVAL_TOKENS} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_fingerprint TEXT NOT NULL,
                        approval_token TEXT UNIQUE NOT NULL,
                        approved_by TEXT NOT NULL,
                        approved_at DATETIME NOT NULL,
                        stage TEXT CHECK (stage IN ('design', 'implementation', 'breaking', 'approval')),
                        issued_timestamp DATETIME,
                        expires_timestamp DATETIME,
                        used_timestamp DATETIME,
                        status TEXT CHECK (status IN ('VALID', 'USED', 'EXPIRED', 'REVOKED')),
                        FOREIGN KEY (test_fingerprint) REFERENCES {TABLE_TEST_VALIDATIONS}(test_fingerprint)
                    )
                ''')

                # Create index on foreign key for performance
                cursor.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_approval_tokens_fingerprint
                    ON {TABLE_APPROVAL_TOKENS} (test_fingerprint)
                ''')

                # Ensure transaction is committed
                conn.commit()
                logger.info("Database tables created successfully")

        except sqlite3.Error as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled.

        DEPRECATED: Use get_db_connection() context manager instead.
        This method is kept for backward compatibility but callers
        are responsible for closing the connection.

        Returns:
            sqlite3.Connection: Database connection

        Raises:
            sqlite3.Error: If connection fails
        """
        logger.warning("get_connection() is deprecated. Use get_db_connection() context manager instead.")
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def get_transaction(self):
        """Get a database connection with automatic transaction management.

        This context manager automatically begins a transaction and either
        commits on success or rolls back on any exception.

        Yields:
            sqlite3.Connection: Database connection in transaction

        Raises:
            sqlite3.Error: If database operations fail
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            # Begin transaction explicitly
            conn.execute("BEGIN")
            with self._lock:
                self._active_connections += 1
            yield conn
            # Commit on successful completion
            conn.commit()
        except Exception as e:
            # Catching Exception to ensure transaction rollback on any failure, regardless of error type
            if conn:
                conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            if conn:
                conn.close()
            with self._lock:
                self._active_connections -= 1

    def get_pool_stats(self) -> dict:
        """Get connection pool statistics.

        Returns:
            dict: Dictionary containing pool statistics
        """
        with self._lock:
            active = self._active_connections
            max_conn = self._max_connections

        return {
            'active_connections': active,
            'max_connections': max_conn,
            'available_connections': max_conn - active
        }
