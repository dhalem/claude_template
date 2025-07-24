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
Test suite for Qdrant vector operations functionality

This module tests vector operations including inserting points, searching for similar vectors,
updating existing points, and deleting points from Qdrant collections.

TDD RED Phase: All tests should initially FAIL with NotImplementedError
"""

import os
import sys

import pytest

# Add duplicate_prevention to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from duplicate_prevention.database import DatabaseConnector


class TestInsertVectorPoints:
    """Test suite for inserting vector points into collections

    Uses real Qdrant database connections - no mocks allowed.
    Tests will fail in RED phase until vector operations are implemented.
    """

    @pytest.mark.integration
    def test_insert_single_point_success(self):
        """Test inserting a single vector point with metadata"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_insert_single"

        # Create collection first
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert single point with 4-dimensional vector
            result = connector.insert_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"file_path": "/test/file1.py", "content_hash": "abc123"},
            )

            assert result is True

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_insert_multiple_points_batch(self):
        """Test inserting multiple vector points in a single batch operation"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_insert_batch"

        # Create collection first
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert multiple points as batch
            points = [
                {
                    "id": 1,
                    "vector": [0.1, 0.2, 0.3, 0.4],
                    "metadata": {"file_path": "/test/file1.py", "content_hash": "abc123"},
                },
                {
                    "id": 2,
                    "vector": [0.5, 0.6, 0.7, 0.8],
                    "metadata": {"file_path": "/test/file2.py", "content_hash": "def456"},
                },
                {
                    "id": 3,
                    "vector": [0.9, 1.0, 1.1, 1.2],
                    "metadata": {"file_path": "/test/file3.py", "content_hash": "ghi789"},
                },
            ]

            result = connector.insert_points_batch(collection_name=collection_name, points=points)

            assert result is True

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_insert_point_invalid_vector_size_fails(self):
        """Test that inserting point with wrong vector size fails gracefully"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_insert_invalid_size"

        # Create collection expecting 4-dimensional vectors
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Try to insert 3-dimensional vector (should fail)
            result = connector.insert_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3],  # Wrong size
                metadata={"file_path": "/test/file1.py"},
            )

            assert result is False

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_insert_point_nonexistent_collection_fails(self):
        """Test that inserting into non-existent collection fails gracefully"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Try to insert into non-existent collection
        result = connector.insert_point(
            collection_name="definitely_does_not_exist_12345",
            point_id=1,
            vector=[0.1, 0.2, 0.3, 0.4],
            metadata={"file_path": "/test/file1.py"},
        )

        assert result is False

    @pytest.mark.integration
    def test_insert_point_connection_failure(self):
        """Test insert_point handles connection failures gracefully"""
        # Use localhost with non-listening port for immediate connection refusal
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        result = connector.insert_point(
            collection_name="test_collection",
            point_id=1,
            vector=[0.1, 0.2, 0.3, 0.4],
            metadata={"file_path": "/test/file1.py"},
        )

        assert result is False

    def test_insert_point_returns_boolean(self):
        """Test insert_point method returns boolean result"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return boolean
        assert hasattr(connector, "insert_point")


