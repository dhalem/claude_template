# Development Guide - Claude Template

This guide covers how to develop and test the template itself, especially the Claude Code hooks and safety guards.

## 🛠️ Development Setup

### 1. Clone for Development
```bash
git clone https://github.com/dhalem/claude_template
cd claude_template

# Set up development environment
./setup-template.sh
source venv/bin/activate
```

### 2. Install Development Dependencies
```bash
# Install hook development dependencies
pip install -r hooks/python/requirements-dev.txt

# Install testing dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

### 3. Set up Development Hooks
```bash
# Install pre-commit hooks for template development
pre-commit install

# Test hooks installation
./hooks/test-hooks.sh
```

## 🧪 Testing Hooks

### Run Hook Tests
```bash
# Test all Python hooks
cd hooks/python && python -m pytest tests/ -v

# Test specific guard
python -m pytest tests/test_path_guards.py -v

# Test with coverage
python -m pytest tests/ --cov=guards --cov-report=html

# Run comprehensive test suite
./hooks/python/tests/run_tests.py
```

### Test Hook Integration
```bash
# Test hooks in isolation
./hooks/test-claude-hooks.sh

# Test specific hook scenarios
cd hooks/python && python tests/standalone_test_python_hooks.py

# Test meta-cognitive features
./hooks/python/run_meta_cognitive_tests.sh
```

### Manual Hook Testing
```bash
# Test adaptive guard directly
echo '{"tool": "bash", "command": "cd ../somewhere"}' | ./hooks/adaptive-guard.sh

# Test Python guard system
cd hooks/python && python main.py --test-mode

# Test specific patterns
echo 'cd relative/path' | python guards/path_guards.py
```

## 🔧 Hook Development

### Adding New Guards

1. **Create the guard module**:
```bash
# Create new guard file
touch hooks/python/guards/my_new_guard.py
```

2. **Implement the guard**:
```python
# hooks/python/guards/my_new_guard.py
from base_guard import BaseGuard
import re

class MyNewGuard(BaseGuard):
    def __init__(self):
        super().__init__("my_new_guard")

    def check(self, command_data):
        """Check command for specific patterns."""
        command = command_data.get('command', '')

        # Add your logic here
        if self._detect_dangerous_pattern(command):
            return {
                'blocked': True,
                'reason': 'Dangerous pattern detected',
                'suggestion': 'Use safer alternative'
            }

        return {'blocked': False}

    def _detect_dangerous_pattern(self, command):
        # Your detection logic
        dangerous_patterns = [r'rm -rf \*', r'sudo.*']
        return any(re.search(pattern, command) for pattern in dangerous_patterns)
```

3. **Add tests**:
```python
# hooks/python/tests/test_my_new_guard.py
import pytest
from guards.my_new_guard import MyNewGuard

class TestMyNewGuard:
    def setup_method(self):
        self.guard = MyNewGuard()

    def test_detects_dangerous_command(self):
        result = self.guard.check({'command': 'rm -rf *'})
        assert result['blocked'] is True

    def test_allows_safe_command(self):
        result = self.guard.check({'command': 'ls -la'})
        assert result['blocked'] is False
```

4. **Register the guard**:
```python
# hooks/python/registry.py
from guards.my_new_guard import MyNewGuard

# Add to the registry
AVAILABLE_GUARDS = {
    # ... existing guards ...
    'my_new_guard': MyNewGuard,
}
```

5. **Test the new guard**:
```bash
cd hooks/python && python -m pytest tests/test_my_new_guard.py -v
```

### Modifying Existing Guards

1. **Find the guard file** in `hooks/python/guards/`
2. **Make your changes**
3. **Update tests** in `hooks/python/tests/`
4. **Run tests** to ensure nothing breaks:
```bash
cd hooks/python && python -m pytest tests/ -v
```

### Shell Hook Development

For shell-based hooks:

1. **Edit hook files** in `hooks/`:
   - `adaptive-guard.sh` - Main adaptive guard
   - `comprehensive-guard.sh` - Comprehensive safety checks
   - `lint-guard.sh` - Code quality checks

2. **Test shell hooks**:
```bash
# Test specific shell hook
echo '{"tool": "bash", "command": "test command"}' | ./hooks/adaptive-guard.sh

