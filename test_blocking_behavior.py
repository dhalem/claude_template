#!/usr/bin/env python3
"""Test duplicate prevention guard blocking behavior locally."""

import sys

sys.path.insert(0, "hooks/python")

from base_guard import GuardContext
from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("🧪 TESTING DUPLICATE PREVENTION BLOCKING BEHAVIOR")
print("=" * 60)

# Clear any existing collection for clean test
import requests

try:
    requests.delete("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10)
    print("✓ Cleared existing collection for clean test")
except:
    print("✓ No existing collection to clear")

# Initialize guard
guard = DuplicatePreventionGuard()
print(f"✓ Guard initialized: {guard.name}")
print(f"✓ Default action: {guard.get_default_action()}")

# First function - should be allowed and store vector
print("\n📝 STEP 1: Create first function (should ALLOW and store vector)")
first_function = '''def sum_numbers(data_list):
    """Sum all numbers in a data list."""
    result = 0
    for item in data_list:
        result += item
    return result'''

context1 = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/test_first.py", "content": first_function},
    file_path="/home/dhalem/github/claude_template/test_first.py",
    content=first_function,
)

# Test the complete guard.check() method, not just should_trigger()
result1 = guard.check(context1, is_interactive=False)
print("✓ First function result:")
print(f"  should_block: {result1.should_block}")
print(f"  message: {result1.message[:100] if result1.message else 'None'}...")

# Check vector count
try:
    collection_info = requests.get(
        "http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10
    ).json()
    vector_count = collection_info.get("result", {}).get("points_count", 0)
    print(f"  vectors stored: {vector_count}")
except:
    print("  vectors stored: 0 (collection not created)")

# Second function - similar, should be BLOCKED
print("\n🚨 STEP 2: Create similar function (should BLOCK with error)")
similar_function = '''def calculate_total(numbers):
    """Calculate the total of all numbers in a list."""
    total = 0
    for num in numbers:
        total += num
    return total'''

context2 = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/test_similar.py", "content": similar_function},
    file_path="/home/dhalem/github/claude_template/test_similar.py",
    content=similar_function,
)

# Test the complete guard.check() method
result2 = guard.check(context2, is_interactive=False)
print("✓ Similar function result:")
print(f"  should_block: {result2.should_block}")
print(f"  exit_code: {result2.exit_code}")

if result2.message:
    print("\n📋 BLOCKING MESSAGE:")
    print("-" * 40)
    print(result2.message)
    print("-" * 40)
else:
    print("  ❌ NO MESSAGE - This is a problem!")

# Third function - different, should be allowed
print("\n📋 STEP 3: Create different function (should ALLOW)")
different_function = '''def find_maximum(values):
    """Find the maximum value in a list."""
    if not values:
        return None
    max_val = values[0]
    for val in values:
        if val > max_val:
            max_val = val
    return max_val'''

context3 = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/test_different.py", "content": different_function},
    file_path="/home/dhalem/github/claude_template/test_different.py",
    content=different_function,
)

result3 = guard.check(context3, is_interactive=False)
print("✓ Different function result:")
print(f"  should_block: {result3.should_block}")

# Final summary
try:
    final_info = requests.get(
        "http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10
    ).json()
    final_count = final_info.get("result", {}).get("points_count", 0)
    print("\n📊 FINAL RESULTS:")
    print(f"  Total vectors stored: {final_count}")
    print("  Expected: 2 (first + different functions only)")

    if final_count == 2:
        print("  ✅ Correct vector count!")
    else:
        print(f"  ❌ Wrong vector count - expected 2, got {final_count}")

except Exception as e:
    print(f"  ❌ Error checking final count: {e}")

print("\n🎯 BLOCKING TEST RESULTS:")
print(f"  First function blocked: {result1.should_block} (should be False)")
print(f"  Similar function blocked: {result2.should_block} (should be True)")
print(f"  Different function blocked: {result3.should_block} (should be False)")

if not result1.should_block and result2.should_block and not result3.should_block:
    print("\n🎉 SUCCESS: Guard blocking behavior works correctly!")
    print("   ✅ Allows unique functions")
    print("   ✅ Blocks duplicate functions")
    print("   ✅ Shows error messages for blocked functions")
else:
    print("\n❌ FAILURE: Guard blocking behavior is incorrect!")

print("\nLocal blocking test complete.")
