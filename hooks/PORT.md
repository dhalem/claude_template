# Hook System Port to Python - Implementation Plan

## Table of Contents

- [Overview](#overview)
- [Goals](#goals)
- [Architecture](#architecture)
- [Implementation Phases](#implementation-phases)
- [Testing Strategy](#testing-strategy)
- [Migration Process](#migration-process)
- [Success Criteria](#success-criteria)

## Overview

This document outlines the plan to port the current shell-based Claude Code hook system to Python, making it more maintainable, testable, and feature-rich.

### Current State

- **Shell Scripts**: `adaptive-guard.sh`, `comprehensive-guard.sh`, `lint-guard.sh`
- **Configuration**: `settings.json` with hard-coded paths
- **Exit Codes**: Uses exit code 2 to block operations (critical discovery from HOOKS.md)
- **Guards Implemented**: 10+ safety checks enforcing CLAUDE.md rules

### Target State

- **Python Package**: Modular, object-oriented hook system
- **Unit Tests**: Comprehensive test coverage for each guard
- **Pre-commit Integration**: Hook tests run automatically before commits
- **Backwards Compatible**: Drop-in replacement for current shell scripts

## Goals

1. **Maintainability**: Easier to add new guards and modify existing ones
2. **Testability**: Unit tests for each guard logic
3. **Performance**: Faster execution with compiled Python
4. **Features**: Better JSON parsing, pattern matching, and error handling
5. **Documentation**: Auto-generated from docstrings
6. **Extensibility**: Plugin architecture for custom guards

## Architecture

### Directory Structure

```
hooks/
├── python/
│   ├── __init__.py
│   ├── main.py                    # Entry points for each hook type
│   ├── base_guard.py              # Abstract base class for guards
│   ├── guards/
│   │   ├── __init__.py
│   │   ├── git_guards.py          # Git-related safety checks
│   │   ├── docker_guards.py       # Docker safety checks
│   │   ├── file_guards.py         # File operation guards
│   │   ├── mock_guards.py         # Mock code prevention
│   │   └── lint_guards.py         # Linting and auto-fix
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── json_parser.py         # JSON input handling
│   │   ├── user_interaction.py    # TTY detection and prompts
│   │   └── patterns.py            # Regex pattern definitions
│   └── tests/
│       ├── __init__.py
│       ├── test_git_guards.py
│       ├── test_docker_guards.py
│       ├── test_file_guards.py
│       ├── test_mock_guards.py
│       ├── test_lint_guards.py
│       └── test_integration.py
├── adaptive-guard.py              # Python wrapper for adaptive-guard
├── lint-guard.py                  # Python wrapper for lint-guard
└── comprehensive-guard.py         # Python wrapper for comprehensive-guard
```

### Class Design

```python
# base_guard.py
class BaseGuard(ABC):
    """Abstract base class for all guards"""

    @abstractmethod
    def should_trigger(self, context: GuardContext) -> bool:
        """Determine if this guard should activate"""
        pass

    @abstractmethod
    def get_message(self, context: GuardContext) -> str:
        """Get the warning message to display"""
        pass

    @abstractmethod
    def get_default_action(self) -> str:
        """Return 'allow' or 'block' for non-interactive mode"""
        pass
```

### Key Components

1. **GuardContext**: Encapsulates all input data (tool name, command, file paths, etc.)
2. **GuardRegistry**: Manages and executes guards based on tool type
3. **UserInteraction**: Handles TTY detection and permission prompts
4. **ExitCodeManager**: Ensures correct exit codes (0=allow, 2=block)

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

1. **Set up Python package structure**
   - Create directories and `__init__.py` files
   - Set up `pyproject.toml` for modern Python packaging
   - Configure linting and formatting tools

2. **Implement base classes**
   - `BaseGuard` abstract class
   - `GuardContext` data class
   - `GuardRegistry` for guard management
   - `UserInteraction` for TTY handling

3. **Create JSON input parser**
   - Handle Claude Code's hook input format
   - Extract tool names, commands, file paths
   - Robust error handling for malformed input

4. **Unit test framework**
   - Set up pytest configuration
   - Create test fixtures for common scenarios
   - Mock TTY interactions

### Phase 2: Port Critical Guards (Week 1-2)

Port guards in order of criticality:

1. **Git No-Verify Prevention**
   - Pattern matching for `--no-verify`
   - User permission prompts
   - Proper exit codes

2. **Docker Restart Prevention**
   - Detect `docker restart` commands
   - Provide correct alternatives
   - Historical incident context

3. **Mock Code Prevention**
   - Pattern detection in file content
   - Support for Edit, Write, MultiEdit tools
   - Permission protocol enforcement

4. **Pre-Commit Config Protection**
   - File path matching for `.pre-commit-config.yaml`
   - Unauthorized modification detection

### Phase 3: Port Remaining Guards (Week 2)

5. **Docker Without Compose Prevention**
6. **Hook Installation Protection**
7. **Git Force Push Prevention**
8. **Directory Awareness Guard**
9. **Test Suite Enforcement Guard**
10. **Container Rebuild Reminder**
11. **Database Schema Verification**
12. **Temporary File Management**

### Phase 4: Lint Guard System (Week 2-3)

1. **Port auto-fix functionality**
   - Trailing whitespace removal
   - Missing newline fixes
   - Language-specific formatters

2. **Integrate linting tools**
   - Python: black, isort, ruff, flake8
   - JavaScript: prettier, eslint
   - YAML: yamllint
   - Shell: shellcheck
   - CSS: stylelint

3. **Non-blocking feedback system**
   - Informational messages only
   - Auto-fix when possible
   - Helpful suggestions

### Phase 5: Testing & Validation (Week 3)

1. **Comprehensive unit tests**
   - Each guard tested individually
   - Edge cases and error conditions
   - Mock user interactions

2. **Integration tests**
   - Full hook execution flow
   - Multiple guards triggering
   - Exit code verification

3. **Backwards compatibility tests**
   - Ensure same behavior as shell scripts
   - Verify all documented scenarios
   - Performance comparison

### Phase 6: Pre-commit Integration (Week 3-4)

1. **Create pre-commit hook**

   ```yaml
   - repo: local
     hooks:
       - id: test-claude-hooks
         name: Test Claude Code Hooks
         entry: python hooks/python/tests/run_tests.py
         language: python
         pass_filenames: false
   ```

2. **Test runner script**
   - Discover and run all hook tests
   - Generate coverage reports
   - Fail on test failures

3. **Documentation updates**
   - Update HOOKS.md with Python information
   - Migration guide for users
   - Developer documentation

## Testing Strategy

### Unit Test Categories

1. **Pattern Matching Tests**
   - Verify regex patterns catch intended commands
   - Test edge cases and variations
   - Ensure no false positives

2. **User Interaction Tests**
   - Mock TTY availability
   - Test both interactive and non-interactive modes
   - Verify correct prompts and responses

3. **Exit Code Tests**
   - Ensure exit 0 for allowed operations
   - Ensure exit 2 for blocked operations
   - No exit 1 (doesn't block in Claude Code)

4. **Integration Tests**
   - Multiple guards in single execution
   - Complex command scenarios
   - Performance benchmarks

### Test Data

Create comprehensive test fixtures:

- Sample Claude Code JSON inputs
- Various command patterns
- File content samples with mock code
- Configuration variations

## Migration Process

### Step 1: Parallel Development

1. Develop Python hooks alongside shell scripts
2. Keep both systems functional
3. Test Python hooks in isolation

### Step 2: Shadow Mode Testing

1. Create wrapper scripts that run both shell and Python
2. Compare outputs and exit codes
3. Log any discrepancies for investigation

### Step 3: Gradual Rollout

1. Replace one hook at a time
2. Start with less critical hooks (lint-guard)
3. Monitor for issues

### Step 4: Full Migration

1. Update `settings.json` to use Python scripts
2. Move shell scripts to `legacy/` directory
3. Update installation script

### Step 5: Cleanup

1. Remove shell script dependencies
2. Update all documentation
3. Archive legacy code

## Success Criteria

1. **Functional Parity**
   - All existing guards work identically
   - Same user experience
   - Correct exit codes

2. **Test Coverage**
   - 95%+ code coverage
   - All guards have unit tests
   - Integration tests pass

3. **Performance**
   - Python hooks execute faster than shell
   - No noticeable delay for users
   - Efficient pattern matching

4. **Maintainability**
   - Clear code structure
   - Comprehensive documentation
   - Easy to add new guards

5. **Pre-commit Integration**
   - Tests run automatically
   - Fast execution (<5 seconds)
   - Clear failure messages

## Timeline

- **Week 1**: Core infrastructure + critical guards
- **Week 2**: Remaining guards + lint system
- **Week 3**: Testing and validation
- **Week 4**: Pre-commit integration + migration

## Risk Mitigation

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Extensive testing, shadow mode, gradual rollout

2. **Risk**: Performance regression
   - **Mitigation**: Benchmark from day 1, optimize critical paths

3. **Risk**: User confusion during migration
   - **Mitigation**: Clear documentation, backwards compatibility

4. **Risk**: Missing edge cases
   - **Mitigation**: Comprehensive test suite, user feedback loop

## Next Steps

1. Review and approve this plan
2. Set up Python package structure
3. Begin Phase 1 implementation
4. Create initial unit tests
5. Start porting first guard

---

**Document Created**: 2025-07-02
**Status**: Planning Phase
**Author**: Claude Code Assistant
