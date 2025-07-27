#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

import os
import sys

print("=== Environment Debug ===")
print(f"Python: {sys.executable}")
print(f"GEMINI_API_KEY: {'SET' if os.environ.get('GEMINI_API_KEY') else 'NOT SET'}")
print(f"GOOGLE_API_KEY: {'SET' if os.environ.get('GOOGLE_API_KEY') else 'NOT SET'}")
print(f"PRE_COMMIT: {os.environ.get('PRE_COMMIT', 'NOT SET')}")
print(f"Current dir: {os.getcwd()}")
print(f"sys.path[0]: {sys.path[0] if sys.path else 'EMPTY'}")

# Try importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "indexing", "src"))
try:
    from gemini_client import GeminiClient

    print("Import successful")
    try:
        client = GeminiClient()
        print("GeminiClient instantiation successful")
    except Exception as e:
        print(f"GeminiClient instantiation failed: {e}")
except Exception as e:
    print(f"Import failed: {e}")
