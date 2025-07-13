#!/bin/bash
# Setup development environment for Claude template development
set -e

echo "🔧 Setting up Claude Template Development Environment"

# Check if we're in the template directory
if [[ ! -f "DEVELOPMENT.md" ]]; then
    echo "❌ This script must be run from the claude_template root directory"
    exit 1
fi

# Set up basic template environment first
echo "📦 Setting up base template environment..."
./setup-template.sh

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install hook development dependencies
echo "🧪 Installing hook development dependencies..."
pip install -r hooks/python/requirements-dev.txt

# Install additional development tools
echo "🛠️ Installing additional development tools..."
pip install \
    pytest-benchmark \
    pytest-profiling \
    pytest-html \
    coverage[toml] \
    pre-commit-hooks \
    pydocstyle \
    vulture

# Set up development pre-commit hooks
echo "🔒 Setting up development pre-commit hooks..."
pre-commit install --hook-type pre-commit
pre-commit install --hook-type commit-msg

# Create development configuration
echo "⚙️ Creating development configuration..."
cat > .env.development << 'EOF'
# Development environment variables
DEBUG=1
HOOK_DEBUG=1
CLAUDE_TEMPLATE_DEV=1
PYTHONPATH=${PWD}/hooks/python:${PYTHONPATH}
EOF

# Set up hook testing environment
echo "🧪 Setting up hook testing environment..."
cd hooks/python

# Create test configuration
cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --disable-warnings
    --tb=short
    --cov=guards
    --cov=utils
    --cov-report=term-missing
    --cov-report=html:htmlcov
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests (may take more than 5s)
    security: Security-related tests
    guard: Guard-specific tests
    performance: Performance tests
EOF

# Run initial tests to verify setup
echo "✅ Running initial test suite..."
python -m pytest tests/ -v --tb=short || echo "⚠️ Some tests failed - this is expected for development setup"

# Test hook functionality
echo "🔍 Testing hook functionality..."
cd ../..
./hooks/test-hooks.sh || echo "⚠️ Some hook tests failed - this is expected for development setup"

# Set up indexing development
echo "🔍 Setting up code indexing development..."
cd indexing
./setup_code_indexing.sh || echo "⚠️ Code indexing setup failed - this is optional for hook development"
cd ..

# Create development scripts
echo "📜 Creating development utility scripts..."

# Create hook development script
cat > scripts/develop-hooks.sh << 'EOF'
#!/bin/bash
# Utility script for hook development
set -e

source venv/bin/activate
export PYTHONPATH="${PWD}/hooks/python:${PYTHONPATH}"

case "$1" in
    "test")
        echo "🧪 Running hook tests..."
        cd hooks/python && python -m pytest tests/ -v
        ;;
    "test-guard")
        if [[ -z "$2" ]]; then
            echo "Usage: $0 test-guard <guard_name>"
            exit 1
        fi
        echo "🧪 Testing guard: $2"
        cd hooks/python && python -m pytest tests/test_${2}.py -v
        ;;
    "test-integration")
        echo "🔧 Running integration tests..."
        ./hooks/test-hooks.sh
        ;;
    "debug")
        echo "🐛 Starting debug session..."
        cd hooks/python && python -m ipdb main.py
        ;;
    "lint")
        echo "🔍 Running linting..."
        cd hooks/python && ruff check . && mypy guards/ utils/
        ;;
    "format")
        echo "✨ Formatting code..."
        cd hooks/python && black . && ruff check --fix .
        ;;
    "coverage")
        echo "📊 Generating coverage report..."
        cd hooks/python && python -m pytest tests/ --cov-report=html && echo "Coverage report: hooks/python/htmlcov/index.html"
        ;;
    "new-guard")
        if [[ -z "$2" ]]; then
            echo "Usage: $0 new-guard <guard_name>"
            exit 1
        fi
        echo "🆕 Creating new guard: $2"
        ./scripts/create-new-guard.sh "$2"
        ;;
    *)
        echo "Usage: $0 {test|test-guard|test-integration|debug|lint|format|coverage|new-guard}"
        echo ""
        echo "Commands:"
        echo "  test              - Run all hook tests"
        echo "  test-guard <name> - Test specific guard"
        echo "  test-integration  - Run integration tests"
        echo "  debug             - Start debug session"
        echo "  lint              - Run linting"
        echo "  format            - Format code"
        echo "  coverage          - Generate coverage report"
        echo "  new-guard <name>  - Create new guard template"
        ;;
esac
EOF

chmod +x scripts/develop-hooks.sh

# Create new guard template script
cat > scripts/create-new-guard.sh << 'EOF'
#!/bin/bash
# Create a new guard template
set -e

if [[ -z "$1" ]]; then
    echo "Usage: $0 <guard_name>"
    exit 1
fi

GUARD_NAME="$1"
GUARD_FILE="hooks/python/guards/${GUARD_NAME}.py"
TEST_FILE="hooks/python/tests/test_${GUARD_NAME}.py"

