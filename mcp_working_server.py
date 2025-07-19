#!/home/dhalem/.claude/mcp/code-review/venv/bin/python
"""MCP server with absolute venv shebang."""

import asyncio
import os
import sys
from pathlib import Path

# Setup logging
log_dir = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "working_server.log"

def log(msg):
    with open(log_file, "a") as f:
        f.write(f"{msg}\n")

log("=== Server started ===")
log(f"Python: {sys.executable}")
log(f"Working dir: {os.getcwd()}")

# Import MCP
try:
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    log("MCP imports successful")
except Exception as e:
    log(f"ERROR importing MCP: {e}")
    sys.exit(1)

# Add src to path for local imports
script_dir = Path(__file__).parent.parent
src_path = script_dir / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
    log(f"Added to path: {src_path}")

# Import local modules
try:
    from file_collector import FileCollector
    from gemini_client import GeminiClient
    from review_formatter import ReviewFormatter
    log("Local imports successful")
except Exception as e:
    log(f"Warning: Could not import local modules: {e}")

async def main():
    log("main() started")

    server = Server("code-review")

    # Initialize components
    file_collector = FileCollector()
    review_formatter = ReviewFormatter()
    default_model = "gemini-2.5-pro"

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        log("handle_list_tools() called")
        return [
            Tool(
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
                            "items": {"type": "string"},
                            "description": "Optional: Specific areas to focus on"
                        },
                        "model": {
                            "type": "string",
                            "description": "Optional: Gemini model to use",
                            "enum": ["gemini-1.5-flash", "gemini-2.5-pro"]
                        }
                    },
                    "required": ["directory"]
                }
            )
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        log(f"handle_call_tool({name}) called")

        if name != "review_code":
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        try:
            directory = Path(arguments["directory"])

            # Collect files
            log(f"Collecting files from {directory}")
            files = file_collector.collect_files(
                directory=directory,
                extensions=None,
                exclude_patterns=None,
                max_file_size=arguments.get("max_file_size", 1048576),
                include_ignored=False
            )

            if not files:
                return [TextContent(type="text", text="No files found to review")]

            log(f"Found {len(files)} files")

            # Format file content
            file_contents = []
            for file_info in files[:50]:  # Limit to 50 files
                with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                file_contents.append({
                    'path': str(file_info.relative_path),
                    'content': content[:10000]  # Limit content size
                })

            # Perform review
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                return [TextContent(type="text", text="Error: GEMINI_API_KEY or GOOGLE_API_KEY not set")]

            gemini_client = GeminiClient(api_key=api_key)
            model = arguments.get("model", default_model)
            focus_areas = arguments.get("focus_areas", [])

            review = gemini_client.review_code(
                file_contents=file_contents,
                focus_areas=focus_areas,
                model=model
            )

            formatted_review = review_formatter.format_review(review, files)
            return [TextContent(type="text", text=formatted_review)]

        except Exception as e:
            log(f"Error in review_code: {e}")
            import traceback
            log(traceback.format_exc())
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Start server
    log("Starting stdio_server...")
    async with stdio_server() as (read_stream, write_stream):
        log("stdio_server started")

        init_options = InitializationOptions(
            server_name="code-review",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )

        log("Starting server.run()...")
        await server.run(read_stream, write_stream, init_options)
        log("server.run() completed")

if __name__ == "__main__":
    try:
        log("Starting asyncio event loop")
        asyncio.run(main())
        log("Event loop completed")
    except KeyboardInterrupt:
        log("Interrupted by user")
    except Exception as e:
        log(f"Fatal error: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
