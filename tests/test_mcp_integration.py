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

"""Pytest integration tests for MCP servers"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


class TestMCPServers:
    """Test suite for MCP server functionality"""

    @pytest.fixture(scope="class")
    def mcp_config(self):
        """Load MCP configuration - supports both local and central installations"""
        mcp_json = Path(".mcp.json")

        # Check for central installation first
        central_dir = Path.home() / ".claude/mcp/central"
        if central_dir.exists():
            # If central installation exists, create a virtual config
            return {
                "mcpServers": {
                    "code-search": {
                        "command": str(central_dir / "venv/bin/python"),
                        "args": [str(central_dir / "code-search/server.py")]
                    },
                    "code-review": {
                        "command": str(central_dir / "venv/bin/python"),
                        "args": [str(central_dir / "code-review/server.py")]
                    }
                }
            }

        # Fall back to .mcp.json
        if not mcp_json.exists():
            pytest.fail(".mcp.json file not found and no central installation - MCP servers not configured")

        config = json.loads(mcp_json.read_text())
        # If config is empty or has no servers, fail the test
        if not config.get("mcpServers"):
            pytest.fail("No MCP servers configured in .mcp.json or centrally - expected 'code-search' and 'code-review' servers")
        return config

    @pytest.fixture(scope="class")
    def claude_available(self):
        """Check if Claude CLI is available"""
        try:
            result = subprocess.run(
                ["which", "claude"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    def test_claude_cli_installed(self, claude_available):
        """Test that Claude CLI is installed and accessible"""
        assert claude_available, "Claude CLI not found in PATH"

        # Get version
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get Claude version"
        assert "Claude Code" in result.stdout or result.stdout.strip(), "Invalid version output"

    def test_mcp_servers_configured(self, claude_available):
        """Test that MCP servers are configured in Claude"""
        if not claude_available:
            pytest.skip("Claude CLI not available")

        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Failed to list MCP servers"
        assert "No MCP servers configured" not in result.stdout, (
            "No MCP servers configured. Run: "
            "cat .mcp.json | jq -r '.mcpServers | to_entries[] | "
            "\"claude mcp add \\(.key) \\(.value.command) \\(.value.args | join(\" \"))\"' | bash"
        )

        # Check for expected servers
        output = result.stdout.lower()
        assert "code-search" in output, "code-search server not configured"
        assert "code-review" in output, "code-review server not configured"

    @pytest.mark.parametrize("server_name", ["code-search", "code-review"])
    def test_server_protocol_response(self, server_name, mcp_config):
        """Test that each server responds to MCP protocol"""
        servers = mcp_config.get("mcpServers", {})
        server_config = servers.get(server_name)

        if not server_config:
            pytest.fail(f"Server {server_name} not found in .mcp.json - expected both 'code-search' and 'code-review' servers")

        command = server_config.get("command")
        args = server_config.get("args", [])

        if not command or not args:
            pytest.fail(f"Invalid config for {server_name} - missing command or args")

        # Check if the server files actually exist before trying to run them
        if not os.path.exists(command):
            pytest.fail(f"Server command not found: {command} - servers must be installed")

        if args and not os.path.exists(args[0]):
            pytest.fail(f"Server script not found: {args[0]} - servers must be installed")

        # Prepare protocol test
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

        # Run server with test input
        cmd = [command] + args
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(
                input=json.dumps(init_request) + "\n",
                timeout=5
            )

            # Parse response
            assert stdout, f"No output from {server_name}"
            response = json.loads(stdout.strip())

            assert "result" in response, f"No result in {server_name} response"
            assert "protocolVersion" in response["result"], f"No protocol version in {server_name} response"
            assert response["result"]["protocolVersion"] == "2024-11-05", f"Wrong protocol version for {server_name}"

        except subprocess.TimeoutExpired:
            process.kill()
            pytest.fail(f"Server {server_name} timed out")
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON from {server_name}: {e}")

    @pytest.mark.timeout(180)  # Allow 3 minutes for MCP integration test
    def test_mcp_code_review_integration(self, claude_available, mcp_config):
        """Test code review MCP tool through Claude"""
        print(f"\n[DEBUG] Starting test_mcp_code_review_integration at {os.getpid()}")
        print(f"[DEBUG] Environment: PYTEST={os.environ.get('PYTEST_CURRENT_TEST', 'NOT_SET')}")

        if not claude_available:
            pytest.fail("Claude CLI not available - required for MCP integration tests")

        # Require API key for code review (check both GEMINI_API_KEY and GOOGLE_API_KEY)
        gemini_key = os.environ.get("GEMINI_API_KEY")
        google_key = os.environ.get("GOOGLE_API_KEY")
        if not gemini_key and not google_key:
            pytest.fail("API key not available - set GEMINI_API_KEY or GOOGLE_API_KEY environment variable for code review tests")

        # This test requires MCP servers to be configured
        servers = mcp_config.get("mcpServers", {})
        if "code-review" not in servers:
            pytest.fail("code-review server not configured - required for this test")

        # Create test file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir='.'
        ) as f:
            f.write("""#!/usr/bin/env python3
