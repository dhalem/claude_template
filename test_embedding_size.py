#!/usr/bin/env python3
"""Check actual embedding size from generator."""

import sys

sys.path.insert(0, "/home/dhalem/.claude/python")

from duplicate_prevention.embedding_generator import EmbeddingGenerator

print("Testing embedding size...")

embed_gen = EmbeddingGenerator()
result = embed_gen.generate_embedding("def test(): pass", "python")

embedding = result["embedding"]
print(f"✓ Embedding size: {len(embedding)} dimensions")
print("✓ Expected by guard: 384 dimensions")
print(f"✓ Match: {len(embedding) == 384}")

if len(embedding) != 384:
    print(f"✗ SIZE MISMATCH: Collection created with 384, but embeddings are {len(embedding)}")
else:
    print("✓ Sizes match perfectly")

print("Embedding size test complete.")
