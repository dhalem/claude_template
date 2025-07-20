#!/bin/bash
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Pre-commit Protection Guard
# Prevents bypassing pre-commit hooks that enforce test execution

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.claude/logs/precommit_protection.log"

# Patterns that indicate pre-commit bypass attempts
BYPASS_PATTERNS=(
    "git commit.*--no-verify"
    "git commit.*-n[[:space:]]"
    "pre-commit uninstall"
    "SKIP="
    "PRE_COMMIT_ALLOW_NO_CONFIG="
    "rm.*\.git/hooks"
    "mv.*\.git/hooks"
    "git config.*core\.hooksPath"
    "git config.*hooks\.skipWorktreeCheck"
)

# Logging function
log_bypass_attempt() {
    local command="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"

    echo "[$timestamp] PRE-COMMIT BYPASS ATTEMPT: $command" >> "$LOG_FILE"
}

# Generate override code
generate_override_code() {
    echo "PCB$(date +%s | tail -c 4)$(shuf -i 100-999 -n 1)"
}

# Check if command contains bypass patterns
contains_bypass_pattern() {
    local command="$1"

    for pattern in "${BYPASS_PATTERNS[@]}"; do
        if echo "$command" | grep -qE "$pattern"; then
            return 0
        fi
    done

    return 1
}

# Show bypass warning
show_bypass_warning() {
    local command="$1"
    local override_code="$2"

    cat >&2 <<EOF
🚨 PRE-COMMIT BYPASS BLOCKED 🚨

❌ OPERATION BLOCKED: Attempting to bypass pre-commit hooks

Command: $command

🔒 PROTECTION REASON:
Pre-commit hooks enforce mandatory test execution and code quality standards.
Bypassing them violates the core principle: "ALL TESTS MUST RUN EVERY TIME"

📋 BLOCKED PATTERNS:
• git commit --no-verify / -n - Skips all pre-commit checks
• pre-commit uninstall - Removes hook enforcement
• SKIP environment variables - Bypasses specific hooks
• .git/hooks modifications - Disables hook execution
• git config changes - Alters hook behavior

⚠️ WHY THIS MATTERS:
- Pre-commit hooks run the MANDATORY FULL TEST SUITE
- They prevent broken code from being committed
- They enforce code quality standards (linting, formatting)
- Previous incident: MCP tests were broken due to bypassed checks

✅ CORRECT APPROACHES:
1. Fix the issues that pre-commit hooks found
2. If tests fail, fix the tests or the code
3. If linting fails, fix the code style
4. NEVER bypass - address the root cause

🔑 OVERRIDE (if authorized):
If this bypass is explicitly authorized by human operator:
  HOOK_OVERRIDE_CODE=$override_code <your command>

🚨 GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, THEY'VE FOUND A REAL PROBLEM
Pre-commit hooks protect code quality. Fix the issue, don't bypass the guard.
EOF
}

# Main guard logic
main() {
    # Parse JSON input from stdin
    local input
    input=$(cat)

    # Find Python interpreter (prefer venv if available)
    local python_cmd="python3"
    if [ -f "/home/dhalem/github/claude_template/venv/bin/python3" ]; then
        python_cmd="/home/dhalem/github/claude_template/venv/bin/python3"
    elif [ -f "venv/bin/python3" ]; then
        python_cmd="venv/bin/python3"
    fi

    # Handle malformed JSON gracefully
    if ! echo "$input" | $python_cmd -c "import json, sys; json.loads(sys.stdin.read())" >/dev/null 2>&1; then
        echo "ERROR: Invalid JSON input" >&2
        exit 1
    fi

    # Extract tool information
    local tool_name
    local command

    tool_name=$(echo "$input" | $python_cmd -c "
import json, sys
input_str = sys.stdin.read()
try:
    data = json.loads(input_str)
    print(data.get('tool_name', ''))
except:
    print('')
")

    # Only check Bash tool calls
    if [[ "$tool_name" != "Bash" ]]; then
        exit 0
    fi

    # Extract command from tool input
    command=$(echo "$input" | $python_cmd -c "
import json, sys
input_str = sys.stdin.read()
try:
    data = json.loads(input_str)
    tool_input = data.get('tool_input', {})
    print(tool_input.get('command', ''))
except:
    print('')
")

    # Skip if no command found
    if [[ -z "$command" ]]; then
        exit 0
    fi

    # Check if command contains bypass patterns
    if contains_bypass_pattern "$command"; then
        # Log the bypass attempt
        log_bypass_attempt "$command"

        # Check for override code
        if [[ -n "${HOOK_OVERRIDE_CODE:-}" ]]; then
            echo "🔑 OVERRIDE APPLIED: Pre-commit bypass allowed with authorization code" >&2
            echo "[$( date '+%Y-%m-%d %H:%M:%S')] OVERRIDE USED: $HOOK_OVERRIDE_CODE for: $command" >> "$LOG_FILE"
            exit 0
        fi

        # Generate override code and show warning
        OVERRIDE_CODE=$(generate_override_code)
        show_bypass_warning "$command" "$OVERRIDE_CODE"

        # Block the operation (close file descriptors to prevent hanging)
        exec 3>&- 2>/dev/null || true
        exec 4>&- 2>/dev/null || true
        exec 5>&- 2>/dev/null || true
        exit 2
    fi

    # Allow operation for non-bypass commands
    exit 0
}

# Run main function
main "$@"
