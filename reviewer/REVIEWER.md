# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Code Review MCP Server

## Overview

An MCP (Model Context Protocol) server that provides automated code review functionality using external LLMs, starting with Gemini 2.5 Pro. The server accepts a directory path, collects all source and documentation files, includes project context (CLAUDE.md), and sends everything to an LLM for comprehensive code review.

## Architecture

### Components

1. **MCP Server** (`code_review_server.py`)
   - Implements the MCP protocol
   - Exposes a `review_code` tool
   - Handles file collection and LLM communication
   - No caching - each review is fresh

2. **File Collector** (`file_collector.py`)
   - Recursively scans directories
   - Filters for source and documentation files
   - Respects gitignore patterns
   - Handles file encoding gracefully

3. **Review Formatter** (`review_formatter.py`)
   - Formats collected files for LLM consumption
   - Includes CLAUDE.md context
   - Structures the review request prompt

4. **Gemini Client** (reuse from `hooks/python/guards/meta_cognitive_guard.py`)
   - Handles Gemini API communication
   - Manages rate limiting and retries
   - Processes review responses

### File Types to Include

**Source Files:**
- Python: `*.py`
- JavaScript/TypeScript: `*.js`, `*.jsx`, `*.ts`, `*.tsx`
- Rust: `*.rs`
- Go: `*.go`
- Java: `*.java`
- C/C++: `*.c`, `*.cpp`, `*.h`, `*.hpp`
- Shell: `*.sh`, `*.bash`
- Configuration: `*.json`, `*.yaml`, `*.yml`, `*.toml`, `*.ini`

**Documentation:**
- Markdown: `*.md`
- RestructuredText: `*.rst`
- Plain text: `*.txt`
- README files (any case)

**Always Include:**
- `CLAUDE.md` (if exists in project root)
- `README.md` (if exists)
- `pyproject.toml`, `package.json`, `Cargo.toml` (project configs)

**Exclude:**
- Binary files
- `.git` directory
- `node_modules`, `venv`, `.venv`, `__pycache__`
- Build directories: `dist`, `build`, `target`
- Log files: `*.log`
- Temporary files: `*.tmp`, `*.temp`

## MCP Protocol Implementation

### Tool Definition

```json
{
  "name": "review_code",
  "description": "Perform a comprehensive code review of a directory using Gemini 2.5 Pro",
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
      }
    },
    "required": ["directory"]
  }
}
```

### Review Prompt Template

```
You are an expert code reviewer. Please review the following codebase comprehensively.

Project Context:
{claude_md_content}

Codebase Structure:
{file_tree}

Code Files:
{code_files}

Please provide a detailed review covering:
1. **Architecture & Design**: Overall structure, patterns, and design decisions
2. **Code Quality**: Readability, maintainability, and adherence to best practices
3. **Security**: Potential vulnerabilities or security concerns
4. **Performance**: Bottlenecks or optimization opportunities
5. **Error Handling**: Robustness, error recovery, and edge case handling
6. **Testing**: Test coverage and quality
7. **Documentation**: Completeness and clarity
8. **Dependencies**: Appropriateness and security of external dependencies

{focus_areas_prompt}

Format your review as follows:
- Executive Summary (2-3 paragraphs)
- Strengths (bullet points)
- Areas for Improvement (organized by severity: Critical, Major, Minor)
- Specific Recommendations (actionable items)
- Code Examples (where applicable)
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. Set up MCP server boilerplate
2. Implement file collection with proper filtering
3. Create review formatter with template system
4. Integrate existing Gemini client code

### Phase 2: Review Engine
1. Build comprehensive prompt generation
2. Handle large codebases (chunking if needed)
3. Implement response parsing and formatting
4. Add error handling and retries

### Phase 3: Enhancements
1. Implement diff-based reviews (changes only)
2. Support for multiple LLM providers
3. Integration with git hooks (future)
4. Add review history tracking

## Configuration

### Environment Variables
```bash
GEMINI_API_KEY=<your-api-key>
GEMINI_MODEL=gemini-2.0-pro-exp  # Default model
REVIEW_MAX_FILE_SIZE=1048576      # 1MB max per file
REVIEW_MAX_TOTAL_SIZE=10485760    # 10MB max total
```

### Example Usage

```bash
# Start the MCP server
python reviewer/code_review_server.py

# In Claude Code or other MCP client:
# Use the review_code tool with directory: "/absolute/path/to/project"
```

## Testing Strategy

1. **Unit Tests**:
   - File collection with various patterns
   - Prompt formatting with different inputs
   - Mock LLM responses

2. **Integration Tests**:
   - Test with sample codebases
   - Verify Gemini API integration
   - Handle rate limiting gracefully

3. **End-to-End Tests**:
   - Review this MCP server's own code
   - Review a complex project with multiple languages
   - Test error scenarios (API failures, large files)

## Security Considerations

1. **File Access**: Only read files, never write
2. **Path Validation**: Ensure absolute paths, prevent directory traversal
3. **API Key Management**: Use environment variables, never hardcode
4. **Content Filtering**: Skip binary files, limit file sizes
5. **Rate Limiting**: Respect API limits, implement backoff

## Future Enhancements

1. **Incremental Reviews**: Only review changed files
2. **PR Integration**: Automatic reviews on pull requests
3. **Custom Rules**: Project-specific review criteria
4. **Multiple LLMs**: Support for Claude, GPT-4, etc.
5. **Review History**: Track reviews over time
6. **IDE Integration**: VSCode extension for inline reviews

## Dependencies

- `mcp` - Model Context Protocol SDK
- `google-generativeai` - Gemini API client
- `pathlib` - File system operations
- `gitignore_parser` - Respect .gitignore files
- `aiofiles` - Async file operations
