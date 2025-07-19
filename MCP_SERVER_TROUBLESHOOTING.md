# MCP Server Troubleshooting Guide for Claude Code

## Overview
This guide provides comprehensive troubleshooting steps for MCP (Model Context Protocol) server issues with Claude Code, based on 2025 best practices and common debugging techniques.

**CRITICAL DISCOVERIES FROM DEBUGGING**:
1. Claude Code CLI and Claude Desktop handle MCP servers completely differently
2. Project-specific `.mcp.json` takes precedence over global configuration
3. Always read FULL debug output - filtering with grep will miss critical errors
4. MCP servers must be manually registered with Claude Code CLI using `claude mcp add`

## Common Issues and Solutions

### 1. "Connection Closed" Errors (MCP error -32000)

**Symptoms:**
- Claude Code shows: `MCP server "server-name": Connection failed: McpError: MCP error -32000: Connection closed`
- Servers appear to start but immediately disconnect

**Common Causes:**
- **Node/NPM Path Issues**: `npx` not found in system PATH
- **Protocol Version Mismatch**: Wrong MCP protocol version
- **Server Startup Failures**: Python import errors, missing dependencies
- **Timeout Issues**: Idle connections dropping after ~5 minutes

### 2. Critical: Claude Code CLI vs Desktop Differences

**IMPORTANT**: Claude Code CLI and Claude Desktop handle MCP servers differently:

- **Claude Desktop**: Automatically loads `.mcp.json` from project root
- **Claude Code CLI**: Requires manual server registration using `claude mcp add`

If using Claude Code CLI, you MUST first add servers before testing:
```bash
# Add servers from .mcp.json manually
claude mcp add code-search /path/to/python /path/to/server.py
claude mcp add code-review /path/to/python /path/to/server.py

# List configured servers
claude mcp list

# Then test
claude --debug -p 'test MCP'
```

#### Configuration Scopes (CRITICAL for Cross-Workspace Support)

Claude Code CLI has three configuration scopes:

- **`local`** (`-s local`): Project-specific, only works in current workspace
- **`user`** (`-s user`): User-wide, works across all workspaces
- **`project`** (`-s project`): Shared via `.mcp.json` file

**For cross-workspace support, ALWAYS use `user` scope:**
```bash
# WRONG: Local scope (workspace-specific)
claude mcp add server-name /path/to/server

# CORRECT: User scope (cross-workspace)
claude mcp add server-name -s user /path/to/server
```

**Common Cross-Workspace Issues:**
- Servers work in one workspace but not others
- "No MCP servers configured" in different directories
- Hardcoded paths in project-specific `.mcp.json`

**Solution:** Use central installation with user scope registration:
```bash
./install-mcp-central.sh      # Installs to ~/.claude/mcp/central/
./register-mcp-global.sh      # Registers with user scope
```

### 3. Debugging Steps (In Order)

#### Step 1: Enable Debug Mode
```bash
claude --debug -p 'hello world'

# For automated testing or when permission prompts interfere:
claude --debug --dangerously-skip-permissions -p 'hello world'
```
This shows detailed MCP connection information and server startup logs.

**Note**: `--mcp-debug` is deprecated, use `--debug` instead.

#### Step 2: Read the FULL Debug Output
**CRITICAL**: When debugging MCP issues, ALWAYS read the complete debug output without filtering. Do not use `grep` initially - you may miss critical error messages.

```bash
# Capture full output
claude --debug --dangerously-skip-permissions -p 'test' 2>&1 | tee debug.log

# Then search for specific patterns
cat debug.log | grep -i "mcp"
```

Look for these key indicators:
- `[DEBUG] MCP server "name": Calling MCP tool: tool_name` - Server is working
- `[DEBUG] MCP server "name": Tool call succeeded` - Call completed successfully
- Absence of any MCP messages - Servers not loaded at all

#### Step 3: Check Log Files
- **macOS/Linux**: `~/Library/Logs/Claude/mcp-server-*.log`
- **Windows**: `%APPDATA%\Claude\logs\`

Monitor logs in real-time:
```bash
tail -f ~/Library/Logs/Claude/mcp-server-*.log
```

#### Step 4: Test Server Manually
Test if the server starts correctly outside of Claude:
```bash
# For Python servers
/path/to/venv/bin/python /path/to/server.py

