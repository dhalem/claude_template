# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# MCP Server Testing Guide

This guide explains how to test that MCP (Model Context Protocol) servers are properly configured and working with Claude Code.

## Quick Test (30 seconds)

Run the quick test script to verify basic functionality:

```bash
./test_mcp_quick.sh
```

This will:
1. Check if servers are configured in Claude Code CLI
2. Test protocol responses from each server
3. Perform a real MCP tool call through Claude

Expected output:
```
✅ MCP servers found
✅ Responds to protocol (for each server)
✅ MCP tool call succeeded!
```

## Comprehensive Test Suite (2-5 minutes)

Run the full Python test suite:

```bash
./test_mcp_servers.py
```

This provides detailed testing of:
- Claude CLI installation
- MCP server configuration
- Protocol compliance
- Individual server responses
- End-to-end tool calls
- Environment setup

## Pytest Integration Tests

Run as part of the standard test suite:

```bash
# Run only MCP tests
pytest tests/test_mcp_integration.py -v

# Run slow tests too (includes integration tests)
pytest tests/test_mcp_integration.py -v -m slow

# Run with coverage
pytest tests/test_mcp_integration.py -v --cov=indexing
```

## What the Tests Check

### 1. **Configuration Tests**
- Claude Code CLI is installed and accessible
- MCP servers are registered with `claude mcp list`
- Required environment variables (GEMINI_API_KEY) are set

### 2. **Protocol Tests**
- Each server responds to MCP initialization request
- Correct protocol version (2024-11-05) is used
- Valid JSON-RPC responses are returned

### 3. **Integration Tests**
- Claude can call MCP tools successfully
- Tool outputs are properly formatted
- Error handling works correctly

## Common Test Failures and Solutions

### "No MCP servers configured"
```bash
# Add servers from .mcp.json
cat .mcp.json | jq -r '.mcpServers | to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"' | bash
```

### "No protocol response"
- Check Python path is correct
- Verify virtual environment exists
- Ensure server files are executable

### "Tool call did not succeed"
- Check full debug output: `claude --debug -p 'test'`
- Verify GEMINI_API_KEY is set (for code-review)
- Ensure server dependencies are installed

### "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Testing in Other Workspaces

When using MCP servers in a different workspace:

1. **Copy the configuration**:
   ```bash
   # In target workspace
   cp /path/to/claude_template/.mcp.json .
   ```

2. **Update paths to use absolute paths**:
   ```json
   {
     "mcpServers": {
       "code-review": {
         "command": "/absolute/path/to/venv/bin/python3",
         "args": ["/absolute/path/to/mcp_review_server.py"]
       }
     }
   }
   ```

3. **Register servers with Claude Code CLI**:
   ```bash
   cat .mcp.json | jq -r '.mcpServers | to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"' | bash
   ```

4. **Test the connection**:
   ```bash
   ./test_mcp_quick.sh
   ```

## Debugging Failed Tests

1. **Enable full debug output**:
   ```bash
   claude --debug --dangerously-skip-permissions -p 'test' 2>&1 | tee debug.log
   ```

2. **Check for MCP messages**:
   ```bash
   grep -i "mcp" debug.log
   ```

3. **Test servers directly**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05"},"id":1}' | \
     /path/to/python /path/to/server.py
   ```

## Continuous Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Test MCP Servers
  run: |
    # Add servers to Claude CLI
    cat .mcp.json | jq -r '.mcpServers | to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"' | bash

    # Run tests
    ./test_mcp_quick.sh
    pytest tests/test_mcp_integration.py -v
```

## Performance Considerations

- Protocol tests should complete in < 5 seconds
- Tool calls may take 30-60 seconds due to AI processing
- Use `@pytest.mark.slow` for integration tests
- Consider mocking Claude calls for unit tests

---

Remember: Always read the FULL debug output when tests fail. The most common issues are configuration related, not code bugs.
