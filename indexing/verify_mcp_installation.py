#!/usr/bin/env python3
"""Verify MCP code-search server installation."""

import json
import os
import sys
from pathlib import Path


def check_directory_structure():
    """Check if the server is installed in the correct structure."""
    print("Checking directory structure...")

    base_dir = Path.home() / ".claude" / "mcp" / "code-search"
    required_dirs = {
        "bin": base_dir / "bin",
        "src": base_dir / "src",
        "venv": base_dir / "venv",
        "logs": base_dir / "logs"
    }

    all_good = True
    for name, path in required_dirs.items():
        if path.exists():
            print(f"  ✓ {name}/: exists")
        else:
            print(f"  ✗ {name}/: missing")
            all_good = False

    # Check server file
    server_file = base_dir / "bin" / "server.py"
    if server_file.exists():
        print("  ✓ bin/server.py: exists")
        # Check if executable
        if os.access(server_file, os.X_OK):
            print("  ✓ bin/server.py: is executable")
        else:
            print("  ✗ bin/server.py: not executable")
            all_good = False
    else:
        print("  ✗ bin/server.py: missing")
        all_good = False

    return all_good

def check_configuration():
    """Check Claude Desktop configuration."""
    print("\nChecking configuration...")

    config_file = Path.home() / ".config" / "claude" / "claude_desktop_config.json"

    if not config_file.exists():
        print("  ✓ No claude_desktop_config.json (auto-discovery will be used)")
        return True

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        if 'mcpServers' in config and 'code-search' in config['mcpServers']:
            print("  ✗ Manual configuration found (should use auto-discovery)")
            print("    Remove the code-search entry from mcpServers")
            return False
        else:
            print("  ✓ No manual configuration (auto-discovery will be used)")
            return True
    except Exception as e:
        print(f"  ✗ Error reading config: {e}")
        return False

def test_server_imports():
    """Test if the server can be imported."""
    print("\nTesting server imports...")

    # Add the server directory to Python path
    server_path = Path.home() / ".claude" / "mcp" / "code-search" / "bin"
    sys.path.insert(0, str(server_path))

    try:
        import server
        print("  ✓ Server module imports successfully")

        # Check if CodeSearcher exists
        if hasattr(server, 'CodeSearcher'):
            print("  ✓ CodeSearcher class found")
        else:
            print("  ✗ CodeSearcher class not found")
            return False

        # Check if main function exists
        if hasattr(server, 'main'):
            print("  ✓ main() function found")
        else:
            print("  ✗ main() function not found")
            return False

        return True
    except ImportError as e:
        print(f"  ✗ Failed to import server: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error testing server: {e}")
        return False

def test_database_access():
    """Test if the server can access the database."""
    print("\nTesting database access...")

    try:
        # Import server and test CodeSearcher
        server_path = Path.home() / ".claude" / "mcp" / "code-search" / "bin"
        sys.path.insert(0, str(server_path))

        from server import CodeSearcher

        searcher = CodeSearcher()
        print(f"  ✓ Database found at: {searcher.db_path}")

        # Try a simple search
        result = searcher.search("test", search_type="name", limit=1)
        if result["success"]:
            print(f"  ✓ Search works (found {result['count']} results)")
        else:
            print(f"  ✗ Search failed: {result.get('error', 'Unknown error')}")
            return False

        return True
    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("MCP Code-Search Server Installation Verification")
    print("=" * 50)

    tests = [
        ("Directory Structure", check_directory_structure),
        ("Configuration", check_configuration),
        ("Server Imports", test_server_imports),
        ("Database Access", test_database_access)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name:<20} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ Installation verified successfully!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. Tools will be available as:")
        print("   - mcp__code-search__search_code")
        print("   - mcp__code-search__list_symbols")
        print("   - mcp__code-search__get_search_stats")
    else:
        print("\n⚠️  Installation has issues. Check the output above.")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
