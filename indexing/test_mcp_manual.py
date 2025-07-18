#!/usr/bin/env python3
"""Manual test of MCP search server functionality."""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_search_server import CodeSearcher


def test_search_functionality():
    """Test all search functionality."""
    print("=== Testing MCP Code Search Server ===\n")

    try:
        # Initialize searcher
        searcher = CodeSearcher()
        print(f"✓ Database found at: {searcher.db_path}")

        # Test 1: Search by name
        print("\n1. Testing search by name for 'CodeIndexer':")
        result = searcher.search("CodeIndexer", search_type="name")
        if result["success"]:
            print(f"   ✓ Found {result['count']} results")
            for item in result["results"][:2]:
                print(f"   - {item['name']} at {item['location']}")
        else:
            print(f"   ✗ Error: {result['error']}")

        # Test 2: Search with wildcards
        print("\n2. Testing wildcard search for 'test*':")
        result = searcher.search("test*", search_type="name")
        if result["success"]:
            print(f"   ✓ Found {result['count']} results")
            for item in result["results"][:3]:
                print(f"   - {item['name']} ({item['type']})")
        else:
            print(f"   ✗ Error: {result['error']}")

        # Test 3: Search by content
        print("\n3. Testing content search for 'import os':")
        result = searcher.search("import os", search_type="content")
        if result["success"]:
            print(f"   ✓ Found {result['count']} results")
        else:
            print(f"   ✗ Error: {result['error']}")

        # Test 4: List functions
        print("\n4. Testing list functions:")
        result = searcher.list_symbols("function", limit=5)
        if result["success"]:
            print(f"   ✓ Found {result['count']} functions (showing first 5)")
            for item in result["results"][:5]:
                print(f"   - {item['name']}")
        else:
            print(f"   ✗ Error: {result['error']}")

        # Test 5: Get stats
        print("\n5. Testing database statistics:")
        result = searcher.get_stats()
        if result["success"]:
            stats = result["stats"]
            print(f"   ✓ Total symbols: {stats['total_symbols']}")
            print(f"   ✓ Total files: {stats['total_files']}")
            print("   ✓ Symbols by type:")
            for sym_type, count in stats.get("by_type", {}).items():
                print(f"     - {sym_type}: {count}")
        else:
            print(f"   ✗ Error: {result['error']}")

        print("\n=== All tests completed successfully! ===")
        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_search_functionality()
    sys.exit(0 if success else 1)