if [[ -f "$GUARD_FILE" ]]; then
    echo "❌ Guard already exists: $GUARD_FILE"
    exit 1
fi

echo "🆕 Creating new guard: $GUARD_NAME"

# Create guard file
cat > "$GUARD_FILE" << GUARD_EOF
"""${GUARD_NAME} guard for Claude Code safety."""
from base_guard import BaseGuard
import re


class ${GUARD_NAME^}Guard(BaseGuard):
    """Guard for detecting ${GUARD_NAME} patterns."""

    def __init__(self):
        super().__init__("${GUARD_NAME}")

    def check(self, command_data):
        """Check command for ${GUARD_NAME} patterns."""
        command = command_data.get('command', '')
        tool = command_data.get('tool', '')

        # TODO: Implement your guard logic here
        if self._detect_pattern(command):
            return {
                'blocked': True,
                'reason': f'${GUARD_NAME} pattern detected',
                'suggestion': 'Consider using a safer alternative',
                'details': {
                    'pattern': '${GUARD_NAME}',
                    'command': command
                }
            }

        return {'blocked': False}

    def _detect_pattern(self, command):
        """Detect ${GUARD_NAME} patterns in command."""
        # TODO: Implement pattern detection
        dangerous_patterns = [
            # Add your patterns here
        ]

        return any(re.search(pattern, command, re.IGNORECASE)
                  for pattern in dangerous_patterns)
GUARD_EOF

# Create test file
cat > "$TEST_FILE" << TEST_EOF
"""Tests for ${GUARD_NAME} guard."""
import pytest
from guards.${GUARD_NAME} import ${GUARD_NAME^}Guard


class Test${GUARD_NAME^}Guard:
    """Test suite for ${GUARD_NAME^}Guard."""

    def setup_method(self):
        """Set up test fixtures."""
        self.guard = ${GUARD_NAME^}Guard()

    def test_detects_dangerous_command(self):
        """Test that dangerous commands are detected."""
        # TODO: Add test for dangerous command
        command_data = {'command': 'dangerous_command_here'}
        result = self.guard.check(command_data)

        # Uncomment when you implement detection
        # assert result['blocked'] is True
        # assert '${GUARD_NAME}' in result['reason']

    def test_allows_safe_command(self):
        """Test that safe commands are allowed."""
        command_data = {'command': 'ls -la'}
        result = self.guard.check(command_data)

        assert result['blocked'] is False

    def test_empty_command(self):
        """Test handling of empty commands."""
        command_data = {'command': ''}
        result = self.guard.check(command_data)

        assert result['blocked'] is False

    def test_invalid_input(self):
        """Test handling of invalid input."""
        result = self.guard.check({})

        assert result['blocked'] is False

    # TODO: Add more specific tests for your guard
TEST_EOF

echo "✅ Created guard files:"
echo "  📄 $GUARD_FILE"
echo "  🧪 $TEST_FILE"
echo ""
echo "Next steps:"
echo "1. Implement guard logic in $GUARD_FILE"
echo "2. Add tests in $TEST_FILE"
echo "3. Register guard in hooks/python/registry.py"
echo "4. Test with: ./scripts/develop-hooks.sh test-guard $GUARD_NAME"
EOF

chmod +x scripts/create-new-guard.sh

# Create performance testing script
cat > scripts/test-performance.sh << 'EOF'
#!/bin/bash
# Performance testing for hooks
set -e

source venv/bin/activate
export PYTHONPATH="${PWD}/hooks/python:${PYTHONPATH}"

echo "⚡ Running performance tests..."

cd hooks/python

# Run benchmark tests
python -m pytest tests/ -m performance --benchmark-only --benchmark-sort=mean

# Profile guard execution
echo "🔍 Profiling guard execution..."
python -m cProfile -s cumulative main.py --test-mode > performance_profile.txt
echo "Profile saved to: hooks/python/performance_profile.txt"

# Memory usage testing
echo "💾 Testing memory usage..."
python -c "
import psutil
import os
from main import main

process = psutil.Process(os.getpid())
mem_before = process.memory_info().rss / 1024 / 1024

# Simulate multiple guard executions
for i in range(100):
    main({'tool': 'bash', 'command': f'ls -la {i}'})

mem_after = process.memory_info().rss / 1024 / 1024
print(f'Memory usage: {mem_before:.1f}MB -> {mem_after:.1f}MB (diff: {mem_after-mem_before:.1f}MB)')
"
EOF

chmod +x scripts/test-performance.sh

echo "✅ Development environment setup complete!"
echo ""
echo "📚 Development Commands:"
echo "  ./scripts/develop-hooks.sh test         - Run all tests"
echo "  ./scripts/develop-hooks.sh lint         - Run linting"
echo "  ./scripts/develop-hooks.sh coverage     - Generate coverage report"
echo "  ./scripts/develop-hooks.sh new-guard    - Create new guard"
echo "  ./scripts/test-performance.sh           - Run performance tests"
echo ""
echo "📖 Read DEVELOPMENT.md for detailed development guide"
echo ""
echo "🚀 Ready for hook development!"
