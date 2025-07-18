# Code Review MCP Server

An MCP (Model Context Protocol) server that provides automated code review functionality using Gemini AI.

## Features

- **Comprehensive File Collection**: Scans directories for source files (.py, .js, .ts, .rs, etc.) and documentation
- **Intelligent Filtering**: Respects .gitignore patterns and skips binary files
- **Multi-Model Support**: Uses Gemini 1.5 Flash for testing and Gemini 2.0 Pro for production reviews
- **Context-Aware**: Includes CLAUDE.md project context in reviews
- **Detailed Reporting**: Provides token usage, cost estimation, and collection statistics

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
# or
export GOOGLE_API_KEY="your-api-key-here"
```

## Usage

### As MCP Child Process (Recommended)

The server runs as a child process spawned by Claude Code, similar to the indexing MCP server.

**MCP Server Script**: `./mcp_code_review_server.py`

**Tool**: `review_code`

**Parameters**:
- `directory` (required): Absolute path to directory to review
- `focus_areas` (optional): Array of specific focus areas (e.g., ["security", "performance"])
- `model` (optional): Gemini model to use ("gemini-1.5-flash" or "gemini-2.0-pro-exp")
- `max_file_size` (optional): Maximum file size in bytes (default: 1048576)

**Example Usage in Claude Code**:
```
Please review the code in /home/user/project using the review_code tool, focusing on security and performance
```

### Manual Testing

Test the MCP server:
```bash
python test_mcp.py
```

### Testing Components

Run the simple test:
```bash
python test_simple.py
```

## Architecture

### Components

1. **FileCollector** (`src/file_collector.py`)
   - Recursively scans directories
   - Filters for relevant file types
   - Handles encoding gracefully
   - Respects .gitignore patterns

2. **GeminiClient** (`src/gemini_client.py`)
   - Interfaces with Gemini API
   - Tracks token usage and costs
   - Handles error responses

3. **ReviewFormatter** (`src/review_formatter.py`)
   - Formats code files for review
   - Includes project context (CLAUDE.md)
   - Structures review prompts

4. **MCPCodeReviewServer** (`mcp_code_review_server.py`)
   - Implements MCP protocol for child process communication
   - Synchronous stdin/stdout communication
   - Orchestrates review process
   - Formats responses

## File Types Supported

**Source Files:**
- Python (.py)
- JavaScript/TypeScript (.js, .jsx, .ts, .tsx)
- Rust (.rs)
- Go (.go)
- Java (.java)
- C/C++ (.c, .cpp, .h, .hpp)
- Shell scripts (.sh, .bash)

**Configuration:**
- JSON (.json)
- YAML (.yaml, .yml)
- TOML (.toml)
- INI (.ini)

**Documentation:**
- Markdown (.md)
- reStructuredText (.rst)
- Plain text (.txt)

## Review Categories

The review covers:
1. **Architecture & Design**: Overall structure and patterns
2. **Code Quality**: Readability and maintainability
3. **Security**: Potential vulnerabilities
4. **Performance**: Bottlenecks and optimizations
5. **Error Handling**: Robustness and edge cases
6. **Testing**: Coverage and quality
7. **Documentation**: Completeness and clarity
8. **Dependencies**: Appropriateness and security

## Configuration

Set these environment variables:
- `GEMINI_API_KEY`: Your Gemini API key
- `GOOGLE_API_KEY`: Alternative name for the API key

## Cost Management

- **Flash Model**: ~$0.00001 per 1k tokens (default for testing)
- **Pro Model**: ~$0.002 per 1k tokens (production reviews)
- Usage tracking and cost estimation included in responses

## Example Response

```markdown
# Code Review Report

## Review Summary
- **Model Used**: gemini-1.5-flash
- **Files Reviewed**: 25
- **Total Size**: 125,432 bytes
- **API Usage**: 1 calls, 15,234 tokens
- **Estimated Cost**: $0.000152

## Review

[Detailed review content from Gemini]

## Collection Details
- **Files Skipped**: 3
- **Skipped Files**: large_file.py (too large), binary.so (read error)
```

## Development

See `TEST_PLAN.md` for comprehensive testing strategy and `REVIEWER.md` for detailed architecture documentation.
