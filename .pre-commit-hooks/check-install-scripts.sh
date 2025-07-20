#!/bin/bash
# Pre-commit hook to detect and block unauthorized install scripts

set -euo pipefail

# Find all install scripts that modify .claude directory
# Exclude legitimate scripts that don't touch .claude
UNAUTHORIZED_SCRIPTS=$(find . -type f -name "*.sh" | \
    grep -E "(install).*\.sh$" | \
    grep -v "safe_install.sh" | \
    grep -v ".git" | \
    grep -v "test_" | \
    grep -v "setup-venv.sh" | \
    grep -v "setup-pre-commit.sh" | \
    grep -v "setup-development.sh" | \
    grep -v "setup-template.sh" | \
    grep -v "check-install-scripts.sh" || true)

if [ -n "$UNAUTHORIZED_SCRIPTS" ]; then
    echo "❌ UNAUTHORIZED INSTALL SCRIPTS DETECTED!"
    echo ""
    echo "The following scripts violate the single install script policy:"
    echo "$UNAUTHORIZED_SCRIPTS" | while read -r script; do
        echo "  - $script"
    done
    echo ""
    echo "ONLY safe_install.sh is allowed for installations!"
    echo ""
    echo "WHY THIS MATTERS:"
    echo "- Multiple install scripts caused confusion and system damage"
    echo "- Users lost work due to conflicting installation procedures"
    echo "- safe_install.sh provides mandatory backups and safety checks"
    echo ""
    echo "ACTION REQUIRED:"
    echo "1. Remove the unauthorized scripts listed above"
    echo "2. Add any needed functionality to safe_install.sh"
    echo "3. Ensure safe_install.sh creates backups before any changes"
    echo ""
    exit 1
fi

echo "✅ Install script check passed - only safe_install.sh found"
exit 0
