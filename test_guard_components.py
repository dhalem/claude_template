#!/usr/bin/env python3
"""Test duplicate prevention guard components."""

import sys

# Add hook path for imports
sys.path.insert(0, "/home/dhalem/.claude/python")

print("Testing guard component imports...")

try:
    from duplicate_prevention.workspace_detector import workspace_detector

    print("✓ workspace_detector imported successfully")

    workspace_info = workspace_detector.get_workspace_info()
    print(f"✓ Workspace info: {workspace_info}")
except Exception as e:
    print(f"✗ workspace_detector import failed: {e}")

try:
    from duplicate_prevention.database import DatabaseConnector

    db = DatabaseConnector(host="localhost", port=6333)
    print("✓ DatabaseConnector imported and created")

    collections = db.list_collections()
    print(f"✓ Collections found: {collections}")
except Exception as e:
    print(f"✗ DatabaseConnector failed: {e}")

try:
    from duplicate_prevention.embedding_generator import EmbeddingGenerator

    embed_gen = EmbeddingGenerator()
    print("✓ EmbeddingGenerator imported and created")

    result = embed_gen.generate_embedding("def test(): pass", "python")
    print(f"✓ Embedding generated: {type(result)}")
except Exception as e:
    print(f"✗ EmbeddingGenerator failed: {e}")

print("Component test complete.")