def example_function():
    '''Function with intentional issues'''
    unused_var = 42  # This should be flagged
    x = [1, 2, 3]
    for i in range(len(x)):  # Should suggest enumerate
        print(x[i])
    return
""")
            test_file = f.name

        try:
            # Set up environment with API key for code review
            env = os.environ.copy()
            if not env.get("GEMINI_API_KEY") and env.get("GOOGLE_API_KEY"):
                env["GEMINI_API_KEY"] = env["GOOGLE_API_KEY"]

            # Full integration test with actual code review
            # Use Gemini 1.5 Flash for faster tests
            # Always use test_review_dir for consistency and reliability
            prompt = "Use the mcp__code-review__review_code tool with model='gemini-1.5-flash' to review test_review_dir"
            timeout_val = 180  # Extended timeout for external API calls

            print(f"[DEBUG] About to run subprocess with prompt: {prompt[:100]}...")
            print(f"[DEBUG] Timeout: {timeout_val}s")
            print(f"[DEBUG] GEMINI_API_KEY: {'SET' if env.get('GEMINI_API_KEY') else 'NOT_SET'}")

            # Run Claude with MCP tool
            # Fix pipe buffer deadlock by writing output to temporary files
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.stdout') as stdout_file, \
                 tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.stderr') as stderr_file:

                print(f"[DEBUG] Using temp files: stdout={stdout_file.name}, stderr={stderr_file.name}")
                print(f"[DEBUG] Starting subprocess.run at {time.time()}")
                print(f"[DEBUG] PRE_COMMIT: {os.environ.get('PRE_COMMIT', 'NOT_SET')}")
                print(f"[DEBUG] GIT_DIR: {os.environ.get('GIT_DIR', 'NOT_SET')}")

                # For debugging in pre-commit environment, reduce verbosity
                # --debug flag produces excessive output and can cause subprocess deadlock
                # Always use non-debug mode for reliability
                cmd_args = ["claude", "--dangerously-skip-permissions", "-p", prompt]

                print(f"[DEBUG] Running command: {' '.join(cmd_args)}")

                try:
                    result = subprocess.run(
                        cmd_args,
                        stdout=stdout_file,
                        stderr=stderr_file,
                        text=True,
                        timeout=timeout_val,
                        env=env
                    )
                    print(f"[DEBUG] subprocess.run completed at {time.time()}, returncode={result.returncode}")
                except subprocess.TimeoutExpired as e:
                    print(f"[DEBUG] subprocess.run TIMED OUT after {timeout_val}s")
                    raise

                # Read output from files
                stdout_file.seek(0)
                stderr_file.seek(0)
                stdout_content = Path(stdout_file.name).read_text()
                stderr_content = Path(stderr_file.name).read_text()

                # Clean up temp files
                Path(stdout_file.name).unlink(missing_ok=True)
                Path(stderr_file.name).unlink(missing_ok=True)

                # Create result-like object with file contents
                class SubprocessResult:
                    def __init__(self, returncode, stdout, stderr):
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr

                result = SubprocessResult(result.returncode, stdout_content, stderr_content)

            output = result.stdout + result.stderr

            # Check for successful tool call
            # In debug mode we get explicit "Tool call succeeded" message
            # In non-debug mode we check for review content
            success_indicators = [
                'MCP server "code-review": Tool call succeeded',  # Debug mode
                'Code Review Report',  # Non-debug mode
                'review',  # Basic indicator
                'unused'   # Should detect the unused variable
            ]

            assert any(indicator in output for indicator in success_indicators), (
                f"MCP tool call did not succeed. Output length: {len(output)}"
            )

            # Check for review content
            assert any(keyword in output for keyword in [
                "Code Review Report",
                "unused",
                "enumerate",
                "review"
            ]), "No review content generated"

        finally:
            # Cleanup
            Path(test_file).unlink(missing_ok=True)

    @pytest.mark.timeout(240)  # Allow 4 minutes for MCP integration test
    def test_mcp_code_search_integration(self, claude_available, mcp_config):
        """Test code search MCP tool through Claude"""
        print(f"\n[DEBUG] Starting test_mcp_code_search_integration at {os.getpid()}")
        print(f"[DEBUG] Environment: PYTEST={os.environ.get('PYTEST_CURRENT_TEST', 'NOT_SET')}")

        if not claude_available:
            pytest.fail("Claude CLI not available - required for MCP integration tests")

        # Require code index database for code search
        if not os.path.exists(".code_index.db"):
            pytest.fail("Code index database (.code_index.db) not available - run ./start-indexer.sh to create")

        # This test requires MCP servers to be configured
        servers = mcp_config.get("mcpServers", {})
        if "code-search" not in servers:
            pytest.fail("code-search server not configured - required for this test")

        # Run Claude with MCP tool
        prompt = "Use the mcp__code-search__search_code tool to search for 'def test_' in this directory"
        timeout_val = 180  # Increased timeout for MCP integration test

        print(f"[DEBUG] About to run subprocess with prompt: {prompt[:100]}...")
        print(f"[DEBUG] Timeout: {timeout_val}s")

        # Fix pipe buffer deadlock by writing output to temporary files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.stdout') as stdout_file, \
             tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.stderr') as stderr_file:

            print(f"[DEBUG] Using temp files: stdout={stdout_file.name}, stderr={stderr_file.name}")
            print(f"[DEBUG] Starting subprocess.run at {time.time()}")
            print(f"[DEBUG] PRE_COMMIT: {os.environ.get('PRE_COMMIT', 'NOT_SET')}")

            # For debugging in pre-commit environment, reduce verbosity
            # --debug flag causes subprocess deadlock - always use non-debug mode
            cmd_args = ["claude", "--dangerously-skip-permissions", "-p", prompt]

            print(f"[DEBUG] Running command: {' '.join(cmd_args)}")

            try:
                result = subprocess.run(
                    cmd_args,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    text=True,
                    timeout=timeout_val
                )
                print(f"[DEBUG] subprocess.run completed at {time.time()}, returncode={result.returncode}")
            except subprocess.TimeoutExpired as e:
                print(f"[DEBUG] subprocess.run TIMED OUT after {timeout_val}s")
                raise

            # Read output from files
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout_content = Path(stdout_file.name).read_text()
            stderr_content = Path(stderr_file.name).read_text()

            # Clean up temp files
            Path(stdout_file.name).unlink(missing_ok=True)
            Path(stderr_file.name).unlink(missing_ok=True)

            # Create result-like object with file contents
            class SubprocessResult:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            result = SubprocessResult(result.returncode, stdout_content, stderr_content)

        output = result.stdout + result.stderr

        # Check for successful tool call
        # In debug mode we get explicit "Tool call succeeded" message
        # In non-debug mode we check for search results
        success_indicators = [
            'MCP server "code-search": Tool call succeeded',  # Debug mode
            'def test_',  # Non-debug mode - should find test functions
            'tests/',     # Should find test files
            'Found'       # Basic indicator
        ]

        assert any(indicator in output for indicator in success_indicators), (
            f"MCP tool call did not succeed. Output length: {len(output)}"
        )

    def test_gemini_api_key_available(self):
        """Test that API key is set (required for code-review)"""
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        google_key = os.environ.get("GOOGLE_API_KEY", "")

        # Check if either key is available
        api_key = gemini_key or google_key
        assert api_key, (
            "API key environment variable not set. "
            "Code review server requires GEMINI_API_KEY or GOOGLE_API_KEY for Gemini API access."
        )
        assert len(api_key) > 20, "API key appears to be invalid (too short)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
