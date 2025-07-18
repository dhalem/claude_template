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

"""MCP server for code review using the official MCP library."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Add src to path for imports (handles both dev and installed locations)
# Handle case where __file__ might not be defined
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # If __file__ is not defined, try to use sys.argv[0] or fallback
    if sys.argv and sys.argv[0]:
        current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Last resort: assume we're in the correct directory
        current_dir = os.path.abspath(".")

# Try both locations: for development (src/) and installed (../src/)
for src_path in [
    os.path.join(current_dir, "src"),      # Development location
    os.path.join(current_dir, "..", "src")  # Installed location
]:
    if os.path.exists(src_path):
        sys.path.insert(0, src_path)
        break

from file_collector import FileCollector
from gemini_client import GeminiClient
from review_formatter import ReviewFormatter

# Set up logging
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main MCP server function."""
    server = Server("code-review")

    # Initialize components
    file_collector = FileCollector()
    review_formatter = ReviewFormatter()
    default_model = "gemini-2.0-pro-exp"

    logger.info("Code Review MCP Server starting")

    @server.list_tools()
    async def handle_list_tools() -> List[Dict[str, Any]]:
        """List available tools."""
        return [
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

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle tool calls."""
        if name != "review_code":
            raise ValueError(f"Unknown tool: {name}")

        try:
            # Extract parameters
            directory = arguments.get("directory")
            focus_areas = arguments.get("focus_areas")
            model = arguments.get("model", default_model)
            max_file_size = arguments.get("max_file_size", 1024 * 1024)

            # Validate directory
            if not directory:
                raise ValueError("Missing required parameter: directory")

            directory_path = Path(directory).resolve()
            if not directory_path.exists():
                raise ValueError(f"Directory does not exist: {directory_path}")

            if not directory_path.is_dir():
                raise ValueError(f"Path is not a directory: {directory_path}")

            logger.info(f"Starting code review for: {directory_path}")

            # Initialize file collector with custom max size
            file_collector.max_file_size = max_file_size

            # Collect files
            files = file_collector.collect_files(str(directory_path))

            if not files:
                raise ValueError("No files found to review")

            # Generate file tree
            file_tree = file_collector.get_file_tree()

            # Format review request
            claude_md_path = directory_path / "CLAUDE.md"
            claude_md_path = str(claude_md_path) if claude_md_path.exists() else None

            review_prompt = review_formatter.format_review_request(
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
            collection_summary = file_collector.get_collection_summary()

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

            return [{
                "type": "text",
                "text": response
            }]

        except Exception as e:
            logger.error(f"Error in review_code: {e}")
            raise

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        init_options = InitializationOptions(
            server_name="code-review",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