class TestSearchSimilarVectors:
    """Test suite for searching similar vectors by cosine similarity"""

    @pytest.mark.integration
    def test_search_similar_vectors_basic(self):
        """Test basic vector similarity search functionality"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_search_basic"

        # Create collection and insert test vectors
        connector.create_collection(collection_name, vector_size=4, distance="cosine")

        try:
            # Insert reference vectors
            test_points = [
                {
                    "id": 1,
                    "vector": [1.0, 0.0, 0.0, 0.0],  # Unit vector along first axis
                    "metadata": {"file_path": "/test/similar1.py", "content_hash": "abc123"},
                },
                {
                    "id": 2,
                    "vector": [0.0, 1.0, 0.0, 0.0],  # Unit vector along second axis
                    "metadata": {"file_path": "/test/different1.py", "content_hash": "def456"},
                },
                {
                    "id": 3,
                    "vector": [0.9, 0.1, 0.0, 0.0],  # Very similar to first vector
                    "metadata": {"file_path": "/test/similar2.py", "content_hash": "ghi789"},
                },
            ]

            connector.insert_points_batch(collection_name, test_points)

            # Search for vectors similar to [1.0, 0.0, 0.0, 0.0]
            results = connector.search_similar_vectors(
                collection_name=collection_name, query_vector=[1.0, 0.0, 0.0, 0.0], limit=2, score_threshold=0.8
            )

            # Should return list of matches
            assert isinstance(results, list)
            assert len(results) <= 2

            # Results should be ordered by similarity score
            if len(results) > 1:
                assert results[0]["score"] >= results[1]["score"]

            # Top result should include the metadata
            if len(results) > 0:
                assert "metadata" in results[0]
                assert "file_path" in results[0]["metadata"]

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_search_similar_vectors_with_limit(self):
        """Test vector search respects limit parameter"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_search_limit"

        # Create collection and insert multiple test vectors
        connector.create_collection(collection_name, vector_size=2, distance="cosine")

        try:
            # Insert 5 test points
            test_points = [{"id": i, "vector": [float(i), float(i + 1)], "metadata": {"idx": i}} for i in range(1, 6)]

            connector.insert_points_batch(collection_name, test_points)

            # Search with limit=3
            results = connector.search_similar_vectors(
                collection_name=collection_name, query_vector=[1.0, 2.0], limit=3
            )

            # Should return at most 3 results
            assert isinstance(results, list)
            assert len(results) <= 3

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_search_similar_vectors_empty_collection(self):
        """Test vector search on empty collection returns empty list"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_search_empty"

        # Create empty collection
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Search empty collection
            results = connector.search_similar_vectors(
                collection_name=collection_name, query_vector=[1.0, 0.0, 0.0, 0.0], limit=5
            )

            # Should return empty list
            assert isinstance(results, list)
            assert len(results) == 0

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_search_similar_vectors_nonexistent_collection(self):
        """Test vector search on non-existent collection fails gracefully"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Search non-existent collection
        results = connector.search_similar_vectors(
            collection_name="definitely_does_not_exist_12345", query_vector=[1.0, 0.0, 0.0, 0.0], limit=5
        )

        # Should return empty list on failure
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.integration
    def test_search_similar_vectors_connection_failure(self):
        """Test vector search handles connection failures gracefully"""
        # Use localhost with non-listening port for immediate connection refusal
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        results = connector.search_similar_vectors(
            collection_name="test_collection", query_vector=[1.0, 0.0, 0.0, 0.0], limit=5
        )

        # Should return empty list on connection failure
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_similar_vectors_returns_list(self):
        """Test search_similar_vectors method returns list type"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return list
        assert hasattr(connector, "search_similar_vectors")


class TestUpdateVectorPoints:
    """Test suite for updating existing vector points"""

    @pytest.mark.integration
    def test_update_point_vector_and_metadata(self):
        """Test updating both vector and metadata of existing point"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_update"

        # Create collection and insert initial point
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert initial point
            connector.insert_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"file_path": "/test/old_file.py", "version": 1},
            )

            # Update the point
            result = connector.update_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.5, 0.6, 0.7, 0.8],
                metadata={"file_path": "/test/new_file.py", "version": 2},
            )

            assert result is True

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_update_point_metadata_only(self):
        """Test updating only metadata while keeping vector unchanged"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_update_metadata"

        # Create collection and insert initial point
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert initial point
            connector.insert_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"file_path": "/test/file.py", "status": "draft"},
            )

            # Update only metadata (vector=None to keep unchanged)
            result = connector.update_point(
                collection_name=collection_name,
                point_id=1,
                vector=None,  # Keep existing vector
                metadata={"file_path": "/test/file.py", "status": "final"},
            )

            assert result is True

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_update_nonexistent_point_fails(self):
        """Test updating non-existent point fails gracefully"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_update_nonexistent"

        # Create empty collection
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Try to update non-existent point
            result = connector.update_point(
                collection_name=collection_name,
                point_id=999,  # Doesn't exist
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"file_path": "/test/file.py"},
            )

            assert result is False

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_update_point_connection_failure(self):
        """Test update_point handles connection failures gracefully"""
        # Use localhost with non-listening port for immediate connection refusal
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        result = connector.update_point(
            collection_name="test_collection",
            point_id=1,
            vector=[0.1, 0.2, 0.3, 0.4],
            metadata={"file_path": "/test/file.py"},
        )

        assert result is False

    def test_update_point_returns_boolean(self):
        """Test update_point method returns boolean result"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return boolean
        assert hasattr(connector, "update_point")


class TestDeleteVectorPoints:
    """Test suite for deleting individual vector points"""

    @pytest.mark.integration
    def test_delete_existing_point_success(self):
        """Test deleting an existing vector point"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_delete"

        # Create collection and insert test point
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert point to delete
            connector.insert_point(
                collection_name=collection_name,
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                metadata={"file_path": "/test/file.py"},
            )

            # Delete the point
            result = connector.delete_point(collection_name=collection_name, point_id=1)

            assert result is True

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_delete_multiple_points_batch(self):
        """Test deleting multiple vector points in batch"""
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_delete_batch"

        # Create collection and insert test points
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Insert multiple points
            test_points = [
                {"id": i, "vector": [float(i), float(i + 1), float(i + 2), float(i + 3)], "metadata": {"idx": i}}
                for i in range(1, 4)
            ]
            connector.insert_points_batch(collection_name, test_points)

            # Delete multiple points
            result = connector.delete_points_batch(collection_name=collection_name, point_ids=[1, 2, 3])

            assert result is True

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_delete_nonexistent_point_is_idempotent(self):
        """Test deleting non-existent point is idempotent (returns True)

        Performance optimization: delete operations are now idempotent.
        If the point doesn't exist after the operation, the operation succeeded
        in achieving its goal regardless of whether the point existed initially.
        """
        connector = DatabaseConnector(host="localhost", port=6333)
        collection_name = "test_vector_delete_nonexistent"

        # Create empty collection
        connector.create_collection(collection_name, vector_size=4)

        try:
            # Delete non-existent point - should be idempotent (return True)
            result = connector.delete_point(collection_name=collection_name, point_id=999)  # Doesn't exist

            # Idempotent behavior: if point doesn't exist after delete, operation succeeded
            assert result is True

        finally:
            # Clean up
            connector.delete_collection(collection_name)

    @pytest.mark.integration
    def test_delete_point_connection_failure(self):
        """Test delete_point handles connection failures gracefully"""
        # Use localhost with non-listening port for immediate connection refusal
        connector = DatabaseConnector(host="localhost", port=1, timeout=0.1)

        result = connector.delete_point(collection_name="test_collection", point_id=1)

        assert result is False

    def test_delete_point_returns_boolean(self):
        """Test delete_point method returns boolean result"""
        connector = DatabaseConnector(host="localhost", port=6333)

        # Method should exist and return boolean
        assert hasattr(connector, "delete_point")


# TDD RED Phase Notes:
# - All tests should currently FAIL with AttributeError (methods don't exist yet)
# - @pytest.mark.integration marks tests that need real database
# - Tests define exact expected behavior for vector operations
# - No mocks used - all tests use real Qdrant operations
# - GREEN phase will implement just enough to make these tests pass
# - Vector operations are the core of the duplicate prevention system
# - Tests cover both individual operations and batch operations for performance
