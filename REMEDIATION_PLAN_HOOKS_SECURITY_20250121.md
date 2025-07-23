# Hooks Directory Security & Quality Remediation Plan

**Generated:** 2025-01-21
**Scope:** `/home/dhalem/github/claude_template/hooks/`
**Review Model:** gemini-2.5-pro
**Files Reviewed:** 107 files (833,589 bytes)

## Executive Summary

The hooks directory code review revealed a mature, security-conscious system with excellent architecture and testing culture. However, several critical security vulnerabilities and quality issues need immediate attention, particularly in the TOTP override system and hardcoded paths that limit portability.

**Overall Assessment:** Strong foundation with critical security gaps requiring immediate remediation.

## Priority Classification

### 🚨 CRITICAL (Security Vulnerabilities)
**Timeline:** Fix within 24 hours

### 🔴 MAJOR (Architecture & Quality Issues)
**Timeline:** Fix within 1 week

### 🟡 MINOR (Code Quality Improvements)
**Timeline:** Fix within 2 weeks

---

## 🚨 CRITICAL SECURITY ISSUES

### 1. TOTP Override System Security Vulnerabilities

**Risk Level:** CRITICAL
**Impact:** Potential security bypass, credential exposure

#### Issues:
1. **Plaintext Secret Storage** - TOTP secrets stored in `~/.claude/.env` without restrictive permissions
2. **Secret Backup Leakage** - `sed -i.backup` creates unprotected backup files with secrets
3. **Weak Fallback Authentication** - Hardcoded test key (`TESTKEY`/`123456`) provides backdoor

#### Remediation:

```bash
# File: setup-authenticator.sh
# IMMEDIATE FIX REQUIRED

# After creating/updating .env file:
chmod 600 "$ENV_FILE"
echo "✅ Secured $ENV_FILE with permissions 600"

# Remove backup files:
if [[ -f "$ENV_FILE.backup" ]]; then
    rm -f "$ENV_FILE.backup"
    echo "✅ Removed insecure backup file"
fi

# Use sed without backup:
sed -i "s/GOOGLE_API_KEY=.*/GOOGLE_API_KEY=$new_key/" "$ENV_FILE"
```

```python
# File: python/guards/base_guard.py
# REMOVE FALLBACK AUTHENTICATION

# DELETE this entire function:
def _validate_simple_totp(self, code: str) -> bool:
    # SECURITY RISK - Remove this fallback
    pass

# Make pyotp a hard dependency:
def validate_override_code(self, code: str) -> bool:
    if not self.totp_secret:
        return False

    try:
        import pyotp
    except ImportError:
        # Fail securely - no fallback
        return False

    totp = pyotp.TOTP(self.totp_secret)
    return totp.verify(code)
```

---

## 🔴 MAJOR QUALITY ISSUES

### 2. Hardcoded Paths Limiting Portability

**Risk Level:** MAJOR
**Impact:** Cannot be used by other users/environments

#### Issues:
- `/home/dhalem/...` paths throughout codebase
- User-specific home directory assumptions
- Non-portable Claude configuration paths

#### Remediation:

```bash
# Standard pattern for all shell scripts:
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

# Example fix for test_debug.sh:
# OLD: /home/dhalem/.claude/adaptive-guard.sh
# NEW: "$CLAUDE_HOME/adaptive-guard.sh"
```

```python
# File: python/guards/awareness_guards.py
import os

def get_message(self) -> str:
    project_root = os.environ.get("PROJECT_ROOT") or os.getcwd()
    return f"""
    1. ACTIVATE VENV FIRST (MANDATORY):
       cd {project_root}
       [ ! -d "venv" ] && ./setup-venv.sh
       source venv/bin/activate
    """
```

### 3. Inconsistent Script Architecture

**Risk Level:** MAJOR
**Impact:** Maintenance overhead, user confusion

#### Issues:
- Multiple JSON parsers (`jq` vs `parse_claude_input.py`)
- Redundant guard scripts (`adaptive-guard.sh`, `comprehensive-guard.sh`, etc.)
- Multiple test runners causing confusion

#### Remediation:

**Phase A: Consolidate Guard Scripts**
```bash
# Keep only these active guards:
- adaptive-guard.sh (main Python wrapper)
- lint-guard.sh (Python wrapper)

# Move to archive/:
- comprehensive-guard.sh
- claude-output-guard.sh
- precommit-protection-guard.sh (standalone)
- test-script-integrity-guard.sh (standalone)
```

