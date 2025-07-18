#!/usr/bin/env python3
"""Full end-to-end test of MCP code search server."""

import json
import os
import subprocess
import sys
from pathlib import Path


def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)

def test_direct_functionality():
    """Test the search functionality directly."""
    print_test_header("Direct Functionality Test")

    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    try:
        from mcp_search_server import CodeSearcher

        searcher = CodeSearcher()
        print(f"✓ Searcher initialized with database: {searcher.db_path}")

        # Test search
        result = searcher.search("CodeIndexer", search_type="name")
        print(f"✓ Search returned {result['count']} results")

        if result['success'] and result['results']:
            print("\nSample results:")
            for item in result['results'][:3]:
                print(f"  - {item['name']} in {item['file_path']}")
                print(f"    Location: {item['location']}")

        return True
    except Exception as e:
        print(f"✗ Direct test failed: {e}")
        return False

def test_server_startup():
    """Test that the server can start without errors."""
    print_test_header("Server Startup Test")

    server_path = Path(__file__).parent / "mcp_search_server.py"
    if not server_path.exists():
        print(f"✗ Server file not found at {server_path}")
        return False

    try:
        # Start the server and send a simple initialization
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        request_str = json.dumps(init_request)
        header = f"Content-Length: {len(request_str)}\r\n\r\n"

        process.stdin.write(header + request_str)
        process.stdin.flush()

        # Wait a bit for response
        import time
        time.sleep(1)

        # Terminate the process
        process.terminate()

        # Check if there were any errors
        stderr = process.stderr.read()
        if stderr and "error" in stderr.lower():
            print(f"✗ Server reported errors: {stderr}")
            return False

        print("✓ Server started without errors")
        return True

    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        return False

def test_configuration():
    """Test that the configuration is correct."""
    print_test_header("Configuration Test")

    config_path = Path.home() / ".config/claude/claude_desktop_config.json"

    if not config_path.exists():
        print(f"✗ Configuration file not found at {config_path}")
        return False

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        if 'mcpServers' not in config:
            print("✗ No mcpServers section in config")
            return False

        if 'code-search' not in config['mcpServers']:
            print("✗ code-search server not configured")
            return False

        server_config = config['mcpServers']['code-search']
        print("✓ Server configured in Claude Desktop")
        print(f"  Command: {server_config.get('command', 'N/A')}")
        print(f"  Script: {server_config.get('args', ['N/A'])[0] if server_config.get('args') else 'N/A'}")

        # Verify the script exists
        if 'args' in server_config and server_config['args']:
            script_path = server_config['args'][0]
            if os.path.exists(script_path):
                print(f"✓ Server script exists at {script_path}")
            else:
                print(f"✗ Server script not found at {script_path}")
                return False

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_database_access():
    """Test database accessibility."""
    print_test_header("Database Access Test")

    db_paths = [
        Path.cwd().parent / ".code_index.db",
        Path("/app/.code_index.db"),
        Path.home() / ".code_index.db"
    ]

    for db_path in db_paths:
        if db_path.exists():
            print(f"✓ Found database at: {db_path}")

            # Check size and basic info
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"  Size: {size_mb:.2f} MB")

            # Try to connect and get basic info
            import sqlite3
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.execute("SELECT COUNT(*) FROM symbols")
                count = cursor.fetchone()[0]
                print(f"  Symbols: {count}")
                conn.close()
                return True
            except Exception as e:
                print(f"  Warning: Could not read database: {e}")

    print("✗ No database found")
    return False

def main():
    """Run all tests."""
    print("MCP CODE SEARCH SERVER - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Database Access", test_database_access),
        ("Direct Functionality", test_direct_functionality),
        ("Server Startup", test_server_startup),
        ("Configuration", test_configuration),
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
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name:<30} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The MCP code-search server is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
