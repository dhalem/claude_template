#!/bin/bash

# ---------------------------------------------------------------------
# CLAUDE CODE LINT GUARD (PreToolUse & PostToolUse)
# ---------------------------------------------------------------------
#
# Provides real-time linting with auto-fix capabilities
# Auto-fixes issues when possible, provides informational feedback
# Uses exit code 0 for success, exit code 1 for non-blocking info only
#
# BEHAVIOR:
# - Auto-fixes: trailing whitespace, missing newlines, Python formatting
# - Auto-fixes: import sorting, JSON formatting, YAML formatting, JS/TS formatting
# - Auto-fixes: Prettier formatting, ESLint fixable issues, CSS/SCSS/LESS formatting
# - Auto-fixes: Stylelint CSS issues, shell script style
# - Provides: Helpful suggestions for issues that can't be auto-fixed
# - Never blocks: All feedback is informational, never prevents operations

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

# ---------------------------------------------------------------------
# LINTER FUNCTIONS
# ---------------------------------------------------------------------

apply_generic_fixes() {
    # Check for trailing whitespace
    if grep -q '[[:space:]]$' "$FILE_PATH" 2>/dev/null; then
        # Auto-fix trailing whitespace
        sed -i 's/[[:space:]]*$//' "$FILE_PATH"
    fi

    # Check for missing final newline
    if [[ -s "$FILE_PATH" ]] && [[ $(tail -c1 "$FILE_PATH" | wc -l) -eq 0 ]]; then
        # Auto-fix missing newline
        echo >> "$FILE_PATH"
    fi
}

run_json_linters() {
    local issues_found=false

    # Check JSON syntax
    if ! jq empty "$FILE_PATH" 2>/dev/null; then
        {
            echo "⚠️ JSON syntax error in $FILE_PATH"
            echo "Run: jq . '$FILE_PATH' to see specific errors"
        } >&2
        issues_found=true
    else
        # Auto-format JSON (pretty print)
        if jq . "$FILE_PATH" > "${FILE_PATH}.tmp" 2>/dev/null; then
            if ! cmp -s "$FILE_PATH" "${FILE_PATH}.tmp"; then
                mv "${FILE_PATH}.tmp" "$FILE_PATH"
                echo "✅ Auto-formatted JSON in $FILE_PATH"
            else
                rm "${FILE_PATH}.tmp"
            fi
        fi
    fi

    # Note: No exit codes - just provide informational feedback
}

run_yaml_linters() {
    local issues_found=false
    local fixed_issues=false

    # Auto-fix YAML formatting with python yaml module
    if python3 -c "import yaml" 2>/dev/null; then
        # Try to reformat YAML with consistent indentation
        if python3 -c "
import yaml
import sys
try:
    with open('$FILE_PATH', 'r') as f:
        data = yaml.safe_load(f)
    with open('$FILE_PATH', 'w') as f:
        yaml.dump(data, f, default_flow_style=False, indent=2, width=120, sort_keys=False)
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
            fixed_issues=true
        fi
    fi

    # Check YAML syntax using python -c (more universal than yq)
    if ! python3 -c "import yaml; yaml.safe_load(open('$FILE_PATH'))" 2>/dev/null; then
        {
            echo "⚠️ YAML syntax error in $FILE_PATH"
            echo "Run: python3 -c \"import yaml; yaml.safe_load(open('$FILE_PATH'))\" for details"
        } >&2
        issues_found=true
    fi

    # Check with yamllint if available
    if command -v yamllint >/dev/null 2>&1; then
        if ! yamllint -c .yamllint.yaml "$FILE_PATH" 2>/dev/null; then
            {
                echo "⚠️ YAML style issues found in $FILE_PATH"
                echo "Run: yamllint '$FILE_PATH' for detailed analysis"
            } >&2
            issues_found=true
        fi
    fi

    # Report summary to stdout
    if [[ "$fixed_issues" == "true" ]] && [[ "$issues_found" == "true" ]]; then
        echo "🔧 Auto-fixed YAML formatting, some manual fixes may still be needed in $FILE_PATH"
    elif [[ "$fixed_issues" == "true" ]]; then
        echo "✅ Auto-fixed YAML formatting in $FILE_PATH"
    elif [[ "$issues_found" == "true" ]]; then
        echo "ℹ️ YAML linting suggestions available for $FILE_PATH"
    fi

    # Note: No exit codes - just provide informational feedback
}

run_shell_linters() {
    local issues_found=false

    # Check with shellcheck
    if command -v shellcheck >/dev/null 2>&1; then
        if ! shellcheck --severity=warning "$FILE_PATH" 2>/dev/null; then
            {
                echo "⚠️ Shell script issues found in $FILE_PATH"
                echo "Run: shellcheck '$FILE_PATH' for detailed analysis"
                echo ""
                echo "Common fixes:"
                echo "  - Quote variables: \"\$var\" instead of \$var"
                echo "  - Use [[ ]] instead of [ ] for conditionals"
                echo "  - Check for unused variables"
            } >&2
            issues_found=true
        fi
    else
        {
            echo "ℹ️ shellcheck not available for $FILE_PATH"
            echo "Install with: apt install shellcheck (or equivalent)"
        } >&2
    fi

    # Note: No exit codes - just provide informational feedback
}

