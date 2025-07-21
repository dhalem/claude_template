# Claude Code Hooks Documentation

This document provides a comprehensive reference for Claude Code hooks based on the official documentation and practical testing.

## Table of Contents

- [Overview](#overview)
- [JSON Configuration Format](#json-configuration-format)
- [Hook Input Format](#hook-input-format)
- [Hook Output Format](#hook-output-format)
- [Event Types](#event-types)
- [User Interaction & Permissions](#user-interaction--permissions)
- [Tool Matchers](#tool-matchers)
- [Configuration Locations](#configuration-locations)
- [Debugging & Troubleshooting](#debugging--troubleshooting)
- [Examples](#examples)

## Overview

Claude Code hooks are user-defined shell commands that execute at various points in Claude Code's lifecycle, providing deterministic control over its behavior. Hooks can:

- **Approve or block** tool calls before execution
- **Log and monitor** Claude Code activities
- **Require user permission** for dangerous operations
- **Modify or validate** tool inputs
- **Provide custom notifications** and feedback

## JSON Configuration Format

### Basic Structure

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "shell-command-here"
          }
        ]
      }
    ]
  }
}
```

### Complete Configuration Example

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/safety-guard.sh"
          }
        ]
      },
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/file-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Tool completed' >> /tmp/claude-log.txt"
          }
        ]
      }
    ]
  }
}
```

## Hook Input Format

### JSON Structure Received by Hooks

Hooks receive JSON input via **stdin** with the following structure:

```json
{
  "session_id": "17ae8441-c0eb-4e47-88fa-d8a4ce1fdfe5",
  "transcript_path": "/home/user/.claude/projects/project-name/session-id.jsonl",
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit -m 'message' --no-verify",
    "description": "Commit changes bypassing hooks"
  }
}
```

### Field Descriptions

- **`session_id`**: Unique identifier for the current Claude Code session
- **`transcript_path`**: Full path to the conversation log file
- **`tool_name`**: Name of the tool being called (Bash, Edit, Write, etc.)
- **`tool_input`**: Tool-specific parameters and data

### Tool-Specific Input Examples

**Bash Tool:**

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "docker restart my-container",
    "description": "Restart container"
  }
}
```

**Edit Tool:**

```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "old_string": "old code",
    "new_string": "new code"
  }
}
```

**Write Tool:**

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/new-file.txt",
    "content": "File contents here"
  }
}
```

## Hook Output Format

### Exit Codes

⚠️ **CRITICAL**: Hooks control Claude Code behavior through **exit codes**:

- **`0`**: **Success** - Allow the tool call to proceed
- **`1`**: ⚠️ **DOES NOT BLOCK** - Hook runs but command executes anyway (MISLEADING!)
- **`2`**: ✅ **BLOCKS COMMAND** - Tool execution prevented, error shown to user
- **Other**: **Error** - Treat as blocking error

🚨 **CRITICAL LEARNING**: Despite intuitive expectations, **exit code 1 does NOT block commands**! Always use **exit code 2** to block tool execution.

⚠️ **DANGER**: Past incidents occurred when developers used `exit 1` thinking it would block operations. The commands executed anyway, causing system failures and security breaches.

✅ **CORRECT USAGE**:
- `exit 0` - Allow operation to proceed
- `exit 2` - Block operation (shows error to user)
- Never use `exit 1` for blocking - it's misleading and dangerous!

### Standard Output & Error

- **`stdout`**: Messages shown to user in Claude Code session
- **`stderr`**: Debug information (visible in transcript mode with Ctrl-R)

### JSON Output (Advanced)

Hooks can also return structured JSON for more control:

```json
{
  "continue": false,
  "stopReason": "Git --no-verify is forbidden by safety policy",
  "decision": "block",
  "reason": "Pre-commit hooks protect code quality and prevent production issues"
}
```

## Event Types

### PreToolUse

- **Timing**: Before Claude Code executes any tool
- **Purpose**: Validate, approve, or block tool calls
- **Common Uses**: Safety guards, permission checks, logging

### PostToolUse

- **Timing**: After tool execution completes
- **Purpose**: React to tool results, cleanup, notifications
- **Common Uses**: Success logging, result processing, notifications

### Notification

- **Timing**: When Claude Code sends notifications
- **Purpose**: Custom notification handling
- **Common Uses**: Integration with external systems, custom alerts

### Stop

- **Timing**: When Claude Code finishes responding
- **Purpose**: Session cleanup and final actions
- **Common Uses**: Session logging, resource cleanup

## User Interaction & Permissions

### Interactive Hooks

Hooks **CAN** prompt users for permission using standard shell input, but there are important limitations:

```bash
#!/bin/bash
# Interactive prompts work when TTY is available

# Always check if interactive mode is possible
IS_INTERACTIVE=false
if [[ -t 0 ]] && [[ -t 1 ]] && [[ -t 2 ]]; then
    IS_INTERACTIVE=true
fi

if [[ "$IS_INTERACTIVE" == "true" ]]; then
    echo "🚨 DANGEROUS OPERATION DETECTED"
    echo "Command: $COMMAND"
    echo ""
    read -p "Do you want to allow this? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Operation blocked by user"
        exit 2  # BLOCKS OPERATION
    else
        echo "✅ User authorized operation"
        exit 0
    fi
else
    echo "🚨 DANGEROUS OPERATION DETECTED (Non-interactive mode)"
    echo "Command: $COMMAND"
    echo "🚨 RULE FAILURE: Operation blocked by safety-first policy"
    exit 2  # BLOCKS OPERATION
fi
```

