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

"""Tests to prevent cross-workspace MCP issues from happening again"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List


def run_command(cmd: List[str]) -> tuple[int, str, str]:
    """Run command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -2, "", str(e)

def test_no_hardcoded_paths():
    """Test that MCP configurations use appropriate paths for central installation"""
    print("🔍 Testing for appropriate paths in MCP configurations...")

    issues = []

    # Check .mcp.json for project-specific paths (these are the real problems)
    mcp_json = Path(".mcp.json")
    if mcp_json.exists():
        try:
            config = json.loads(mcp_json.read_text())
            for server_name, server_config in config.get("mcpServers", {}).items():
                command = server_config.get("command", "")
                args = server_config.get("args", [])

                # Check for project-specific paths (the real problem)
                if "claude_template" in command:
                    issues.append(f"Project-specific path in {server_name} command: {command}")

                for arg in args:
                    if "claude_template" in str(arg):
                        issues.append(f"Project-specific path in {server_name} args: {arg}")

                # Central installation paths are OK - they're supposed to be absolute
                # Only warn if using home directory path without central structure
                if "/home/" in command and ".claude/mcp/central" not in command:
                    issues.append(f"Non-central path in {server_name} command: {command}")
        except json.JSONDecodeError:
            issues.append("Invalid JSON in .mcp.json")

    if issues:
        print("❌ Found path configuration issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No problematic paths found (central installation paths are expected)")
        return True

def test_central_installation_exists():
    """Test that central MCP installation exists"""
    print("🏠 Testing central MCP installation...")

    central_dir = Path.home() / ".claude/mcp/central"
    required_dirs = [
        central_dir / "venv",
        central_dir / "code-search",
        central_dir / "code-review"
    ]

    required_files = [
        central_dir / "venv/bin/python",
        central_dir / "code-search/server.py",
        central_dir / "code-review/server.py"
    ]

    missing = []

    for dir_path in required_dirs:
        if not dir_path.exists():
            missing.append(f"Directory: {dir_path}")

    for file_path in required_files:
        if not file_path.exists():
            missing.append(f"File: {file_path}")

    if missing:
        print("❌ Central installation incomplete:")
        for item in missing:
            print(f"  - Missing: {item}")
        print("💡 Solution: Run ./safe_install.sh")
        return False
    else:
        print("✅ Central installation exists")
        return True

def test_user_scope_registration():
    """Test that MCP servers are registered with user scope"""
    print("👤 Testing MCP server user scope registration...")

    if not Path("/usr/local/bin/claude").exists():
        print("⚠️  Claude CLI not found - skipping scope test")
        return True

    rc, stdout, stderr = run_command(["claude", "mcp", "list"])

    if rc != 0:
        print(f"❌ Failed to list MCP servers: {stderr}")
        return False

    if "No MCP servers configured" in stdout:
        print("❌ No MCP servers registered")
        print("💡 Solution: Run ./register-mcp-global.sh")
        return False

    # Check if servers are using central paths
    lines = stdout.strip().split('\n')
    central_path_servers = 0
    local_path_servers = 0

    for line in lines:
        if ":" in line:
            if ".claude/mcp/central" in line:
                central_path_servers += 1
            elif "claude_template" in line or "/venv/bin/python3" in line:
                local_path_servers += 1

    if local_path_servers > 0:
        print(f"❌ Found {local_path_servers} servers with local paths")
        print("💡 Solution: Run ./register-mcp-global.sh to use central paths")
        return False

    if central_path_servers < 2:
        print(f"❌ Expected 2 central servers, found {central_path_servers}")
        return False

    print(f"✅ Found {central_path_servers} servers with central paths")
    return True

