# Code Review MCP Server

## Installation
✅ **INSTALLED**: The code review MCP server is now available at `indexing/mcp_code_review_server.py`

## Usage

### Set API Key
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Use in Claude Code
The MCP server will be automatically available as a tool. You can use it by asking Claude to review code:

```
Please review the code in /home/user/project using the review_code tool
```

### Manual Testing
```bash
# Test tools list
echo '{"method": "tools/list", "params": {}}' | ./venv/bin/python3 indexing/mcp_code_review_server.py

# Test code review (requires API key)
echo '{"method": "tools/call", "params": {"name": "review_code", "arguments": {"directory": "/path/to/code", "model": "gemini-1.5-flash"}}}' | ./venv/bin/python3 indexing/mcp_code_review_server.py
```

## Tool Parameters

**Tool Name**: `review_code`

**Required**:
- `directory`: Absolute path to directory to review

**Optional**:
- `focus_areas`: Array of focus areas (e.g., ["security", "performance"])
- `model`: "gemini-1.5-flash" (cheap) or "gemini-2.0-pro-exp" (expensive, default)
- `max_file_size`: Maximum file size in bytes (default: 1048576)

## Response Format

The tool returns a comprehensive review including:
- Review summary with model used, files reviewed, token usage, and cost
- Detailed code review from Gemini
- Collection details showing any skipped files

## Source Files

The MCP server uses components from `reviewer/src/`:
- `file_collector.py`: Collects and filters source files
- `gemini_client.py`: Handles Gemini API communication
- `review_formatter.py`: Formats review prompts

## Logging

Logs are written to `~/.claude/code_review.log` to avoid interfering with MCP communication.
