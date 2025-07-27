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

echo "=== Environment Debug ==="
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:+SET}"
echo "GOOGLE_API_KEY: ${GOOGLE_API_KEY:+SET}"

# Source and activate venv like run_tests.sh does
source venv/bin/activate

echo "=== After venv activation ==="
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:+SET}"
echo "GOOGLE_API_KEY: ${GOOGLE_API_KEY:+SET}"

# Try to run the same pytest command
./venv/bin/python -c "import os; print(f'Python sees GEMINI_API_KEY: {bool(os.environ.get(\"GEMINI_API_KEY\"))}')"
./venv/bin/python -c "import os; print(f'Python sees GOOGLE_API_KEY: {bool(os.environ.get(\"GOOGLE_API_KEY\"))}')"