run_python_linters() {
    local issues_found=false
    local fixed_issues=false

    # Auto-fix formatting (run silently)
    if command -v black >/dev/null 2>&1; then
        if black --line-length=120 --quiet "$FILE_PATH" 2>/dev/null; then
            fixed_issues=true
        fi
    fi

    if command -v isort >/dev/null 2>&1; then
        if isort --profile=black --line-length=120 --quiet "$FILE_PATH" 2>/dev/null; then
            fixed_issues=true
        fi
    fi

    # Auto-fix style issues with ruff (fast)
    if command -v ruff >/dev/null 2>&1; then
        # Try to auto-fix issues
        if ruff check --fix "$FILE_PATH" --quiet 2>/dev/null; then
            fixed_issues=true
        fi

        # Check if any issues remain after auto-fix
        if ! ruff check "$FILE_PATH" --quiet 2>/dev/null; then
            {
                echo "⚠️ Python style issues remain in $FILE_PATH after auto-fix"
                echo "Run: ruff check '$FILE_PATH' to see remaining issues"
            } >&2
            issues_found=true
        fi
    fi

    # Check for style issues with flake8 (comprehensive)
    if command -v flake8 >/dev/null 2>&1; then
        if ! flake8 --config=.flake8 "$FILE_PATH" 2>/dev/null; then
            {
                echo "⚠️ Code style issues found in $FILE_PATH"
                echo "Run: flake8 '$FILE_PATH' for detailed analysis"
            } >&2
            issues_found=true
        fi
    fi

    # Report summary to stdout
    if [[ "$fixed_issues" == "true" ]] && [[ "$issues_found" == "true" ]]; then
        echo "🔧 Auto-fixed Python issues, some manual fixes may still be needed in $FILE_PATH"
    elif [[ "$fixed_issues" == "true" ]]; then
        echo "✅ Auto-fixed Python code style in $FILE_PATH"
    elif [[ "$issues_found" == "true" ]]; then
        echo "ℹ️ Python linting suggestions available for $FILE_PATH"
    fi

    # Note: No exit 2 - we just auto-fix and inform, don't block
}

run_javascript_linters() {
    local issues_found=false
    local fixed_issues=false

    # Auto-fix formatting with Prettier
    if command -v prettier >/dev/null 2>&1; then
        if prettier --write --print-width=120 --single-quote --trailing-comma=es5 "$FILE_PATH" 2>/dev/null; then
            fixed_issues=true
        fi
    fi

    # Auto-fix code issues with ESLint
    if command -v eslint >/dev/null 2>&1; then
        # Try to auto-fix with ESLint
        if eslint --fix "$FILE_PATH" 2>/dev/null; then
            fixed_issues=true
        fi

        # Check if any issues remain after auto-fix
        if ! eslint "$FILE_PATH" 2>/dev/null; then
            {
                echo "⚠️ JavaScript/TypeScript style issues remain in $FILE_PATH after auto-fix"
                echo "Run: eslint '$FILE_PATH' to see remaining issues"
            } >&2
            issues_found=true
        fi
    fi

    # Report summary to stdout
    if [[ "$fixed_issues" == "true" ]] && [[ "$issues_found" == "true" ]]; then
        echo "🔧 Auto-fixed JS/TS formatting, some manual fixes may still be needed in $FILE_PATH"
    elif [[ "$fixed_issues" == "true" ]]; then
        echo "✅ Auto-fixed JavaScript/TypeScript formatting in $FILE_PATH"
    elif [[ "$issues_found" == "true" ]]; then
        echo "ℹ️ JavaScript/TypeScript linting suggestions available for $FILE_PATH"
    fi

    # Note: No exit codes - just provide informational feedback
}

run_css_linters() {
    local issues_found=false
    local fixed_issues=false

    # Auto-fix formatting with Prettier
    if command -v prettier >/dev/null 2>&1; then
        if prettier --write --print-width=120 "$FILE_PATH" 2>/dev/null; then
            fixed_issues=true
        fi
    fi

    # Auto-fix CSS issues with Stylelint
    if command -v stylelint >/dev/null 2>&1; then
        # Try to auto-fix with Stylelint
        if stylelint --fix "$FILE_PATH" 2>/dev/null; then
            fixed_issues=true
        fi

        # Check if any issues remain after auto-fix
        if ! stylelint "$FILE_PATH" 2>/dev/null; then
            {
                echo "⚠️ CSS style issues remain in $FILE_PATH after auto-fix"
                echo "Run: stylelint '$FILE_PATH' to see remaining issues"
            } >&2
            issues_found=true
        fi
    fi

    # Report summary to stdout
    if [[ "$fixed_issues" == "true" ]] && [[ "$issues_found" == "true" ]]; then
        echo "🔧 Auto-fixed CSS formatting, some manual fixes may still be needed in $FILE_PATH"
    elif [[ "$fixed_issues" == "true" ]]; then
        echo "✅ Auto-fixed CSS formatting in $FILE_PATH"
    elif [[ "$issues_found" == "true" ]]; then
        echo "ℹ️ CSS linting suggestions available for $FILE_PATH"
    fi

    # Note: No exit codes - just provide informational feedback
}


# ---------------------------------------------------------------------
# MAIN LINTING DISPATCH
# ---------------------------------------------------------------------

# Always apply generic fixes first
apply_generic_fixes

# Run appropriate linters based on file type
case "$FILE_PATH" in
    *.py) run_python_linters ;;
    *.json) run_json_linters ;;
    *.yaml|*.yml) run_yaml_linters ;;
    *.sh|*.bash) run_shell_linters ;;
    *.js|*.jsx|*.ts|*.tsx|*.mjs) run_javascript_linters ;;
    *.css|*.scss|*.less) run_css_linters ;;
    *) ;;  # Generic fixes already applied above
esac

# Default success
exit 0
