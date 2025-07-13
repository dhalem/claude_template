# Claude Code Safety Hooks - Complete Documentation

**⚠️ MANDATORY UPDATE RULE**: This file MUST be updated every time a hook is added, modified, or removed. Search for "UPDATE CHECKLIST" to find the required update locations.

This directory contains a comprehensive safety hook system for Claude Code that enforces critical rules from `CLAUDE.md` and prevents costly mistakes that have caused real harm in the past.

## Table of Contents

- [Overview](#overview)
- [Hook System Architecture](#hook-system-architecture)
- [Quick Installation](#quick-installation)
- [Python Hook System](#python-hook-system)
- [Current Guards Reference](#current-guards-reference)
- [Adding New Hooks](#adding-new-hooks)
- [Testing Hooks](#testing-hooks)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Repository Synchronization](#repository-synchronization)
- [Version History](#version-history)

## Overview

### What Are Claude Code Hooks?

Claude Code hooks are user-defined commands that execute at various points in Claude Code's lifecycle, providing deterministic control over its behavior. They allow you to:

- Prevent dangerous operations before they execute
- Enforce coding standards and safety protocols
- Require explicit permission for risky actions
- Provide guidance and alternatives when rules are violated

### Why This Hook System Exists

This hook system was created after several critical incidents documented in `CLAUDE.md`:

- **June 23, 2025**: Woke up user's wife by playing audio without checking volume
- **June 30, 2025**: Used `docker restart` instead of rebuild, breaking entire SMAPI service
- **July 2, 2025**: Multiple issues with pip dependencies and Python venv usage
- **Multiple incidents**: Bypassed pre-commit hooks, created mock code, claimed work complete without testing

These hooks prevent these specific mistakes from happening again.

## Hook System Architecture

### Evolution: Shell to Python

The hook system has evolved from simple shell scripts to a comprehensive Python-based framework:

```text
Original (Shell):
Claude Code Tool Call → Shell Script → Allow/Block

Current (Python):
Claude Code Tool Call
        ↓
settings.json Hook Configuration
        ↓
Python Main Entry (main.py)
        ↓
Guard Registry
        ↓
Individual Guard Classes
        ↓
User Interaction (if needed)
        ↓
GuardResult (allow/block with message)
```

### Key Components

1. **settings.json**: Configures which scripts run for which tools
2. **main.py**: Entry point that parses input and runs guards
3. **registry.py**: Manages guard registration for different tools
4. **base_guard.py**: Base class all guards inherit from
5. **guards/**: Individual guard implementations
6. **utils/**: Helper functions for parsing and patterns

## Quick Installation

### Prerequisites

- Claude Code installed and configured
- Python 3.8+ available
- Bash shell available

### Installation Steps

1. **Clone or copy this hooks directory** to your project

2. **Run the installation script**:

   ```bash
   cd hooks
   ./install-hooks.sh
   ```

3. **Verify installation**:

   ```bash
   ls -la ~/.claude/
   # Should show settings.json and guard scripts
   ```

4. **Test the hooks**:

   ```bash
   cd hooks/python
   python3 tests/run_tests.py
   ```

### What Gets Installed

- `~/.claude/settings.json` - Hook configuration for Claude Code
- `~/.claude/adaptive-guard.sh` - Shell wrapper for Python guards
- `~/.claude/lint-guard.sh` - Shell wrapper for lint checking
- Backup of existing settings (if any)

## Python Hook System

### How It Works

1. **Tool Invocation**: Claude Code attempts to use a tool (Bash, Edit, Write, etc.)
2. **Hook Matching**: settings.json determines which script to run
3. **Python Execution**: adaptive-guard.sh calls Python main.py
4. **Guard Registry**: Guards registered for that tool type are checked
5. **Guard Logic**: Each guard's `should_trigger()` method determines if it applies
6. **User Interaction**: If triggered, guard may ask for permission
7. **Result**: GuardResult with exit code determines if operation proceeds

### Guard Types

1. **Blocking Guards** (exit code 2): Prevent dangerous operations
2. **Warning Guards** (exit code 0): Show warnings but allow operation
3. **Interactive Guards**: Ask user permission before proceeding

### Exit Code Requirements

⚠️ **CRITICAL**: Claude Code hooks require specific exit codes:

- **Exit 0**: Allow operation to proceed
- **Exit 1**: Hook error (operation may still proceed)
- **Exit 2**: Block operation (shows "operation blocked by hook")

## Current Guards Reference

**UPDATE CHECKLIST**: When adding/modifying guards, update this section!

### Git Guards (`guards/git_guards.py`)

#### GitNoVerifyGuard

- **Triggers**: `git commit --no-verify`
- **Purpose**: Prevents bypassing pre-commit hooks
- **Type**: Interactive (asks permission)
- **Rule**: CLAUDE.md - "PRE-COMMIT HOOKS MAY NEVER BE DISABLED"

#### GitForcePushGuard

- **Triggers**: `git push --force` or `-f`
- **Purpose**: Prevents destructive force pushes
- **Type**: Interactive (asks permission)

#### GitCheckoutSafetyGuard

- **Triggers**: `git checkout` to protected branches
- **Purpose**: Prevents direct work on main/master branches
- **Type**: Warning

#### PreCommitConfigGuard

- **Triggers**: Editing `.pre-commit-config.yaml`
- **Purpose**: Prevents unauthorized pre-commit changes
- **Type**: Interactive

#### GitHookProtectionGuard

- **Triggers**: Any attempt to modify `.git/hooks/`, use `--no-verify`, `pre-commit uninstall`, or disable hooks via git config
- **Purpose**: Prevents disabling or bypassing git hooks which enforce security and quality standards
- **Type**: Always blocks (non-interactive)
- **Rule**: Critical security control - hooks must never be disabled or modified

### Docker Guards (`guards/docker_guards.py`)

#### DockerRestartGuard

- **Triggers**: `docker restart` or `docker compose restart`
- **Purpose**: Prevents using old images after code changes
- **Type**: Blocking
- **Critical**: Has broken production systems

#### DockerWithoutComposeGuard

- **Triggers**: Direct `docker run/create` commands
- **Purpose**: Enforces docker-compose usage
- **Type**: Blocking

#### ContainerStateGuard

- **Triggers**: File debugging patterns ("file not found", etc.)
- **Purpose**: Suggests checking container state first
- **Type**: Suggestion (non-blocking)

### Awareness Guards (`guards/awareness_guards.py`)

#### DirectoryAwarenessGuard

- **Triggers**: Location-dependent commands
- **Purpose**: Enforces `pwd` verification
- **Type**: Warning

#### TestSuiteEnforcementGuard

- **Triggers**: Completion claims ("done", "complete", etc.)
- **Purpose**: Prevents false completion claims
- **Type**: Blocking

#### PipInstallGuard

- **Triggers**: Direct `pip install` commands
- **Purpose**: Enforces requirements.txt usage
- **Type**: Blocking
- **Exceptions**: `-r requirements.txt`, `--upgrade pip`, `--user`

#### PythonVenvGuard 🆕

- **Triggers**: Python commands without venv
- **Purpose**: Enforces virtual environment usage
- **Type**: Blocking
- **Exceptions**: `--version`, `-m venv`, venv paths

### File Guards (`guards/file_guards.py`)

#### MockCodeGuard

- **Triggers**: Mock patterns in code (`@mock.patch`, etc.)
- **Purpose**: Prevents forbidden mock code
- **Type**: Blocking

#### HookInstallationGuard

- **Triggers**: Editing `install-hooks.sh`
- **Purpose**: Protects hook installation script
- **Type**: Interactive

### Reminder Guards (`guards/reminder_guards.py`)

#### ContainerRebuildReminder

- **Triggers**: Editing Dockerfiles
- **Purpose**: Reminds to rebuild containers
- **Type**: Reminder (non-blocking)

#### DatabaseSchemaReminder

- **Triggers**: Editing SQL/migration files
- **Purpose**: Reminds to check schema changes
- **Type**: Reminder (non-blocking)

#### TempFileLocationGuard

- **Triggers**: Creating files in root directory
- **Purpose**: Suggests using temp/ directory
- **Type**: Warning

### Lint Guards (`guards/lint_guards.py`)

#### LintGuard

- **Triggers**: After file modifications
- **Purpose**: Runs linting tools automatically
- **Type**: Post-operation

## Adding New Hooks

**UPDATE CHECKLIST**: When adding hooks, update all marked sections!

### Step 1: Create Guard Class

Create a new file in `hooks/python/guards/` or add to existing file:

```python
"""REMINDER: Update HOOKS.md when modifying guards!"""

from base_guard import BaseGuard, GuardAction, GuardContext

class YourNewGuard(BaseGuard):
    """Brief description of what this guard prevents."""

    def __init__(self):
        super().__init__(
            name="Your Guard Name",
            description="Detailed description of guard purpose"
        )

    def should_trigger(self, context: GuardContext) -> bool:
        """Determine if this guard should activate."""
        if context.tool_name != "Bash":  # or other tool
            return False

        # Your detection logic here
        return your_condition_check(context.command)

    def get_message(self, context: GuardContext) -> str:
        """Return the message to show when triggered."""
        return f"""🚨 YOUR GUARD TITLE: Brief alert

Command: {context.command}

❌ PROBLEM: What's wrong

✅ CORRECT APPROACH:
  - Alternative 1
  - Alternative 2

⚠️ WHY THIS MATTERS:
  Explanation of consequences"""

    def get_default_action(self) -> GuardAction:
        """Return default action (BLOCK or ALLOW)."""
        return GuardAction.BLOCK
```

### Step 2: Export Guard

**UPDATE CHECKLIST**: Update `guards/__init__.py`:

```python
# Add import
from .your_module import YourNewGuard

# Add to __all__
__all__ = [
    # ... existing guards ...
    "YourNewGuard",
]
```

### Step 3: Register Guard

**UPDATE CHECKLIST**: Update `main.py`:

```python
# Add import
from guards import YourNewGuard

# In create_registry() function, add:
registry.register(YourNewGuard(), ["Bash"])  # or other tools
```

### Step 4: Write Tests

Create `tests/test_your_guard.py`:

```python
"""REMINDER: Update HOOKS.md when adding new test files!"""

import unittest
from base_guard import GuardContext
from guards.your_module import YourNewGuard

class TestYourNewGuard(unittest.TestCase):
    def setUp(self):
        self.guard = YourNewGuard()

    def test_should_trigger_on_pattern(self):
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "your test command"},
            command="your test command"
        )
        self.assertTrue(self.guard.should_trigger(context))
```

### Step 5: Update Documentation

**UPDATE CHECKLIST**: Update these locations in HOOKS.md:

1. Add to "Current Guards Reference" section
2. Update "Version History" with new guard
3. Run tests and verify guard works

### Step 6: Install and Test

```bash
cd hooks
./install-hooks.sh
cd python
python3 tests/test_your_guard.py
```

## Testing Hooks

### Unit Tests

Run individual guard tests:

```bash
cd hooks/python
python3 tests/test_docker_guards.py
python3 tests/test_awareness_guards.py
# etc.
```

### Integration Tests

Test hook system end-to-end:

```bash
cd hooks
./test-hooks.sh

# Or test specific scenarios:
echo '{"tool_name": "Bash", "tool_input": {"command": "docker restart x"}}' | \
    python3 python/main.py adaptive
```

### Manual Testing

Try commands that should trigger guards:

```bash
# Test Python venv guard
python3 script.py

# Test pip install guard
pip install requests

# Test docker guards
docker restart container
```

## Troubleshooting

### Common Issues

#### Hooks Not Triggering

- Check `~/.claude/settings.json` exists and is valid
- Verify scripts are executable: `chmod +x ~/.claude/*.sh`
- Check Python path in shell scripts

#### Permission Denied Errors

```bash
chmod +x ~/.claude/adaptive-guard.sh
chmod +x ~/.claude/lint-guard.sh
```

#### Import Errors

- Ensure Python path includes hook directory
- Check `sys.path.insert()` in main.py

#### Exit Code Issues

- Remember: Exit 2 blocks, Exit 0 allows
- Exit 1 is for errors, not blocking

### Debug Mode

Add debug output:

```python
# In any guard's should_trigger method:
print(f"DEBUG: Checking {self.name} with command: {context.command}", file=sys.stderr)
```

### Disable Hooks Temporarily

```bash
# Backup current settings
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# Minimal settings (no hooks)
echo '{"hooks": []}' > ~/.claude/settings.json

# Re-enable
mv ~/.claude/settings.json.backup ~/.claude/settings.json
```

## Maintenance

### Regular Tasks

#### When Adding/Modifying Guards

**UPDATE CHECKLIST**:

1. Update guard implementation
2. Update/add tests
3. Update guards/**init**.py exports
4. Update main.py registration
5. **UPDATE THIS DOCUMENTATION**
6. Commit all changes together

#### Monthly Review

- Review CLAUDE.md for new rules to automate
- Check guard effectiveness
- Review false positive reports
- Update patterns if needed

#### Testing Protocol

```bash
# Before committing guard changes:
cd hooks/python
python3 -m pytest tests/
./test-hooks.sh
```

### Documentation Update Reminders

All Python files include reminders:

```python
"""REMINDER: Update HOOKS.md when modifying guards!"""
```

This ensures documentation stays synchronized with code.

## Repository Synchronization

### Critical Rule: Keep Repository and Installation Synchronized

When updating hooks:

1. **Update repository files**
2. **Run install-hooks.sh**
3. **Test in live environment**
4. **Commit both changes**

### Sync Commands

```bash
# Check differences
diff hooks/python/main.py ~/.claude/adaptive-guard.sh
diff hooks/settings.json ~/.claude/settings.json

# Update installation
cd hooks
./install-hooks.sh

# Verify
ls -la ~/.claude/
```

## Version History

**UPDATE CHECKLIST**: Add entry when making changes!

### v2.1 (2025-01-07): Git Hook Protection

- Added GitHookProtectionGuard to prevent disabling/modifying git hooks
- Blocks attempts to move, delete, or modify .git/hooks files
- Prevents use of --no-verify, pre-commit uninstall, and SKIP environment variables
- Critical security enhancement after discovering hook bypass vulnerability

### v2.0 (2025-07-02): Python Migration

- Migrated from shell scripts to Python framework
- Added comprehensive guard system with 15+ guards
- Added PythonVenvGuard for venv enforcement
- Added PipInstallGuard for dependency management
- Improved testing infrastructure
- Added documentation update reminders

### v1.1 (2025-07-02): Exit Code Fix

- Fixed critical exit code issue (1 → 2 for blocking)
- Added documentation about exit codes

### v1.0 (2025-07-02): Initial System

- Basic shell-based guards
- Git, Docker, and file operation protection

---

## Support

For issues:

1. **Check this documentation** - common issues covered
2. **Run tests** - `python3 tests/run_tests.py`
3. **Review CLAUDE.md** - understand rules being enforced
4. **Check debug output** - add print statements if needed

Remember: These hooks exist to prevent costly mistakes that have caused real harm. When a hook blocks an action, it's protecting you from repeating past mistakes documented in `CLAUDE.md`.

**Final Reminder**: This documentation must be updated whenever hooks change!
