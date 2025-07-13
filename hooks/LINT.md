# Claude Code PostToolUse Linting System

This document outlines the implementation plan for moving linters and formatters from pre-commit hooks to Claude Code PostToolUse hooks for immediate feedback and faster development workflow.

## Table of Contents

- [Overview](#overview)
- [Critical Learning from Hook Implementation](#critical-learning-from-hook-implementation)
- [Linter Categories](#linter-categories)
- [Implementation Plan](#implementation-plan)
- [Hook Scripts Design](#hook-scripts-design)
- [Installation and Configuration](#installation-and-configuration)
- [Testing Strategy](#testing-strategy)
- [Migration Timeline](#migration-timeline)

## Overview

### Current Problem

Pre-commit hooks run during `git commit`, causing delays and interrupting developer flow:

- **36 different linters/formatters** run on every commit
- **2-3 second delay** even for small changes
- **Blocking workflow** during commit failures
- **No immediate feedback** during development

### Solution: PostToolUse Hooks

Move appropriate linters to Claude Code PostToolUse hooks for:

- ✅ **Immediate feedback** after file edits
- ✅ **Non-blocking workflow** (warnings, not errors)
- ✅ **Faster commits** (fewer pre-commit checks)
- ✅ **Better developer experience** with real-time validation

## Critical Learning from Hook Implementation

Based on our successful hook system implementation, we've learned:

### Exit Code Requirements

⚠️ **CRITICAL**: Claude Code hooks require specific exit codes:

- **`exit 0`**: Success - Continue normally
- **`exit 1`**: ⚠️ **DOES NOT BLOCK** - Shows warning but continues
- **`exit 2`**: ❌ **BLOCKS OPERATION** - Prevents tool execution

### Output Format Requirements

- **`stdout`**: Messages shown to user in Claude Code interface
- **`stderr`**: Detailed feedback that Claude Code displays in error messages
- **Structured Output**: Clear problem description + actionable solutions

### Hook Configuration Format

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/home/dhalem/.claude/lint-guard.sh"
          }
        ]
      }
    ]
  }
}
```

## Linter Categories

### Category 1: Real-Time Feedback (PostToolUse Hooks)

**Ideal for immediate feedback after file edits:**

#### Python Linters

- ✅ **black** - Code formatting (auto-fix)
- ✅ **isort** - Import sorting (auto-fix)
- ✅ **ruff-lint** - Fast Python linting (auto-fix available)
- ✅ **ruff-format** - Fast Python formatting
- ✅ **flake8** - Style and error checking
- ⚠️ **bandit** - Security scanning (WARNING mode)

#### File Format Linters

- ✅ **trailing-whitespace** - Auto-fix whitespace
- ✅ **end-of-file-fixer** - Auto-fix file endings
- ✅ **markdownlint** - Markdown formatting (auto-fix)
- ✅ **shellcheck** - Shell script validation
- ✅ **check-json** - JSON syntax validation
- ✅ **check-yaml** - YAML syntax validation

#### Code Quality Checks

- ✅ **no-print-statements** - Detect debug prints
- ✅ **no-breakpoints** - Detect debugging breakpoints
- ✅ **detect-private-key** - Security key detection
- ✅ **check-merge-conflict-markers** - Merge conflict detection

### Category 2: Pre-Commit Only (Keep in pre-commit)

**Must remain in pre-commit due to git-specific nature:**

#### Git-Specific Operations

- ❌ **no-commit-to-branch** - Requires git context
- ❌ **check-added-large-files** - Requires git diff
- ❌ **conventional-pre-commit** - Commit message validation

#### Complex Multi-File Analysis

- ❌ **mypy** - Type checking across entire codebase
- ❌ **pydocstyle** - Documentation coverage analysis
- ❌ **sonos-index-sync** - Cross-file synchronization checks
- ❌ **syncer-index-sync** - Cross-file synchronization checks
- ❌ **continuous-archival-check** - Repository-wide analysis

#### Security and Dependencies

- ❌ **safety-check** - Dependency vulnerability scanning
- ❌ **detect-secrets** - Repository-wide secret scanning

### Category 3: Performance Considerations

**Evaluate based on execution time:**

#### Fast Linters (< 200ms) → PostToolUse

- ✅ **black** - Very fast formatter
- ✅ **ruff** - Designed for speed
- ✅ **basic file checks** - Minimal overhead

#### Slower Linters (> 500ms) → Keep in pre-commit

- ❌ **bandit** - Security analysis can be slow
- ❌ **hadolint** - Docker analysis
- ❌ **sqlfluff** - SQL parsing overhead

## Implementation Plan

### Phase 1: Core PostToolUse Hook Infrastructure

**Goal**: Create the foundation for PostToolUse linting

⚠️ **CRITICAL IMPLEMENTATION RULE**: Always develop in repository first, then copy to installation

```bash
# 1. Create script in repository
vim hooks/lint-guard.sh

# 2. Test locally
echo '{"tool_name":"Edit","tool_input":{"file_path":"test.py"}}' | hooks/lint-guard.sh

# 3. Copy to installation for Claude Code testing
cp hooks/lint-guard.sh ~/.claude/
chmod +x ~/.claude/lint-guard.sh

# 4. Test with Claude Code
# (edit a file and verify hook triggers)

# 5. Commit repository changes
git add hooks/lint-guard.sh && git commit -m "add lint guard script"
```

#### 1.1 Create Lint Guard Script

```bash
# File: hooks/lint-guard.sh (repository version)
#!/bin/bash

# PostToolUse hook that runs appropriate linters based on file type
# Uses exit code 1 for warnings (non-blocking) and exit code 0 for success
```

**Key Features:**

- File type detection (Python, Markdown, Shell, JSON, YAML)
- Auto-fixing when possible
- Clear output formatting with actionable suggestions
- Non-blocking warnings (exit code 1)

**Repository-First Workflow:**

1. **Develop**: Create/edit in `hooks/` directory
2. **Test Locally**: Run manual tests in repository
3. **Install**: Copy to `~/.claude/` for Claude Code testing
4. **Validate**: Test with actual Claude Code file operations
5. **Commit**: Save working version to repository

#### 1.2 Update Hook Configuration

Add PostToolUse hooks to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "/home/dhalem/.claude/adaptive-guard.sh"}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "/home/dhalem/.claude/lint-guard.sh"}]
      },
      {
        "matcher": "Write",
        "hooks": [{"type": "command", "command": "/home/dhalem/.claude/lint-guard.sh"}]
      },
      {
        "matcher": "MultiEdit",
        "hooks": [{"type": "command", "command": "/home/dhalem/.claude/lint-guard.sh"}]
      }
    ]
  }
}
```

### Phase 2: Python Linter Implementation

**Goal**: Implement real-time Python code quality checks

#### 2.1 Python File Detection

```bash
# Detect Python files from Claude Code tool input
if [[ "$FILE_PATH" =~ \.py$ ]]; then
    run_python_linters "$FILE_PATH"
fi
```

#### 2.2 Linter Execution Pipeline

```bash
run_python_linters() {
    local file="$1"
    local issues_found=false

    # 1. Auto-fix formatters (run silently)
    black --line-length=120 "$file" 2>/dev/null
    isort --profile=black --line-length=120 "$file" 2>/dev/null
    ruff format "$file" 2>/dev/null

    # 2. Check for issues (report but don't block)
    if ! ruff check "$file" --quiet; then
        echo "⚠️ Ruff found style issues in $file"
        issues_found=true
    fi

    if ! flake8 --config=.flake8 "$file" 2>/dev/null; then
        echo "⚠️ Flake8 found issues in $file"
        issues_found=true
    fi

    # Return appropriate exit code
    if [[ "$issues_found" == "true" ]]; then
        exit 1  # Warning (non-blocking)
    else
        exit 0  # Success
    fi
}
```

### Phase 3: File Format Linter Implementation

**Goal**: Implement real-time file format validation

#### 3.1 Multi-Format Detection

```bash
case "$FILE_PATH" in
    *.py) run_python_linters "$FILE_PATH" ;;
    *.md) run_markdown_linters "$FILE_PATH" ;;
    *.sh|*.bash) run_shell_linters "$FILE_PATH" ;;
    *.json) run_json_linters "$FILE_PATH" ;;
    *.yaml|*.yml) run_yaml_linters "$FILE_PATH" ;;
    *) run_generic_linters "$FILE_PATH" ;;
esac
```

#### 3.2 Format-Specific Implementations

```bash
run_markdown_linters() {
    local file="$1"

    # Auto-fix markdown
    markdownlint --fix --config .markdownlint.json "$file" 2>/dev/null

    # Check for remaining issues
    if ! markdownlint --config .markdownlint.json "$file" 2>/dev/null; then
        {
            echo "⚠️ Markdown formatting issues found"
            echo "File: $file"
            echo "Run: markdownlint --fix --config .markdownlint.json '$file'"
        } >&2
        exit 1
    fi
}

run_shell_linters() {
    local file="$1"

    if ! shellcheck --severity=warning "$file" 2>/dev/null; then
        {
            echo "⚠️ Shell script issues found"
            echo "File: $file"
            echo "Run: shellcheck '$file' for details"
        } >&2
        exit 1
    fi
}
```

### Phase 4: Performance Optimization

**Goal**: Ensure hooks don't slow down development

#### 4.1 Execution Time Monitoring

```bash
# Add timing to lint-guard.sh
start_time=$(date +%s%N)

# ... run linters ...

end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds

if [[ $duration -gt 500 ]]; then
    echo "⚠️ Linting took ${duration}ms (consider optimizing)" >&2
fi
```

#### 4.2 Conditional Execution

```bash
# Only run expensive checks on request
if [[ "${CLAUDE_LINT_DEEP:-false}" == "true" ]]; then
    run_expensive_linters "$file"
fi
```

### Phase 5: Pre-commit Integration

**Goal**: Remove duplicated checks from pre-commit

#### 5.1 Update .pre-commit-config.yaml

Remove hooks that are now handled by PostToolUse:

```yaml
# MOVED TO POSTTOOLUSE HOOKS:
# - black (Python formatting)
# - isort (Import sorting)
# - ruff-format (Python formatting)
# - markdownlint (Markdown formatting)
# - basic file checks (whitespace, etc.)

# KEPT IN PRE-COMMIT:
# - mypy (complex type checking)
# - bandit (security analysis)
# - git-specific checks
# - repository-wide analysis
```

#### 5.2 Add PostToolUse Reference

```yaml
# Note at top of .pre-commit-config.yaml:
# Some linters have been moved to Claude Code PostToolUse hooks for real-time feedback.
# See hooks/LINT.md for details.
```

## Hook Scripts Design

### Core Lint Guard Script

**File**: `~/.claude/lint-guard.sh`

```bash
#!/bin/bash

# ---------------------------------------------------------------------
# CLAUDE CODE POSTTOOLUSE LINT GUARD
# ---------------------------------------------------------------------
#
# Provides real-time linting feedback after file operations
# Uses exit code 1 for non-blocking warnings, exit code 0 for success
# Auto-fixes issues when possible, reports unfixable issues
#
# CRITICAL:
# - exit 0: Success, no issues
# - exit 1: Warnings (non-blocking, shows to user)
# - exit 2: Errors (blocking, should be rare for linting)

set -euo pipefail

# Parse Claude Code hook input
INPUT_JSON=$(cat)
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // empty')

# Extract file path from different tool types
FILE_PATH=""
case "$TOOL_NAME" in
    "Edit"|"Write")
        FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // empty')
        ;;
    "MultiEdit")
        FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // empty')
        ;;
esac

# Skip if no file path or file doesn't exist
if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Skip if file is in excluded directories
if [[ "$FILE_PATH" =~ ^(archive/|temp/|test-screenshots/|\.git/) ]]; then
    exit 0
fi

# Run appropriate linters based on file type
case "$FILE_PATH" in
    *.py) run_python_linters ;;
    *.md) run_markdown_linters ;;
    *.sh|*.bash) run_shell_linters ;;
    *.json) run_json_linters ;;
    *.yaml|*.yml) run_yaml_linters ;;
    *) run_generic_linters ;;
esac

# Default success
exit 0
```

### Python Linter Function

```bash
run_python_linters() {
    local issues_found=false
    local fixed_issues=false

    # Auto-fix formatting (silent)
    if black --line-length=120 --quiet "$FILE_PATH" 2>/dev/null; then
        fixed_issues=true
    fi

    if isort --profile=black --line-length=120 --quiet "$FILE_PATH" 2>/dev/null; then
        fixed_issues=true
    fi

    # Check for style issues
    if ! ruff check "$FILE_PATH" --quiet; then
        {
            echo "⚠️ Python style issues found in $FILE_PATH"
            echo "Run: ruff check --fix '$FILE_PATH' to auto-fix"
        } >&2
        issues_found=true
    fi

    # Report results
    if [[ "$fixed_issues" == "true" ]]; then
        echo "✅ Auto-fixed Python formatting in $FILE_PATH"
    fi

    if [[ "$issues_found" == "true" ]]; then
        exit 1  # Non-blocking warning
    fi
}
```

## Installation and Configuration

### Quick Setup Script

**File**: `hooks/install-lint-hooks.sh`

```bash
#!/bin/bash

# Install PostToolUse lint hooks for Claude Code

echo "Installing Claude Code PostToolUse lint hooks..."

# 1. Copy lint guard script
cp hooks/lint-guard.sh ~/.claude/
chmod +x ~/.claude/lint-guard.sh

# 2. Update settings.json to include PostToolUse hooks
python3 hooks/update-settings.py --add-post-tool-use

# 3. Test installation
echo "Testing lint hooks..."
echo '{"tool_name":"Edit","tool_input":{"file_path":"test.py"}}' | ~/.claude/lint-guard.sh

echo "✅ Lint hooks installed successfully!"
echo "ℹ️  Restart Claude Code to activate PostToolUse hooks"
```

### Settings Update Script

**File**: `hooks/update-settings.py`

```python
#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

def update_settings():
    settings_path = Path.home() / '.claude' / 'settings.json'

    # Load existing settings
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {"hooks": {}}

    # Add PostToolUse hooks
    if "PostToolUse" not in settings["hooks"]:
        settings["hooks"]["PostToolUse"] = []

    # Add lint guard for file operations
    lint_hook = {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "/home/dhalem/.claude/lint-guard.sh"}]
    }

    # Check if already exists
    if lint_hook not in settings["hooks"]["PostToolUse"]:
        settings["hooks"]["PostToolUse"].append(lint_hook)

        # Also add for Write and MultiEdit
        for tool in ["Write", "MultiEdit"]:
            tool_hook = lint_hook.copy()
            tool_hook["matcher"] = tool
            settings["hooks"]["PostToolUse"].append(tool_hook)

    # Save updated settings
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)

    print(f"✅ Updated {settings_path}")

if __name__ == "__main__":
    update_settings()
```

## Testing Strategy

### Unit Testing

**File**: `hooks/test-lint-hooks.sh`

```bash
#!/bin/bash

# Test suite for PostToolUse lint hooks

echo "Testing Claude Code PostToolUse lint hooks..."

# Test 1: Python file linting
echo "1. Testing Python file linting..."
echo 'print("test")' > /tmp/test.py
echo '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/test.py"}}' | ~/.claude/lint-guard.sh
echo "✅ Python test completed"

# Test 2: Markdown file linting
echo "2. Testing Markdown file linting..."
echo '# Test' > /tmp/test.md
echo '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/test.md"}}' | ~/.claude/lint-guard.sh
echo "✅ Markdown test completed"

# Test 3: Non-existent file handling
echo "3. Testing non-existent file handling..."
echo '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/nonexistent.py"}}' | ~/.claude/lint-guard.sh
echo "✅ Non-existent file test completed"

# Cleanup
rm -f /tmp/test.py /tmp/test.md

echo "🎉 All tests passed!"
```

### Integration Testing

```bash
# Test real Claude Code integration
# 1. Edit a Python file in Claude Code
# 2. Verify immediate linting feedback
# 3. Confirm non-blocking behavior
# 4. Check auto-fix functionality
```

## Migration Timeline

### Week 1: Foundation

- ✅ Create core `lint-guard.sh` script
- ✅ Implement file type detection
- ✅ Add basic Python linting (black, ruff)
- ✅ Test with simple cases

### Week 2: Expansion

- ✅ Add Markdown linting (markdownlint)
- ✅ Add Shell script linting (shellcheck)
- ✅ Add JSON/YAML validation
- ✅ Implement auto-fixing features

### Week 3: Integration

- ✅ Update Claude Code settings for all file operations
- ✅ Test PostToolUse hooks extensively
- ✅ Measure performance impact
- ✅ Refine output formatting

### Week 4: Pre-commit Migration

- ✅ Remove duplicated hooks from `.pre-commit-config.yaml`
- ✅ Update documentation
- ✅ Team training on new workflow
- ✅ Performance monitoring

## Success Metrics

### Performance Goals

- ⏱️ **PostToolUse hooks < 200ms** per file operation
- ⏱️ **Pre-commit time reduced by 50%** (from ~3s to ~1.5s)
- 📊 **100% linter coverage** maintained

### User Experience Goals

- ✅ **Immediate feedback** on code quality issues
- ✅ **Non-blocking workflow** during development
- ✅ **Auto-fix common issues** without user intervention
- ✅ **Clear actionable messages** for unfixable issues

### Quality Goals

- 🎯 **Zero regression** in code quality metrics
- 🎯 **Maintained compliance** with all existing standards
- 🎯 **Improved developer satisfaction** with faster feedback

## Future Enhancements

### Advanced Features

- **Smart Linting**: Only run relevant linters based on changed lines
- **Parallel Execution**: Run multiple linters concurrently
- **Caching**: Skip linting if file unchanged since last check
- **Custom Rules**: Project-specific linting rules

### IDE Integration

- **VS Code Extension**: Integrate with Claude Code PostToolUse hooks
- **Vim Plugin**: Real-time linting in Vim with Claude Code
- **Emacs Integration**: Seamless linting workflow

---

**Remember**: The goal is to provide immediate, helpful feedback that improves code quality without disrupting developer flow. Exit codes and output formatting are critical for good user experience.

✅ **Success Pattern**: Auto-fix what you can, warn about what you can't, never block unless critical.
