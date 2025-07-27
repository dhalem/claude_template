# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Real-Time Duplicate Prevention System

This module provides real-time code similarity detection and duplicate prevention
for Claude Code workflows. Built using TDD methodology with comprehensive testing.

Modules:
    database: Vector database connection and management (Qdrant)
    embedding: Code embedding and similarity detection (UniXcoder)
    detection: Core duplicate detection logic
    hooks: Claude Code hook integration
"""

__version__ = "0.1.0"
__author__ = "Claude Code Assistant"
