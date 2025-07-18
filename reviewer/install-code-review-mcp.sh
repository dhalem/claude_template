#!/bin/bash
# Install Code Review MCP Server
# This script installs the code review MCP server to ~/.claude/mcp/code-review/

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
MCP_DIR="$CLAUDE_DIR/mcp"
CODE_REVIEW_DIR="$MCP_DIR/code-review"

echo -e "${GREEN}Installing Code Review MCP Server...${NC}"

# Create backup if directory exists
if [ -d "$CODE_REVIEW_DIR" ]; then
    BACKUP_DIR="${CODE_REVIEW_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}Creating backup: $BACKUP_DIR${NC}"
    mv "$CODE_REVIEW_DIR" "$BACKUP_DIR"
fi

# Create directories
mkdir -p "$CODE_REVIEW_DIR"
mkdir -p "$CODE_REVIEW_DIR/src"
mkdir -p "$CODE_REVIEW_DIR/logs"

# Copy source files
echo -e "${GREEN}Copying source files...${NC}"
cp "$SCRIPT_DIR/src/file_collector.py" "$CODE_REVIEW_DIR/src/"
cp "$SCRIPT_DIR/src/gemini_client.py" "$CODE_REVIEW_DIR/src/"
cp "$SCRIPT_DIR/src/review_formatter.py" "$CODE_REVIEW_DIR/src/"
cp "$SCRIPT_DIR/mcp_code_review_server.py" "$CODE_REVIEW_DIR/"

# Update the path in the server script to use local src
sed -i 's|reviewer_src = os.path.join(os.path.dirname(__file__), "..", "reviewer", "src")|reviewer_src = os.path.join(os.path.dirname(__file__), "src")|' "$CODE_REVIEW_DIR/mcp_code_review_server.py"

# Create startup script
cat > "$CODE_REVIEW_DIR/start-server.sh" << 'EOF'
#!/bin/bash
# Startup script for MCP code review server

# Get the current working directory (where Claude Code is running)
export MCP_CWD="$PWD"

# Use the project venv from the current directory
VENV_PYTHON="$PWD/venv/bin/python3"

# Fallback to system python if venv not found
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

# Run the server
exec "$VENV_PYTHON" "$HOME/.claude/mcp/code-review/mcp_code_review_server.py"
EOF

chmod +x "$CODE_REVIEW_DIR/start-server.sh"

# Create requirements file
echo "requests>=2.31.0" > "$CODE_REVIEW_DIR/requirements.txt"

# Create documentation
cat > "$CODE_REVIEW_DIR/README.md" << 'EOF'
# Code Review MCP Server

This server provides automated code review functionality using Gemini AI.

## Usage

Set your API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

The server will be automatically available in Claude Code as the `review_code` tool.

## Configuration

- Server script: `mcp_code_review_server.py`
- Startup script: `start-server.sh`
- Source files: `src/`
- Logs: `logs/`

## Source Repository

Original source: https://github.com/user/repo/reviewer/
EOF

# Add to Claude MCP configuration
echo -e "${GREEN}Adding to Claude MCP configuration...${NC}"

# Remove existing if present
claude mcp remove code-review -s local 2>/dev/null || true

# Add the server
claude mcp add code-review bash "$CODE_REVIEW_DIR/start-server.sh"

echo -e "${GREEN}✓ Code Review MCP Server installed successfully!${NC}"
echo -e "${GREEN}✓ Added to Claude MCP configuration${NC}"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "  1. Set GEMINI_API_KEY environment variable"
echo "  2. Use 'review_code' tool in Claude Code"
echo "  3. Logs will be written to: $CODE_REVIEW_DIR/logs/"
echo ""
echo -e "${YELLOW}To verify installation:${NC}"
echo "  claude mcp list"
echo "  claude mcp get code-review"
echo ""
echo -e "${YELLOW}To test:${NC}"
echo "  cd your-project && echo '{\"method\": \"tools/list\", \"params\": {}}' | bash $CODE_REVIEW_DIR/start-server.sh"
