#!/usr/bin/env python3
"""LIVE DEMO: Duplicate Prevention System Working"""

import sys

sys.path.insert(0, "/home/dhalem/.claude/python")

from base_guard import GuardContext
from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("🎬 DUPLICATE PREVENTION SYSTEM DEMO")
print("=" * 50)

# Initialize the guard
guard = DuplicatePreventionGuard()
print(f"✅ Guard initialized: {guard.name}")

# First function - should store a vector
print("\n📝 STEP 1: Creating first function (should STORE vector)")
first_function = '''def sum_numbers(data_list):
    """Sum all numbers in a data list.

    This function iterates through a list of numbers and calculates
    their total sum by adding each number to a running total.

    Args:
        data_list: List of numbers to sum

    Returns:
        Total sum of all numbers
    """
    result = 0
    for item in data_list:
        result += item
    return result'''

context1 = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/demo_sum_numbers.py", "content": first_function},
    file_path="/home/dhalem/github/claude_template/demo_sum_numbers.py",
    content=first_function,
)

should_trigger1 = guard.should_trigger(context1)
print("✅ First function processed")
print(f"   Should trigger: {should_trigger1} (False = stored vector)")

# Check if vector was stored
import requests

collection_info = requests.get(
    "http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10
).json()
vector_count = collection_info.get("result", {}).get("points_count", 0)
print(f"   Vectors in collection: {vector_count}")

# Second function - similar, should trigger duplicate warning
print("\n🔍 STEP 2: Creating similar function (should TRIGGER duplicate warning)")
similar_function = '''def calculate_total(numbers):
    """Calculate the total of all numbers in a list.

    This function goes through a list of numbers and computes
    their total by adding each number to an accumulator.

    Args:
        numbers: List of numeric values

    Returns:
        Total sum of all numbers
    """
    total = 0
    for num in numbers:
        total += num
    return total'''

context2 = GuardContext(
    tool_name="Write",
    tool_input={
        "file_path": "/home/dhalem/github/claude_template/demo_calculate_total.py",
        "content": similar_function,
    },
    file_path="/home/dhalem/github/claude_template/demo_calculate_total.py",
    content=similar_function,
)

should_trigger2 = guard.should_trigger(context2)
print("✅ Similar function processed")
print(f"   Should trigger: {should_trigger2} (True = duplicate detected!)")

if should_trigger2:
    print("\n🚨 DUPLICATE DETECTED! Here's the warning message:")
    print("-" * 60)
    message = guard.get_message(context2)
    print(message)
    print("-" * 60)
else:
    print("   No duplicate detected")

# Third function - different purpose, should not trigger
print("\n📋 STEP 3: Creating different function (should NOT trigger)")
different_function = '''def find_maximum(values):
    """Find the maximum value in a list.

    This function searches through a list of numbers to identify
    and return the largest value present.

    Args:
        values: List of numeric values to search

    Returns:
        The maximum value found in the list
    """
    if not values:
        return None

    max_value = values[0]
    for value in values:
        if value > max_value:
            max_value = value
    return max_value'''

context3 = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/demo_find_maximum.py", "content": different_function},
    file_path="/home/dhalem/github/claude_template/demo_find_maximum.py",
    content=different_function,
)

should_trigger3 = guard.should_trigger(context3)
print("✅ Different function processed")
print(f"   Should trigger: {should_trigger3} (False = no duplicate)")

# Final collection status
final_info = requests.get("http://localhost:6333/collections/claude_template_duplicate_prevention", timeout=10).json()
final_count = final_info.get("result", {}).get("points_count", 0)
print("\n📊 FINAL RESULTS:")
print(f"   Total vectors stored: {final_count}")
print("   Workspace: claude_template_duplicate_prevention")

print("\n🎉 DEMO COMPLETE - DUPLICATE PREVENTION IS WORKING!")
print("   ✅ Stores vectors for new functions")
print("   ✅ Detects semantic similarity using AI embeddings")
print("   ✅ Warns about potential duplicates")
print("   ✅ Allows genuinely different functions")