**Phase B: Standardize JSON Parsing**
```bash
# Update all remaining shell scripts to use:
"$SCRIPT_DIR/parse_claude_input.py" --field "tool_input.command"

# Remove jq dependencies from:
- claude-output-guard.sh
- comprehensive-guard.sh
```

**Phase C: Consolidate Test Runners**
```bash
# Make run_tests.sh the single entry point
# Remove or deprecate:
- test-hooks.sh
- test-claude-hooks.sh
- python/tests/run_tests.py (keep as library)
```

### 4. Documentation Inconsistency

**Risk Level:** MAJOR
**Impact:** Developer confusion, maintenance issues

#### Issues:
- `HOOKS.md` lists 27 guards, but only ~18 are registered
- Missing guards: `AssumptionDetectionGuard`, `FalseSuccessGuard`
- Commented out guards: `TestSuiteEnforcementGuard`

#### Remediation:

```python
# File: python/main.py - Audit create_registry()
def create_registry() -> GuardRegistry:
    registry = GuardRegistry()

    # Ensure ALL documented guards are either:
    # 1. Registered here, OR
    # 2. Marked as "Status: Planned" in HOOKS.md

    # Add missing guards or remove from docs:
    # registry.register(AssumptionDetectionGuard())  # Add if implemented
    # registry.register(FalseSuccessGuard())         # Add if implemented
    registry.register(TestSuiteEnforcementGuard())   # Uncomment if working
```

```markdown
# File: HOOKS.md - Add status indicators
## Current Guards Reference

### ✅ Active Guards (Implemented & Registered)
- GitNoVerifyGuard - Prevents git --no-verify
- DockerRestartGuard - Suggests rebuild over restart

### 🚧 Planned Guards (Documented but not implemented)
- AssumptionDetectionGuard - Status: Planned
- FalseSuccessGuard - Status: Planned

### ⚠️ Disabled Guards (Implemented but not registered)
- TestSuiteEnforcementGuard - Status: Disabled (needs debugging)
```

---

## 🟡 MINOR IMPROVEMENTS

### 5. Code Quality Issues

#### Remove `eval` Usage
```bash
# File: test-hooks.sh
# Replace eval with direct execution
run_test() {
    local test_name="$1"
    local command="$2"
    shift 2

    # Instead of: eval "$test_command"
    $command "$@"
}
```

#### Consolidate Environment Loading
```python
# File: python/main.py
import os
from dotenv import load_dotenv

def main():
    # Load .env files consistently
    load_dotenv(os.path.expanduser("~/.claude/.env"))
    load_dotenv(".env")  # Project-level overrides
```

#### Reduce Boilerplate
```bash
# Replace verbose RULE #0 headers with:
# See CLAUDE.md Rule #0 for mandatory requirements
```

---

## Implementation Plan

### Phase 1: Critical Security (24 hours)
1. ✅ Fix TOTP secret file permissions
2. ✅ Remove backup file creation
3. ✅ Remove fallback authentication
4. ✅ Test override system security

### Phase 2: Path Portability (3 days)
1. ✅ Replace all hardcoded `/home/dhalem/` paths
2. ✅ Use dynamic path resolution in shell scripts
3. ✅ Update Python guards to use configurable paths
4. ✅ Test in fresh environment

### Phase 3: Architecture Cleanup (1 week)
1. ✅ Archive redundant guard scripts
2. ✅ Standardize on centralized JSON parsing
3. ✅ Consolidate test runners
4. ✅ Update documentation consistency

### Phase 4: Quality Improvements (2 weeks)
1. ✅ Remove eval usage
2. ✅ Standardize environment loading
3. ✅ Reduce boilerplate comments
4. ✅ Final testing and validation

## Success Criteria

- [ ] All critical security vulnerabilities resolved
- [ ] System works for any user (no hardcoded paths)
- [ ] Single authoritative test runner
- [ ] Documentation matches implementation
- [ ] All existing tests continue to pass
- [ ] New security tests added for TOTP system

## Risk Mitigation

1. **Backup Strategy**: Full git branch backup before changes
2. **Testing Strategy**: Run full test suite after each phase
3. **Rollback Plan**: Each phase can be individually reverted
4. **Validation**: Test in clean environment with different user

---

**Total Estimated Effort:** 2-3 weeks
**Critical Path:** Security fixes (Phase 1) must be completed first
**Review Required:** Security expert review of TOTP fixes before deployment
