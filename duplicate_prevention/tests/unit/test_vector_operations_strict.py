# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Test suite for strict vector operations that raise exceptions instead of returning False

This module tests the strict versions of vector operations that provide clear error
disambiguation through specific exception types (ValueError, DatabaseError,
DatabaseConnectionError, DatabaseTimeoutError) instead of returning False for all errors.
"""

import os
import sys

import pytest

# Add duplicate_prevention to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from duplicate_prevention.database import DatabaseConnectionError, DatabaseConnector, DatabaseError


class TestInsertVectorPointsStrict:
    """Test suite for strict insert_point operations that raise exceptions"""

    @pytest.mark.integration
    def test_insert_point_strict_success(self):
        """Test successful strict point insertion"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_insert_strict_success"

        # Create collection first
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert single point - should not raise exception
            connector.insert_point_strict(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"file_path": "/test/file1.py", "content_hash": "abc123"}
            )

            # Verify point was inserted
            results = connector.search_similar_vectors(
                collection_name=collection_name,
                query_vector=[0.1, 0.2, 0.3, 0.4],
                limit=1
            )
            assert len(results) == 1
            assert results[0]["id"] == 1

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_insert_point_strict_empty_collection_name(self):
        """Test insert_point_strict raises ValueError for empty collection name"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.insert_point_strict(
                collection_name="",
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"test": "data"}
            )

        assert "empty collection name" in str(exc_info.value)

    @pytest.mark.integration
    def test_insert_point_strict_invalid_point_id(self):
        """Test insert_point_strict raises ValueError for invalid point ID"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Test negative ID
        with pytest.raises(ValueError) as exc_info:
            connector.insert_point_strict(
                collection_name="test_collection",
                point_id=-1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"test": "data"}
            )

        assert "Invalid point ID" in str(exc_info.value)

    @pytest.mark.integration
    def test_insert_point_strict_invalid_vector(self):
        """Test insert_point_strict raises ValueError for invalid vector"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Test empty vector
        with pytest.raises(ValueError) as exc_info:
            connector.insert_point_strict(
                collection_name="test_collection",
                point_id=1,
                vector=[],
                metadata={"test": "data"}
            )

        assert "Invalid vector data" in str(exc_info.value)

    @pytest.mark.integration
    def test_insert_point_strict_nonexistent_collection(self):
        """Test insert_point_strict raises DatabaseError for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(DatabaseError) as exc_info:
            connector.insert_point_strict(
                collection_name="definitely_does_not_exist_12345",
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"test": "data"}
            )

        assert "does not exist" in str(exc_info.value)

    @pytest.mark.integration
    def test_insert_point_strict_connection_failure(self):
        """Test insert_point_strict raises DatabaseConnectionError on connection failure"""
        # Use unreachable host
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises(DatabaseConnectionError) as exc_info:
            connector.insert_point_strict(
                collection_name="test_collection",
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"test": "data"}
            )

        assert "Connection error" in str(exc_info.value)


class TestInsertPointsBatchStrict:
    """Test suite for strict insert_points_batch operations"""

    @pytest.mark.integration
    def test_insert_points_batch_strict_success(self):
        """Test successful strict batch point insertion"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_batch_strict_success"

        # Create collection first
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert multiple points - should not raise exception
            points = [
                {
                    "id": 1,
                    "vector": [0.1, 0.2, 0.3, 0.4],
                    "metadata": {"file_path": "/test/file1.py"}
                },
                {
                    "id": 2,
                    "vector": [0.5, 0.6, 0.7, 0.8],
                    "metadata": {"file_path": "/test/file2.py"}
                }
            ]

            connector.insert_points_batch_strict(
                collection_name=collection_name,
                points=points
            )

            # Verify points were inserted
            results = connector.search_similar_vectors(
                collection_name=collection_name,
                query_vector=[0.1, 0.2, 0.3, 0.4],
                limit=10
            )
            assert len(results) >= 2

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_insert_points_batch_strict_empty_points(self):
        """Test insert_points_batch_strict raises ValueError for empty points list"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.insert_points_batch_strict(
                collection_name="test_collection",
                points=[]
            )

        assert "non-empty list" in str(exc_info.value)

    @pytest.mark.integration
    def test_insert_points_batch_strict_invalid_point_format(self):
        """Test insert_points_batch_strict raises ValueError for invalid point format"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Missing 'id' field
        with pytest.raises(ValueError) as exc_info:
            connector.insert_points_batch_strict(
                collection_name="test_collection",
                points=[{"vector": [0.1, 0.2, 0.3, 0.4]}]
            )

        assert "missing required 'id' field" in str(exc_info.value)

        # Missing 'vector' field
        with pytest.raises(ValueError) as exc_info:
            connector.insert_points_batch_strict(
                collection_name="test_collection",
                points=[{"id": 1}]
            )

        assert "missing required 'vector' field" in str(exc_info.value)

    @pytest.mark.integration
    def test_insert_points_batch_strict_nonexistent_collection(self):
        """Test insert_points_batch_strict raises DatabaseError for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        points = [{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4]}]

        with pytest.raises(DatabaseError) as exc_info:
            connector.insert_points_batch_strict(
                collection_name="definitely_does_not_exist_12345",
                points=points
            )

        assert "does not exist" in str(exc_info.value)


