# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Test suite for Qdrant collection management strict functionality

This module tests collection operations with strict error handling,
including creating, listing, checking existence, and deleting collections in Qdrant.
These methods raise specific exceptions instead of returning False/empty values.
"""

import os
import sys

import pytest

# Add duplicate_prevention to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from duplicate_prevention.database import (
    DatabaseConnectionError,
    DatabaseConnector,
    DatabaseError,
    DatabaseTimeoutError,
)


class TestCreateCollectionStrict:
    """Test suite for create_collection_strict method"""

    @pytest.mark.integration
    def test_create_collection_strict_success(self):
        """Test creating a new collection with strict error handling"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_strict_create"

        # Clean up any existing collection
        try:
            connector.delete_collection(collection_name)
        except:
            pass

        # This should succeed and not return anything (void method)
        result = connector.create_collection_strict(collection_name=collection_name, vector_size=768, distance="cosine")

        # Method returns None on success
        assert result is None

        # Verify collection was actually created
        assert connector.collection_exists(collection_name) is True

        # Clean up
        connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_create_collection_strict_duplicate_raises_error(self):
        """Test that creating a collection with existing name raises DatabaseError"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_strict_duplicate"

        # Clean up any existing collection
        try:
            connector.delete_collection(collection_name)
        except:
            pass

        # Create collection first time - should succeed
        connector.create_collection_strict(collection_name, vector_size=768)

        # Create collection second time - should raise DatabaseError
        with pytest.raises(DatabaseError) as exc_info:
            connector.create_collection_strict(collection_name, vector_size=768)

        assert "already exists" in str(exc_info.value)

        # Clean up
        connector.delete_collection(collection_name)

    def test_create_collection_strict_invalid_parameters_raises_valueerror(self):
        """Test that invalid parameters raise ValueError"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Test invalid vector size (must be positive)
        with pytest.raises(ValueError) as exc_info:
            connector.create_collection_strict("test_invalid", vector_size=0)
        assert "positive integer" in str(exc_info.value)

        # Test invalid distance metric
        with pytest.raises(ValueError) as exc_info:
            connector.create_collection_strict("test_invalid", vector_size=768, distance="invalid")
        assert "Must be 'cosine', 'dot', or 'euclid'" in str(exc_info.value)

        # Test empty collection name
        with pytest.raises(ValueError) as exc_info:
            connector.create_collection_strict("", vector_size=768)
        assert "empty name" in str(exc_info.value)

    @pytest.mark.integration
    def test_create_collection_strict_connection_failure_raises_error(self):
        """Test create_collection_strict raises DatabaseConnectionError on connection failure"""
        # Use unreachable host
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises((DatabaseConnectionError, DatabaseTimeoutError)) as exc_info:
            connector.create_collection_strict("test_unreachable", vector_size=768)

        # Either timeout or connection error is acceptable for unreachable host
        assert any(word in str(exc_info.value) for word in ["Timeout", "Connection error"])


class TestCollectionExistsStrict:
    """Test suite for collection_exists_strict method"""

    @pytest.mark.integration
    def test_collection_exists_strict_true_for_existing_collection(self):
        """Test collection_exists_strict returns True for existing collection"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_strict_exists_true"

        # Create collection first
        connector.create_collection(collection_name, vector_size=768)

        # Check existence with strict method
        result = connector.collection_exists_strict(collection_name)
        assert result is True

        # Clean up
        connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_collection_exists_strict_false_for_nonexistent_collection(self):
        """Test collection_exists_strict returns False for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Check non-existent collection
        result = connector.collection_exists_strict("definitely_does_not_exist_strict_12345")
        assert result is False

    @pytest.mark.integration
    def test_collection_exists_strict_connection_failure_raises_error(self):
        """Test collection_exists_strict raises DatabaseConnectionError on connection failure"""
        # Use unreachable host
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises((DatabaseConnectionError, DatabaseTimeoutError)) as exc_info:
            connector.collection_exists_strict("test_collection")

        # Either timeout or connection error is acceptable for unreachable host
        assert any(word in str(exc_info.value) for word in ["Timeout", "Connection error"])


class TestDeleteCollectionStrict:
    """Test suite for delete_collection_strict method"""

    @pytest.mark.integration
    def test_delete_collection_strict_success(self):
        """Test successfully deleting an existing collection with strict handling"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_strict_delete_success"

        # Create collection first
        connector.create_collection(collection_name, vector_size=768)
        assert connector.collection_exists(collection_name) is True

        # Delete collection with strict method (returns None on success)
        result = connector.delete_collection_strict(collection_name)
        assert result is None

        # Verify collection is gone
        assert connector.collection_exists(collection_name) is False

    @pytest.mark.integration
    def test_delete_collection_strict_nonexistent_raises_error(self):
        """Test deleting non-existent collection raises DatabaseError"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Try to delete non-existent collection
        with pytest.raises(DatabaseError) as exc_info:
            connector.delete_collection_strict("definitely_does_not_exist_strict_12345")

        assert "does not exist" in str(exc_info.value)

    @pytest.mark.integration
    def test_delete_collection_strict_connection_failure_raises_error(self):
        """Test delete_collection_strict raises DatabaseConnectionError on connection failure"""
        # Use unreachable host
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises((DatabaseConnectionError, DatabaseTimeoutError)) as exc_info:
            connector.delete_collection_strict("test_collection")

        # Either timeout or connection error is acceptable for unreachable host
        assert any(word in str(exc_info.value) for word in ["Timeout", "Connection error"])


class TestListCollectionsStrict:
    """Test suite for list_collections_strict method"""

    @pytest.mark.integration
    def test_list_collections_strict_returns_list(self):
        """Test list_collections_strict returns a list of collection names"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Clean slate - create known collections
        test_collections = ["test_strict_list_1", "test_strict_list_2", "test_strict_list_3"]

        # Clean up any existing test collections
        for collection in test_collections:
            try:
                connector.delete_collection(collection)
            except:
                pass

        # Create test collections
        for collection in test_collections:
            connector.create_collection(collection, vector_size=768)

        # List collections with strict method
        result = connector.list_collections_strict()
        assert isinstance(result, list)

        # All our test collections should be in the list
        for collection in test_collections:
            assert collection in result

        # Clean up
        for collection in test_collections:
            connector.delete_collection(collection)

    @pytest.mark.integration
    def test_list_collections_strict_empty_database(self):
        """Test list_collections_strict returns empty list when no collections exist"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Delete all collections first (clean slate)
        existing = connector.list_collections()
        for collection in existing:
            connector.delete_collection(collection)

        # List should now be empty
        result = connector.list_collections_strict()
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.integration
    def test_list_collections_strict_connection_failure_raises_error(self):
        """Test list_collections_strict raises DatabaseConnectionError on connection failure"""
        # Use unreachable host
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises((DatabaseConnectionError, DatabaseTimeoutError)) as exc_info:
            connector.list_collections_strict()

        # Either timeout or connection error is acceptable for unreachable host
        assert any(word in str(exc_info.value) for word in ["Timeout", "Connection error"])


# TDD Notes for Strict Methods:
# - These tests verify that strict methods provide clear error disambiguation
# - Success cases return specific values (None for void methods, bool/list for queries)
# - Failure cases raise specific exceptions (ValueError, DatabaseError, etc.)
# - No ambiguous return values - callers can handle specific error conditions
# - All tests use real Qdrant database for integration testing
