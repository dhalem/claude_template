#!/usr/bin/env python3
"""Real integration tests for MCP code search server.

NO MOCKS. NO FALLBACKS. NO CHEATING.
Tests the actual MCP server with real Docker containers and real search.
"""

# Import the real server code
import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("server", Path(__file__).parent / "code-search-server.py")
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)
WorkspaceAwareSearchServer = server_module.WorkspaceAwareSearchServer


class TestRealDockerIntegration(unittest.TestCase):
    """Test MCP server with real Docker infrastructure."""

    def setUp(self):
        """Set up test environment."""
        self.repo_root = Path(__file__).parent.parent.parent.resolve()
        self.original_cwd = os.getcwd()

        # Create a test server instance
        self.server = WorkspaceAwareSearchServer()

        # Override config to point to this repository
        self.server.config = {
            "workspaces": {
                str(self.repo_root): {
                    "docker_context": "musicbot",
                    "container_name": "DISCOVERY_NEEDED",  # Server should find this
                    "indexing_path": "/app/indexing"
                }
            },
            "cache_ttl": 300
        }

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)

    def test_local_search_works_first(self):
        """Verify the local search system works before testing MCP server."""
        # Change to repo root
        os.chdir(self.repo_root)

        # Test the existing search system directly
        cmd = [str(self.repo_root / "venv" / "bin" / "python3"),
               str(self.repo_root / "indexing" / "claude_code_search.py"),
               "search", "get_metadata"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        self.assertEqual(result.returncode, 0, f"Local search failed: {result.stderr}")

        # Parse the JSON response
        response = json.loads(result.stdout)
        self.assertTrue(response["success"])
        self.assertGreater(response["count"], 0, "Should find get_metadata functions")

        print(f"✓ Local search works: found {response['count']} results")

    def test_workspace_detection(self):
        """Test that the server can detect this workspace correctly."""
        os.chdir(self.repo_root)

        # Test workspace detection
        workspace = self.server.detect_workspace(str(self.repo_root))

        self.assertEqual(workspace.repo_root, self.repo_root)
        self.assertEqual(workspace.docker_context, "musicbot")

        print(f"✓ Workspace detected: {workspace.repo_root}")

    def test_find_running_containers(self):
        """Find what containers are actually running that might have indexing."""
        # This test discovers the real container infrastructure
        try:
            # Try different compose files to find running services
            compose_files = [
                self.repo_root / "docker-compose.yml",
                self.repo_root / "sonos_server" / "docker-compose.yaml",
                self.repo_root / "gemini_playlist_suggester" / "docker-compose.yml",
                self.repo_root / "syncer" / "docker-compose.yaml"
            ]

            running_containers = []

            for compose_file in compose_files:
                if compose_file.exists():
                    try:
                        cmd = ["docker", "-c", "musicbot", "compose", "-f", str(compose_file), "ps", "--format", "json"]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                        if result.returncode == 0 and result.stdout.strip():
                            # Parse each line as JSON
                            for line in result.stdout.strip().split('\n'):
                                if line.strip():
                                    container_info = json.loads(line)
                                    running_containers.append({
                                        "name": container_info.get("Name"),
                                        "service": container_info.get("Service"),
                                        "state": container_info.get("State"),
                                        "compose_file": str(compose_file)
                                    })
                    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
                        # Skip failed compose files
                        continue

            print(f"✓ Found {len(running_containers)} running containers:")
            for container in running_containers:
                print(f"  - {container['name']} ({container['service']}) [{container['state']}]")

            # The server should be able to find one of these containers for indexing
            self.assertGreater(len(running_containers), 0, "No running containers found")

            return running_containers

        except Exception as e:
            self.fail(f"Failed to discover running containers: {e}")

    def test_container_has_search_capability(self):
        """Test that at least one running container has search capability."""
        containers = self.test_find_running_containers()

        search_capable_containers = []

        for container in containers:
            container_name = container["name"]

            # Test if this container has the search script
            try:
                cmd = ["docker", "-c", "musicbot", "exec", container_name,
                       "test", "-f", "/app/indexing/claude_code_search.py"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    search_capable_containers.append(container_name)
                    print(f"✓ Container {container_name} has search capability")

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                # This container doesn't have search capability
                continue

        self.assertGreater(len(search_capable_containers), 0,
                           "No containers found with search capability")

        return search_capable_containers[0]  # Return the first working container

    def test_mcp_server_with_real_container(self):
        """Test the MCP server end-to-end with a real container."""
        os.chdir(self.repo_root)

        # First, find a working container
        working_container = self.test_container_has_search_capability()

        # Update the server config with the real container name
        self.server.config["workspaces"][str(self.repo_root)]["container_name"] = working_container

        # Test the full MCP workflow
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {"query": "get_metadata"}
            }
        }

        # This should work with the real container
        response = self.server.handle_request(request)

        self.assertIn("content", response)
        content_text = response["content"][0]["text"]
        result = json.loads(content_text)

        self.assertTrue(result["success"])
        self.assertGreater(result["count"], 0)

        print(f"✓ MCP server works with container {working_container}")
        print(f"✓ Found {result['count']} search results")

    def test_mcp_protocol_compliance(self):
        """Test that the MCP server follows the protocol correctly."""
        os.chdir(self.repo_root)

        # Test tools/list
        list_request = {"method": "tools/list", "params": {}}
        list_response = self.server.handle_request(list_request)

        self.assertIn("tools", list_response)
        tools = list_response["tools"]
        self.assertGreater(len(tools), 0)

        # Verify all tools have required fields
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)

        print(f"✓ MCP protocol compliance verified: {len(tools)} tools exposed")

    def test_error_propagation(self):
        """Test that errors propagate correctly without fallbacks."""
        os.chdir(self.repo_root)

        # Test with invalid container name - should fail fast
        bad_config = {
            "workspaces": {
                str(self.repo_root): {
                    "docker_context": "musicbot",
                    "container_name": "nonexistent-container-12345",
                    "indexing_path": "/app/indexing"
                }
            }
        }

        self.server.config = bad_config

        request = {
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {"query": "test"}
            }
        }

        # This should raise an exception, not return a fallback
        with self.assertRaises(RuntimeError) as cm:
            self.server.handle_request(request)

        self.assertIn("Docker command failed", str(cm.exception))
        print("✓ Error propagation works correctly - no fallbacks")


def run_real_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("🔥 REAL INTEGRATION TESTS - NO MOCKS, NO FALLBACKS")
    print("=" * 60)

    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_real_tests()
