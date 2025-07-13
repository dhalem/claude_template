#!/bin/bash

# ===========================================================================
# CLAUDE CODE STDERR OUTPUT SAFETY GUARD
# ===========================================================================
#
# This script outputs messages to stderr so they appear in Claude Code
# according to the documentation: stderr shows debug info visible with Ctrl-R
#
# ===========================================================================

set -euo pipefail

# Parse the hook input JSON from Claude Code
INPUT_JSON=$(cat)

# Extract parameters from Claude Code hook format
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command // empty')

# ===========================================================================
# GIT NO-VERIFY PREVENTION GUARD
# ===========================================================================

if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ git[[:space:]]+.*commit.*--no-verify ]]; then
    {
        echo ""
        echo "🚨 BLOCKED: Git --no-verify is forbidden by CLAUDE.md safety rules"
        echo ""
        echo "COMMAND ATTEMPTED:"
        echo "  $COMMAND"
        echo ""
        echo "WHY THIS IS BLOCKED:"
        echo "  • Pre-commit hooks protect code quality and prevent production issues"
        echo "  • Bypassing hooks has caused real harm documented in CLAUDE.md"
        echo "  • Your project explicitly forbids --no-verify without permission"
        echo ""
        echo "WHAT TO DO INSTEAD:"
        echo "  1. Remove --no-verify and fix the underlying hook failures"
        echo "  2. Check what specific hooks are failing and address those issues"
        echo "  3. If absolutely necessary, get explicit user permission first"
        echo ""
        echo "This protection exists because bypassing hooks has caused production failures."
        echo ""
    } >&2
    exit 1
fi

# ===========================================================================
# DOCKER RESTART PREVENTION GUARD
# ===========================================================================

if [[ "$TOOL_NAME" == "Bash" ]] && ([[ "$COMMAND" =~ docker.*restart ]] || [[ "$COMMAND" =~ docker.*compose.*restart ]]); then
    {
        echo ""
        echo "🚨 BLOCKED: Docker restart after code changes is catastrophically dangerous"
        echo ""
        echo "COMMAND ATTEMPTED:"
        echo "  $COMMAND"
        echo ""
        echo "WHY THIS IS BLOCKED:"
        echo "  • 'docker restart' only stops/starts containers with EXISTING images"
        echo "  • Your code changes are NOT loaded into the running container"
        echo "  • This broke the entire SMAPI service on June 30, 2025"
        echo "  • Hours of debugging were required to recover from this mistake"
        echo ""
        echo "CORRECT PROCEDURE AFTER CODE CHANGES:"
        echo "  1. docker -c musicbot compose build service-name"
        echo "  2. docker -c musicbot compose up -d service-name"
        echo "  3. Test that your changes actually work"
        echo ""
        echo "QUICK STATUS CHECK (if that's what you wanted):"
        echo "  docker -c musicbot compose ps"
        echo ""
        echo "This protection exists because docker restart has caused real system breakage."
        echo ""
    } >&2
    exit 1
fi

# Allow all other commands
exit 0
