# MCP Server Installation Prompt

**🔧 Use this prompt to install MCP server documentation in any project:**

```
Please install the MCP server usage instructions from https://github.com/dhalem/claude_template/blob/main/indexing/MCP_SERVER_USAGE.md into my CLAUDE.md file. Add a comprehensive MCP Server section that includes:

1. **Installation instructions** for both Claude Desktop and Claude Code CLI
2. **Complete API reference** for both code-search and code-review MCP servers
3. **Troubleshooting guide** with common connection issues and solutions
4. **Testing procedures** for verifying MCP server functionality
5. **Best practices** for development and maintenance

The section should reference the GitHub repository at https://github.com/dhalem/claude_template and include all tool parameters, examples, and requirements. Make sure to include cross-workspace setup instructions for Claude Code CLI users.

If CLAUDE.md doesn't exist, create it and add the MCP server section. If it exists, add the MCP section without overwriting existing content.
```

## What This Installs

This prompt will add comprehensive MCP server documentation to your project's CLAUDE.md file, including:

### Code Search Server (`code-search`)
- **Purpose**: Search through indexed codebase for symbols, content, and files
- **Tools**: `search_code`, `list_symbols`, `get_search_stats`
- **Requirements**: Code index database (`.code_index.db`)

### Code Review Server (`code-review`)
- **Purpose**: AI-powered code review using Google Gemini
- **Tools**: `review_code` with focus areas and model selection
- **Requirements**: `GEMINI_API_KEY` environment variable

### Installation Coverage
- **Claude Desktop**: Automatic `.mcp.json` detection
- **Claude Code CLI**: Manual server registration commands
- **Cross-workspace setup**: Works from any directory once installed

### Troubleshooting & Testing
- Connection verification commands
- Log file locations
- Common problems and solutions
- Test suite integration

## Usage Notes

- **Safe**: Only adds documentation, no code changes
- **Non-destructive**: Won't overwrite existing CLAUDE.md content
- **Complete**: Includes all API parameters and examples
- **Up-to-date**: References the latest MCP protocol (2024-11-05)

The installed documentation will be kept in sync with the servers at https://github.com/dhalem/claude_template.
