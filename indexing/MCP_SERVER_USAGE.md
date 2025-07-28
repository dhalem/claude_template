# MCP Server Usage Guide

## Overview
This directory contains two MCP (Model Context Protocol) servers for Claude Code integration:

1. **code-search**: Search code symbols, content, and files using indexed database
2. **code-review**: AI-powered code review using Google Gemini

**Repository**: [github.com/dhalem/claude_template](https://github.com/dhalem/claude_template)

## Recent Architecture Updates
The code review server has been refactored with a shared component architecture:
- **BaseCodeAnalyzer**: Provides common workflow and parameter handling
- **ReviewCodeAnalyzer**: Specializes the base analyzer for code review
- **BugFindingAnalyzer**: New analyzer for focused bug detection (Phase 3)
- **Enhanced Response Parsing**: Robust JSON extraction from AI responses
- **Unified Error Handling**: Consistent user experience across all tools

## Installation and Setup

**Prerequisites:**
- Python virtual environment activated (`source venv/bin/activate`)
- For code-review: `GEMINI_API_KEY` environment variable set

**Installation:**
```bash
# For Claude Desktop (automatic .mcp.json detection)
./install-mcp-servers.sh

# For Claude Code CLI (requires manual registration)
./install-mcp-central.sh
claude mcp add code-search /home/$USER/.claude/mcp/central/venv/bin/python /home/$USER/.claude/mcp/central/code-search/server.py
claude mcp add code-review /home/$USER/.claude/mcp/central/venv/bin/python /home/$USER/.claude/mcp/central/code-review/server.py
```

## Code Search Server (`code-search`)

**Purpose**: Search through indexed codebase for symbols, content, and files

**Server File**: `mcp_search_server.py`

**Available Tools:**

### 1. `search_code` - Search for code symbols by name, content, or file path
**Parameters:**
- `query` (required): Search query (supports * and ? wildcards)
- `search_type` (optional): "name" (default), "content", or "file"
- `symbol_type` (optional): "function", "class", "method", or "variable"
- `limit` (optional): Maximum results (default: 50)

**Examples:**
```bash
# Search for functions containing "parse"
search_code query="parse*" search_type="name" symbol_type="function"

# Search file content for "TODO"
search_code query="TODO" search_type="content"

# Find files with "config" in name
search_code query="*config*" search_type="file"
```

### 2. `list_symbols` - List all symbols of a specific type
**Parameters:**
- `symbol_type` (required): "function", "class", "method", or "variable"
- `limit` (optional): Maximum results (default: 100)

**Examples:**
```bash
# List all classes
list_symbols symbol_type="class"

# List first 20 functions
list_symbols symbol_type="function" limit=20
```

### 3. `get_search_stats` - Get statistics about the code index database
**Parameters:** None required

**Returns:** Database statistics including total symbols, files, and breakdown by type

**Requirements:**
- Code index database (`.code_index.db`) must exist
- Run `./start-indexer.sh` if database missing
- Server searches for database in: current directory, parent directories (3 levels), home directory, `/app/`

## Code Review Server (`code-review`)

**Purpose**: Perform comprehensive AI-powered code review using Google Gemini

**Server File**: `mcp_review_server.py`

**Available Tools:**

### 1. `review_code` - Perform comprehensive code review of a directory
**Parameters:**
- `directory` (required): Absolute path to directory to review
- `focus_areas` (optional): Array of specific focus areas (e.g., ["security", "performance"])
- `model` (optional): Gemini model - "gemini-1.5-flash" or "gemini-2.5-pro" (default)
- `max_file_size` (optional): Maximum file size in bytes (default: 1048576)

**Examples:**
```bash
# Basic code review
review_code directory="/path/to/project"

# Security-focused review
review_code directory="/path/to/project" focus_areas=["security", "error_handling"]

# Use different model with larger file limit
review_code directory="/path/to/project" model="gemini-2.5-pro" max_file_size=2097152
```

### 2. `analyze_files` - Analyze specific files with custom prompt
**NEW TOOL**: Analyze specific files with a dynamic, user-defined prompt for flexible code analysis.

**Parameters:**
- `file_paths` (required): Array of absolute file paths to analyze
- `prompt` (required): Custom analysis prompt for Gemini
- `model` (optional): Gemini model - "gemini-1.5-flash" or "gemini-2.5-pro" (default)
- `max_file_size` (optional): Maximum file size in bytes (default: 1048576)

**Examples:**
```bash
# Security vulnerability scan
analyze_files file_paths=["/path/to/auth.py", "/path/to/db.py"] prompt="Scan these files for security vulnerabilities, especially SQL injection, XSS, and authentication bypasses. Provide specific line numbers and remediation steps."

# Performance analysis
analyze_files file_paths=["/path/to/api.py"] prompt="Analyze this API code for performance bottlenecks. Look for N+1 queries, inefficient loops, memory leaks, and suggest optimizations."

# Code modernization
analyze_files file_paths=["/path/to/legacy.py", "/path/to/old_utils.py"] prompt="Suggest modernization improvements for these Python files. Focus on type hints, async/await patterns, and current best practices."

# Documentation review
analyze_files file_paths=["/path/to/complex_module.py"] prompt="Review the documentation and comments in this file. Identify missing docstrings, unclear variable names, and suggest improvements for readability."

# Architecture analysis
analyze_files file_paths=["/path/to/models.py", "/path/to/views.py", "/path/to/serializers.py"] prompt="Analyze the architecture of these Django components. Check for proper separation of concerns, adherence to MVC patterns, and suggest structural improvements."

```

### Tool Comparison: `review_code` vs `analyze_files`

| Feature | `review_code` | `analyze_files` |
|---------|---------------|-----------------|
| **Input** | Directory path | Specific file paths |
| **Prompt** | Fixed code review template | Custom user-defined prompt |
| **Use Case** | Comprehensive project review | Targeted analysis with specific goals |
| **File Discovery** | Automatic (respects gitignore) | Manual selection |
| **Focus Areas** | Predefined categories | Completely flexible |
| **Best For** | New projects, general review | Specific issues, custom analysis |

**When to use `review_code`:**
- Initial project assessment
- General code quality review
- Comprehensive security/performance audit
- Following standardized review practices

**When to use `analyze_files`:**
- Investigating specific issues
- Targeted security scans
- Code modernization tasks
- Custom analysis requirements
- Educational code walkthroughs

**Features:**
- Automatic file collection (respects gitignore patterns)
- Supports multiple programming languages (.py, .js, .ts, .go, .rs, etc.)
- Includes project context (CLAUDE.md file if present)
- Usage tracking and cost estimation
- Comprehensive file tree analysis
- Excludes common build/cache directories

**File Types Supported:**
- **Source**: .py, .js, .jsx, .ts, .tsx, .rs, .go, .java, .c, .cpp, .h, .hpp, .sh, .bash
- **Config**: .json, .yaml, .yml, .toml, .ini
- **Documentation**: .md, .rst, .txt

**Requirements:**
- `GEMINI_API_KEY` environment variable
- Directory must exist and be readable
- Files must be under max_file_size limit

## Supporting Components

### Core Analysis Components

#### BaseCodeAnalyzer (`src/base_code_analyzer.py`)
Base class providing common functionality for all code analysis tools:
- Parameter validation and standardization
- File collection and processing orchestration
- Result formatting and error handling
- Usage tracking integration

#### ReviewCodeAnalyzer (`src/review_code_analyzer.py`)
Specialized analyzer for comprehensive code review:
- Inherits all BaseCodeAnalyzer functionality
- Customized prompts for code quality analysis
- Review-specific result formatting

#### BugFindingAnalyzer (`src/bug_finding_analyzer.py`)
Specialized analyzer for bug detection (Phase 3):
- Focused on security vulnerabilities and errors
- Deep analysis of potential issues
- Bug-specific result formatting

### AI Communication

#### GeminiClient (`src/gemini_client.py`)
Enhanced Google Gemini API client:
- Generic `analyze_content` method for multiple analysis types
- Robust JSON response extraction
- Built-in retry logic and error handling
- Cost estimation per analysis type

### Utility Components

#### CodeSearcher (`src/code_searcher.py`)
Handles database operations for code search functionality. Automatically finds and connects to the code index database.

#### FileCollector (`src/file_collector.py`)
Recursively scans directories for source and documentation files, respecting gitignore patterns and handling encoding gracefully.

#### ReviewFormatter (`src/review_formatter.py`)
Formats code review requests with file content, project context, and focus areas for optimal Gemini analysis.

#### BugFormatter (`src/bug_formatter.py`)
Specialized formatter for bug finding requests, emphasizing security and error detection patterns.

#### UsageTracker (`src/usage_tracker.py`)
Centralized usage and cost tracking across all analysis types:
- Per-tool usage statistics
- Cost projections and tracking
- Performance metrics collection

## Troubleshooting MCP Servers

**Connection Issues:**
```bash
# Test MCP server connectivity
claude --debug -p 'hello world'

# Look for connection messages in debug output:
# ✅ "MCP server 'code-search': Connected successfully"
# ✅ "MCP server 'code-review': Connected successfully"
# ❌ "Connection closed" or "MCP error -32000"
```

**Common Problems:**
1. **Servers not listed**: Run `claude mcp list` - if empty, re-run installation commands
2. **Database not found**: Run `./start-indexer.sh` to create code index
3. **Gemini API errors**: Verify `GEMINI_API_KEY` is set and valid
4. **Permission errors**: Ensure paths are absolute and accessible
5. **Protocol errors**: Verify MCP protocol version `2024-11-05`

**Log Locations:**
- Code Search: `~/.claude/mcp/code-search/logs/server_YYYYMMDD.log`
- Code Review: `~/.claude/mcp/code-review/logs/server_YYYYMMDD.log`

## MCP Server Protocol Requirements

**Critical Requirements for Claude Code CLI:**
- Must use protocol version `2024-11-05`
- STDIO transport only (no HTTP)
- Absolute paths in configuration
- No stdout/stderr output during operation (breaks JSON-RPC)
- File-based logging only

**Configuration Location:**
- Claude Desktop: `~/.config/claude/claude_desktop_config.json`
- Claude Code CLI: Use `claude mcp add` commands

## Testing MCP Integration

**Quick Test (30 seconds):**
```bash
./test_mcp_quick.sh
```

**Comprehensive Test:**
```bash
./test_mcp_servers.py
pytest tests/test_mcp_integration.py -v
```

**Manual Server Test:**
```bash
# Test individual server startup
/home/$USER/.claude/mcp/central/venv/bin/python \
  /home/$USER/.claude/mcp/central/code-search/server.py
```

**Expected Startup Messages:**
- Code Search: "Code Search MCP Server starting"
- Code Review: "Code Review MCP Server starting"

## Best Practices

1. **Always activate virtual environment** before using MCP servers
2. **Check logs** when troubleshooting connection issues
3. **Use absolute paths** in all configurations
4. **Test connectivity** with debug mode before important operations
5. **Monitor usage** for code-review server (tracks tokens and cost)
6. **Keep index updated** by running indexer regularly
7. **Use appropriate models** - flash for quick reviews, pro for comprehensive analysis
8. **Set reasonable limits** to avoid API rate limits and costs

## Development and Updates

When modifying the MCP servers:

1. **Update this documentation** to reflect any API changes
2. **Test both servers** with the test suite
3. **Update version numbers** in server initialization
4. **Check protocol compatibility** with current MCP standard
5. **Verify logging** doesn't interfere with STDIO protocol

**Server Locations:**
- `mcp_search_server.py` - Main search server
- `mcp_review_server.py` - Main review server
- `src/` - Supporting modules and utilities

## Architecture Benefits

The shared component architecture provides:

### Code Reusability
- **70%+ shared code** between review and bug finding tools
- Common parameter validation and error handling
- Unified file collection and processing
- Consistent usage tracking across all tools

### Maintainability
- Single source of truth for common functionality
- Bug fixes automatically benefit all analysis tools
- Consistent behavior across different analysis types
- Simplified testing with isolated components

### Extensibility
- Easy to add new analysis types (security, performance, etc.)
- New analyzers inherit all base functionality
- Plug-and-play architecture for new tools
- Minimal changes required to existing code

### Performance
- Optimized file collection shared by all tools
- Efficient AI communication with retry logic
- Smart caching opportunities in base components
- Consistent performance characteristics

This documentation should be updated whenever the server APIs or functionality change.
