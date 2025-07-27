#!/usr/bin/env python3
"""Test improved duplicate prevention blocking with location details."""

import sys

sys.path.insert(0, "hooks/python")

from base_guard import GuardContext
from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("🧪 TESTING IMPROVED DUPLICATE PREVENTION BLOCKING")
print("=" * 60)

# Clear collection for clean test
import requests

try:
    requests.delete("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10)
    print("✓ Cleared collection for clean test")
except:
    print("✓ No existing collection to clear")

guard = DuplicatePreventionGuard()
print(f"✓ Guard default action: {guard.get_default_action()}")

# STEP 1: First function - should be allowed
print("\n📝 STEP 1: First function (should be ALLOWED)")
first_function = '''def sum_numbers(data_list):
    """Sum all numbers in a data list."""
    result = 0
    for item in data_list:
        result += item
    return result'''

context1 = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/first_func.py", "content": first_function},
    file_path="/home/dhalem/github/claude_template/first_func.py",
    content=first_function,
)

result1 = guard.check(context1, is_interactive=False)
print(f"  should_block: {result1.should_block}")
print(f"  exit_code: {result1.exit_code}")

# Check vectors stored
try:
    info = requests.get("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10).json()
    count = info.get("result", {}).get("points_count", 0)
    print(f"  vectors stored: {count}")
except:
    print("  vectors stored: 0")

# STEP 2: Similar function - should be BLOCKED with location details
print("\n🚨 STEP 2: Similar function (should be BLOCKED with locations)")
similar_function = '''def calculate_total(numbers):
    """Calculate the total of all numbers in a list."""
    total = 0
    for num in numbers:
        total += num
    return total'''

context2 = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/similar_func.py", "content": similar_function},
    file_path="/home/dhalem/github/claude_template/similar_func.py",
    content=similar_function,
)

result2 = guard.check(context2, is_interactive=False)
print(f"  should_block: {result2.should_block}")
print(f"  exit_code: {result2.exit_code}")

if result2.should_block and result2.message:
    print("\n📋 BLOCKING MESSAGE WITH LOCATIONS:")
    print("=" * 50)
    print(result2.message)
    print("=" * 50)
elif result2.message:
    print(f"  message: {result2.message[:100]}...")
else:
    print("  ❌ NO BLOCKING MESSAGE!")

# STEP 3: Different function - should be allowed
print("\n📋 STEP 3: Different function (should be ALLOWED)")
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
    tool_input={"file_path": "/home/dhalem/github/claude_template/different_func.py", "content": different_function},
    file_path="/home/dhalem/github/claude_template/different_func.py",
    content=different_function,
)

result3 = guard.check(context3, is_interactive=False)
print(f"  should_block: {result3.should_block}")

# Final results
try:
    final_info = requests.get(
        "http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10
    ).json()
    final_count = final_info.get("result", {}).get("points_count", 0)
    print(f"\n📊 FINAL VECTOR COUNT: {final_count}")
except:
    print("\n📊 FINAL VECTOR COUNT: 0")

print("\n🎯 EXPECTED BEHAVIOR:")
print("  First function: ALLOW (unique code)")
print("  Similar function: BLOCK (duplicate detected)")
print("  Different function: ALLOW (different purpose)")

print("\n🎯 ACTUAL RESULTS:")
print(f"  First function: {'BLOCK' if result1.should_block else 'ALLOW'}")
print(f"  Similar function: {'BLOCK' if result2.should_block else 'ALLOW'}")
print(f"  Different function: {'BLOCK' if result3.should_block else 'ALLOW'}")

success = (
    not result1.should_block
    and result2.should_block  # First should be allowed
    and not result3.should_block  # Similar should be blocked  # Different should be allowed
)

if success:
    print("\n🎉 SUCCESS: Blocking behavior works correctly!")
else:
    print("\n❌ FAILURE: Blocking behavior is incorrect!")

print("\nImproved blocking test complete.")
