# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# MCP Cross-Workspace Setup Guide

This guide explains how to set up MCP servers to work across all workspaces, not just the claude_template directory.

## Problem Statement

Initially, MCP servers were configured with hardcoded paths to the claude_template directory:
```json
{
  "mcpServers": {
    "code-review": {
      "command": "/home/dhalem/github/claude_template/venv/bin/python3",
      "args": ["/home/dhalem/github/claude_template/indexing/mcp_review_server.py"]
    }
  }
}
```

This meant:
- Servers only worked in the claude_template workspace
- Other projects couldn't use the MCP servers
- Paths were user-specific and non-portable

## Solution: Central Installation

### 1. Central Installation Location
```
~/.claude/mcp/central/
├── venv/                    # Shared Python environment
├── code-search/
│   ├── server.py
│   └── src/                 # Dependencies
└── code-review/
    ├── server.py
    └── src/                 # Dependencies
```

### 2. Configuration Strategy

**For Claude Desktop:**
- Global config: `~/.config/claude/claude_desktop_config.json`
- Uses `$HOME` paths that work for any user
- Automatically loaded by all workspaces

**For Claude Code CLI:**
- User scope registration: `claude mcp add -s user`
- Works in any directory
- Shared across all projects

## Installation Process

### Run Central Installation
```bash
cd /path/to/claude_template
./install-mcp-central.sh
```

This script:
1. ✅ Copies servers to `~/.claude/mcp/central/`
2. ✅ Creates isolated Python environment
3. ✅ Installs dependencies
4. ✅ Updates Claude Desktop global config
5. ✅ Registers servers globally with Claude CLI
6. ✅ Creates template for other projects

### Manual Global Registration (if needed)
```bash
# Remove any local/project registrations first
claude mcp remove code-search -s local 2>/dev/null || true
claude mcp remove code-review -s local 2>/dev/null || true
claude mcp remove code-search -s project 2>/dev/null || true
claude mcp remove code-review -s project 2>/dev/null || true

# Add with user scope (requires override code due to hooks)
HOOK_OVERRIDE_CODE=<code> claude mcp add code-search -s user \
  "$HOME/.claude/mcp/central/venv/bin/python" \
  "$HOME/.claude/mcp/central/code-search/server.py"

HOOK_OVERRIDE_CODE=<code> claude mcp add code-review -s user \
  "$HOME/.claude/mcp/central/venv/bin/python" \
  "$HOME/.claude/mcp/central/code-review/server.py"
```

## Testing Cross-Workspace Functionality

### Test Script
```bash
./test_mcp_other_workspace.sh /path/to/other/project
```

### Manual Test
```bash
cd /path/to/other/project

# Check global registration
claude mcp list

# Test functionality
claude --debug --dangerously-skip-permissions \
  -p "Use mcp__code-review__review_code to review a file"
```

### Expected Results
- ✅ `claude mcp list` shows servers in any directory
- ✅ MCP tools work without local `.mcp.json`
- ✅ Servers use central installation, not project-specific paths

## Configuration Scopes

Claude Code CLI has three scopes:

1. **User** (`-s user`): User-wide, works across all workspaces
2. **Local** (`-s local`): Project-specific to current workspace
3. **Project** (`-s project`): Shared via `.mcp.json` file

For cross-workspace support, use **user** scope.

## Troubleshooting

### Issue: "No MCP servers configured"
**Cause**: Servers not registered globally
**Solution**: Run `./install-mcp-central.sh`

### Issue: Servers work in claude_template but not elsewhere
**Cause**: Local/project scope registration with hardcoded paths
**Solution**:
1. Remove local/project registrations
2. Add global registrations
3. Verify with `claude mcp list` from different directory

### Issue: Permission errors during registration
**Cause**: Adaptive guard hook blocking legitimate MCP operations
**Solution**: Request hook override code from user

### Issue: Servers fail with import errors
**Cause**: Central installation missing dependencies
**Solution**:
1. Delete `~/.claude/mcp/central/`
2. Re-run `./install-mcp-central.sh`

## Best Practices

1. **Always use global scope** for MCP servers you want across projects
2. **Use central installation** to avoid path dependencies
3. **Test in multiple workspaces** before considering setup complete
4. **Document server requirements** (e.g., GEMINI_API_KEY)
5. **Keep central installation updated** when servers change

## Environment Requirements

- `GEMINI_API_KEY` - Required for code-review server
- Python 3.11+ - For MCP server execution
- Claude Code CLI - For global registration

## Files Created/Modified

- `~/.claude/mcp/central/` - Central installation directory
- `~/.config/claude/claude_desktop_config.json` - Claude Desktop config
- `~/.claude/mcp/central/mcp.json.template` - Template for other projects

## Verification Commands

```bash
# Check global registration
claude mcp list

# Test from different directory
cd /tmp && claude mcp list

# Test actual functionality
cd /any/project && claude --debug -p "test MCP servers"

# Check central installation
ls -la ~/.claude/mcp/central/
```

## Migration from Local to Global

If you have existing local MCP configurations:

1. **Backup existing config**:
   ```bash
   cp .mcp.json .mcp.json.backup
   ```

2. **Remove local registrations**:
   ```bash
   claude mcp remove code-search -s local
   claude mcp remove code-review -s local
   claude mcp remove code-search -s project
   claude mcp remove code-review -s project
   ```

3. **Install centrally**:
   ```bash
   ./install-mcp-central.sh
   ```

4. **Verify global access**:
   ```bash
   cd /tmp && claude mcp list
   ```

This ensures MCP servers work consistently across all your projects, not just the original development workspace.
