#!/usr/bin/env python3
"""Test duplicate prevention guard directly."""

import sys

# Add hook path for imports
sys.path.insert(0, "/home/dhalem/.claude/python")

from base_guard import GuardContext
from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("Testing DuplicatePreventionGuard directly...")

# Create a guard instance
guard = DuplicatePreventionGuard()
print(f"✓ Guard created: {guard.name}")

# Create a context that mimics a Write operation
test_content = '''def add_numbers(data):
    """Add all numbers in the data list."""
    result = 0
    for num in data:
        result += num
    return result'''

context = GuardContext(
    tool_name="Write",
    tool_input={"file_path": "/home/dhalem/github/claude_template/test_direct.py", "content": test_content},
    file_path="/home/dhalem/github/claude_template/test_direct.py",
    content=test_content,
)

print(f"✓ Context created for file: {context.file_path}")
print(f"✓ Content length: {len(context.content)} chars")

# Test if guard should trigger
should_trigger = guard.should_trigger(context)
print(f"✓ Should trigger: {should_trigger}")

if should_trigger:
    message = guard.get_message(context)
    print(f"✓ Guard message: {message}")
else:
    print("✓ No trigger - this should store a vector for future comparison")

print("Direct guard test complete.")