class TestSearchSimilarVectorsStrict:
    """Test suite for strict search_similar_vectors operations"""

    @pytest.mark.integration
    def test_search_similar_vectors_strict_success(self):
        """Test successful strict vector search"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_search_strict_success"

        # Create collection and insert test data
        connector.create_collection(collection_name, vector_size=4, distance="cosine")

        try:
            # Insert test vectors
            test_points = [
                {
                    "id": 1,
                    "vector": [1.0, 0.0, 0.0, 0.0],
                    "metadata": {"file_path": "/test/file1.py"}
                },
                {
                    "id": 2,
                    "vector": [0.9, 0.1, 0.0, 0.0],
                    "metadata": {"file_path": "/test/file2.py"}
                }
            ]
            connector.insert_points_batch(collection_name, test_points)

            # Search - should not raise exception
            results = connector.search_similar_vectors_strict(
                collection_name=collection_name,
                query_vector=[1.0, 0.0, 0.0, 0.0],
                limit=2
            )

            assert isinstance(results, list)
            assert len(results) <= 2

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_search_similar_vectors_strict_empty_collection_name(self):
        """Test search_similar_vectors_strict raises ValueError for empty collection name"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.search_similar_vectors_strict(
                collection_name="",
                query_vector=[1.0, 0.0, 0.0, 0.0],
                limit=5
            )

        assert "empty collection name" in str(exc_info.value)

    @pytest.mark.integration
    def test_search_similar_vectors_strict_invalid_query_vector(self):
        """Test search_similar_vectors_strict raises ValueError for invalid query vector"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.search_similar_vectors_strict(
                collection_name="test_collection",
                query_vector=[],
                limit=5
            )

        assert "non-empty list" in str(exc_info.value)

    @pytest.mark.integration
    def test_search_similar_vectors_strict_invalid_limit(self):
        """Test search_similar_vectors_strict raises ValueError for invalid limit"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.search_similar_vectors_strict(
                collection_name="test_collection",
                query_vector=[1.0, 0.0, 0.0, 0.0],
                limit=0
            )

        assert "Limit must be positive" in str(exc_info.value)

    @pytest.mark.integration
    def test_search_similar_vectors_strict_nonexistent_collection(self):
        """Test search_similar_vectors_strict raises DatabaseError for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(DatabaseError) as exc_info:
            connector.search_similar_vectors_strict(
                collection_name="definitely_does_not_exist_12345",
                query_vector=[1.0, 0.0, 0.0, 0.0],
                limit=5
            )

        assert "does not exist" in str(exc_info.value)


class TestUpdateVectorPointsStrict:
    """Test suite for strict update_point operations"""

    @pytest.mark.integration
    def test_update_point_strict_success(self):
        """Test successful strict point update"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_update_strict_success"

        # Create collection and insert initial point
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert initial point
            connector.insert_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"version": 1}
            )

            # Update the point - should not raise exception
            connector.update_point_strict(
                collection_name=collection_name,
                point_id=1,
                vector=[0.5, 0.6, 0.7, 0.8],
                metadata={"version": 2}
            )

            # Verify update
            results = connector.search_similar_vectors(
                collection_name=collection_name,
                query_vector=[0.5, 0.6, 0.7, 0.8],
                limit=1
            )
            assert len(results) == 1
            assert results[0]["metadata"]["version"] == 2

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_update_point_strict_empty_collection_name(self):
        """Test update_point_strict raises ValueError for empty collection name"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.update_point_strict(
                collection_name="",
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4]
            )

        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.integration
    def test_update_point_strict_no_updates(self):
        """Test update_point_strict raises ValueError when neither vector nor metadata provided"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.update_point_strict(
                collection_name="test_collection",
                point_id=1,
                vector=None,
                metadata=None
            )

        assert "At least one of vector or metadata must be provided" in str(exc_info.value)

    @pytest.mark.integration
    def test_update_point_strict_nonexistent_point(self):
        """Test update_point_strict raises DatabaseError for non-existent point"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_update_strict_nonexistent"

        # Create empty collection
        connector.create_collection(collection_name, vector_size=4)

        try:
            with pytest.raises(DatabaseError) as exc_info:
                connector.update_point_strict(
                    collection_name=collection_name,
                    point_id=999,
                    vector=[0.1, 0.2, 0.3, 0.4]
                )

            assert "does not exist" in str(exc_info.value)

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_update_point_strict_nonexistent_collection(self):
        """Test update_point_strict raises DatabaseError for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(DatabaseError) as exc_info:
            connector.update_point_strict(
                collection_name="definitely_does_not_exist_12345",
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4]
            )

        assert "does not exist" in str(exc_info.value)


