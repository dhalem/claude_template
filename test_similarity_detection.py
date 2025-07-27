#!/usr/bin/env python3
"""Test similarity detection between first and similar functions."""

import sys

sys.path.insert(0, "hooks/python")

import requests
from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("🔍 TESTING SIMILARITY DETECTION")
print("=" * 50)

# Clear and setup
try:
    requests.delete("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10)
except:
    pass

guard = DuplicatePreventionGuard()

# First function
first_function = '''def sum_numbers(data_list):
    """Sum all numbers in a data list."""
    result = 0
    for item in data_list:
        result += item
    return result'''

# Similar function
similar_function = '''def calculate_total(numbers):
    """Calculate the total of all numbers in a list."""
    total = 0
    for num in numbers:
        total += num
    return total'''

print("📝 STEP 1: Store first function")
result1 = guard._check_similarity(first_function, "/home/dhalem/github/claude_template/first.py")
print(f"  First function result: {result1}")

# Check vectors after first
try:
    info = requests.get("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10).json()
    count1 = info.get("result", {}).get("points_count", 0)
    print(f"  Vectors after first: {count1}")
except:
    print("  Vectors after first: 0")

print("\n🔍 STEP 2: Test similar function (should detect duplicate)")
result2 = guard._check_similarity(similar_function, "/home/dhalem/github/claude_template/similar.py")
print(f"  Similar function result: {result2}")

# Check if _similar_files was populated
if hasattr(guard, "_similar_files"):
    print(f"  Similar files found: {len(guard._similar_files)}")
    for i, sim in enumerate(guard._similar_files):
        score = sim.get("score", 0)
        metadata = sim.get("metadata", {})
        file_path = metadata.get("file_path", "Unknown")
        print(f"    {i+1}. Score: {score:.3f} ({int(score*100)}%) - {file_path}")
else:
    print("  ❌ No _similar_files attribute found")

# Check vectors after similar
try:
    info = requests.get("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10).json()
    count2 = info.get("result", {}).get("points_count", 0)
    print(f"  Vectors after similar: {count2}")
except:
    print("  Vectors after similar: 0")

# Test the embeddings directly
print("\n🔍 STEP 3: Test embeddings directly")
try:
    embed1 = guard.embedding_generator.generate_embedding(first_function, "python")
    embed2 = guard.embedding_generator.generate_embedding(similar_function, "python")

    if embed1 and embed2 and "embedding" in embed1 and "embedding" in embed2:
        vec1 = embed1["embedding"]
        vec2 = embed2["embedding"]

        # Calculate cosine similarity manually
        import numpy as np

        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        cosine_sim = np.dot(vec1_np, vec2_np) / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np))
        print(f"  Manual cosine similarity: {cosine_sim:.3f} ({int(cosine_sim*100)}%)")
        print(f"  Threshold: {guard.similarity_threshold} ({int(guard.similarity_threshold*100)}%)")
        print(f"  Above threshold: {cosine_sim >= guard.similarity_threshold}")
    else:
        print("  ❌ Failed to generate embeddings")

except Exception as e:
    print(f"  Error testing embeddings: {e}")

print("\n🎯 EXPECTED:")
print("  First function: Store vector (result=False)")
print("  Similar function: Detect duplicate (result=True)")
print("  Similarity score: >75% (above threshold)")

print("\n🎯 ACTUAL:")
print(f"  First function result: {result1}")
print(f"  Similar function result: {result2}")

if result1 == False and result2 == True:
    print("\n🎉 SUCCESS: Similarity detection working!")
else:
    print("\n❌ FAILURE: Similarity detection broken!")

print("\nSimilarity detection test complete.")
