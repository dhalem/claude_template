#!/bin/bash
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Automated MCP Server Creation Script
# Creates a new MCP server from template with all required integrations

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate input
validate_server_name() {
    local name="$1"

    # Check format (lowercase, hyphens allowed)
    if [[ ! "$name" =~ ^[a-z][a-z0-9-]*$ ]]; then
        log_error "Server name must be lowercase, start with letter, contain only letters, numbers, and hyphens"
        return 1
    fi

    # Check if already exists
    if [ -f "indexing/mcp_${name//-/_}_server.py" ]; then
        log_error "Server already exists: indexing/mcp_${name//-/_}_server.py"
        return 1
    fi

    return 0
}

# Generate server code from template
create_server_file() {
    local server_name="$1"
    local description="$2"
    local tool_name="$3"
    local tool_description="$4"

    local file_name="indexing/mcp_${server_name//-/_}_server.py"
    local display_name="${server_name^} Server"

    log_info "Creating server file: $file_name"

    cat > "$file_name" << EOF
#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.

"""
$display_name MCP Server - $description

Key features:
- $tool_description
- Cross-workspace compatible
- User scope registration
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging to file only (NEVER stdout - breaks MCP protocol)
log_dir = Path.home() / ".claude" / "mcp" / "central" / "$server_name" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger(__name__)

# MCP imports (CRITICAL: Use exact versions)
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

# Initialize server
server = Server("$server_name")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools - MUST return list[Tool] not ListToolsResult"""
    logger.info("Listing available tools")

    return [
        Tool(
            name="$tool_name",
            description="$tool_description",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter for the tool"
                    },
                    "options": {
                        "type": "object",
                        "description": "Optional configuration",
                        "default": {}
                    }
                },
                "required": ["input"]
            }
        ),
    ]

