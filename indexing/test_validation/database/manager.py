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

    @contextmanager
    def get_db_connection(self):
        """Get a database connection with automatic resource management.

        Yields:
            sqlite3.Connection: Database connection with foreign keys enabled

        Raises:
            sqlite3.Error: If database connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

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
                        test_name TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        validation_stage TEXT NOT NULL CHECK (validation_stage IN ('design', 'implementation', 'breaking', 'approval')),
                        status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
                        gemini_analysis TEXT,
                        validation_timestamp DATETIME NOT NULL,
                        approval_token TEXT UNIQUE,
                        cost_cents INTEGER DEFAULT 0,
                        user_value_statement TEXT,
                        expiration_timestamp DATETIME
                    )
                ''')

                # Create validation_history table with foreign key
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {TABLE_VALIDATION_HISTORY} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_fingerprint TEXT NOT NULL,
                        stage TEXT NOT NULL CHECK (stage IN ('design', 'implementation', 'breaking', 'approval')),
                        attempt_number INTEGER NOT NULL,
                        status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
                        feedback TEXT,
                        timestamp DATETIME NOT NULL,
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
                        token TEXT PRIMARY KEY,
                        test_fingerprint TEXT NOT NULL,
                        stage TEXT NOT NULL CHECK (stage IN ('design', 'implementation', 'breaking', 'approval')),
                        issued_timestamp DATETIME NOT NULL,
                        expires_timestamp DATETIME NOT NULL,
                        used_timestamp DATETIME,
                        status TEXT NOT NULL CHECK (status IN ('VALID', 'USED', 'EXPIRED', 'REVOKED')),
                        FOREIGN KEY (test_fingerprint) REFERENCES {TABLE_TEST_VALIDATIONS}(test_fingerprint)
                    )
                ''')

                # Create index on foreign key for performance
                cursor.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_approval_tokens_fingerprint
                    ON {TABLE_APPROVAL_TOKENS} (test_fingerprint)
                ''')

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
