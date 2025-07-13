#!/bin/bash

# ===========================================================================
# CLAUDE CODE OUTPUT SAFETY GUARD
# ===========================================================================
#
# This script implements safety protections with proper Claude Code output
# formatting to ensure messages are visible to the user.
#
# KEY INSIGHT: Claude Code hooks need properly formatted output to display
# messages in the user interface. This version focuses on clear, visible
# output that Claude Code will show to the user.
#
# GUARDS IMPLEMENTED:
# 1. Git No-Verify Prevention - Stops bypassing pre-commit hooks
# 2. Docker Restart Prevention - Prevents catastrophic restart after code changes
#
# OUTPUT STRATEGY:
# - Use stdout for messages that should appear in Claude Code
# - Use clear, formatted output that stands out
# - Provide actionable guidance for blocked operations
# - Return proper exit codes to control tool execution
#
# ===========================================================================

set -euo pipefail

# Parse the hook input JSON from Claude Code
INPUT_JSON=$(cat)

# Validate JSON input
if [[ -z "$INPUT_JSON" ]]; then
    echo "❌ ERROR: No hook input received"
    exit 1
fi

# Extract parameters from Claude Code hook format
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command // empty')

# Validate extracted parameters
if [[ -z "$TOOL_NAME" ]] || [[ -z "$COMMAND" ]]; then
    echo "❌ ERROR: Invalid hook input format"
    exit 1
fi

# ===========================================================================
# GIT NO-VERIFY PREVENTION GUARD
# ===========================================================================

if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ git[[:space:]]+.*commit.*--no-verify ]]; then
    cat << 'EOF'

🚨 BLOCKED: Git --no-verify is forbidden by CLAUDE.md safety rules

COMMAND ATTEMPTED:
EOF
    echo "  $COMMAND"
    cat << 'EOF'

WHY THIS IS BLOCKED:
  • Pre-commit hooks protect code quality and prevent production issues
  • Bypassing hooks has caused real harm documented in CLAUDE.md
  • Your project explicitly forbids --no-verify without permission

WHAT TO DO INSTEAD:
  1. Remove --no-verify and fix the underlying hook failures
  2. Check what specific hooks are failing and address those issues
  3. If absolutely necessary, get explicit user permission first

This protection exists because bypassing hooks has caused production failures.

EOF
    exit 1
fi

# ===========================================================================
# DOCKER RESTART PREVENTION GUARD
# ===========================================================================

if [[ "$TOOL_NAME" == "Bash" ]] && ([[ "$COMMAND" =~ docker.*restart ]] || [[ "$COMMAND" =~ docker.*compose.*restart ]]); then
    cat << 'EOF'

🚨 BLOCKED: Docker restart after code changes is catastrophically dangerous

COMMAND ATTEMPTED:
EOF
    echo "  $COMMAND"
    cat << 'EOF'

WHY THIS IS BLOCKED:
  • 'docker restart' only stops/starts containers with EXISTING images
  • Your code changes are NOT loaded into the running container
  • This broke the entire SMAPI service on June 30, 2025
  • Hours of debugging were required to recover from this mistake

CORRECT PROCEDURE AFTER CODE CHANGES:
  1. docker -c musicbot compose build service-name
  2. docker -c musicbot compose up -d service-name
  3. Test that your changes actually work

QUICK STATUS CHECK (if that's what you wanted):
  docker -c musicbot compose ps

This protection exists because docker restart has caused real system breakage.

EOF
    exit 1
fi

# ===========================================================================
# ALLOW ALL OTHER COMMANDS
# ===========================================================================

# If we reach here, the command is safe to execute
exit 0
