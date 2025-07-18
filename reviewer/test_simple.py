#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Simple test for the code review MCP server components."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from file_collector import FileCollector
from gemini_client import GeminiClient
from review_formatter import ReviewFormatter


def test_file_collector():
    """Test file collector with the reviewer directory."""
    print("Testing FileCollector...")

    collector = FileCollector()
    current_dir = Path(__file__).parent.absolute()

    # Collect files from current directory
    files = collector.collect_files(str(current_dir))

    print(f"Collected {len(files)} files:")
    for path in sorted(files.keys()):
        print(f"  {path}")

    # Get file tree
    tree = collector.get_file_tree()
    print(f"\nFile tree:\n{tree}")

    # Get summary
    summary = collector.get_collection_summary()
    print(f"\nSummary: {summary}")

    return files


def test_review_formatter(files):
    """Test review formatter."""
    print("\nTesting ReviewFormatter...")

    formatter = ReviewFormatter()

    # Create a simple file tree
    file_tree = "reviewer/\n  src/\n    file_collector.py\n    gemini_client.py"

    # Format a simple review request
    simple_prompt = formatter.format_simple_review("def hello(): return 'world'")
    print(f"Simple prompt length: {len(simple_prompt)}")
    print(f"Simple prompt preview: {simple_prompt[:200]}...")

    # Format full review request with a subset of files
    small_files = dict(list(files.items())[:2])  # Just first 2 files
    full_prompt = formatter.format_review_request(
        files=small_files,
        file_tree=file_tree,
        focus_areas=["security", "performance"]
    )
    print(f"\nFull prompt length: {len(full_prompt)}")
    print(f"Full prompt preview: {full_prompt[:300]}...")

    return simple_prompt


def test_gemini_client(prompt):
    """Test Gemini client (requires API key)."""
    print("\nTesting GeminiClient...")

    # Check if API key is available
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("No API key found. Skipping Gemini test.")
        return

    try:
        # Use Flash model for testing
        client = GeminiClient(model="gemini-1.5-flash")

        # Test with simple prompt
        print("Sending simple review request to Gemini...")
        response = client.review_code(prompt)

        print(f"Response length: {len(response)}")
        print(f"Response preview: {response[:300]}...")

        # Get usage report
        usage = client.get_usage_report()
        print(f"\nUsage report: {usage}")

    except Exception as e:
        print(f"Error testing Gemini client: {e}")


def main():
    """Run all tests."""
    print("Running simple tests for Code Review MCP Server components\n")

    # Test components
    files = test_file_collector()
    prompt = test_review_formatter(files)
    test_gemini_client(prompt)

    print("\nAll tests completed!")


if __name__ == "__main__":
    main()