class TestDeleteVectorPointsStrict:
    """Test suite for strict delete_point operations"""

    @pytest.mark.integration
    def test_delete_point_strict_success(self):
        """Test successful strict point deletion"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_delete_strict_success"

        # Create collection and insert test point
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert point to delete
            connector.insert_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"test": "data"}
            )

            # Delete the point - should not raise exception
            connector.delete_point_strict(
                collection_name=collection_name,
                point_id=1
            )

            # Verify deletion
            results = connector.search_similar_vectors(
                collection_name=collection_name,
                query_vector=[0.1, 0.2, 0.3, 0.4],
                limit=1
            )
            assert len(results) == 0

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_delete_point_strict_idempotent(self):
        """Test delete_point_strict is idempotent - no error for non-existent point"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_delete_strict_idempotent"

        # Create empty collection
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Delete non-existent point - should not raise exception (idempotent)
            connector.delete_point_strict(
                collection_name=collection_name,
                point_id=999
            )

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_delete_point_strict_empty_collection_name(self):
        """Test delete_point_strict raises ValueError for empty collection name"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.delete_point_strict(
                collection_name="",
                point_id=1
            )

        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.integration
    def test_delete_point_strict_nonexistent_collection(self):
        """Test delete_point_strict raises DatabaseError for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(DatabaseError) as exc_info:
            connector.delete_point_strict(
                collection_name="definitely_does_not_exist_12345",
                point_id=1
            )

        assert "does not exist" in str(exc_info.value)


class TestDeletePointsBatchStrict:
    """Test suite for strict delete_points_batch operations"""

    @pytest.mark.integration
    def test_delete_points_batch_strict_success(self):
        """Test successful strict batch point deletion"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_delete_batch_strict_success"

        # Create collection and insert test points
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert points to delete
            test_points = [
                {"id": i, "vector": [float(i), float(i+1), float(i+2), float(i+3)]}
                for i in range(1, 4)
            ]
            connector.insert_points_batch(collection_name, test_points)

            # Delete multiple points - should not raise exception
            connector.delete_points_batch_strict(
                collection_name=collection_name,
                point_ids=[1, 2, 3]
            )

            # Verify deletion
            results = connector.search_similar_vectors(
                collection_name=collection_name,
                query_vector=[1.0, 2.0, 3.0, 4.0],
                limit=10
            )
            assert len(results) == 0

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_delete_points_batch_strict_empty_ids(self):
        """Test delete_points_batch_strict raises ValueError for empty IDs list"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.delete_points_batch_strict(
                collection_name="test_collection",
                point_ids=[]
            )

        assert "non-empty list" in str(exc_info.value)

    @pytest.mark.integration
    def test_delete_points_batch_strict_invalid_ids(self):
        """Test delete_points_batch_strict raises ValueError for invalid IDs"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(ValueError) as exc_info:
            connector.delete_points_batch_strict(
                collection_name="test_collection",
                point_ids=[1, -5, 3]
            )

        assert "Invalid point ID at index 1" in str(exc_info.value)

    @pytest.mark.integration
    def test_delete_points_batch_strict_nonexistent_collection(self):
        """Test delete_points_batch_strict raises DatabaseError for non-existent collection"""
        connector = DatabaseConnector(host="localhost", port=6333)

        with pytest.raises(DatabaseError) as exc_info:
            connector.delete_points_batch_strict(
                collection_name="definitely_does_not_exist_12345",
                point_ids=[1, 2, 3]
            )

        assert "does not exist" in str(exc_info.value)

    @pytest.mark.integration
    def test_delete_points_batch_strict_connection_failure(self):
        """Test delete_points_batch_strict raises DatabaseConnectionError on connection failure"""
        # Use unreachable host
        connector = DatabaseConnector(host="192.0.2.1", port=6333, timeout=1)

        with pytest.raises(DatabaseConnectionError) as exc_info:
            connector.delete_points_batch_strict(
                collection_name="test_collection",
                point_ids=[1, 2, 3]
            )

        assert "Connection error" in str(exc_info.value)


# TDD GREEN Phase Notes:
# - All strict vector operation methods implemented with proper exception handling
# - Tests verify successful operations and all error scenarios
# - Clear error disambiguation through specific exception types
# - Maintains backward compatibility with original non-strict methods
# - Addresses MCP reviewer feedback on API ambiguity
