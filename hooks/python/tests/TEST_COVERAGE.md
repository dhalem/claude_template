# Hook System Test Coverage Report

Generated: 2025-07-05

## Test Suite Status

- **Total Tests**: 251
- **Status**: ❌ FAILING (9 failures, 8 errors)
- **Test Runner**: `tests/run_tests.py` (comprehensive runner exists ✅)

## Coverage by Guard

### ✅ Guards WITH Test Coverage

1. **Git Guards** (`test_git_guards.py`)
   - GitCheckoutSafetyGuard
   - GitForcePushGuard
   - GitNoVerifyGuard
   - PreCommitConfigGuard

2. **Docker Guards** (`test_docker_guards.py`)
   - DockerRestartGuard
   - DockerWithoutComposeGuard
   - ContainerStateGuard (`test_container_state_guard.py`)

3. **Awareness Guards** (`test_awareness_guards.py`)
   - DirectoryAwarenessGuard
   - TestSuiteEnforcementGuard
   - PipInstallGuard (`test_pip_install_guard.py`)

4. **File Guards** (`test_file_guards.py`)
   - HookInstallationGuard
   - MockCodeGuard
   - PreCommitConfigGuard

5. **Environment Guards**
   - EnvBypassGuard (`test_env_bypass_guard.py`)
   - PythonVenvGuard (`test_python_venv_guard.py`)

6. **Reminder Guards** (`test_reminder_guards.py`)
   - ContainerRebuildReminder
   - DatabaseSchemaReminder
   - TempFileLocationGuard

7. **Base Classes** (`test_base_guard.py`)
   - BaseGuard functionality

8. **Utilities** (`test_patterns.py`)
   - Pattern matching utilities

### ❌ Guards WITHOUT Test Coverage

1. **LintGuard** - No test file exists
2. **DockerEnvGuard** - New guard, not yet integrated

## Failing Tests Summary

The test suite has several failing tests that need attention:

1. **Directory Awareness**: Issues with complex command patterns
2. **Docker Guards**: False positive detection problems
3. **Database Schema Reminder**: Triggering on non-SQL content
4. **Container Rebuild Reminder**: Path matching issues

## Integration Tests

- `standalone_test_python_hooks.py` - Tests hook system integration

## Recommendations

1. **Create tests for LintGuard** - This is a critical post-operation guard
2. **Fix failing tests** - 17 tests need attention
3. **Add DockerEnvGuard tests** - Once the guard is integrated
4. **Add coverage reporting** - Use pytest-cov to track test coverage percentage

## Running the Test Suite

```bash
# Run all tests
cd hooks/python
/path/to/venv/bin/python3 tests/run_tests.py

# Run specific test file
/path/to/venv/bin/python3 tests/test_git_guards.py -v

# Run with coverage (if pytest-cov installed)
/path/to/venv/bin/python3 -m pytest tests/ --cov=. --cov-report=html
```
