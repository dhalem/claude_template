#!/bin/bash
# Test override mechanism

GUARD_SCRIPT="/home/dhalem/github/claude_template/hooks/precommit-protection-guard.sh"
TEST_INPUT='{"tool_name": "Bash", "tool_input": {"command": "pre-commit uninstall"}}'

# Test with override
export HOOK_OVERRIDE_CODE="TEST123"
echo "$TEST_INPUT" | "$GUARD_SCRIPT" >/dev/null 2>&1
exit_code=$?
unset HOOK_OVERRIDE_CODE

echo "Override test exit code: $exit_code"
if [ $exit_code -eq 0 ]; then
    echo "✅ Override mechanism works correctly"
else
    echo "❌ Override mechanism failed"
fi