#### Interactive Mode Limitations

- **TTY Detection Required**: Always check for TTY availability before using `read`
- **Environment Dependent**: May not work in all Claude Code execution contexts
- **Safety-First Fallback**: Always provide non-interactive fallback that blocks by default
- **No Hanging**: Never use `read` without TTY check (will hang indefinitely)

### Non-Interactive Hooks

For automated environments, hooks can block without user input:

```bash
#!/bin/bash
# Non-interactive blocking

if [[ "$COMMAND" =~ dangerous-pattern ]]; then
    echo "🚨 BLOCKED: Dangerous operation forbidden"
    exit 2  # BLOCKS OPERATION
fi

exit 0
```

## Tool Matchers

### Exact Matching

```json
"matcher": "Bash"           // Matches only Bash tool
"matcher": "Edit"           // Matches only Edit tool
"matcher": "Write"          // Matches only Write tool
```

### Regex Matching

```json
"matcher": "Edit|Write|MultiEdit"    // Matches any file operation
"matcher": ".*"                      // Matches all tools
"matcher": "Bash|Task"               // Matches command-line tools
```

### Available Tool Names

- `Bash` - Command execution
- `Edit` - Single file edits
- `MultiEdit` - Multiple file edits
- `Write` - File creation
- `Read` - File reading
- `Glob` - File pattern matching
- `Grep` - Content searching
- `Task` - Subprocess tasks
- `WebFetch` - Web content retrieval
- `WebSearch` - Web searching

## Configuration Locations

### Priority Order (highest to lowest)

1. **`.claude/settings.local.json`** - Local project settings (not committed)
2. **`.claude/settings.json`** - Project-level settings (committed)
3. **`~/.claude/settings.json`** - User-level global settings

### Example File Locations

```text
/home/user/.claude/settings.json              # Global user settings
/project/.claude/settings.json                # Project settings
/project/.claude/settings.local.json          # Local project settings
```

## Debugging & Troubleshooting

### Testing Hooks

Use the `/hooks` slash command in Claude Code to:

- View current hook configuration
- Validate hook setup
- Debug hook issues

### Manual Testing

Test hooks manually to debug issues:

```bash
# Test hook with sample input
echo '{"tool_name":"Bash","tool_input":{"command":"git commit --no-verify"}}' | /path/to/hook.sh

# Check exit code
echo $?
```

### Debugging Output

- **Transcript Mode**: Press `Ctrl-R` to see detailed hook execution
- **Log Files**: Write debug info to `/tmp/` files
- **stderr**: Debug messages visible in transcript mode

### Common Issues

1. **Hook not triggering**: Check configuration format and tool matcher
2. **Permission denied**: Ensure hook script is executable (`chmod +x`)
3. **JSON parsing errors**: Validate JSON with `jq`
4. **Path issues**: Use absolute paths in hook commands

## Examples

### 1. Git Safety Guard

**Purpose**: Prevent bypassing pre-commit hooks

```bash
#!/bin/bash
INPUT_JSON=$(cat)
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name')
COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command')

if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ --no-verify ]]; then
    echo "🚨 BLOCKED: --no-verify bypasses safety checks"
    echo "Fix the underlying hook failures instead."
    exit 2  # BLOCKS OPERATION
fi
exit 0
```

### 2. Docker Safety Guard

**Purpose**: Prevent dangerous docker restart commands

```bash
#!/bin/bash
INPUT_JSON=$(cat)
COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command')

if [[ "$COMMAND" =~ docker.*restart ]]; then
    echo "🚨 BLOCKED: docker restart doesn't load new code"
    echo "Use: docker compose build && docker compose up -d"
    exit 2  # BLOCKS OPERATION
fi
exit 0
```

### 3. File Protection Guard

**Purpose**: Protect critical configuration files

```bash
#!/bin/bash
INPUT_JSON=$(cat)
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path')

if [[ "$TOOL_NAME" =~ Edit|Write ]] && [[ "$FILE_PATH" =~ \.pre-commit-config\.yaml$ ]]; then
    echo "🚨 CRITICAL FILE: .pre-commit-config.yaml"
    read -p "Authorize modification? (y/N): " -n 1 -r
    echo ""
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 2  # BLOCKS OPERATION
fi
exit 0
```

### 4. Command Logging

**Purpose**: Log all commands for audit trail

```bash
#!/bin/bash
INPUT_JSON=$(cat)
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name')
COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command // "N/A"')

echo "$(date): $TOOL_NAME - $COMMAND" >> ~/.claude/command-log.txt
exit 0
```

### Configuration for Examples

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/.claude/git-safety-guard.sh"
          },
          {
            "type": "command",
            "command": "/home/user/.claude/docker-safety-guard.sh"
          }
        ]
      },
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/.claude/file-protection-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/.claude/command-logger.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Summary

Claude Code hooks provide powerful control over Claude's behavior through:

- **JSON configuration** in settings files
- **Shell script execution** with full user permissions
- **Interactive permission prompts** for dangerous operations
- **Flexible tool matching** with regex support
- **Multiple event types** for different lifecycle points
- **Debugging support** through transcript mode and logging

Hooks are essential for implementing safety policies, audit trails, and custom workflows in Claude Code environments.
