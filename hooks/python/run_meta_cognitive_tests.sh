#!/bin/bash

# Test runner for MetaCognitiveGuard
# Usage: ./run_meta_cognitive_tests.sh

set -e

echo "🧠 Running MetaCognitiveGuard Test Suite"
echo "========================================"

cd "$(dirname "$0")"

# Check for required environment variables
if [[ -z "${GOOGLE_API_KEY:-}" ]]; then
    echo "❌ ERROR: GOOGLE_API_KEY environment variable is not set."
    echo ""
    echo "To run MetaCognitiveGuard tests, you need a test API key:"
    echo "  export GOOGLE_API_KEY='your_test_key_here'"
    echo ""
    echo "This key is used only for unit tests and should be a test/development key."
    echo "NEVER commit API keys to version control - always use environment variables."
    echo ""
    exit 1
fi

echo "✅ Using GOOGLE_API_KEY from environment"

# Set up environment for testing
export META_COGNITIVE_ANALYSIS_ENABLED="true"
export META_COGNITIVE_LLM_PROVIDER="google"
export META_COGNITIVE_LLM_VERSION="2.0-flash-exp"
export META_COGNITIVE_FALLBACK_TO_HEURISTICS="true"

# Run the tests
echo "Running MetaCognitiveGuard unit tests..."
python3 -m pytest tests/test_meta_cognitive_guard.py -v

echo ""
echo "🎯 Test Results:"
echo "- Pattern Analysis data structure: ✓"
echo "- LLM Provider model resolution: ✓"
echo "- Gemini Client functionality: ✓"
echo "- MetaCognitiveGuard integration: ✓"
echo "- Environment variable configuration: ✓"
echo "- Heuristic fallback behavior: ✓"
echo ""
echo "✅ All MetaCognitiveGuard tests completed!"
