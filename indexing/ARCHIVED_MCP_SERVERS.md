# Archived MCP Server Implementations

These MCP server implementations have been superseded by the official installation in the `reviewer/` directory.

## Archive Reason
Multiple experimental MCP server implementations were created during development. The canonical implementation is now:
- **Installation script**: `/reviewer/install_mcp_server.sh`
- **Installed location**: `~/.claude/mcp/code-review/`

## Archived Files
The following files are legacy implementations and should not be used:

1. `mcp_code_search_server.py` - Basic stdio implementation
2. `mcp_code_search_server_real.py` - Uses official MCP SDK
3. `mcp_code_search_server_global.py` - Global search variant
4. `mcp_code_search_server_workspace_aware.py` - Workspace-aware variant
5. `mcp_server_proper.py` - Another MCP SDK attempt
6. `mcp/simple_mcp_server.py` - Simple test implementation

## Note on mcp_code_review_server.py
This file remains as it contains the simple stdio implementation that may be useful for reference or debugging.

## Clean Installation
To properly install the code review MCP server:
```bash
cd reviewer/
./install_mcp_server.sh
```

Then follow the instructions to register with Claude Code.