def test_cross_workspace_functionality():
    """Test that MCP servers work in a different directory"""
    print("🌐 Testing cross-workspace functionality...")

    if not Path("/usr/local/bin/claude").exists():
        print("⚠️  Claude CLI not found - skipping cross-workspace test")
        return True

    # Create temporary directory to test from
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Test that MCP servers are still listed
            rc, stdout, stderr = run_command(["claude", "mcp", "list"])

            if rc != 0:
                print(f"❌ MCP servers not accessible from other directory: {stderr}")
                return False

            if "No MCP servers configured" in stdout:
                print("❌ MCP servers not available in other workspace")
                return False

            # Check for expected servers
            if "code-search" not in stdout or "code-review" not in stdout:
                print("❌ Expected servers not found in other workspace")
                return False

            print("✅ MCP servers accessible from other workspace")
            return True

        finally:
            os.chdir(original_dir)

def test_no_project_specific_mcp_json():
    """Test that .mcp.json doesn't contain project-specific paths"""
    print("📄 Testing .mcp.json for project independence...")

    mcp_json = Path(".mcp.json")
    if not mcp_json.exists():
        print("✅ No .mcp.json file (using central/user config)")
        return True

    try:
        config = json.loads(mcp_json.read_text())
        servers = config.get("mcpServers", {})

        if not servers:
            print("✅ Empty .mcp.json (using central/user config)")
            return True

        # If .mcp.json has servers, they should use central paths
        for server_name, server_config in servers.items():
            command = server_config.get("command", "")
            args = server_config.get("args", [])

            if "claude_template" in command or any("claude_template" in str(arg) for arg in args):
                print(f"❌ .mcp.json contains project-specific paths for {server_name}")
                print("💡 Solution: Remove .mcp.json or update to use central paths")
                return False

            if not (".claude/mcp/central" in command or command.startswith("~/")):
                print(f"❌ .mcp.json should use central paths for {server_name}")
                return False

        print("✅ .mcp.json uses central paths")
        return True

    except json.JSONDecodeError:
        print("❌ Invalid JSON in .mcp.json")
        return False

def test_installation_scripts_exist():
    """Test that installation and setup scripts exist"""
    print("📜 Testing installation scripts exist...")

    required_scripts = [
        "safe_install.sh",
        "register-mcp-global.sh",
        "test_mcp_other_workspace.sh",
        "test_mcp_quick.sh"
    ]

    missing = []
    for script in required_scripts:
        if not Path(script).exists():
            missing.append(script)
        elif not os.access(script, os.X_OK):
            missing.append(f"{script} (not executable)")

    if missing:
        print("❌ Missing installation scripts:")
        for script in missing:
            print(f"  - {script}")
        return False
    else:
        print("✅ All installation scripts exist and are executable")
        return True

def main():
    """Run all cross-workspace prevention tests"""
    print("🚨 MCP Cross-Workspace Issue Prevention Tests")
    print("=" * 60)
    print()

    # Quick check if Claude CLI is available
    if not Path("/usr/local/bin/claude").exists():
        print("⚠️  Claude CLI not found - many tests will be skipped")
        print("✅ This is expected in CI environments without Claude CLI")

    tests = [
        ("Path Configuration", test_no_hardcoded_paths),
        ("Central Installation", test_central_installation_exists),
        ("User Scope Registration", test_user_scope_registration),
        ("Cross-Workspace Access", test_cross_workspace_functionality),
        ("Project Independence", test_no_project_specific_mcp_json),
        ("Installation Scripts", test_installation_scripts_exist),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * (len(test_name) + 1))

        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All cross-workspace prevention tests passed!")
        print("✅ MCP servers should work correctly across all workspaces")
        return 0
    else:
        print("⚠️  Some tests failed - review and fix issues above")
        print("\n💡 Quick fixes:")
        print("  1. Run: ./safe_install.sh")
        print("  2. Run: ./register-mcp-global.sh")
        print("  3. Remove project-specific .mcp.json if present")
        print("  4. Test with: ./test_mcp_other_workspace.sh /tmp/test")
        return 1

if __name__ == "__main__":
    sys.exit(main())
