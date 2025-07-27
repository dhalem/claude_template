#!/usr/bin/env python3
"""Debug why duplicate prevention guard isn't working."""

import sys

sys.path.insert(0, "hooks/python")

from base_guard import GuardContext
from guards.duplicate_prevention_guard import DuplicatePreventionGuard

print("🔍 DEBUGGING DUPLICATE PREVENTION GUARD ISSUES")
print("=" * 60)

guard = DuplicatePreventionGuard()

# Test first function in detail
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

print("🔍 DEBUGGING FIRST FUNCTION:")
print(f"  Tool name: {context1.tool_name}")
print(f"  File path: {context1.file_path}")
print(f"  Content length: {len(context1.content)} chars")
print(f"  Content lines: {len(context1.content.split(chr(10)))}")

# Test if guard should trigger at all
should_trigger = guard.should_trigger(context1)
print(f"  Should trigger: {should_trigger}")

# Check file extension
from pathlib import Path

file_ext = Path(context1.file_path).suffix.lower()
print(f"  File extension: {file_ext}")
print(f"  Supported extensions: {guard.supported_extensions}")
print(f"  Extension supported: {file_ext in guard.supported_extensions}")

# Check line count requirement
line_count = len(context1.content.split("\n"))
print(f"  Line count: {line_count}")
print(f"  Min required: {guard.min_file_size}")
print(f"  Meets minimum: {line_count >= guard.min_file_size}")

# Test content extraction
extracted_content = guard._extract_content(context1)
print(f"  Extracted content length: {len(extracted_content)}")
print(f"  Extracted content: {repr(extracted_content[:100])}...")

# Test components
print("\n🔍 COMPONENT STATUS:")
print(f"  db_connector available: {guard.db_connector is not None}")
print(f"  embedding_generator available: {guard.embedding_generator is not None}")
print(f"  workspace_detector available: {guard.workspace_detector is not None}")

if guard.workspace_detector:
    collection_name = guard.get_workspace_collection_name()
    print(f"  Collection name: {collection_name}")

# Test similarity check directly
print("\n🔍 TESTING SIMILARITY CHECK:")
try:
    similarity_result = guard._check_similarity(context1.content, context1.file_path)
    print(f"  Similarity check result: {similarity_result}")
except Exception as e:
    print(f"  Similarity check error: {e}")
    import traceback

    traceback.print_exc()

print("\nDebug complete.")
