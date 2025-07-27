#!/usr/bin/env python3
"""Debug why first function isn't storing vector."""

import sys

sys.path.insert(0, "hooks/python")

import requests
from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("🔍 DEBUGGING VECTOR STORAGE ISSUE")
print("=" * 50)

# Clear collection
try:
    requests.delete("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10)
    print("✓ Cleared collection")
except:
    pass

guard = DuplicatePreventionGuard()
test_content = '''def sum_numbers(data_list):
    """Sum all numbers in a data list."""
    result = 0
    for item in data_list:
        result += item
    return result'''

test_file_path = "/home/dhalem/github/claude_template/debug_first.py"

print("\n📝 Testing _check_similarity for first function:")
print(f"  Content: {len(test_content)} chars")
print(f"  File: {test_file_path}")

# Test components before similarity check
print("\n🔍 Component status:")
print(f"  db_connector: {guard.db_connector is not None}")
print(f"  embedding_generator: {guard.embedding_generator is not None}")
print(f"  workspace_detector: {guard.workspace_detector is not None}")

if guard.workspace_detector:
    collection_name = guard.get_workspace_collection_name()
    print(f"  Collection name: {collection_name}")

    # Check if collection exists before test
    try:
        info = requests.get(f"http://localhost:6333/collections/{collection_name}", timeout=10).json()
        print(f"  Collection exists: {info.get('status') == 'ok'}")
    except:
        print("  Collection exists: False")

# Call _check_similarity and trace what happens
print("\n🔍 Calling _check_similarity:")
try:
    result = guard._check_similarity(test_content, test_file_path)
    print(f"  Result: {result}")

    # Check collection status after call
    try:
        info = requests.get(f"http://localhost:6333/collections/{collection_name}", timeout=10).json()
        vector_count = info.get("result", {}).get("points_count", 0)
        print(f"  Vectors after call: {vector_count}")

        if vector_count > 0:
            print("  ✅ Vector was stored!")
        else:
            print("  ❌ No vector stored!")

    except Exception as e:
        print(f"  Error checking vectors: {e}")

except Exception as e:
    print(f"  Error in _check_similarity: {e}")
    import traceback

    traceback.print_exc()

# Test the complete should_trigger logic
print("\n🔍 Testing should_trigger:")
from base_guard import GuardContext

context = GuardContext(
    tool_name="Write",
    tool_input={"file_path": test_file_path, "content": test_content},
    file_path=test_file_path,
    content=test_content,
)

should_trigger = guard.should_trigger(context)
print(f"  should_trigger result: {should_trigger}")

# Final collection status
try:
    info = requests.get(f"http://localhost:6333/collections/{collection_name}", timeout=10).json()
    final_count = info.get("result", {}).get("points_count", 0)
    print(f"  Final vector count: {final_count}")
except:
    print("  Final vector count: 0")

print("\nVector storage debug complete.")
