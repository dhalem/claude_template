# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Remediation Tracking: 2025-01-21 - Hooks System

## Review Summary
- **Directory Reviewed**: /home/dhalem/github/claude_template/hooks
- **Review Tool**: mcp__code-review__review_code (gemini-2.5-pro)
- **Focus Areas**: test_coverage, installation_safety
- **Total Issues Found**: 11 (4 Critical, 4 Major, 3 Minor)

## Issue Categories
- **Critical**: 4 - Hardcoded paths, missing safe_install.sh, documentation errors, hanging scripts
- **Major**: 4 - Redundant test scripts, fragile JSON parsing, hardcoded logic, inconsistent settings
- **Minor**: 3 - Verbose comments, repetitive wrappers, redundant hook configuration

## Remediation Status
- [ ] Phase 1: Critical Issues
- [ ] Phase 2: Major Issues
- [ ] Phase 3: Minor Issues
- [ ] Phase 4: Validation & Documentation

---

# 🔥 Phase 1: Critical Issues Remediation

## Critical Issue 1: Hardcoded Absolute Paths
- **Issue Type**: Critical
- **Files Affected**: precommit-protection-guard.sh, test-script-integrity-guard.sh, update-settings.py, settings.json
- **Expected Changes**: Replace `/home/dhalem/` with relative paths or dynamic detection
- **Status**: Pending
- **Risk**: System completely non-portable, security risk, fails for other users

## Critical Issue 2: Missing safe_install.sh Script
- **Issue Type**: Critical
- **Files Affected**: README.md references non-existent script
- **Expected Changes**: Create safe_install.sh or update README warning
- **Status**: Pending
- **Risk**: Users left with only "unsafe" installation methods

## Critical Issue 3: Dangerous Exit Code Documentation
- **Issue Type**: Critical
- **Files Affected**: DOCS.md
- **Expected Changes**: Fix examples that incorrectly use `exit 1` for blocking
- **Status**: Pending
- **Risk**: Developers writing ineffective guards based on wrong documentation

## Critical Issue 4: Potential Hanging Scripts
- **Issue Type**: Critical
- **Files Affected**: Shell guards that parse JSON via Python subprocess
- **Expected Changes**: Fix stdin handling to prevent hangs
- **Status**: Pending
- **Risk**: Guards failing silently or hanging in production

---

# 🔧 Phase 2: Major Issues Remediation

## Major Issue 1: Redundant Test Scripts
- **Issue Type**: Major
- **Files Affected**: test_simple.sh, test_working.sh, test_final.sh, test_debug.sh
- **Expected Changes**: Consolidate into single reliable test suite
- **Status**: Pending
- **Risk**: Chaotic testing, unclear which tests are authoritative

## Major Issue 2: Fragile JSON Parsing in Shell
- **Issue Type**: Major
- **Files Affected**: Multiple shell scripts calling `python -c "import json..."`
- **Expected Changes**: Migrate to Python framework or improve error handling
- **Status**: Pending
- **Risk**: Brittle guards, dependency on specific Python executable

## Major Issue 3: Hardcoded Logic in update-settings.py
- **Issue Type**: Major
- **Files Affected**: update-settings.py
- **Expected Changes**: Make portable, remove hardcoded paths and logic
- **Status**: Pending
- **Risk**: Non-portable configuration updates

## Major Issue 4: Inconsistent settings.json Formats
- **Issue Type**: Major
- **Files Affected**: settings.json, settings_simple.json
- **Expected Changes**: Standardize on one format, use regex matchers
- **Status**: Pending
- **Risk**: Configuration confusion and errors

---

# ✨ Phase 3: Minor Issues Remediation

## Minor Issue 1: Verbose RULE #0 Comments
- **Issue Type**: Minor
- **Files Affected**: Almost every script file
- **Expected Changes**: Create more concise reminder format
- **Status**: Pending
- **Risk**: Reduced signal-to-noise ratio in code

## Minor Issue 2: Repetitive Wrapper Scripts
- **Issue Type**: Minor
- **Files Affected**: adaptive-guard.py, lint-guard.py
- **Expected Changes**: Consolidate into single script with guard type parameter
- **Status**: Pending
- **Risk**: Unnecessary code duplication

## Minor Issue 3: Redundant Hook Configuration
- **Issue Type**: Minor
- **Files Affected**: settings.json hook registrations
- **Expected Changes**: Use regex matchers for cleaner configuration
- **Status**: Pending
- **Risk**: Verbose, harder to maintain configuration

---

# ✅ Phase 4: Validation & Documentation

## Phase 4: Final Validation
- **Status**: Pending
- **Started**: [To be filled when started]

## Planned Validation Steps:
1. Run complete test suite
2. Re-run MCP code review on hooks directory
3. Compare findings with original review
4. Update documentation as needed
5. Push all changes

---

# 🛡️ Implementation Priority Order

**Immediate (Critical):**
1. Fix hardcoded paths (blocks all other users)
2. Correct exit code documentation (prevents ineffective guards)
3. Create missing safe_install.sh (installation safety)
4. Fix hanging script potential (production reliability)

**High Priority (Major):**
1. Consolidate test scripts (testing clarity)
2. Improve JSON parsing robustness (guard reliability)
3. Fix update-settings.py portability (configuration management)
4. Standardize settings.json format (configuration consistency)

**Medium Priority (Minor):**
1. Reduce RULE #0 comment verbosity (code readability)
2. Consolidate wrapper scripts (code maintainability)
3. Simplify hook configuration (maintenance burden)

---

# 📊 Success Metrics

**Critical Success Criteria:**
- [ ] System works for users other than `/home/dhalem/`
- [ ] All documentation examples use correct exit codes
- [ ] Safe installation method available
- [ ] No hanging scripts in production

**Quality Improvements:**
- [ ] Single authoritative test suite per guard
- [ ] Robust error handling in all guards
- [ ] Portable configuration management
- [ ] Consistent settings format

**Code Quality:**
- [ ] Reduced code duplication
- [ ] Cleaner configuration syntax
- [ ] Improved code readability

---

# 🔄 Next Steps

**Ready to begin Phase 1 with:**
1. Pre-change safety check: `./run_tests.sh`
2. Start with hardcoded paths fix (highest impact)
3. Work through critical issues systematically
4. Commit each fix individually with proper verification
5. Update this tracking document after each completion

**Emergency Contact:**
- Original issue: MCP code review identified installation safety risks
- Template source: REVIEW_REMEDIATION_TEMPLATE.md
- Related postmortem: POSTMORTEM_FAST_MODE_VIOLATION_20250121.md
