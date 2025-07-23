# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Configuration management for duplicate prevention system

This module provides configuration settings and environment management
for the duplicate prevention system components.
"""

import os
from typing import Any, Dict

# Default configuration values
DEFAULT_CONFIG = {
    "database": {
        "host": "localhost",
        "port": 6333,
        "timeout": 30,
        "protocol": "http",  # TODO: Change to HTTPS when Qdrant supports TLS in docker-compose
        "api_key": None,  # Should be set via environment variable
        "collection_name": "code_vectors",
        "vector_size": 768  # UniXcoder embedding size
    },
    "similarity": {
        "threshold": 0.65,
        "max_results": 5
    },
    "performance": {
        "max_response_time_ms": 200,
        "max_concurrent_requests": 50
    }
}


def get_database_config() -> Dict[str, Any]:
    """Get database configuration with environment variable overrides

    Returns:
        Dictionary with database configuration
    """
    config = DEFAULT_CONFIG["database"].copy()

    # Allow environment variable overrides
    if os.getenv("QDRANT_HOST"):
        config["host"] = os.getenv("QDRANT_HOST")
    if os.getenv("QDRANT_PORT"):
        config["port"] = int(os.getenv("QDRANT_PORT"))
    if os.getenv("QDRANT_TIMEOUT"):
        config["timeout"] = int(os.getenv("QDRANT_TIMEOUT"))

    # Security configuration
    if os.getenv("QDRANT_PROTOCOL"):
        config["protocol"] = os.getenv("QDRANT_PROTOCOL")
    if os.getenv("QDRANT_API_KEY"):
        config["api_key"] = os.getenv("QDRANT_API_KEY")

    return config


def get_full_config() -> Dict[str, Any]:
    """Get complete configuration for duplicate prevention system

    Returns:
        Complete configuration dictionary
    """
    return DEFAULT_CONFIG.copy()
