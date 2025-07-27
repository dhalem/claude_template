#!/usr/bin/env python3
"""Test search_similar_vectors on empty collection."""

import sys

sys.path.insert(0, "/home/dhalem/.claude/python")

from duplicate_prevention.database import DatabaseConnector
from duplicate_prevention.embedding_generator import EmbeddingGenerator

print("Testing search on empty collection...")

# Create components
db = DatabaseConnector(host="localhost", port=6333)
embed_gen = EmbeddingGenerator()

# Generate a test embedding
result = embed_gen.generate_embedding("def test(): pass", "python")
embedding = result["embedding"]

print(f"✓ Generated embedding with {len(embedding)} dimensions")

# Search in empty collection
collection_name = "claude_template_duplicate_prevention"
similar_results = db.search_similar_vectors(collection_name=collection_name, query_vector=embedding, limit=5)

print(f"✓ Search results: {similar_results}")
print(f"✓ Search results type: {type(similar_results)}")
print(f"✓ Search results length: {len(similar_results) if similar_results else 'None'}")
print(f"✓ Search results bool: {bool(similar_results)}")

print("Search test complete.")
