#!/bin/bash

# Setup script for Tree-sitter and LSP code indexing
# This provides fast function/code search with automatic index updates

set -e

echo "Setting up code indexing for Spotidal project..."

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: Not in a virtual environment. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install Python LSP server and plugins
echo "Installing Python LSP server..."
pip install python-lsp-server[all] python-lsp-ruff pylsp-mypy

# Install tree-sitter and Python bindings
echo "Installing tree-sitter..."
pip install tree-sitter tree-sitter-languages

# Install pyright for advanced type checking (optional but recommended)
echo "Installing pyright..."
npm install -g pyright || echo "Note: npm not found, skipping pyright installation"

# Create LSP configuration
echo "Creating LSP configuration..."
mkdir -p .lsp

cat > .lsp/pylsp_config.json << 'EOF'
{
    "pylsp": {
        "plugins": {
            "pycodestyle": {
                "enabled": true,
                "maxLineLength": 120
            },
            "pyflakes": {
                "enabled": true
            },
            "pylint": {
                "enabled": false
            },
            "ruff": {
                "enabled": true
            },
            "mypy": {
                "enabled": true,
                "live_mode": false
            }
        }
    }
}
EOF

# Create pyright configuration
cat > pyrightconfig.json << 'EOF'
{
    "include": [
        "sonos_server",
        "syncer",
        "syncer_v2",
        "gemini_playlist_suggester",
        "monitoring"
    ],
    "exclude": [
        "**/node_modules",
        "**/__pycache__",
        "**/venv",
        "archive",
        "temp"
    ],
    "reportMissingImports": false,
    "reportMissingTypeStubs": false,
    "pythonVersion": "3.11"
}
EOF

echo "Setup complete! Code indexing tools installed."
echo ""
echo "Next steps:"
echo "1. Run the indexing script: python3 code_indexer.py"
echo "2. Use the search script: python3 search_code.py <query>"