# For Node servers
npx -y @modelcontextprotocol/server-filesystem /path/to/directory
```

#### Step 5: Validate MCP Protocol
Send a test initialization request:
```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0.0"},"capabilities":{}},"id":1}' | /path/to/server
```

### 3. Configuration Best Practices

#### Use Absolute Paths
```json
{
  "mcpServers": {
    "server-name": {
      "command": "/absolute/path/to/python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/modules"
      }
    }
  }
}
```

#### Correct Protocol Version
Always use the current MCP protocol version: `2024-11-05`

#### Environment Variables
Expand variables like `${APPDATA}` to full paths in configuration.

### 4. Configuration File Locations

**CRITICAL: Project config takes precedence over global config!**

- **Project-specific**: `.mcp.json` in project root (CHECKED FIRST)
- **Global**:
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - Linux: `~/.config/claude/claude_desktop_config.json`

**Common Issue**: If you have a `.mcp.json` in your project pointing to non-existent paths, it will override your working global configuration, causing connection failures.

### 5. Server Requirements

#### Python MCP Servers
- **Protocol Version**: Must use `2024-11-05`
- **Dependencies**: `mcp` library installed in venv
- **Return Types**: Use `list[Tool]` not `ListToolsResult`
- **Logging**: Only to files, never stdout/stderr during operation
- **Environment**: Isolated virtual environment per server

#### Node MCP Servers
- **Node Version**: Compatible with system's Node.js
- **NPX Path**: Must be in system PATH
- **Dependencies**: All packages properly installed

### 6. Advanced Debugging

#### For Import Errors
```python
# Add to top of Python server
import sys
import os
print(f"Python: {sys.executable}", file=sys.stderr)
print(f"Path: {sys.path}", file=sys.stderr)
print(f"Working dir: {os.getcwd()}", file=sys.stderr)
```

#### For Protocol Issues
```python
# Log all MCP communication
import logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='/tmp/mcp_debug.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### 7. Verification Commands

#### Check Server Status
```bash
# In Claude Code
/mcp
```
Shows connection status of all configured servers.

#### List Available Tools
After successful connection, tools appear as:
- `mcp__server-name__tool-name`

### 8. Common Fixes

#### Fix 1: Path Issues
- Use absolute paths for all commands and arguments
- Verify Python/Node executables exist at specified paths
- Check that virtual environments are properly activated

#### Fix 2: Permission Issues
- Ensure server files are executable: `chmod +x server.py`
- Check file ownership and permissions
- Verify write access to log directories

#### Fix 3: Dependency Issues
- Reinstall MCP library: `pip install --upgrade mcp`
- Check for conflicting package versions
- Use isolated virtual environments

#### Fix 4: Protocol Issues
- Update MCP library to latest version
- Use correct protocol version in server code
- Ensure proper JSON-RPC message format

### 9. Installation Methods Comparison

#### Central Installation (Recommended)
```
~/.claude/mcp/central/
├── venv/                   # Shared virtual environment
├── code-search/
│   └── server.py
└── code-review/
    └── server.py
```

#### Auto-Discovery Structure
```
~/.claude/mcp/server-name/
├── bin/server.py          # Must be named exactly server.py
├── venv/                  # Isolated environment
└── logs/
```

### 10. Emergency Fixes

#### Complete Reset
1. Remove all MCP configuration:
   ```bash
   rm ~/.config/claude/claude_desktop_config.json
   rm .mcp.json
   ```

2. Reinstall servers from scratch
3. Start with minimal configuration
4. Test one server at a time

#### Minimal Test Configuration
```json
{
  "mcpServers": {
    "test": {
      "command": "echo",
      "args": ["hello"]
    }
  }
}
```

### 11. Resources

- **Official Documentation**: https://modelcontextprotocol.io/
- **Claude Code Issues**: https://github.com/anthropics/claude-code/issues
- **Community Support**: Anthropic Discord server
- **Debug Flag**: Always use `--mcp-debug` when troubleshooting

### 12. Prevention

- **Regular Updates**: Keep MCP library and Claude Code updated
- **Testing**: Test servers independently before integrating
- **Monitoring**: Set up log rotation and monitoring
- **Backup**: Keep working configurations backed up
- **Documentation**: Document custom server configurations

## Quick Setup Guide for Claude Code CLI

1. **Check if servers are configured**:
   ```bash
   claude mcp list
   ```

2. **If no servers listed, add them from .mcp.json**:
   ```bash
   # Extract and run add commands
   cat .mcp.json | jq -r '.mcpServers | to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"' | bash
   ```

3. **Test the connection**:
   ```bash
   claude --debug --dangerously-skip-permissions -p 'Use mcp__code-review__review_code to review a file' 2>&1 | tee test.log
   ```

4. **Look for success indicators**:
   ```bash
   grep "MCP server.*Tool call succeeded" test.log
   ```

## Quick Checklist

When MCP servers fail to connect:

- [ ] Check if using Claude Code CLI vs Desktop (different setup required)
- [ ] Enable debug mode: `claude --debug`
- [ ] For testing: `claude --debug --dangerously-skip-permissions -p 'test'`
- [ ] Read FULL debug output, not just filtered results
- [ ] Check log files for errors
- [ ] Test server manually outside Claude
- [ ] Verify absolute paths in configuration
- [ ] Check protocol version (should be 2024-11-05)
- [ ] Ensure virtual environment is properly set up
- [ ] Verify file permissions and executability
- [ ] Test with minimal configuration first
- [ ] Use `claude mcp list` to check registered servers
- [ ] Restart Claude Code after configuration changes