@server.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls"""
    logger.info(f"Tool called: {request.params.name}")

    try:
        if request.params.name == "$tool_name":
            return await handle_${tool_name//-/_}(request)
        else:
            error_msg = f"Unknown tool: {request.params.name}"
            logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {error_msg}")]
            )

    except Exception as e:
        error_msg = f"Error in tool {request.params.name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {error_msg}")]
        )

async def handle_${tool_name//-/_}(request: CallToolRequest) -> CallToolResult:
    """Implementation of $tool_name"""
    args = request.params.arguments or {}
    input_data = args.get("input", "")
    options = args.get("options", {})

    logger.info(f"Processing tool with input={input_data}, options={options}")

    # TODO: Implement your tool logic here
    result = f"Processed: {input_data}"

    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def main():
    """Main server function"""
    logger.info("$display_name MCP Server starting")

    # CRITICAL: Use exact protocol version
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="$server_name",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
EOF

    chmod +x "$file_name"
    log_success "Created $file_name"
}

# Update installation script
update_install_script() {
    local server_name="$1"
    local file_name="mcp_${server_name//-/_}_server.py"

    log_info "Updating install-mcp-central.sh"

    # Create backup
    cp install-mcp-central.sh install-mcp-central.sh.backup

    # Add to SERVER_CONFIGS array (before the closing parenthesis)
    sed -i "/^)$/i\\    [\"$server_name\"]=\"indexing/$file_name\"" install-mcp-central.sh

    log_success "Updated install-mcp-central.sh"
}

# Update registration script
update_register_script() {
    local server_name="$1"
    local display_name="${server_name^} Server"

    log_info "Updating register-mcp-global.sh"

    # Create backup
    cp register-mcp-global.sh register-mcp-global.sh.backup

    # Add registration block before the final status check
    sed -i "/^echo \"📋 Current MCP registration:\"/i\\
echo \"\"\\
echo \"Registering $server_name...\"\\
if claude mcp add $server_name -s user \"\$CENTRAL_PYTHON\" \"\$HOME/.claude/mcp/central/$server_name/server.py\"; then\\
    echo \"✅ $server_name registered for user (cross-workspace)\"\\
else\\
    echo \"❌ Failed to register $server_name for user\"\\
    echo \"   You may need to request an override code and run:\"\\
    echo \"   HOOK_OVERRIDE_CODE=<code> claude mcp add $server_name -s user '\$CENTRAL_PYTHON' '\$HOME/.claude/mcp/central/$server_name/server.py'\"\\
fi" register-mcp-global.sh

    log_success "Updated register-mcp-global.sh"
}

# Update test script
update_test_script() {
    local server_name="$1"

    log_info "Updating test_mcp_cross_workspace_prevention.py"

    # Create backup
    cp test_mcp_cross_workspace_prevention.py test_mcp_cross_workspace_prevention.py.backup

    # Update expected servers count and list
    sed -i "s/central_path_servers < 2/central_path_servers < 3/" test_mcp_cross_workspace_prevention.py
    sed -i "s/Expected 2 central servers/Expected 3 central servers/" test_mcp_cross_workspace_prevention.py
    sed -i "s/\"code-review\" not in stdout/\"code-review\" not in stdout or \"$server_name\" not in stdout/" test_mcp_cross_workspace_prevention.py

    log_success "Updated test_mcp_cross_workspace_prevention.py"
}

# Create documentation
create_documentation() {
    local server_name="$1"
    local description="$2"
    local tool_name="$3"
    local tool_description="$4"

    local doc_file="docs/MCP_${server_name^^}_SERVER.md"

    log_info "Creating documentation: $doc_file"

    mkdir -p docs

    cat > "$doc_file" << EOF
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.

# ${server_name^} Server Documentation

## Overview

$description

## Tools

### \`$tool_name\`

**Description**: $tool_description

**Parameters**:
- \`input\` (string, required): Input parameter for the tool
- \`options\` (object, optional): Optional configuration

**Example**:
\`\`\`bash
claude -p 'Use $tool_name with input "test data"'
\`\`\`

## Installation

### Central Installation
\`\`\`bash
./install-mcp-central.sh
\`\`\`

### User Scope Registration
\`\`\`bash
./register-mcp-global.sh
\`\`\`

## Testing

### Local Testing
\`\`\`bash
# Test server startup
python3 indexing/mcp_${server_name//-/_}_server.py

# Register locally
claude mcp add $server_name -s local ./venv/bin/python3 indexing/mcp_${server_name//-/_}_server.py

# Test functionality
claude --debug -p 'Use $tool_name to test'
\`\`\`

### Cross-Workspace Testing
\`\`\`bash
./test_mcp_other_workspace.sh /tmp/test_$server_name
\`\`\`

## Troubleshooting

See \`MCP_SERVER_TROUBLESHOOTING.md\` for common issues and solutions.

## Development

To modify this server:

1. Edit \`indexing/mcp_${server_name//-/_}_server.py\`
2. Test locally
3. Run central installation
4. Re-register for user scope
5. Test cross-workspace functionality

## Environment Variables

Document any required environment variables here:

\`\`\`bash
# Example if API keys are needed
export CUSTOM_API_KEY="your-key-here"
\`\`\`
EOF

    log_success "Created $doc_file"
}

# Test the new server
test_server() {
    local server_name="$1"
    local file_name="indexing/mcp_${server_name//-/_}_server.py"

    log_info "Testing server startup..."

    # Activate virtual environment
    source venv/bin/activate

    # Test server can start
    timeout 5s python3 "$file_name" > /dev/null 2>&1 || {
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_success "Server starts correctly (timed out as expected)"
        else
            log_error "Server failed to start (exit code: $exit_code)"
            return 1
        fi
    }

    log_success "Server testing completed"
}

# Main function
main() {
    # Check if we're in the right directory
    if [ ! -f "CLAUDE.md" ]; then
        log_error "Must be run from claude_template root directory"
        exit 1
    fi

    # Check for required arguments
    if [ $# -lt 4 ]; then
        echo "Usage: $0 <server-name> <description> <tool-name> <tool-description>"
        echo ""
        echo "Example:"
        echo "  $0 file-manager 'File system management server' list_files 'List files in a directory'"
        echo ""
        echo "Server name requirements:"
        echo "  - Lowercase letters, numbers, hyphens only"
        echo "  - Must start with a letter"
        echo "  - Example: file-manager, data-processor, api-client"
        exit 1
    fi

    local server_name="$1"
    local description="$2"
    local tool_name="$3"
    local tool_description="$4"

    log_info "Creating new MCP server: $server_name"
    log_info "Description: $description"
    log_info "Tool: $tool_name - $tool_description"

    # Validate inputs
    if ! validate_server_name "$server_name"; then
        exit 1
    fi

    # Create all components
    create_server_file "$server_name" "$description" "$tool_name" "$tool_description"
    update_install_script "$server_name"
    update_register_script "$server_name"
    update_test_script "$server_name"
    create_documentation "$server_name" "$description" "$tool_name" "$tool_description"

    # Test the server
    test_server "$server_name"

    log_success "New MCP server created successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Edit indexing/mcp_${server_name//-/_}_server.py to implement your tool logic"
    echo "2. Test locally: python3 indexing/mcp_${server_name//-/_}_server.py"
    echo "3. Install centrally: ./install-mcp-central.sh"
    echo "4. Register globally: ./register-mcp-global.sh"
    echo "5. Test cross-workspace: ./test_mcp_other_workspace.sh /tmp/test"
    echo ""
    echo "📖 Documentation created: docs/MCP_${server_name^^}_SERVER.md"
    echo ""
    echo "⚠️  Don't forget to implement the TODO section in your tool handler!"
}

# Run main function
main "$@"
