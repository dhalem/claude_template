#!/bin/bash
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Code Review MCP Server...${NC}"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MCP_DIR="$HOME/.claude/mcp/code-review"

# Create MCP directory structure
echo "Creating MCP directory structure..."
mkdir -p "$MCP_DIR"/{bin,src,venv,logs}

# Copy the reviewer source files
echo "Copying source files..."
cp -v "$SCRIPT_DIR/src/"*.py "$MCP_DIR/src/" || {
    echo -e "${RED}Error: Could not find source files in $SCRIPT_DIR/src/${NC}"
    echo "Make sure you're running this from the reviewer directory"
    exit 1
}

# Copy the MCP server script
echo "Copying MCP server..."
cat > "$MCP_DIR/bin/server.py" << 'EOF'
#!/usr/bin/env python3
"""MCP server for code review using the official MCP library with proper types."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, "..", "src"))

from file_collector import FileCollector
from gemini_client import GeminiClient
from review_formatter import ReviewFormatter

# Set up logging
LOG_DIR = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        # Don't log to stderr to avoid interfering with MCP protocol
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
    async def handle_list_tools() -> list[Tool]:
        """List available tools."""
        tool = Tool(
            name="review_code",
            description="Perform a comprehensive code review of a directory using Gemini AI",
            inputSchema={
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
        )
        return [tool]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle tool calls."""
        try:
            if name != "review_code":
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                )

            # Extract arguments
            directory = arguments.get("directory")
            focus_areas = arguments.get("focus_areas", [])
            model = arguments.get("model", default_model)
            max_file_size = arguments.get("max_file_size", 1048576)  # 1MB default

            if not directory:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: directory parameter is required")]
                )

            directory_path = Path(directory)
            if not directory_path.exists():
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: Directory '{directory}' does not exist")]
                )

            if not directory_path.is_dir():
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: '{directory}' is not a directory")]
                )

            logger.info(f"Starting code review for: {directory}")

            # Set file size limit
            file_collector.max_file_size = max_file_size

            # Collect files
            files = file_collector.collect_files(str(directory_path))

            if not files:
                return CallToolResult(
                    content=[TextContent(type="text", text="No files found to review")]
                )

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

            # Format final response
            response = f"""# Code Review Report

## Summary
- **Directory**: {directory}
- **Model**: {model}
- **Files Reviewed**: {collection_summary['files_collected']}
- **Total Size**: {collection_summary['total_size']:,} bytes
- **Focus Areas**: {', '.join(focus_areas) if focus_areas else 'General review'}

## Usage Statistics
- **Total Tokens**: {usage['total_tokens']:,}
- **Input Tokens**: {usage['input_tokens']:,}
- **Output Tokens**: {usage['output_tokens']:,}
- **Estimated Cost**: ${usage['estimated_cost']:.6f}

---

{review_text}

---

*Generated by Code Review MCP Server using {model}*
"""

            logger.info(f"Review completed. Files: {collection_summary['files_collected']}, "
                       f"Tokens: {usage['total_tokens']}, Cost: ${usage['estimated_cost']:.6f}")

            return CallToolResult(
                content=[TextContent(type="text", text=response)]
            )

        except Exception as e:
            logger.error(f"Error in review_code: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        init_options = InitializationOptions(
            server_name="code-review",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x "$MCP_DIR/bin/server.py"

# Create the start script
echo "Creating start script..."
cat > "$MCP_DIR/start-server.sh" << 'EOF'
#!/bin/bash
# Startup script for MCP code review server

# Get the current working directory (where Claude Code is running)
export MCP_CWD="$PWD"

# Run the server with its own venv
exec "$HOME/.claude/mcp/code-review/venv/bin/python3" "$HOME/.claude/mcp/code-review/bin/server.py"
EOF

chmod +x "$MCP_DIR/start-server.sh"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$MCP_DIR/venv"

# Install dependencies
echo "Installing dependencies..."
"$MCP_DIR/venv/bin/pip" install --upgrade pip
"$MCP_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Register with Claude Code
echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "\nTo register the MCP server with Claude Code, run:"
echo -e "${YELLOW}claude mcp add code-review stdio bash $MCP_DIR/start-server.sh${NC}"
echo -e "\nThen restart Claude Code for the changes to take effect."
echo -e "\n${GREEN}Usage:${NC}"
echo -e "After restarting, you can use the code review tool with:"
echo -e "  'Please review the code in /path/to/directory'"
echo -e "\nMake sure to set your Gemini API key:"
echo -e "${YELLOW}export GEMINI_API_KEY='your-api-key-here'${NC}"
