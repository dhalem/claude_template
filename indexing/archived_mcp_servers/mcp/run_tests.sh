#!/bin/bash
# Test runner for MCP code search server

cd "$(dirname "$0")"

echo "Running MCP server tests..."

# Activate venv if available
if [ -d "../../venv" ]; then
    source ../../venv/bin/activate
    echo "Using virtual environment: $(which python3)"
fi

# Run the tests
python3 test_mcp_server.py

echo "Test run complete."
