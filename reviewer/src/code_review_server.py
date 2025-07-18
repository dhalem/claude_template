# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Code Review MCP Server.

Provides automated code review functionality using Gemini AI.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from file_collector import FileCollector
from gemini_client import GeminiClient
from review_formatter import ReviewFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeReviewServer:
    """MCP server for code review functionality."""

    def __init__(self):
        self.name = "code-review-server"
        self.version = "1.0.0"

        # Initialize components
        self.file_collector = FileCollector()
        self.review_formatter = ReviewFormatter()

        # Gemini client will be initialized per request with specified model
        self.default_model = "gemini-2.0-pro-exp"  # Production model by default

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        try:
            method = request.get("method")

            if method == "initialize":
                return await self._handle_initialize(request)
            elif method == "tools/list":
                return await self._handle_tools_list(request)
            elif method == "tools/call":
                return await self._handle_tools_call(request)
            else:
                return self._error_response(
                    request.get("id"),
                    -32601,
                    f"Method not found: {method}"
                )

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(
                request.get("id"),
                -32603,
                f"Internal error: {str(e)}"
            )

    async def _handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }

    async def _handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": "review_code",
                "description": "Perform a comprehensive code review of a directory using Gemini AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Absolute path to the directory to review"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Optional: Specific areas to focus on (e.g., 'security', 'performance', 'style')"
                        },
                        "include_patterns": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Optional: Additional file patterns to include"
                        },
                        "exclude_patterns": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Optional: Additional file patterns to exclude"
                        },
                        "model": {
                            "type": "string",
                            "description": "Optional: Gemini model to use (default: gemini-2.0-pro-exp)",
                            "enum": ["gemini-1.5-flash", "gemini-2.0-pro-exp"]
                        }
                    },
                    "required": ["directory"]
                }
            }
        ]

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": tools
            }
        }

    async def _handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        params = request.get("params", {})
        tool_name = params.get("name")

        if tool_name == "review_code":
            return await self._handle_review_code(request)
        else:
            return self._error_response(
                request.get("id"),
                -32601,
                f"Tool not found: {tool_name}"
            )

    async def _handle_review_code(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle review_code tool call."""
        try:
            params = request.get("params", {})
            arguments = params.get("arguments", {})

            # Extract parameters
            directory = arguments.get("directory")
            focus_areas = arguments.get("focus_areas")
            include_patterns = arguments.get("include_patterns")
            exclude_patterns = arguments.get("exclude_patterns")
            model = arguments.get("model", self.default_model)

            # Validate directory
            if not directory:
                return self._error_response(
                    request.get("id"),
                    -32602,
                    "Missing required parameter: directory"
                )

            # Ensure absolute path
            directory_path = Path(directory).resolve()
            if not directory_path.exists():
                return self._error_response(
                    request.get("id"),
                    -32602,
                    f"Directory does not exist: {directory_path}"
                )

            if not directory_path.is_dir():
                return self._error_response(
                    request.get("id"),
                    -32602,
                    f"Path is not a directory: {directory_path}"
                )

            # Collect files
            logger.info(f"Collecting files from: {directory_path}")
            files = self.file_collector.collect_files(str(directory_path))

            if not files:
                return self._error_response(
                    request.get("id"),
                    -32603,
                    "No files found to review"
                )

            # Generate file tree
            file_tree = self.file_collector.get_file_tree()

            # Format review request
            claude_md_path = directory_path / "CLAUDE.md"
            claude_md_path = str(claude_md_path) if claude_md_path.exists() else None

            review_prompt = self.review_formatter.format_review_request(
                files=files,
                file_tree=file_tree,
                focus_areas=focus_areas,
                claude_md_path=claude_md_path
            )

            # Initialize Gemini client with specified model
            gemini_client = GeminiClient(model=model)

            # Get review from Gemini
            logger.info(f"Sending review request to Gemini ({model})")
            review_text = gemini_client.review_code(review_prompt)

            # Get usage statistics
            usage = gemini_client.get_usage_report()
            collection_summary = self.file_collector.get_collection_summary()

            # Format response
            response_content = f"""# Code Review Report

## Review Summary
- **Model Used**: {usage['model']}
- **Files Reviewed**: {collection_summary['files_collected']}
- **Total Size**: {collection_summary['total_size']:,} bytes
- **API Usage**: {usage['call_count']} calls, {usage['total_tokens']} tokens
- **Estimated Cost**: ${usage['estimated_cost']:.6f}

## Review

{review_text}

## Collection Details
- **Files Skipped**: {collection_summary['files_skipped']}
- **Skipped Files**: {', '.join(collection_summary['skipped_files']) if collection_summary['skipped_files'] else 'None'}
"""

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": response_content
                        }
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Error in review_code: {e}")
            return self._error_response(
                request.get("id"),
                -32603,
                f"Review failed: {str(e)}"
            )

    def _error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


async def main():
    """Run the MCP server."""
    server = CodeReviewServer()

    logger.info(f"Starting {server.name} v{server.version}")

    # Simple stdio-based MCP server
    while True:
        try:
            # Read request from stdin
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )

            if not line:
                break

            # Parse JSON request
            try:
                request = json.loads(line.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                continue

            # Handle request
            response = await server.handle_request(request)

            # Send response to stdout - MCP protocol output
            print(json.dumps(response), flush=True)  # noqa: T201 MCP protocol output

        except KeyboardInterrupt:
            logger.info("Shutting down server")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())
