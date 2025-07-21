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

# Test Script Integrity Guard
# Protects critical test enforcement files from unauthorized modification

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.claude/logs/test_protection.log"
OVERRIDE_CODE=""

# Critical files that this guard protects
PROTECTED_FILES=(
    "run_tests.sh"
    ".pre-commit-config.yaml"
    "CLAUDE.md"
)

PROTECTED_PATTERNS=(
    "tests/"
    "indexing/tests/"
    "/test_"
    "_test.py"
)

# Logging function
log_protection_attempt() {
    local file_path="$1"
    local action="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"

    echo "[$timestamp] TEST PROTECTION: $action attempted on $file_path" >> "$LOG_FILE"
}

# Generate random override code
generate_override_code() {
    echo "TST$(date +%s | tail -c 4)$(shuf -i 100-999 -n 1)"
}

# Check if file is protected
is_protected_file() {
    local file_path="$1"
    local basename_file
    basename_file=$(basename "$file_path")

    # Check exact protected files
    for protected in "${PROTECTED_FILES[@]}"; do
        if [[ "$basename_file" == "$protected" ]] || [[ "$file_path" == *"$protected" ]]; then
            return 0
        fi
    done

    # Check protected patterns
    for pattern in "${PROTECTED_PATTERNS[@]}"; do
        if [[ "$file_path" == *"$pattern"* ]]; then
            return 0
        fi
    done

    return 1
}

# Show test protection warning
show_test_protection_warning() {
    local file_path="$1"
    local override_code="$2"

    cat >&2 <<EOF
🚨 TEST PROTECTION GUARD ACTIVATED 🚨

❌ OPERATION BLOCKED: Modification of test enforcement file

File: $file_path

🔒 PROTECTION REASON:
This file is critical to the mandatory full test suite enforcement system.
Modifying it could compromise test integrity and allow bypassing safety measures.

📋 PROTECTED ELEMENTS:
• run_tests.sh - Core test script that MUST run all tests
• .pre-commit-config.yaml - Pre-commit hooks enforcing test execution
• Test directories - Test files that ensure software quality
• CLAUDE.md - Rules document containing test enforcement requirements

⚠️ WHY THIS MATTERS:
Previous incidents occurred when test enforcement was weakened:
- MCP tests were broken and went undetected
- System failures occurred due to untested code
- User mandate: "ONE SCRIPT THAT RUNS ALL TESTS EVERY TIME. NO FAST MODE. NO EXCEPTIONS."

✅ CORRECT APPROACHES:
1. If this is an authorized maintenance task, request override code from human operator
2. If adding new tests, ensure they integrate with existing test suite
3. If fixing test issues, fix the root cause, don't weaken the enforcement

🔑 OVERRIDE (if authorized):
If this modification is explicitly authorized by human operator:
  HOOK_OVERRIDE_CODE=$override_code <your command>

🚨 GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, THEY'VE FOUND A REAL PROBLEM
This guard is protecting test integrity. Fix the underlying issue, don't bypass the guard.
EOF
}

# Main guard logic
main() {
    # Parse JSON input from stdin
    local input
    input=$(cat)

    # Find Python interpreter (prefer venv if available)
    local python_cmd="python3"

    # Try to find project root dynamically
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root=""

    # Look for project root by finding CLAUDE.md or venv directory
    local search_dir="$script_dir"
    for _ in {1..5}; do
        if [[ -f "$search_dir/CLAUDE.md" ]] || [[ -d "$search_dir/venv" ]]; then
            project_root="$search_dir"
            break
        fi
        search_dir="$(dirname "$search_dir")"
        if [[ "$search_dir" == "/" ]]; then
            break
        fi
    done

    # Set Python command with dynamic project root
    if [[ -n "$project_root" && -f "$project_root/venv/bin/python3" ]]; then
        python_cmd="$project_root/venv/bin/python3"
    elif [[ -f "venv/bin/python3" ]]; then
        python_cmd="venv/bin/python3"
    fi

    # Handle malformed JSON gracefully
    if ! echo "$input" | $python_cmd -c "import json, sys; json.loads(sys.stdin.read())" >/dev/null 2>&1; then
        echo "ERROR: Invalid JSON input" >&2
        exit 1
    fi

    # Extract tool information
    local tool_name
    local file_path

    tool_name=$(echo "$input" | $python_cmd -c "
import json, sys
input_str = sys.stdin.read()
try:
    data = json.loads(input_str)
    print(data.get('tool_name', ''))
except:
    print('')
")

    # Only check Edit, Write, and MultiEdit tools
    if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" && "$tool_name" != "MultiEdit" ]]; then
        exit 0
    fi

    # Extract file path from tool input
    file_path=$(echo "$input" | $python_cmd -c "
import json, sys
input_str = sys.stdin.read()
try:
    data = json.loads(input_str)
    tool_input = data.get('tool_input', {})
    if 'file_path' in tool_input:
        print(tool_input['file_path'])
    elif 'edits' in tool_input and tool_input['edits']:
        print(tool_input['file_path'])
except:
    print('')
")

    # Skip if no file path found
    if [[ -z "$file_path" ]]; then
        exit 0
    fi

    # Check if this is a protected file
    if is_protected_file "$file_path"; then
        # Log the protection attempt
        log_protection_attempt "$file_path" "$tool_name"

        # Check for override code
        if [[ -n "${HOOK_OVERRIDE_CODE:-}" ]]; then
            echo "🔑 OVERRIDE APPLIED: Test protection bypassed with authorization code" >&2
            echo "[$( date '+%Y-%m-%d %H:%M:%S')] OVERRIDE USED: $HOOK_OVERRIDE_CODE for $file_path" >> "$LOG_FILE"
            exit 0
        fi

        # Generate override code and show warning
        OVERRIDE_CODE=$(generate_override_code)
        show_test_protection_warning "$file_path" "$OVERRIDE_CODE"

        # Block the operation (close file descriptors to prevent hanging)
        exec 3>&- 2>/dev/null || true
        exec 4>&- 2>/dev/null || true
        exec 5>&- 2>/dev/null || true
        exit 2
    fi

    # Allow operation for non-protected files
    exit 0
}

# Run main function
main "$@"
