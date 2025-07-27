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
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestEnvironment(unittest.TestCase):
    def test_env_vars(self):
        """Debug environment variables."""
        print(f"\nGEMINI_API_KEY: {'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
        print(f"GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
        self.assertTrue(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

    def test_import_gemini(self):
        """Test importing GeminiClient."""
        from gemini_client import GeminiClient

        client = GeminiClient()
        self.assertIsNotNone(client)


if __name__ == "__main__":
    unittest.main()
