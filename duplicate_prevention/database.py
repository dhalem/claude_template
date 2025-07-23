# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Database connection and management for duplicate prevention system

This module provides connection management and health monitoring for the Qdrant
vector database used to store and retrieve code similarity vectors.

Classes:
    DatabaseConnector: Main interface for database operations
    DatabaseConfig: Configuration management for database settings

Functions:
    get_health_status: Check database health and connectivity
"""

from typing import Any, Dict, List, Optional

import requests


# Custom Exception Classes
class DatabaseError(Exception):
    """Base exception for database operations"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass


class DatabaseTimeoutError(DatabaseConnectionError):
    """Raised when database operations timeout"""
    pass


class DatabaseHealthCheckError(DatabaseError):
    """Raised when health check operations fail"""
    pass


class DatabaseConnector:
    """Main interface for Qdrant database operations

    Provides connection management and health monitoring for Qdrant database.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, timeout: Optional[int] = None,
                 protocol: Optional[str] = None, api_key: Optional[str] = None,
                 connect_timeout: Optional[int] = None, read_timeout: Optional[int] = None,
                 max_retries: int = 3, pool_connections: int = 10, pool_maxsize: int = 10):
        """Initialize database connector with configuration

        Args:
            host: Database host address (defaults to config value)
            port: Database port number (defaults to config value)
            timeout: Connection timeout in seconds (defaults to config value)
            protocol: Protocol to use - 'http' or 'https' (defaults to config value)
            api_key: API key for authentication (defaults to config value)
            connect_timeout: Connection establishment timeout (defaults to timeout)
            read_timeout: Read operation timeout (defaults to timeout)
            max_retries: Maximum number of retry attempts for failed requests
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections to save in the pool
        """
        # Load default configuration
        from duplicate_prevention.config import get_database_config
        config = get_database_config()

        # Use provided parameters or fall back to configuration
        self.host = host if host is not None else config["host"]
        self.port = port if port is not None else config["port"]
        self.timeout = timeout if timeout is not None else config["timeout"]
        self.protocol = protocol if protocol is not None else config["protocol"]
        self.api_key = api_key if api_key is not None else config["api_key"]

        # Validate protocol
        if self.protocol not in ["http", "https"]:
            raise ValueError(f"Invalid protocol '{self.protocol}'. Must be 'http' or 'https'")

        self.base_url = f"{self.protocol}://{self.host}:{self.port}"

        # Advanced timeout configuration
        self.connect_timeout = connect_timeout if connect_timeout is not None else self.timeout
        self.read_timeout = read_timeout if read_timeout is not None else self.timeout
        self.timeout_tuple = (self.connect_timeout, self.read_timeout)

        # Connection pooling configuration
        self.max_retries = max_retries
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize

        # Removed stateful error tracking for thread safety
        # Errors are now raised as exceptions instead of stored state

        # Set up logging
        import logging
        self.logger = logging.getLogger(f"{__name__}.DatabaseConnector")

        # Set up connection pooling session
        self._setup_session()

        # Log initialization
        self.logger.info(
            "DatabaseConnector initialized",
            extra={
                "host": self.host,
                "port": self.port,
                "timeout": self.timeout,
                "connect_timeout": self.connect_timeout,
                "read_timeout": self.read_timeout,
                "pool_connections": self.pool_connections,
                "pool_maxsize": self.pool_maxsize,
                "max_retries": self.max_retries
            }
        )

    def _setup_session(self) -> None:
        """Set up HTTP session with connection pooling and retry strategy"""
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        # Create session for connection pooling
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.1,  # 0.1s, 0.2s, 0.4s delays
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["GET", "PUT", "DELETE"],  # Retry idempotent operations
            # Don't retry on connection errors (includes timeouts) to maintain predictable timeout behavior
            raise_on_status=False,
            connect=0,  # Don't retry connection errors
        )

        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=self.pool_connections,
            pool_maxsize=self.pool_maxsize,
            max_retries=retry_strategy
        )

        # Mount adapter for HTTP connections
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set up API key authentication if provided
        if self.api_key:
            self.session.headers.update({"api-key": self.api_key})

    def connect(self) -> bool:
        """Establish connection to database

        Returns:
            True if connection successful, False otherwise
        """
        self.logger.debug(
            "Attempting database connection",
            extra={"base_url": self.base_url, "timeout": self.timeout_tuple}
        )

        try:
            response = self.session.get(f"{self.base_url}/", timeout=self.timeout_tuple)
            success = response.status_code == 200

            if success:
                self.logger.info(
                    "Database connection successful",
                    extra={"base_url": self.base_url, "status_code": response.status_code}
                )
            else:
                self.logger.warning(
                    "Database connection failed - unexpected status code",
                    extra={"base_url": self.base_url, "status_code": response.status_code}
                )

            return success
        except requests.exceptions.Timeout as e:
            # Log the timeout but still return False for backward compatibility
            # Log detailed error for debugging, but create sanitized user message
            self.logger.error(
                "Database connection timeout",
                extra={
                    "base_url": self.base_url,
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout,
                    "error": str(e)
                }
            )
            return False
        except requests.exceptions.ConnectionError as e:
            # Log connection error but still return False for backward compatibility
            # Log detailed error for debugging, but create sanitized user message
            self.logger.error(
                "Database connection error",
                extra={"base_url": self.base_url, "error": str(e)}
            )
            return False
        except requests.exceptions.RequestException as e:
            # Log any other requests-related error but still return False for backward compatibility
            # Log detailed error for debugging, but create sanitized user message
            self.logger.error(
                "Database request error",
                extra={"base_url": self.base_url, "error": str(e)}
            )
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check database health status

        Returns:
            Dictionary with health status information
        """
        self.logger.debug(
            "Performing database health check",
            extra={"base_url": self.base_url, "endpoint": "/healthz"}
        )

        try:
            response = self.session.get(f"{self.base_url}/healthz", timeout=self.timeout_tuple)
            if response.status_code == 200:
                self.logger.info(
                    "Database health check successful",
                    extra={
                        "base_url": self.base_url,
                        "status_code": response.status_code,
                        "response": response.text.strip()
                    }
                )
                return {
                    "status": "ok",
                    "message": response.text.strip(),
                    "host": self.host,
                    "port": self.port
                }
            else:
                error_msg = f"Health check returned HTTP {response.status_code}"
                return {
                    "status": "error",
                    "message": error_msg,
                    "host": self.host,
                    "port": self.port,
                    "http_status": response.status_code
                }
        except requests.exceptions.Timeout:
            error_msg = f"Health check to {self.base_url}/healthz timed out (connect: {self.connect_timeout}s, read: {self.read_timeout}s)"
            return {
                "status": "error",
                "message": error_msg,
                "error_type": "timeout",
                "host": self.host,
                "port": self.port,
                "connect_timeout": self.connect_timeout,
                "read_timeout": self.read_timeout
            }
        except requests.exceptions.ConnectionError:
            error_msg = f"Failed to connect to {self.base_url}/healthz"
            return {
                "status": "error",
                "message": error_msg,
                "error_type": "connection",
                "host": self.host,
                "port": self.port
            }
        except requests.exceptions.RequestException:
            error_msg = f"Request failed to {self.base_url}/healthz"
            return {
                "status": "error",
                "message": error_msg,
                "error_type": "request",
                "host": self.host,
                "port": self.port
            }

    # Removed stateful error tracking methods for thread safety
    # Errors are now logged and included in return values instead of stored state

    def create_collection(self, collection_name: str, vector_size: int, distance: str = "cosine") -> bool:
        """Create a new collection in Qdrant

        Args:
            collection_name: Name of the collection to create
            vector_size: Dimension of vectors to store
            distance: Distance metric ("cosine", "dot", "euclid")

        Returns:
            True if collection created successfully, False otherwise
        """
        # Validate parameters
        if not collection_name or collection_name.strip() == "":
            self.logger.error("Cannot create collection with empty name")
            return False

        if vector_size <= 0:
            self.logger.error(f"Invalid vector size: {vector_size}. Must be positive integer")
            return False

        if distance not in ["cosine", "dot", "euclid"]:
            self.logger.error(f"Invalid distance metric: {distance}. Must be 'cosine', 'dot', or 'euclid'")
            return False

        self.logger.debug(
            "Creating collection",
            extra={
                "collection_name": collection_name,
                "vector_size": vector_size,
                "distance": distance,
                "base_url": self.base_url
            }
        )

        # Prepare collection configuration
        collection_config = {
            "vectors": {
                "size": vector_size,
                "distance": distance.capitalize()  # Qdrant expects "Cosine", "Dot", "Euclid"
            }
        }

        try:
            # Create collection via Qdrant REST API
            response = self.session.put(
                f"{self.base_url}/collections/{collection_name}",
                json=collection_config,
                timeout=self.timeout_tuple
            )

            success = response.status_code in [200, 201]

            if success:
                self.logger.info(
                    "Collection created successfully",
                    extra={
                        "collection_name": collection_name,
                        "vector_size": vector_size,
                        "distance": distance,
                        "status_code": response.status_code
                    }
                )
            else:
                # Check if collection already exists (409 Conflict)
                if response.status_code == 409:
                    self.logger.warning(
                        "Collection already exists",
                        extra={
                            "collection_name": collection_name,
                            "status_code": response.status_code
                        }
                    )
                    return False
                else:
                    self.logger.error(
                        "Failed to create collection",
                        extra={
                            "collection_name": collection_name,
                            "status_code": response.status_code,
                            "response_text": response.text[:200]  # Truncate long responses
                        }
                    )

            return success

        except requests.exceptions.Timeout:
            self.logger.error(
                "Timeout creating collection",
                extra={
                    "collection_name": collection_name,
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(
                "Connection error creating collection",
                extra={
                    "collection_name": collection_name,
                    "base_url": self.base_url
                }
            )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Request error creating collection",
                extra={
                    "collection_name": collection_name,
                    "error": str(e)
                }
            )
            return False

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if collection exists, False otherwise
        """
        self.logger.debug(
            "Checking if collection exists",
            extra={
                "collection_name": collection_name,
                "base_url": self.base_url
            }
        )

        try:
            # Get collection info via Qdrant REST API
            response = self.session.get(
                f"{self.base_url}/collections/{collection_name}",
                timeout=self.timeout_tuple
            )

            exists = response.status_code == 200

            if exists:
                self.logger.debug(
                    "Collection exists",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code
                    }
                )
            else:
                if response.status_code == 404:
                    self.logger.debug(
                        "Collection does not exist",
                        extra={
                            "collection_name": collection_name,
                            "status_code": response.status_code
                        }
                    )
                else:
                    self.logger.warning(
                        "Unexpected status checking collection existence",
                        extra={
                            "collection_name": collection_name,
                            "status_code": response.status_code
                        }
                    )

            return exists

        except requests.exceptions.Timeout:
            self.logger.error(
                "Timeout checking collection existence",
                extra={
                    "collection_name": collection_name,
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(
                "Connection error checking collection existence",
                extra={
                    "collection_name": collection_name,
                    "base_url": self.base_url
                }
            )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Request error checking collection existence",
                extra={
                    "collection_name": collection_name,
                    "error": str(e)
                }
            )
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from Qdrant

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True if collection deleted successfully, False otherwise
        """
        self.logger.debug(
            "Deleting collection",
            extra={
                "collection_name": collection_name,
                "base_url": self.base_url
            }
        )

        try:
            # Delete collection via Qdrant REST API
            response = self.session.delete(
                f"{self.base_url}/collections/{collection_name}",
                timeout=self.timeout_tuple
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    # Qdrant returns {"result": true} if collection existed and was deleted
                    # {"result": false} if collection didn't exist
                    success = data.get("result", False)

                    if success:
                        self.logger.info(
                            "Collection deleted successfully",
                            extra={
                                "collection_name": collection_name,
                                "status_code": response.status_code
                            }
                        )
                    else:
                        self.logger.warning(
                            "Collection does not exist, cannot delete",
                            extra={
                                "collection_name": collection_name,
                                "status_code": response.status_code
                            }
                        )

                    return success

                except (ValueError, KeyError) as e:
                    self.logger.error(
                        "Error parsing delete response",
                        extra={
                            "collection_name": collection_name,
                            "response_text": response.text[:200],
                            "error": str(e)
                        }
                    )
                    return False
            else:
                self.logger.error(
                    "Failed to delete collection",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code,
                        "response_text": response.text[:200]  # Truncate long responses
                    }
                )
                return False

        except requests.exceptions.Timeout:
            self.logger.error(
                "Timeout deleting collection",
                extra={
                    "collection_name": collection_name,
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(
                "Connection error deleting collection",
                extra={
                    "collection_name": collection_name,
                    "base_url": self.base_url
                }
            )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Request error deleting collection",
                extra={
                    "collection_name": collection_name,
                    "error": str(e)
                }
            )
            return False

    def list_collections(self) -> List[str]:
        """List all collections in Qdrant

        Returns:
            List of collection names
        """
        self.logger.debug(
            "Listing all collections",
            extra={"base_url": self.base_url}
        )

        try:
            # Get collections list via Qdrant REST API
            response = self.session.get(
                f"{self.base_url}/collections",
                timeout=self.timeout_tuple
            )

            if response.status_code == 200:
                data = response.json()

                # Extract collection names from response
                # Qdrant API returns: {"result": {"collections": [{"name": "collection1"}, ...]}}
                collections = []
                if isinstance(data, dict) and "result" in data:
                    result = data["result"]
                    if isinstance(result, dict) and "collections" in result:
                        for collection_info in result["collections"]:
                            if isinstance(collection_info, dict) and "name" in collection_info:
                                collections.append(collection_info["name"])

                self.logger.info(
                    "Successfully listed collections",
                    extra={
                        "collection_count": len(collections),
                        "collections": collections[:10]  # Only log first 10 for brevity
                    }
                )

                return collections
            else:
                self.logger.error(
                    "Failed to list collections",
                    extra={
                        "status_code": response.status_code,
                        "response_text": response.text[:200]  # Truncate long responses
                    }
                )
                return []

        except requests.exceptions.Timeout:
            self.logger.error(
                "Timeout listing collections",
                extra={
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            return []
        except requests.exceptions.ConnectionError:
            self.logger.error(
                "Connection error listing collections",
                extra={"base_url": self.base_url}
            )
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Request error listing collections",
                extra={"error": str(e)}
            )
            return []
        except (ValueError, KeyError) as e:
            self.logger.error(
                "Error parsing collections response",
                extra={"error": str(e)}
            )
            return []

    def create_collection_strict(self, collection_name: str, vector_size: int, distance: str = "cosine") -> None:
        """Create a new collection in Qdrant with strict error handling

        Args:
            collection_name: Name of the collection to create
            vector_size: Dimension of vectors to store
            distance: Distance metric ("cosine", "dot", "euclid")

        Raises:
            ValueError: If parameters are invalid
            DatabaseTimeoutError: If operation times out
            DatabaseConnectionError: If connection fails
            DatabaseError: For other database-related errors
        """
        # Validate parameters
        if not collection_name or collection_name.strip() == "":
            raise ValueError("Cannot create collection with empty name")

        if vector_size <= 0:
            raise ValueError(f"Invalid vector size: {vector_size}. Must be positive integer")

        if distance not in ["cosine", "dot", "euclid"]:
            raise ValueError(f"Invalid distance metric: {distance}. Must be 'cosine', 'dot', or 'euclid'")

        self.logger.debug(
            "Creating collection (strict mode)",
            extra={
                "collection_name": collection_name,
                "vector_size": vector_size,
                "distance": distance,
                "base_url": self.base_url
            }
        )

        # Prepare collection configuration
        collection_config = {
            "vectors": {
                "size": vector_size,
                "distance": distance.capitalize()  # Qdrant expects "Cosine", "Dot", "Euclid"
            }
        }

        try:
            # Create collection via Qdrant REST API
            response = self.session.put(
                f"{self.base_url}/collections/{collection_name}",
                json=collection_config,
                timeout=self.timeout_tuple
            )

            if response.status_code in [200, 201]:
                self.logger.info(
                    "Collection created successfully (strict mode)",
                    extra={
                        "collection_name": collection_name,
                        "vector_size": vector_size,
                        "distance": distance,
                        "status_code": response.status_code
                    }
                )
            elif response.status_code == 409:
                # Collection already exists - this is a specific application error
                error_msg = f"Collection '{collection_name}' already exists"
                self.logger.error(error_msg)
                raise DatabaseError(error_msg)
            else:
                error_msg = f"Failed to create collection '{collection_name}': HTTP {response.status_code}"
                self.logger.error(
                    "Failed to create collection (strict mode)",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code,
                        "response_text": response.text[:200]
                    }
                )
                raise DatabaseError(error_msg)

        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout creating collection '{collection_name}' (connect: {self.connect_timeout}s, read: {self.read_timeout}s)"
            self.logger.error(
                "Timeout creating collection (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            raise DatabaseTimeoutError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error creating collection '{collection_name}'"
            self.logger.error(
                "Connection error creating collection (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "base_url": self.base_url
                }
            )
            raise DatabaseConnectionError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error creating collection '{collection_name}'"
            self.logger.error(
                "Request error creating collection (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "error": str(e)
                }
            )
            raise DatabaseError(error_msg) from e

    def collection_exists_strict(self, collection_name: str) -> bool:
        """Check if a collection exists with strict error handling

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if collection exists, False if it doesn't exist

        Raises:
            DatabaseTimeoutError: If operation times out
            DatabaseConnectionError: If connection fails
            DatabaseError: For other database-related errors
        """
        self.logger.debug(
            "Checking if collection exists (strict mode)",
            extra={
                "collection_name": collection_name,
                "base_url": self.base_url
            }
        )

        try:
            # Get collection info via Qdrant REST API
            response = self.session.get(
                f"{self.base_url}/collections/{collection_name}",
                timeout=self.timeout_tuple
            )

            if response.status_code == 200:
                self.logger.debug(
                    "Collection exists (strict mode)",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code
                    }
                )
                return True
            elif response.status_code == 404:
                self.logger.debug(
                    "Collection does not exist (strict mode)",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code
                    }
                )
                return False
            else:
                error_msg = f"Unexpected status checking collection existence: HTTP {response.status_code}"
                self.logger.error(
                    "Unexpected status checking collection existence (strict mode)",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code
                    }
                )
                raise DatabaseError(error_msg)

        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout checking collection existence for '{collection_name}' (connect: {self.connect_timeout}s, read: {self.read_timeout}s)"
            self.logger.error(
                "Timeout checking collection existence (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            raise DatabaseTimeoutError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error checking collection existence for '{collection_name}'"
            self.logger.error(
                "Connection error checking collection existence (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "base_url": self.base_url
                }
            )
            raise DatabaseConnectionError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error checking collection existence for '{collection_name}'"
            self.logger.error(
                "Request error checking collection existence (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "error": str(e)
                }
            )
            raise DatabaseError(error_msg) from e

    def delete_collection_strict(self, collection_name: str) -> None:
        """Delete a collection from Qdrant with strict error handling

        Args:
            collection_name: Name of the collection to delete

        Raises:
            DatabaseError: If collection doesn't exist or deletion fails
            DatabaseTimeoutError: If operation times out
            DatabaseConnectionError: If connection fails
        """
        self.logger.debug(
            "Deleting collection (strict mode)",
            extra={
                "collection_name": collection_name,
                "base_url": self.base_url
            }
        )

        # First check if collection exists for better error messages
        if not self.collection_exists_strict(collection_name):
            error_msg = f"Collection '{collection_name}' does not exist, cannot delete"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

        try:
            # Delete collection via Qdrant REST API
            response = self.session.delete(
                f"{self.base_url}/collections/{collection_name}",
                timeout=self.timeout_tuple
            )

            if response.status_code == 200:
                self.logger.info(
                    "Collection deleted successfully (strict mode)",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code
                    }
                )
            else:
                error_msg = f"Failed to delete collection '{collection_name}': HTTP {response.status_code}"
                self.logger.error(
                    "Failed to delete collection (strict mode)",
                    extra={
                        "collection_name": collection_name,
                        "status_code": response.status_code,
                        "response_text": response.text[:200]
                    }
                )
                raise DatabaseError(error_msg)

        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout deleting collection '{collection_name}' (connect: {self.connect_timeout}s, read: {self.read_timeout}s)"
            self.logger.error(
                "Timeout deleting collection (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            raise DatabaseTimeoutError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error deleting collection '{collection_name}'"
            self.logger.error(
                "Connection error deleting collection (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "base_url": self.base_url
                }
            )
            raise DatabaseConnectionError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error deleting collection '{collection_name}'"
            self.logger.error(
                "Request error deleting collection (strict mode)",
                extra={
                    "collection_name": collection_name,
                    "error": str(e)
                }
            )
            raise DatabaseError(error_msg) from e

    def list_collections_strict(self) -> List[str]:
        """List all collections in Qdrant with strict error handling

        Returns:
            List of collection names

        Raises:
            DatabaseTimeoutError: If operation times out
            DatabaseConnectionError: If connection fails
            DatabaseError: For other database-related errors
        """
        self.logger.debug(
            "Listing all collections (strict mode)",
            extra={"base_url": self.base_url}
        )

        try:
            # Get collections list via Qdrant REST API
            response = self.session.get(
                f"{self.base_url}/collections",
                timeout=self.timeout_tuple
            )

            if response.status_code == 200:
                try:
                    data = response.json()

                    # Extract collection names from response
                    # Qdrant API returns: {"result": {"collections": [{"name": "collection1"}, ...]}}
                    collections = []
                    if isinstance(data, dict) and "result" in data:
                        result = data["result"]
                        if isinstance(result, dict) and "collections" in result:
                            for collection_info in result["collections"]:
                                if isinstance(collection_info, dict) and "name" in collection_info:
                                    collections.append(collection_info["name"])

                    self.logger.info(
                        "Successfully listed collections (strict mode)",
                        extra={
                            "collection_count": len(collections),
                            "collections": collections[:10]  # Only log first 10 for brevity
                        }
                    )

                    return collections

                except (ValueError, KeyError) as e:
                    error_msg = f"Error parsing collections response: {e}"
                    self.logger.error(
                        "Error parsing collections response (strict mode)",
                        extra={"error": str(e)}
                    )
                    raise DatabaseError(error_msg) from e
            else:
                error_msg = f"Failed to list collections: HTTP {response.status_code}"
                self.logger.error(
                    "Failed to list collections (strict mode)",
                    extra={
                        "status_code": response.status_code,
                        "response_text": response.text[:200]
                    }
                )
                raise DatabaseError(error_msg)

        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout listing collections (connect: {self.connect_timeout}s, read: {self.read_timeout}s)"
            self.logger.error(
                "Timeout listing collections (strict mode)",
                extra={
                    "connect_timeout": self.connect_timeout,
                    "read_timeout": self.read_timeout
                }
            )
            raise DatabaseTimeoutError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = "Connection error listing collections"
            self.logger.error(
                "Connection error listing collections (strict mode)",
                extra={"base_url": self.base_url}
            )
            raise DatabaseConnectionError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error listing collections: {e}"
            self.logger.error(
                "Request error listing collections (strict mode)",
                extra={"error": str(e)}
            )
            raise DatabaseError(error_msg) from e

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection configuration information

        Returns:
            Dictionary with connection settings and pool status
        """
        return {
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "protocol": self.protocol,
            "api_key_configured": self.api_key is not None,  # Don't expose actual key
            "timeout": self.timeout,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "max_retries": self.max_retries,
            "pool_connections": self.pool_connections,
            "pool_maxsize": self.pool_maxsize,
            "session_active": hasattr(self, 'session') and self.session is not None
        }

    def close(self) -> None:
        """Close database connection and clean up session"""
        self.logger.debug("Closing database connection and session")

        # Close the session and its connection pool
        if hasattr(self, 'session'):
            self.session.close()
            self.logger.info(
                "Database session closed",
                extra={"base_url": self.base_url}
            )

        # Session cleanup handles all necessary resource deallocation

    def connect_strict(self) -> None:
        """Establish connection to database with strict error handling

        Raises:
            DatabaseTimeoutError: If connection times out
            DatabaseConnectionError: If connection fails
            DatabaseError: For other unexpected errors
        """
        self.logger.debug(
            "Attempting strict database connection",
            extra={"base_url": self.base_url, "timeout": self.timeout_tuple}
        )

        try:
            response = self.session.get(f"{self.base_url}/", timeout=self.timeout_tuple)
            if response.status_code != 200:
                raise DatabaseConnectionError(
                    f"Database connection failed with HTTP {response.status_code}"
                )

            self.logger.info(
                "Strict database connection successful",
                extra={"base_url": self.base_url, "status_code": response.status_code}
            )
        except requests.exceptions.Timeout as e:
            error_msg = f"Connection to {self.base_url} timed out (connect: {self.connect_timeout}s, read: {self.read_timeout}s)"
            self.logger.error(
                "Database connection timeout",
                extra={"base_url": self.base_url, "error": str(e)}
            )
            raise DatabaseTimeoutError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to {self.base_url}"
            self.logger.error(
                "Database connection error",
                extra={"base_url": self.base_url, "error": str(e)}
            )
            raise DatabaseConnectionError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed to {self.base_url}"
            self.logger.error(
                "Database request error",
                extra={"base_url": self.base_url, "error": str(e)}
            )
            raise DatabaseConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error connecting to {self.base_url}"
            self.logger.error(
                "Unexpected database connection error",
                extra={"base_url": self.base_url, "error": str(e)}
            )
            raise DatabaseError(error_msg) from e

    def health_check_strict(self) -> Dict[str, Any]:
        """Check database health status with strict error handling

        Returns:
            Dictionary with health status for successful checks

        Raises:
            DatabaseTimeoutError: If health check times out
            DatabaseHealthCheckError: If health check fails
            DatabaseConnectionError: If connection fails
        """
        self.logger.debug(
            "Performing strict database health check",
            extra={"base_url": self.base_url, "endpoint": "/healthz"}
        )

        try:
            response = self.session.get(f"{self.base_url}/healthz", timeout=self.timeout_tuple)
            if response.status_code == 200:
                self.logger.info(
                    "Strict database health check successful",
                    extra={"base_url": self.base_url, "status_code": response.status_code}
                )
                return {
                    "status": "ok",
                    "message": response.text.strip(),
                    "host": self.host,
                    "port": self.port
                }
            else:
                error_msg = f"Health check returned HTTP {response.status_code}"
                raise DatabaseHealthCheckError(error_msg)

        except requests.exceptions.Timeout as e:
            error_msg = f"Health check to {self.base_url}/healthz timed out (connect: {self.connect_timeout}s, read: {self.read_timeout}s)"
            raise DatabaseTimeoutError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to {self.base_url}/healthz"
            raise DatabaseConnectionError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed to {self.base_url}/healthz"
            raise DatabaseHealthCheckError(error_msg) from e
        except Exception as e:
            error_msg = "Unexpected error during health check"
            raise DatabaseError(error_msg) from e


class DatabaseConfig:
    """Configuration management for database settings

    Provides a unified interface for accessing database configuration
    with environment variable support and validation.
    """

    def __init__(self):
        """Initialize database configuration manager"""
        from duplicate_prevention.config import get_database_config
        self._config = get_database_config()

    @property
    def host(self) -> str:
        """Get database host"""
        return self._config["host"]

    @property
    def port(self) -> int:
        """Get database port"""
        return self._config["port"]

    @property
    def timeout(self) -> int:
        """Get connection timeout in seconds"""
        return self._config["timeout"]

    @property
    def collection_name(self) -> str:
        """Get default collection name for vectors"""
        return self._config["collection_name"]

    @property
    def vector_size(self) -> int:
        """Get vector embedding size"""
        return self._config["vector_size"]

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return self._config.copy()

    def get_connection_params(self) -> Dict[str, Any]:
        """Get parameters for DatabaseConnector initialization"""
        return {
            "host": self.host,
            "port": self.port,
            "timeout": self.timeout
        }


def get_health_status(host: Optional[str] = None, port: Optional[int] = None) -> Dict[str, Any]:
    """Quick health check function for database

    Args:
        host: Database host (defaults to config value)
        port: Database port (defaults to config value)

    Returns:
        Health status information
    """
    connector = DatabaseConnector(host=host, port=port)
    return connector.health_check()
