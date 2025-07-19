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

"""Test suite to verify MCP servers are properly configured and working"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(msg: str) -> None:
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{msg.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

def print_test(name: str, status: str, details: str = "") -> None:
    """Print test result"""
    icon = "✓" if status == "PASS" else "✗"
    color = GREEN if status == "PASS" else RED
    print(f"{color}{icon} {name}{RESET}")
    if details:
        print(f"  {details}")

def run_command(cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -2, "", str(e)

def test_claude_installed() -> bool:
    """Test if Claude Code CLI is installed"""
    print_header("Testing Claude Code CLI Installation")

    rc, stdout, stderr = run_command(["which", "claude"])
    if rc == 0:
        claude_path = stdout.strip()
        print_test("Claude CLI found", "PASS", f"Path: {claude_path}")

        # Get version
        rc, stdout, stderr = run_command(["claude", "--version"])
        if rc == 0:
            print_test("Claude version", "PASS", f"Version: {stdout.strip()}")
            return True
        else:
            print_test("Claude version", "FAIL", "Could not get version")
            return False
    else:
        print_test("Claude CLI found", "FAIL", "Claude not in PATH")
        return False

def test_mcp_servers_configured() -> Dict[str, bool]:
    """Test if MCP servers are configured"""
    print_header("Testing MCP Server Configuration")

    rc, stdout, stderr = run_command(["claude", "mcp", "list"])

    servers = {}
    if rc == 0:
        lines = stdout.strip().split('\n')
        if "No MCP servers configured" in stdout:
            print_test("MCP servers configured", "FAIL", "No servers found")
            return servers

        for line in lines:
            if ':' in line:
                server_name = line.split(':')[0].strip()
                servers[server_name] = True
                print_test(f"Server '{server_name}'", "PASS", "Configured")
    else:
        print_test("MCP server list", "FAIL", f"Error: {stderr}")

    # Check for expected servers
    for expected in ["code-search", "code-review"]:
        if expected not in servers:
            print_test(f"Server '{expected}'", "FAIL", "Not configured")
            servers[expected] = False

    return servers

def test_server_protocol(server_name: str, server_path: str, python_path: str) -> bool:
    """Test if server responds to MCP protocol"""
    print(f"\n{BOLD}Testing {server_name} protocol response...{RESET}")

    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "test",
                "version": "1.0.0"
            },
            "capabilities": {}
        },
        "id": 1
    }

    # Run server with protocol test
    cmd = f'echo \'{json.dumps(init_request)}\' | {python_path} {server_path}'
    rc, stdout, stderr = run_command(["bash", "-c", cmd], timeout=5)

    if rc == 0 and stdout:
        try:
            response = json.loads(stdout.strip())
            if "result" in response and "protocolVersion" in response["result"]:
                print_test(f"{server_name} protocol", "PASS",
                           f"Version: {response['result']['protocolVersion']}")
                return True
            else:
                print_test(f"{server_name} protocol", "FAIL", "Invalid response format")
                return False
        except json.JSONDecodeError:
            print_test(f"{server_name} protocol", "FAIL", "Invalid JSON response")
            return False
    else:
        print_test(f"{server_name} protocol", "FAIL",
                   f"No response (rc={rc}, stderr={stderr[:100]})")
        return False

def test_mcp_tool_call() -> bool:
    """Test actual MCP tool calls through Claude"""
    print_header("Testing MCP Tool Functionality")

    # Create a test file
    test_file = Path("test_mcp_review_target.py")
    test_file.write_text('''#!/usr/bin/env python3
"""Test file for MCP review"""

def hello_world():
    print("Hello, World!")
    x = 1  # unused variable
    return

if __name__ == "__main__":
    hello_world()
''')

    try:
        # Test code-review tool
        print(f"\n{BOLD}Testing code-review tool...{RESET}")
        cmd = [
            "claude", "--debug", "--dangerously-skip-permissions",
            "-p", f"Use the mcp__code-review__review_code tool to review the file {test_file.absolute()}"
        ]

        rc, stdout, stderr = run_command(cmd, timeout=60)
        full_output = stdout + stderr

        # Check for success indicators
        if "MCP server \"code-review\": Tool call succeeded" in full_output:
            print_test("code-review tool call", "PASS", "Tool executed successfully")

            # Check if review was generated
            if "Code Review Report" in full_output or "unused variable" in full_output:
                print_test("code-review output", "PASS", "Review content generated")
                review_success = True
            else:
                print_test("code-review output", "FAIL", "No review content found")
                review_success = False
        else:
            print_test("code-review tool call", "FAIL", "Tool call did not succeed")
            review_success = False

            # Check for common errors
            if "MCP server \"code-review\": Calling MCP tool" in full_output:
                print(f"  {YELLOW}Tool was called but failed to complete{RESET}")
            elif "mcp__code-review__review_code" not in full_output:
                print(f"  {YELLOW}Tool was not recognized by Claude{RESET}")

        # Test code-search tool
        print(f"\n{BOLD}Testing code-search tool...{RESET}")
        cmd = [
            "claude", "--debug", "--dangerously-skip-permissions",
            "-p", "Use the mcp__code-search__search_code tool to search for 'def hello' in this directory"
        ]

        rc, stdout, stderr = run_command(cmd, timeout=60)
        full_output = stdout + stderr

        if "MCP server \"code-search\": Tool call succeeded" in full_output:
            print_test("code-search tool call", "PASS", "Tool executed successfully")
            search_success = True
        else:
            print_test("code-search tool call", "FAIL", "Tool call did not succeed")
            search_success = False

        return review_success and search_success

    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

def get_server_paths() -> Dict[str, Tuple[str, str]]:
    """Get server paths from .mcp.json or claude mcp list"""
    servers = {}

    # Try to read from .mcp.json first
    mcp_json = Path(".mcp.json")
    if mcp_json.exists():
        try:
            config = json.loads(mcp_json.read_text())
            for name, server_config in config.get("mcpServers", {}).items():
                command = server_config.get("command", "")
                args = server_config.get("args", [])
                if args:
                    servers[name] = (command, args[0])
        except:
            pass

    # If not found, try to parse from claude mcp list
    if not servers:
        rc, stdout, stderr = run_command(["claude", "mcp", "list"])
        if rc == 0:
            for line in stdout.strip().split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    name = parts[0].strip()
                    cmd_parts = parts[1].strip().split()
                    if len(cmd_parts) >= 2:
                        servers[name] = (cmd_parts[0], cmd_parts[1])

    return servers

def main():
    """Run all MCP server tests"""
    print_header("MCP Server Test Suite")
    print("Testing MCP servers for Claude Code integration\n")

    all_passed = True

    # Test 1: Claude installation
    if not test_claude_installed():
        print(f"\n{RED}FATAL: Claude Code CLI not properly installed{RESET}")
        return 1

    # Test 2: MCP server configuration
    configured_servers = test_mcp_servers_configured()
    if not any(configured_servers.values()):
        print(f"\n{YELLOW}No MCP servers configured. Run setup first:{RESET}")
        print("cat .mcp.json | jq -r '.mcpServers | to_entries[] | \"claude mcp add \\(.key) \\(.value.command) \\(.value.args | join(\" \"))\"' | bash")
        all_passed = False

    # Test 3: Server protocol responses
    server_paths = get_server_paths()
    for server_name, (python_path, server_path) in server_paths.items():
        if configured_servers.get(server_name, False):
            if not test_server_protocol(server_name, server_path, python_path):
                all_passed = False

    # Test 4: Actual tool calls
    if any(configured_servers.values()):
        if not test_mcp_tool_call():
            all_passed = False

    # Summary
    print_header("Test Summary")
    if all_passed:
        print(f"{GREEN}✓ All tests passed!{RESET}")
        print("\nMCP servers are properly configured and working.")
        return 0
    else:
        print(f"{RED}✗ Some tests failed{RESET}")
        print("\nPlease check the errors above and:")
        print("1. Ensure servers are added: claude mcp list")
        print("2. Check server files exist and are executable")
        print("3. Verify Python paths and virtual environments")
        print("4. Check GEMINI_API_KEY is set (for code-review)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
