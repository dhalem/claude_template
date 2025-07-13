#!/bin/bash
# Test runner for Claude Code hooks - designed for pre-commit integration.

set -euo pipefail

# Change to hooks directory
cd "$(dirname "$0")"

echo "🧪 Running Claude Code Python hooks tests..."

# Run Python unit tests
if PYTHONPATH=. python3 python/tests/run_tests.py; then
    echo "✅ All Python hook tests passed!"
else
    echo "❌ Python hook tests failed!"
    exit 1
fi

# Test that all guards can be imported
echo "🔍 Testing guard imports..."
if PYTHONPATH=. python3 -c "
import sys
sys.path.insert(0, 'python')
from guards import *
from base_guard import *
from registry import *
print('✅ All imports successful')
"; then
    echo "✅ All guard imports successful!"
else
    echo "❌ Guard import test failed!"
    exit 1
fi

echo "🎉 All Claude Code hook tests passed!"
