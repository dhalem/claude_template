#!/bin/bash
# Fix code-search server to use virtual environment

set -e

echo "Fixing code-search server with virtual environment..."

CODE_SEARCH_DIR="$HOME/.claude/mcp/code-search"
mkdir -p "$CODE_SEARCH_DIR"

# Create virtual environment
echo "Creating virtual environment..."
cd "$CODE_SEARCH_DIR"
python3 -m venv venv

# Install MCP
echo "Installing MCP library..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install mcp

# Update start script to use venv
cat > "$HOME/.claude/mcp/start-search-server.sh" << 'EOF'
#!/bin/bash
# Startup script for MCP code search server with venv

# Get the home directory MCP path
MCP_DIR="$HOME/.claude/mcp"

# Start the server from the home directory using venv
cd "$MCP_DIR"
exec "$HOME/.claude/mcp/code-search/venv/bin/python3" code-search-server.py
EOF

chmod +x "$HOME/.claude/mcp/start-search-server.sh"

echo "Fixed! Code-search server now uses virtual environment with MCP installed."
