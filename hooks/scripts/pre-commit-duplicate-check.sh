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

# Pre-commit hook script for duplicate code prevention
# This script checks all modified code files for similarity to existing code

set -euo pipefail

# Ensure we're in the repository root
cd "$(git rev-parse --show-toplevel)"

# Activate Python virtual environment if available
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Using virtual environment: venv"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Using virtual environment: .venv"
else
    echo "⚠️  No virtual environment found, using system Python" >&2
    # Check if required Python packages are available
    if ! python3 -c "import sys; sys.path.insert(0, '.'); from duplicate_prevention.database import DatabaseConnector" 2>/dev/null; then
        echo "❌ ERROR: Required Python packages not available" >&2
        echo "💡 Please run: ./setup-venv.sh" >&2
        exit 1
    fi
fi

# Get list of modified files (staged for commit)
# Filter to only include supported code file extensions
MODIFIED_FILES=$(git diff --cached --name-only --diff-filter=AM | grep -E '\.(py|js|jsx|ts|tsx|java|cpp|c|go|rs)$' || true)

if [ -z "$MODIFIED_FILES" ]; then
    echo "✅ No code files to check for duplicates"
    exit 0
fi

echo "🔍 Checking for duplicate code in modified files..."

# Check if duplicate prevention system is available
if [ ! -f "hooks/python/main.py" ]; then
    echo "⚠️  Duplicate prevention system not found, skipping check"
    exit 0
fi

# Skip indexing during pre-commit (hangs due to large repository)
echo "⚠️  Skipping repository indexing during pre-commit (too slow)"
echo "💡 Repository should be indexed separately using: ./scripts/index_repository.py"

# Process each modified file
EXIT_CODE=0
for FILE in $MODIFIED_FILES; do
    if [ ! -f "$FILE" ]; then
        continue  # File might be deleted
    fi

    echo "  Checking: $FILE"

    # Get file content and escape it for JSON
    FILE_CONTENT=$(cat "$FILE" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read()))')

    # Create temporary JSON input for the hook system
    JSON_INPUT=$(cat <<EOF
{
    "tool": "Write",
    "toolInput": {
        "file_path": "$(pwd)/$FILE",
        "content": $FILE_CONTENT
    }
}
EOF
)

    # Run the duplicate prevention guard
    REPO_ROOT=$(git rev-parse --show-toplevel)
    if echo "$JSON_INPUT" | (cd "$REPO_ROOT/hooks/python" && timeout 30 python3 main.py Write) 2>&1; then
        # Guard allowed the operation (no duplicates found)
        continue
    else
        GUARD_EXIT_CODE=$?
        if [ $GUARD_EXIT_CODE -eq 2 ]; then
            # Guard blocked the operation (duplicates found)
            echo ""
            echo "🚨 DUPLICATE CODE DETECTED IN: $FILE"
            echo ""
            echo "The duplicate prevention system has detected that this file contains"
            echo "code similar to existing code in the repository."
            echo ""
            echo "🤔 RECOMMENDATIONS:"
            echo "  1. Check if you can extend existing similar code instead"
            echo "  2. Refactor common functionality into shared utilities"
            echo "  3. If the code is truly different, consider renaming to clarify intent"
            echo ""
            echo "📋 TO SEE DETAILED SIMILARITY ANALYSIS:"
            echo "  Run: echo '$JSON_INPUT' | (cd \"$REPO_ROOT/hooks/python\" && python3 main.py Write)"
            echo ""
            EXIT_CODE=1
        else
            # Guard encountered an error
            echo "⚠️  Warning: Duplicate prevention check failed for $FILE (exit code: $GUARD_EXIT_CODE)" >&2
        fi
    fi
done

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ COMMIT BLOCKED: Duplicate code detected"
    echo ""
    echo "💡 To resolve:"
    echo "  1. Review the similarity analysis above"
    echo "  2. Edit existing similar files instead of creating new ones"
    echo "  3. Or ensure your new code is sufficiently different"
    echo ""
    echo "🚫 This check helps maintain code quality and reduce duplication"
    exit $EXIT_CODE
fi

echo "✅ No duplicate code detected"
exit 0
