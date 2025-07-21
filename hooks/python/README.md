# Claude Template Hooks

Safety hooks and guards for the Claude Template AI assistant system.

## Overview

This package provides a comprehensive set of safety guards that intercept and validate Claude's actions before execution. The guards help prevent common mistakes and enforce best practices.

## Installation

```bash
pip install -e .
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Guard Categories

### Git Guards
- `GitCheckoutSafetyGuard` - Prevents unsafe git checkout operations
- `GitForcePushGuard` - Blocks force push operations
- `GitNoVerifyGuard` - Prevents bypassing pre-commit hooks

### Docker Guards
- `DockerRestartGuard` - Suggests proper rebuild instead of restart
- `DockerWithoutComposeGuard` - Enforces docker-compose usage
- `DockerEnvGuard` - Ensures required .env files exist
- `ContainerStateGuard` - Detects debugging in wrong container state

### File Guards
- `MockCodeGuard` - Prevents creation of mock/simulation code
- `PreCommitConfigGuard` - Protects pre-commit configuration
- `HookInstallationGuard` - Ensures safe hook installation

### Awareness Guards
- `DirectoryAwarenessGuard` - Ensures location awareness
- `TestSuiteEnforcementGuard` - Enforces test execution
- `PipInstallGuard` - Manages pip install operations

### Environment Guards
- `EnvBypassGuard` - Prevents environment variable bypasses
- `PythonVenvGuard` - Enforces virtual environment usage

### Special Guards
- `MetaCognitiveGuard` - LLM-based pattern detection
- `ConversationLogGuard` - Analyzes conversation patterns

## Testing

Run all tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=guards --cov-report=html
```

## Architecture

The hook system uses a base `BaseGuard` class that all guards inherit from. Guards implement:

- `should_trigger()` - Determines if the guard should activate
- `get_message()` - Returns the warning/error message
- `get_default_action()` - Returns "allow" or "block"

## Override System

Guards support TOTP-based overrides for authorized exceptions. Set `HOOK_OVERRIDE_CODE` environment variable with a valid code to bypass a guard when necessary.

## Contributing

All guards must have comprehensive test coverage. See the `tests/` directory for examples.
