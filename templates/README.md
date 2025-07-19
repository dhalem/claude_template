# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# MCP Server Templates

This directory contains templates and examples for creating new MCP servers quickly and correctly.

## Quick Start

Use the automated script to create a new server:

```bash
./create_new_mcp_server.sh my-server "My server description" my_tool "My tool description"
```

This will:
- ✅ Create the server file from template
- ✅ Update installation scripts
- ✅ Update registration scripts
- ✅ Update test scripts
- ✅ Create documentation
- ✅ Test server startup

## Templates Available

### `mcp_server_template.py`
Complete MCP server template with:
- Proper protocol implementation
- File-based logging
- Error handling patterns
- Input validation
- Status tool for debugging
- Cross-workspace compatibility

### Usage Pattern

1. **Copy template**:
   ```bash
   cp templates/mcp_server_template.py indexing/mcp_myserver_server.py
   ```

2. **Replace placeholders**:
   - `TEMPLATE_SERVER` → `my-server`
   - `TEMPLATE_TOOL` → `my_tool_name`
   - `TEMPLATE_STATUS` → `my_status`

3. **Implement tool logic**:
   - Replace TODO sections with actual functionality
   - Add proper input validation
   - Include comprehensive error handling

4. **Update installation scripts**:
   - Add to `install-mcp-central.sh`
   - Add to `register-mcp-global.sh`
   - Update test scripts

## Server Examples by Use Case

### File System Server
```python
# Tools: list_files, read_file, write_file, search_files
# Use cases: File management, content analysis, workspace navigation

inputSchema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Directory or file path"},
        "pattern": {"type": "string", "description": "Search pattern"},
        "recursive": {"type": "boolean", "default": True}
    }
}
```

### API Integration Server
```python
# Tools: api_call, parse_response, format_data
# Use cases: External service integration, data fetching

inputSchema = {
    "type": "object",
    "properties": {
        "endpoint": {"type": "string", "description": "API endpoint"},
        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
        "headers": {"type": "object", "description": "HTTP headers"},
        "payload": {"type": "object", "description": "Request payload"}
    }
}
```

### Data Processing Server
```python
# Tools: process_data, analyze_data, generate_report
# Use cases: Data transformation, analysis, reporting

inputSchema = {
    "type": "object",
    "properties": {
        "data_source": {"type": "string", "description": "Data source path or URL"},
        "format": {"type": "string", "enum": ["json", "csv", "xml"]},
        "operations": {"type": "array", "items": {"type": "string"}}
    }
}
```

### Development Tools Server
```python
# Tools: run_command, parse_logs, check_status, format_output
# Use cases: Development workflow automation, CI/CD integration

inputSchema = {
    "type": "object",
    "properties": {
        "command": {"type": "string", "description": "Command to execute"},
        "working_dir": {"type": "string", "description": "Working directory"},
        "timeout": {"type": "integer", "default": 30, "description": "Timeout in seconds"}
    }
}
```

## Critical Requirements Checklist

When creating any new server, ensure:

### Protocol Requirements
- [ ] **Protocol Version**: Uses working MCP version
- [ ] **Return Types**: `list[Tool]` not `ListToolsResult`
- [ ] **No stdout/stderr**: Only file logging during operation
- [ ] **Proper imports**: Exact MCP library versions that work

### Path Requirements
- [ ] **User scope**: Registered with `-s user` for cross-workspace
- [ ] **Central paths**: Uses `~/.claude/mcp/central/` installation
- [ ] **No hardcoded paths**: Uses `$HOME` variables
- [ ] **Absolute paths**: All configuration paths are absolute

### Code Quality
- [ ] **Input validation**: All parameters validated
- [ ] **Error handling**: Comprehensive try/catch blocks
- [ ] **Logging**: File-based logging with proper levels
- [ ] **Documentation**: Clear docstrings and comments
- [ ] **Type hints**: Proper typing throughout

### Testing Requirements
- [ ] **Local testing**: Server starts without errors
- [ ] **CLI registration**: Works with `claude mcp add`
- [ ] **Cross-workspace**: Functions in different directories
- [ ] **Tool functionality**: Each tool returns correct responses

### Integration Requirements
- [ ] **Installation script**: Added to `install-mcp-central.sh`
- [ ] **Registration script**: Added to `register-mcp-global.sh`
- [ ] **Test script**: Added to prevention tests
- [ ] **Documentation**: Created server-specific docs

## Common Patterns

### Input Validation
```python
def validate_input(args: dict) -> tuple[bool, str]:
    """Validate input parameters"""
    required_fields = ["input"]

    for field in required_fields:
        if field not in args or not args[field]:
            return False, f"Missing required field: {field}"

    return True, ""

# Usage
valid, error = validate_input(args)
if not valid:
    return CallToolResult(
        content=[TextContent(type="text", text=f"Error: {error}")]
    )
```

### Async Error Handling
```python
async def handle_tool_safely(request: CallToolRequest) -> CallToolResult:
    """Safe tool handler with comprehensive error handling"""
    try:
        # Tool logic here
        result = await process_request(request)
        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Validation error: {e}")]
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Internal error: {e}")]
        )
```

### Environment Variables
```python
import os

def get_required_env(var_name: str) -> str:
    """Get required environment variable with helpful error"""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Environment variable {var_name} is required")
    return value

# Usage
try:
    api_key = get_required_env("CUSTOM_API_KEY")
except ValueError as e:
    logger.error(str(e))
    return CallToolResult(
        content=[TextContent(type="text", text=str(e))]
    )
```

## Testing Your Server

### Local Testing
```bash
# Test server startup
python3 indexing/mcp_myserver_server.py

# Register locally
claude mcp add my-server -s local ./venv/bin/python3 indexing/mcp_myserver_server.py

# Test tools
claude --debug -p 'Use my_tool to test functionality'
```

### Cross-Workspace Testing
```bash
# Install centrally
./install-mcp-central.sh

# Register globally
./register-mcp-global.sh

# Test from different directory
./test_mcp_other_workspace.sh /tmp/test_myserver
```

### Automated Testing
```bash
# Run prevention tests
python3 test_mcp_cross_workspace_prevention.py

# Run full test suite
./run_tests.sh
```

## Best Practices

1. **Start with the template** - Don't write from scratch
2. **Use the automation script** - Handles all integrations
3. **Test early and often** - Verify each step works
4. **Follow the patterns** - Use proven error handling
5. **Document thoroughly** - Future you will thank you
6. **Think cross-workspace** - Design for portability from day one

## Troubleshooting

If your server doesn't work:

1. **Check logs**: `~/.claude/mcp/central/your-server/logs/`
2. **Test startup**: `python3 indexing/mcp_yourserver_server.py`
3. **Verify registration**: `claude mcp list`
4. **Check paths**: Ensure no hardcoded paths
5. **Run prevention tests**: Catch common issues

## Further Reading

- `../MCP_SERVER_DEVELOPMENT_GUIDE.md` - Comprehensive development guide
- `../MCP_KEY_LEARNINGS.md` - Critical discoveries and patterns
- `../MCP_SERVER_TROUBLESHOOTING.md` - Debugging guide
- `../indexing/mcp_search_server.py` - Reference implementation
- `../indexing/mcp_review_server.py` - API integration example
