#!/usr/bin/env python3
"""Test suite for MCP code search server."""

import json

# Import the server code
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

spec = importlib.util.spec_from_file_location("server", Path(__file__).parent / "code-search-server.py")
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)
WorkspaceAwareSearchServer = server_module.WorkspaceAwareSearchServer
WorkspaceInfo = server_module.WorkspaceInfo


class TestWorkspaceDetection(unittest.TestCase):
    """Test workspace detection functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.server = WorkspaceAwareSearchServer()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_detect_workspace_no_git(self):
        """Test workspace detection when no .git directory exists."""
        non_repo_dir = Path(self.temp_dir) / "not_a_repo"
        non_repo_dir.mkdir()

        with self.assertRaises(ValueError) as cm:
            self.server.detect_workspace(str(non_repo_dir))

        self.assertIn("No git repository found", str(cm.exception))

    def test_detect_workspace_not_configured(self):
        """Test workspace detection for unconfigured repository."""
        # Create a fake git repo
        repo_dir = Path(self.temp_dir) / "test_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        with self.assertRaises(ValueError) as cm:
            self.server.detect_workspace(str(repo_dir))

        self.assertIn("Workspace not configured", str(cm.exception))

    def test_detect_workspace_no_indexing(self):
        """Test workspace detection when indexing directory missing."""
        # Create a fake git repo
        repo_dir = Path(self.temp_dir) / "test_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        # Configure the workspace
        self.server.config["workspaces"][str(repo_dir)] = {
            "docker_context": "test",
            "container_name": "test-container",
            "indexing_path": "/app/indexing"
        }

        with self.assertRaises(ValueError) as cm:
            self.server.detect_workspace(str(repo_dir))

        self.assertIn("No indexing directory found", str(cm.exception))

    def test_detect_workspace_no_search_script(self):
        """Test workspace detection when search script missing."""
        # Create a fake git repo with indexing dir
        repo_dir = Path(self.temp_dir) / "test_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        (repo_dir / "indexing").mkdir()

        # Configure the workspace
        self.server.config["workspaces"][str(repo_dir)] = {
            "docker_context": "test",
            "container_name": "test-container",
            "indexing_path": "/app/indexing"
        }

        with self.assertRaises(ValueError) as cm:
            self.server.detect_workspace(str(repo_dir))

        self.assertIn("No search script found", str(cm.exception))

    def test_detect_workspace_success(self):
        """Test successful workspace detection."""
        # Create a complete fake git repo
        repo_dir = Path(self.temp_dir) / "test_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        indexing_dir = repo_dir / "indexing"
        indexing_dir.mkdir()
        (indexing_dir / "claude_code_search.py").touch()

        # Configure the workspace
        self.server.config["workspaces"][str(repo_dir)] = {
            "docker_context": "test",
            "container_name": "test-container",
            "indexing_path": "/app/indexing"
        }

        workspace = self.server.detect_workspace(str(repo_dir))

        self.assertEqual(workspace.repo_root, repo_dir)
        self.assertEqual(workspace.docker_context, "test")
        self.assertEqual(workspace.container_name, "test-container")
        self.assertEqual(workspace.indexing_path, "/app/indexing")

    def test_detect_workspace_caching(self):
        """Test that workspace detection results are cached."""
        # Create a complete fake git repo
        repo_dir = Path(self.temp_dir) / "test_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        indexing_dir = repo_dir / "indexing"
        indexing_dir.mkdir()
        (indexing_dir / "claude_code_search.py").touch()

        # Configure the workspace
        self.server.config["workspaces"][str(repo_dir)] = {
            "docker_context": "test",
            "container_name": "test-container",
            "indexing_path": "/app/indexing"
        }

        # First call
        workspace1 = self.server.detect_workspace(str(repo_dir))

        # Second call should use cache
        workspace2 = self.server.detect_workspace(str(repo_dir))

        self.assertIs(workspace1, workspace2)  # Same object reference


class TestDockerRouting(unittest.TestCase):
    """Test Docker command routing functionality."""

    def setUp(self):
        """Set up test environment."""
        self.server = WorkspaceAwareSearchServer()
        self.workspace = WorkspaceInfo(
            repo_root=Path("/test/repo"),
            docker_context="test-context",
            container_name="test-container",
            indexing_path="/app/indexing"
        )

    @patch('subprocess.run')
    def test_route_search_basic(self, mock_run):
        """Test basic search routing."""
        # Mock successful subprocess response
        mock_result = Mock()
        mock_result.stdout = '{"success": true, "results": []}'
        mock_run.return_value = mock_result

        result = self.server.route_search(
            self.workspace,
            "search",
            {"query": "test_function"}
        )

        # Verify command was called correctly
        expected_cmd = [
            "docker", "-c", "test-context", "exec", "test-container",
            "python3", "/app/indexing/claude_code_search.py",
            "search", "test_function"
        ]
        mock_run.assert_called_once_with(
            expected_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        self.assertEqual(result, {"success": True, "results": []})

    @patch('subprocess.run')
    def test_route_search_with_symbol_type(self, mock_run):
        """Test search routing with symbol type filter."""
        mock_result = Mock()
        mock_result.stdout = '{"success": true, "results": []}'
        mock_run.return_value = mock_result

        self.server.route_search(
            self.workspace,
            "search",
            {"query": "test_function", "symbol_type": "function"}
        )

        expected_cmd = [
            "docker", "-c", "test-context", "exec", "test-container",
            "python3", "/app/indexing/claude_code_search.py",
            "search", "test_function", "function"
        ]
        mock_run.assert_called_once_with(
            expected_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

    @patch('subprocess.run')
    def test_route_search_file_method(self, mock_run):
        """Test search_file method routing."""
        mock_result = Mock()
        mock_result.stdout = '{"success": true, "results": []}'
        mock_run.return_value = mock_result

        self.server.route_search(
            self.workspace,
            "search_file",
            {"file_pattern": "*.py", "name_pattern": "test_*"}
        )

        expected_cmd = [
            "docker", "-c", "test-context", "exec", "test-container",
            "python3", "/app/indexing/claude_code_search.py",
            "search_file", "*.py", "test_*"
        ]
        mock_run.assert_called_once_with(
            expected_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

    @patch('subprocess.run')
    def test_route_search_docker_error(self, mock_run):
        """Test handling of Docker command errors."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "docker", stderr="Container not found"
        )

        with self.assertRaises(RuntimeError) as cm:
            self.server.route_search(
                self.workspace,
                "search",
                {"query": "test"}
            )

        self.assertIn("Docker command failed", str(cm.exception))
        self.assertIn("Container not found", str(cm.exception))

    @patch('subprocess.run')
    def test_route_search_timeout(self, mock_run):
        """Test handling of Docker command timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("docker", 30)

        with self.assertRaises(RuntimeError) as cm:
            self.server.route_search(
                self.workspace,
                "search",
                {"query": "test"}
            )

        self.assertIn("Search operation timed out", str(cm.exception))

    @patch('subprocess.run')
    def test_route_search_invalid_json(self, mock_run):
        """Test handling of invalid JSON response."""
        mock_result = Mock()
        mock_result.stdout = 'invalid json response'
        mock_run.return_value = mock_result

        with self.assertRaises(RuntimeError) as cm:
            self.server.route_search(
                self.workspace,
                "search",
                {"query": "test"}
            )

        self.assertIn("Invalid JSON response", str(cm.exception))

    def test_route_search_unknown_method(self):
        """Test handling of unknown search method."""
        with self.assertRaises(ValueError) as cm:
            self.server.route_search(
                self.workspace,
                "unknown_method",
                {"query": "test"}
            )

        self.assertIn("Unknown search method", str(cm.exception))


class TestMCPProtocol(unittest.TestCase):
    """Test MCP protocol handling."""

    def setUp(self):
        """Set up test environment."""
        self.server = WorkspaceAwareSearchServer()

    def test_list_tools(self):
        """Test tools/list method."""
        request = {"method": "tools/list", "params": {}}
        response = self.server.handle_request(request)

        self.assertIn("tools", response)
        tools = response["tools"]

        # Check that all expected tools are present
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["search_code", "list_symbols", "explore_file", "search_in_files"]

        for expected_tool in expected_tools:
            self.assertIn(expected_tool, tool_names)

    def test_unknown_method(self):
        """Test handling of unknown MCP method."""
        request = {"method": "unknown/method", "params": {}}

        with self.assertRaises(ValueError) as cm:
            self.server.handle_request(request)

        self.assertIn("Method not found", str(cm.exception))

    @patch.object(WorkspaceAwareSearchServer, 'detect_workspace')
    @patch.object(WorkspaceAwareSearchServer, 'route_search')
    def test_call_tool_search_code(self, mock_route, mock_detect):
        """Test tools/call method for search_code."""
        # Mock workspace detection
        mock_workspace = WorkspaceInfo(
            repo_root=Path("/test"),
            docker_context="test",
            container_name="test",
            indexing_path="/app"
        )
        mock_detect.return_value = mock_workspace

        # Mock search routing
        mock_route.return_value = {"success": True, "results": []}

        request = {
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {"query": "test_function"}
            }
        }

        with patch('os.getcwd', return_value="/test/project"):
            response = self.server.handle_request(request)

        # Verify response format
        self.assertIn("content", response)
        content = response["content"][0]
        self.assertEqual(content["type"], "text")

        # Verify method calls
        mock_detect.assert_called_once_with("/test/project")
        mock_route.assert_called_once_with(mock_workspace, "search", {"query": "test_function"})

    def test_call_tool_unknown_tool(self):
        """Test tools/call method with unknown tool."""
        request = {
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        }

        with patch('os.getcwd', return_value="/test"):
            with self.assertRaises(ValueError) as cm:
                self.server.handle_request(request)

        self.assertIn("Unknown tool", str(cm.exception))


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete server."""

    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_full_search_workflow(self, mock_run):
        """Test complete search workflow from MCP request to Docker execution."""
        # Create test repository structure
        repo_dir = Path(self.temp_dir) / "test_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        indexing_dir = repo_dir / "indexing"
        indexing_dir.mkdir()
        (indexing_dir / "claude_code_search.py").touch()

        # Create server with test configuration
        server = WorkspaceAwareSearchServer()
        server.config = {
            "workspaces": {
                str(repo_dir): {
                    "docker_context": "test-context",
                    "container_name": "test-container",
                    "indexing_path": "/app/indexing"
                }
            },
            "cache_ttl": 300
        }

        # Mock Docker response
        mock_result = Mock()
        mock_result.stdout = json.dumps({
            "success": True,
            "query": "test_function",
            "results": [
                {
                    "name": "test_function",
                    "type": "function",
                    "file_path": "/app/test.py",
                    "line_number": 10
                }
            ]
        })
        mock_run.return_value = mock_result

        # Simulate MCP request
        request = {
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {"query": "test_function"}
            }
        }

        with patch('os.getcwd', return_value=str(repo_dir)):
            response = server.handle_request(request)

        # Verify the complete workflow
        self.assertIn("content", response)
        content_text = response["content"][0]["text"]
        result = json.loads(content_text)

        self.assertTrue(result["success"])
        self.assertEqual(result["query"], "test_function")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "test_function")

        # Verify Docker command was called correctly
        expected_cmd = [
            "docker", "-c", "test-context", "exec", "test-container",
            "python3", "/app/indexing/claude_code_search.py",
            "search", "test_function"
        ]
        mock_run.assert_called_once_with(
            expected_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading functionality."""

    def setUp(self):
        """Set up configuration test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up configuration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_config_missing_file(self):
        """Test loading configuration when file doesn't exist."""
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            server = WorkspaceAwareSearchServer()

        # Should have default configuration
        expected_config = {
            "workspaces": {},
            "cache_ttl": 300
        }
        self.assertEqual(server.config, expected_config)

    def test_load_config_existing_file(self):
        """Test loading configuration from existing file."""
        # Create config directory and file
        claude_dir = Path(self.temp_dir) / ".claude"
        mcp_dir = claude_dir / "mcp"
        mcp_dir.mkdir(parents=True)

        config_data = {
            "workspaces": {
                "/test/repo": {
                    "docker_context": "test",
                    "container_name": "test-container",
                    "indexing_path": "/app"
                }
            },
            "cache_ttl": 600
        }

        config_file = mcp_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            server = WorkspaceAwareSearchServer()

        self.assertEqual(server.config, config_data)


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
