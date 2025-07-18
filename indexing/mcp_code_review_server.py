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

"""MCP server for code review functionality."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add reviewer src to path for imports
reviewer_src = os.path.join(os.path.dirname(__file__), "..", "reviewer", "src")
sys.path.insert(0, reviewer_src)

from file_collector import FileCollector
from gemini_client import GeminiClient
from review_formatter import ReviewFormatter

# Configure logging to a file to avoid interfering with MCP communication
log_file = Path.home() / ".claude" / "code_review.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        # Don't log to stderr to avoid interfering with MCP protocol
    ]
)
logger = logging.getLogger(__name__)


class MCPCodeReviewServer:
    """MCP server for code review functionality."""

    def __init__(self):
        self.file_collector = FileCollector()
        self.review_formatter = ReviewFormatter()
        self.default_model = "gemini-2.0-pro-exp"

        logger.info("Code Review MCP Server initialized")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return self._list_tools()
        elif method == "tools/call":
            return self._call_tool(params)
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    def _list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
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
                                "description": "Optional: Specific areas to focus on (e.g., 'security', 'performance')"
                            },
                            "model": {
                                "type": "string",
                                "description": "Optional: Gemini model to use (default: gemini-2.0-pro-exp)",
                                "enum": ["gemini-1.5-flash", "gemini-2.0-pro-exp"]
                            },
                            "max_file_size": {
                                "type": "number",
                                "description": "Optional: Maximum file size in bytes (default: 1048576)"
                            }
                        },
                        "required": ["directory"]
                    }
                }
            ]
        }

    def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "review_code":
                result = self._review_code(arguments)
            else:
                return {
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

            return {"content": [{"type": "text", "text": result}]}

        except Exception as e:
            logger.error(f"Error in tool call: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    def _review_code(self, args: Dict[str, Any]) -> str:
        """Perform code review."""
        directory = args.get("directory")
        focus_areas = args.get("focus_areas")
        model = args.get("model", self.default_model)
        max_file_size = args.get("max_file_size", 1024 * 1024)  # 1MB default

        # Validate directory
        if not directory:
            raise ValueError("Missing required parameter: directory")

        directory_path = Path(directory).resolve()
        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")

        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

        logger.info(f"Starting code review for: {directory_path}")

        # Initialize file collector with custom max size if provided
        self.file_collector.max_file_size = max_file_size

        # Collect files
        files = self.file_collector.collect_files(str(directory_path))

        if not files:
            raise ValueError("No files found to review")

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

        # Initialize Gemini client
        gemini_client = GeminiClient(model=model)

        # Get review from Gemini
        logger.info(f"Sending review request to Gemini ({model})")
        review_text = gemini_client.review_code(review_prompt)

        # Get usage and collection statistics
        usage = gemini_client.get_usage_report()
        collection_summary = self.file_collector.get_collection_summary()

        # Format comprehensive response
        response = f"""# Code Review Report

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

        logger.info(f"Review completed. Files: {collection_summary['files_collected']}, "
                    f"Tokens: {usage['total_tokens']}, Cost: ${usage['estimated_cost']:.6f}")

        return response


def main():
    """Main MCP server loop."""
    server = MCPCodeReviewServer()

    # Read from stdin in a loop
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            error_response = {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
