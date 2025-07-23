# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Test suite for duplicate prevention system

This package contains comprehensive tests for the duplicate prevention system
following TDD methodology with proper test organization.

Test Structure:
    unit/: Fast unit tests (<1s each) for individual components
    integration/: Integration tests (<30s each) for component interactions
    performance/: Performance benchmarks and load tests
"""
