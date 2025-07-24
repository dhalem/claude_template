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
Test suite for Qdrant collection management functionality

This module tests collection operations including creating, listing,
checking existence, and deleting collections in Qdrant.

TDD RED Phase: All tests should initially FAIL with NotImplementedError
"""

import os
import sys

import pytest

# Add duplicate_prevention to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from duplicate_prevention.database import DatabaseConnector


class TestCollectionManagement:
    """Test suite for collection management operations

    Uses real Qdrant database connections - no mocks allowed.
    Tests will fail in RED phase until collection management is implemented.
    """

    @pytest.mark.integration
    def test_create_collection_success(self):
        """Test creating a new collection with default vector configuration"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_collection_create"

        # Clean up any existing collection
        try:
            connector.delete_collection(collection_name)
        except:
            pass  # Collection might not exist

        # This should succeed - create collection with 768-dimensional vectors (UniXcoder default)
        result = connector.create_collection(collection_name=collection_name, vector_size=768, distance="cosine")

        assert result is True

        # Verify collection was actually created
        assert connector.collection_exists(collection_name) is True

        # Clean up
        connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_create_collection_with_custom_config(self):
        """Test creating collection with custom vector configuration"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_collection_custom"

        # Clean up any existing collection
        try:
            connector.delete_collection(collection_name)
        except:
            pass

        # Create collection with custom configuration
        result = connector.create_collection(
            collection_name=collection_name,
            vector_size=512,  # Custom embedding size
            distance="dot",  # Dot product similarity
        )

        assert result is True
        assert connector.collection_exists(collection_name) is True

        # Clean up
        connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_create_collection_duplicate_name_fails(self):
        """Test that creating a collection with existing name fails gracefully"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_collection_duplicate"

        # Clean up any existing collection
        try:
            connector.delete_collection(collection_name)
        except:
            pass

        # Create collection first time - should succeed
        result1 = connector.create_collection(collection_name, vector_size=768)
        assert result1 is True

        # Create collection second time - should fail gracefully
        result2 = connector.create_collection(collection_name, vector_size=768)
        assert result2 is False

        # Clean up
        connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_create_collection_invalid_parameters_fails(self):
        """Test that invalid parameters cause create_collection to fail"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Test invalid vector size (must be positive)
        result1 = connector.create_collection("test_invalid", vector_size=0)
        assert result1 is False

        # Test invalid distance metric
        result2 = connector.create_collection("test_invalid", vector_size=768, distance="invalid")
        assert result2 is False

        # Test empty collection name
        result3 = connector.create_collection("", vector_size=768)
        assert result3 is False

    @pytest.mark.integration
    def test_create_collection_connection_failure(self):
        """Test create_collection handles connection failures gracefully"""
        # Use unreachable host
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        result = connector.create_collection("test_unreachable", vector_size=768)
        assert result is False

    def test_create_collection_returns_boolean(self):
        """Test create_collection method returns boolean result"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return boolean
        assert hasattr(connector, "create_collection")

        # Clean up any existing test collection
        try:
            connector.delete_collection("test_collection_boolean")
        except:
            pass

        # Test that method returns boolean (True for success)
        result = connector.create_collection("test_collection_boolean", vector_size=768)
        assert isinstance(result, bool)

        # Clean up
        connector.delete_collection("test_collection_boolean")


class TestCollectionExists:
    """Test suite for checking collection existence"""

    @pytest.mark.integration
    def test_collection_exists_true_for_existing_collection(self):
        """Test collection_exists returns True for existing collection"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_exists_true"

        # Create collection first
        connector.create_collection(collection_name, vector_size=768)

        # Check existence
        result = connector.collection_exists(collection_name)
        assert result is True

        # Clean up
        connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_collection_exists_false_for_nonexistent_collection(self):
        """Test collection_exists returns False for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Check non-existent collection
        result = connector.collection_exists("definitely_does_not_exist_12345")
        assert result is False

    @pytest.mark.integration
    def test_collection_exists_connection_failure(self):
        """Test collection_exists handles connection failures gracefully"""
        # Use unreachable host
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        result = connector.collection_exists("test_collection")
        assert result is False

    def test_collection_exists_returns_boolean(self):
        """Test collection_exists method returns boolean result"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return boolean
        assert hasattr(connector, "collection_exists")

        # Test that method returns boolean (False for non-existent collection)
        result = connector.collection_exists("definitely_does_not_exist_12345")
        assert isinstance(result, bool)
        assert result is False


class TestDeleteCollection:
    """Test suite for deleting collections"""

    @pytest.mark.integration
    def test_delete_collection_success(self):
        """Test successfully deleting an existing collection"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_delete_success"

        # Create collection first
        connector.create_collection(collection_name, vector_size=768)
        assert connector.collection_exists(collection_name) is True

        # Delete collection
        result = connector.delete_collection(collection_name)
        assert result is True

        # Verify collection is gone
        assert connector.collection_exists(collection_name) is False

    @pytest.mark.integration
    def test_delete_collection_nonexistent_fails_gracefully(self):
        """Test deleting non-existent collection fails gracefully"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Try to delete non-existent collection
        result = connector.delete_collection("definitely_does_not_exist_12345")
        assert result is False

    @pytest.mark.integration
    def test_delete_collection_connection_failure(self):
        """Test delete_collection handles connection failures gracefully"""
        # Use unreachable host
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        result = connector.delete_collection("test_collection")
        assert result is False

    def test_delete_collection_returns_boolean(self):
        """Test delete_collection method returns boolean result"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return boolean
        assert hasattr(connector, "delete_collection")

        # Test that method returns boolean (False for non-existent collection)
        result = connector.delete_collection("definitely_does_not_exist_12345")
        assert isinstance(result, bool)
        assert result is False


class TestListCollections:
    """Test suite for listing all collections"""

    @pytest.mark.integration
    def test_list_collections_returns_list(self):
        """Test list_collections returns a list of collection names"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Clean slate - create known collections
        test_collections = ["test_list_1", "test_list_2", "test_list_3"]

        # Clean up any existing test collections
        for collection in test_collections:
            try:
                connector.delete_collection(collection)
            except:
                pass

        # Create test collections
        for collection in test_collections:
            connector.create_collection(collection, vector_size=768)

        # List collections
        result = connector.list_collections()
        assert isinstance(result, list)

        # All our test collections should be in the list
        for collection in test_collections:
            assert collection in result

        # Clean up
        for collection in test_collections:
            connector.delete_collection(collection)

    @pytest.mark.integration
    def test_list_collections_empty_database(self):
        """Test list_collections returns empty list when no collections exist"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Delete all collections first (clean slate)
        existing = connector.list_collections()
        for collection in existing:
            connector.delete_collection(collection)

        # List should now be empty
        result = connector.list_collections()
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.integration
    def test_list_collections_connection_failure(self):
        """Test list_collections handles connection failures gracefully"""
        # Use unreachable host
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        result = connector.list_collections()
        assert isinstance(result, list)
        assert len(result) == 0  # Should return empty list on failure

    def test_list_collections_returns_list_type(self):
        """Test list_collections method returns list type"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return list
        assert hasattr(connector, "list_collections")

        # Test that method returns list type
        result = connector.list_collections()
        assert isinstance(result, list)


# TDD RED Phase Notes:
# - All tests should currently FAIL with NotImplementedError
# - @pytest.mark.integration marks tests that need real database
# - Tests define exact expected behavior for collection management
# - No mocks used - all tests use real Qdrant operations
# - GREEN phase will implement just enough to make these tests pass
# - Database installation already complete from A1.1 phase