# Test all shell hooks
./hooks/test-hooks.sh
```

3. **Debug shell hooks**:
```bash
# Run with debug output
DEBUG=1 echo '{"command": "test"}' | ./hooks/adaptive-guard.sh
```

## 🔍 Code Search Development

### Testing Code Search
```bash
# Test search functionality
cd indexing && python claude_code_search.py search 'BaseGuard' class

# Test MCP server
cd indexing/mcp && python test_mcp_server.py

# Test comprehensive search
python test_mcp_server_comprehensive.py
```

### Adding Search Features
```bash
# Edit main search file
vim indexing/claude_code_search.py

# Test new features
cd indexing && python claude_code_search.py --help
```

## 📊 Monitoring and Debugging

### Hook Execution Logs
```bash
# View hook execution logs
tail -f ~/.claude/hook_execution.log

# Debug specific hook failures
grep "BLOCKED" ~/.claude/hook_execution.log

# Analyze guard patterns
cd hooks/python && python guards/conversation_log_analyzer.py
```

### Performance Testing
```bash
# Test hook performance
cd hooks/python && python tests/test_performance.py

# Profile guard execution
python -m cProfile guards/adaptive_guard.py
```

### Integration Testing
```bash
# Test full Claude Code integration
./hooks/test-claude-hooks.sh --integration

# Test with real Claude Code commands
# (requires Claude Code to be running)
```

## 🚀 Contributing Changes

### Before Committing
```bash
# Run all tests
./scripts/run_tests.sh

# Run pre-commit checks
pre-commit run --all-files

# Test hook functionality
./hooks/test-hooks.sh

# Test code search
cd indexing && python test_mcp_server_comprehensive.py
```

### Commit Guidelines
```bash
# For hook changes
git commit -m "feat(hooks): add new safety guard for X

- Detects dangerous pattern Y
- Provides helpful suggestions
- Includes comprehensive tests"

# For search changes
git commit -m "feat(search): improve pattern matching

- Support for wildcard patterns
- Better performance on large codebases
- MCP server compatibility"
```

### Testing Changes Across Projects
```bash
# Test template changes in a sample project
mkdir test-project && cd test-project
git init

# Pull your development template
curl -sO https://raw.githubusercontent.com/dhalem/claude_template/main/pull-templates.sh
# Edit the script to use your local development version
sed -i 's|dhalem/claude_template|file:///path/to/your/development/claude_template|' pull-templates.sh

# Test installation
echo "1" | ./pull-templates.sh
```

## 🧩 Architecture

### Hook System Architecture
```
hooks/
├── adaptive-guard.sh           # Main entry point
├── python/
│   ├── main.py                # Python hook coordinator
│   ├── registry.py            # Guard registry
│   ├── guards/                # Individual guard modules
│   └── tests/                 # Comprehensive test suite
└── settings.json              # Claude Code configuration
```

### Guard Development Pattern
1. **BaseGuard**: All guards inherit from this
2. **Registry**: Central registration of all guards
3. **Main**: Coordinates guard execution
4. **Tests**: Each guard has corresponding tests

### Code Search Architecture
```
indexing/
├── claude_code_search.py      # Main search interface
├── mcp/                       # MCP server implementation
├── code_indexer.py           # Core indexing logic
└── setup_code_indexing.sh    # Installation script
```

## 📚 Documentation

### Updating Documentation
```bash
# Update hook documentation
vim hooks/README.md
vim hooks/HOOKS.md

# Update search documentation
vim indexing/README.md
vim indexing/INDEXING.md

# Update main documentation
vim README.md
```

### Adding Examples
```bash
# Add hook examples
vim hooks/DOCS.md

# Add search examples
vim indexing/INDEX.md
```

## 🔐 Security Considerations

### Testing Security Guards
```bash
# Test security bypass attempts
cd hooks/python && python tests/test_security_bypasses.py

# Test with malicious inputs
python tests/test_malicious_patterns.py
```

### Validating Safety
```bash
# Ensure guards don't have false negatives
./hooks/python/tests/test_safety_validation.py

# Test edge cases
python tests/test_edge_cases.py
```

---

This development setup allows you to:
- 🧪 **Test hooks thoroughly** with comprehensive test suites
- 🔧 **Develop new guards** with proper architecture
- 🔍 **Enhance code search** capabilities
- 📊 **Monitor performance** and debug issues
- 🚀 **Contribute safely** with validation processes

The template is now a complete development environment for building AI safety tools! 🛡️
