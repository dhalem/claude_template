#!/usr/bin/env python3
"""Workspace-aware MCP code search server.

This server detects the current workspace and routes search requests
to the correct Docker container for that repository.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class WorkspaceInfo:
    """Information about a detected workspace."""
    repo_root: Path
    docker_context: str
    container_name: str
    indexing_path: str


class WorkspaceAwareSearchServer:
    """MCP server that routes to correct Docker containers per workspace."""

    def __init__(self):
        self.workspace_cache = {}
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load server configuration."""
        config_path = Path.home() / ".claude" / "mcp" / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            "workspaces": {},
            "cache_ttl": 300
        }

    def detect_workspace(self, cwd: str) -> WorkspaceInfo:
        """Detect repository and indexing configuration."""
        cwd_path = Path(cwd).resolve()

        # Check cache first
        cache_key = str(cwd_path)
        if cache_key in self.workspace_cache:
            return self.workspace_cache[cache_key]

        # Walk up directory tree to find .git
        current = cwd_path
        repo_root = None

        while current != current.parent:
            if (current / ".git").exists():
                repo_root = current
                break
            current = current.parent

        if not repo_root:
            raise ValueError(f"No git repository found for: {cwd}")

        # Check if workspace is configured
        repo_str = str(repo_root)
        if repo_str not in self.config["workspaces"]:
            raise ValueError(f"Workspace not configured: {repo_root}")

        workspace_config = self.config["workspaces"][repo_str]

        # Validate indexing infrastructure exists
        indexing_dir = repo_root / "indexing"
        if not indexing_dir.exists():
            raise ValueError(f"No indexing directory found: {indexing_dir}")

        search_script = indexing_dir / "claude_code_search.py"
        if not search_script.exists():
            raise ValueError(f"No search script found: {search_script}")

        workspace_info = WorkspaceInfo(
            repo_root=repo_root,
            docker_context=workspace_config["docker_context"],
            container_name=workspace_config["container_name"],
            indexing_path=workspace_config["indexing_path"]
        )

        # Cache the result
        self.workspace_cache[cache_key] = workspace_info
        return workspace_info

    def route_search(self, workspace: WorkspaceInfo, method: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Route search to appropriate Docker container."""
        # Build command for docker exec
        cmd = [
            "docker", "-c", workspace.docker_context, "exec", workspace.container_name,
            "python3", f"{workspace.indexing_path}/claude_code_search.py"
        ]

        # Add method and arguments
        if method == "search":
            cmd.extend(["search", args["query"]])
            if args.get("symbol_type"):
                cmd.append(args["symbol_type"])
        elif method == "search_file":
            cmd.extend(["search_file", args["file_pattern"]])
            if args.get("name_pattern"):
                cmd.append(args["name_pattern"])
        elif method == "list_type":
            cmd.extend(["list_type", args["symbol_type"]])
        elif method == "file_symbols":
            cmd.extend(["file_symbols", args["file_path"]])
        else:
            raise ValueError(f"Unknown search method: {method}")

        # Execute the command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker command failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Search operation timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return self._list_tools()
        elif method == "tools/call":
            return self._call_tool(params)
        else:
            raise ValueError(f"Method not found: {method}")

    def _list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "search_code",
                    "description": "Search for functions, classes, and symbols in the current workspace",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (supports wildcards like 'get_*')"
                            },
                            "symbol_type": {
                                "type": "string",
                                "enum": ["function", "class", "method", "variable"],
                                "description": "Filter by symbol type (optional)"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "list_symbols",
                    "description": "List all symbols of a specific type in the current workspace",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol_type": {
                                "type": "string",
                                "enum": ["function", "class", "method", "variable"],
                                "description": "Type of symbols to list"
                            }
                        },
                        "required": ["symbol_type"]
                    }
                },
                {
                    "name": "explore_file",
                    "description": "Get all symbols in a specific file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to explore (relative to repo root)"
                            }
                        },
                        "required": ["file_path"]
                    }
                },
                {
                    "name": "search_in_files",
                    "description": "Search for symbols in specific files matching a pattern",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_pattern": {
                                "type": "string",
                                "description": "File pattern to search in (e.g., '*.py', 'src/*')"
                            },
                            "name_pattern": {
                                "type": "string",
                                "description": "Symbol name pattern to find (optional)"
                            }
                        },
                        "required": ["file_pattern"]
                    }
                }
            ]
        }

    def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Check for valid tool first
        valid_tools = ["search_code", "list_symbols", "explore_file", "search_in_files"]
        if tool_name not in valid_tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Get current working directory from environment
        cwd = os.getcwd()

        try:
            # Detect workspace
            workspace = self.detect_workspace(cwd)

            # Route the search
            if tool_name == "search_code":
                result = self.route_search(workspace, "search", arguments)
            elif tool_name == "list_symbols":
                result = self.route_search(workspace, "list_type", arguments)
            elif tool_name == "explore_file":
                result = self.route_search(workspace, "file_symbols", arguments)
            elif tool_name == "search_in_files":
                result = self.route_search(workspace, "search_file", arguments)

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        except Exception:
            # Let exceptions propagate as requested - no fallback handling
            raise


def main():
    """Main MCP server loop."""
    server = WorkspaceAwareSearchServer()

    # Read from stdin in a loop
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            # Return error response but let exceptions propagate for debugging
            error_response = {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
            # Re-raise for debugging
            raise


if __name__ == "__main__":
    main()
