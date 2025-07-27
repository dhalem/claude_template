#!/usr/bin/env python3
"""Debug duplicate prevention guard _check_similarity method."""

import sys

sys.path.insert(0, "/home/dhalem/.claude/python")

from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("Testing guard components within guard context...")

# Create guard
guard = DuplicatePreventionGuard()

# Test content
test_content = '''def add_numbers(data):
    """Add all numbers in the data list."""
    result = 0
    for num in data:
        result += num
    return result'''

test_file_path = "/home/dhalem/github/claude_template/test_debug.py"

print(f"✓ Testing with content length: {len(test_content)} chars")
print(f"✓ Testing with file path: {test_file_path}")

# Test each component individually within guard
print("\n--- Testing guard components ---")

try:
    print(f"✓ db_connector: {guard.db_connector is not None}")
    if guard.db_connector:
        collections = guard.db_connector.list_collections()
        print(f"✓ Collections accessible: {collections}")
    else:
        print("✗ db_connector is None")
except Exception as e:
    print(f"✗ db_connector error: {e}")

try:
    print(f"✓ embedding_generator: {guard.embedding_generator is not None}")
    if guard.embedding_generator:
        result = guard.embedding_generator.generate_embedding("test", "python")
        print(f"✓ Embedding generation works: {type(result)}")
    else:
        print("✗ embedding_generator is None")
except Exception as e:
    print(f"✗ embedding_generator error: {e}")

try:
    print(f"✓ workspace_detector: {guard.workspace_detector is not None}")
    if guard.workspace_detector:
        collection_name = guard.get_workspace_collection_name()
        print(f"✓ Collection name: {collection_name}")
    else:
        print("✗ workspace_detector is None")
except Exception as e:
    print(f"✗ workspace_detector error: {e}")

# Test _check_similarity directly
print("\n--- Testing _check_similarity directly ---")
try:
    result = guard._check_similarity(test_content, test_file_path)
    print(f"✓ _check_similarity result: {result}")
except Exception as e:
    print(f"✗ _check_similarity error: {e}")
    import traceback

    traceback.print_exc()

print("\nDebug test complete.")
