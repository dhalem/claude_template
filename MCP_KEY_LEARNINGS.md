# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# MCP Server Key Learnings - 2025

This document summarizes critical discoveries made while debugging MCP (Model Context Protocol) server issues.

## 🚨 Most Important Discoveries

### 1. **Claude Code CLI and Claude Desktop are COMPLETELY DIFFERENT**:
- Claude Desktop: Automatically loads `.mcp.json` from project root
- Claude Code CLI: Requires manual `claude mcp add` commands
- This was the root cause of "servers not working" - they weren't registered!

### 2. **Cross-Workspace Issue - The CRITICAL Problem**:
- MCP servers with hardcoded paths only work in the original workspace
- Project-specific `.mcp.json` files create workspace dependencies
- **Solution**: Central installation + user scope registration

## Critical Learnings

### 1. Configuration Precedence
- Project-specific `.mcp.json` takes precedence over global config
- Claude Code searches for `.mcp.json` in project root FIRST
- If `.mcp.json` points to non-existent paths, servers fail silently

### 2. Debugging Methodology
- **ALWAYS read FULL debug output** - never filter with grep initially
- Missing MCP messages in debug = servers not loaded at all
- `[DEBUG] MCP server "name": Tool call succeeded` = working correctly

### 3. Configuration Scopes (CRITICAL)
Claude Code CLI has three scopes:
- **local**: Project-specific, stored in local config
- **user**: User-wide, works across all workspaces
- **project**: Shared via `.mcp.json` file

**For cross-workspace support, ALWAYS use `user` scope!**

### 4. Testing Commands That Actually Work
```bash
# For automated testing without permission prompts
claude --debug --dangerously-skip-permissions -p 'test'

# Check if servers are registered (CLI only)
claude mcp list

# WRONG: Local/project scope (workspace-specific)
claude mcp add server-name /local/path

# CORRECT: User scope (cross-workspace)
claude mcp add server-name -s user /central/path
```

### 5. Protocol Requirements
- Must use protocol version `2024-11-05`
- Servers must return `list[Tool]` not `ListToolsResult`
- Never write to stdout - breaks JSON-RPC communication
- Use `stdio_server()` from `mcp.server.stdio`

### 6. Common Failure Patterns
1. **No MCP output**: Servers not registered with CLI
2. **Connection closed**: Import errors or missing dependencies
3. **Tool recognized but fails**: Server crashes during execution
4. **Hardcoded paths**: `/home/username/` paths break portability
5. **Wrong scope**: local/project scope limits servers to one workspace
6. **Central installation missing**: Servers point to non-existent paths

## Test Suite Integration

### Quick Verification (30 seconds)
```bash
./test_mcp_quick.sh
```

### Comprehensive Testing
```bash
# Full test suite with diagnostics
./test_mcp_servers.py

# Pytest integration (excludes slow tests for pre-commit)
pytest tests/test_mcp_integration.py -m "not slow"

# Run all tests including MCP
./run_tests.sh
```

### Pre-commit Integration
MCP tests are automatically run via `run_tests.sh` in pre-commit hooks:
- Quick protocol tests run on every commit
- Slow integration tests excluded from pre-commit
- Non-blocking warnings for MCP issues (won't prevent commits)

## Setup Checklist for Cross-Workspace Support

1. **Install Claude Code CLI** (if not present)
2. **Run central installation**: `./install-mcp-central.sh`
3. **Register for user scope**: `./register-mcp-global.sh`
4. **Set environment variables**: `export GEMINI_API_KEY="..."`
5. **Test cross-workspace**: `./test_mcp_other_workspace.sh /tmp/test`
6. **Verify user scope**: `claude mcp list` (should work from any directory)

## File Organization

- **Tests**:
  - `test_mcp_quick.sh` - Bash quick test
  - `test_mcp_servers.py` - Python comprehensive test
  - `tests/test_mcp_integration.py` - Pytest integration
- **Documentation**:
  - `MCP_TESTING_GUIDE.md` - How to test
  - `MCP_SERVER_TROUBLESHOOTING.md` - Debug guide
  - `MCP_COMPREHENSIVE_ANALYSIS.md` - Deep technical analysis
- **Servers**:
  - `indexing/mcp_review_server.py` - Code review server
  - `indexing/mcp_search_server.py` - Code search server

## Why This Matters

The distinction between Claude Desktop and Claude Code CLI wasted hours of debugging time. The servers were working perfectly - they just weren't registered with the CLI. This highlights the importance of:

1. Understanding tool differences before debugging
2. Reading complete output instead of filtering
3. Testing the simplest case first (is it even loaded?)
4. Documenting platform-specific behaviors

Remember: When MCP servers "don't work", first check if they're registered with `claude mcp list`!
