#!/bin/bash

# Simple setup script for code indexing
# Run this from a fresh clone to set up the indexing system

set -e

echo "Setting up code indexing for Spotidal project..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Check Python version
python3 --version >/dev/null 2>&1 || { echo "Python 3 is required but not found"; exit 1; }

# Install watchdog for file monitoring (optional but recommended)
echo "Installing optional dependencies..."
pip install --user watchdog 2>/dev/null || echo "Note: watchdog not installed, file watching will use polling mode"

# Build initial index
echo "Building code index..."
python3 "$SCRIPT_DIR/code_indexer.py"

echo ""
echo "Setup complete! Code index built successfully."
echo ""
echo "Usage:"
echo "  Search:     python3 $SCRIPT_DIR/search_code.py <query>"
echo "  Rebuild:    python3 $SCRIPT_DIR/code_indexer.py"
echo "  Watch:      python3 $SCRIPT_DIR/watch_and_index.py"
echo ""
echo "Examples:"
echo "  python3 $SCRIPT_DIR/search_code.py get_metadata"
echo "  python3 $SCRIPT_DIR/search_code.py 'get_*' -t function"
echo "  python3 $SCRIPT_DIR/search_code.py --list-classes"
