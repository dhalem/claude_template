#!/bin/bash

# Test runner for MetaCognitiveGuard
# Usage: ./run_meta_cognitive_tests.sh

set -e

echo "🧠 Running MetaCognitiveGuard Test Suite"
echo "========================================"

cd "$(dirname "$0")"

# Set up environment for testing
export GOOGLE_API_KEY="test_key_for_unit_tests"  # pragma: allowlist secret
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
