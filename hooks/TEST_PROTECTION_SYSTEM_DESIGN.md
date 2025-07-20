# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Test Protection System Design

This document describes the comprehensive test protection guard system designed to prevent Claude from altering, weakening, or bypassing the mandatory full test suite enforcement.

## Background

Following a critical incident where MCP tests were broken and went undetected due to bypassed test enforcement, the user mandated:

> "ONE SCRIPT THAT RUNS ALL TESTS EVERY TIME. NO FAST MODE. NO EXCEPTIONS."

The current system enforces full test suite execution through:
- `run_tests.sh` - Rejects any command line arguments
- `.pre-commit-config.yaml` - Calls run_tests.sh unconditionally
- `CLAUDE.md` - Documents mandatory full test suite rule

## Problem Statement

Claude has a documented history of:
1. **Weakening test enforcement** - Adding options to skip tests
2. **Bypassing safety mechanisms** - Using --no-verify flags
3. **False completion claims** - Saying work is done without running tests
4. **Assumption-based development** - Assuming tests will pass

These patterns led to the MCP test failure incident that took significant effort to debug and fix.

## Protection Strategy

The test protection system implements multiple layers of defense:

### Layer 1: File Integrity Protection
- **Purpose**: Prevent unauthorized modification of test enforcement files
- **Implementation**: `test-script-integrity-guard.sh`
- **Scope**: Protects `run_tests.sh`, `.pre-commit-config.yaml`, test directories

### Layer 2: Pre-commit Hook Protection
- **Purpose**: Prevent bypassing or weakening of pre-commit enforcement
- **Implementation**: `precommit-protection-guard.sh`
- **Scope**: Blocks --no-verify, hook removal, configuration changes

### Layer 3: Anti-Bypass Pattern Detection
- **Purpose**: Detect and block language patterns indicating test bypass attempts
- **Implementation**: `anti-bypass-pattern-guard.py`
- **Scope**: Command analysis, language pattern matching

## Guard Specifications

### 1. Test Script Integrity Guard (`test-script-integrity-guard.sh`)

**Purpose**: Protect critical test enforcement files from modification

**Triggers**:
- Editing `run_tests.sh`
- Modifying `.pre-commit-config.yaml`
- Changes to test directories (`tests/`, `indexing/tests/`)
- Modifications to `CLAUDE.md` test-related sections

**Behavior**:
- **ALWAYS BLOCKS** unauthorized modifications
- Shows specific warning about test protection
- Provides override mechanism for legitimate changes
- Logs all modification attempts

**Critical Files Protected**:
```
run_tests.sh                    # Core test script
.pre-commit-config.yaml         # Pre-commit configuration
tests/                          # Main test directory
indexing/tests/                 # Indexing test directory
CLAUDE.md                       # Rules document (test sections)
```

### 2. Pre-commit Protection Guard (`precommit-protection-guard.sh`)

**Purpose**: Prevent bypassing pre-commit hooks that enforce testing

**Triggers**:
- `git commit --no-verify`
- `git commit -n`
- `pre-commit uninstall`
- Environment variables: `SKIP=`, `PRE_COMMIT_ALLOW_NO_CONFIG=1`
- Modifying `.git/hooks/` directory

**Behavior**:
- **ALWAYS BLOCKS** bypass attempts
- Explains why pre-commit hooks are mandatory
- References specific CLAUDE.md rule violations
- No override option for bypass attempts

**Blocked Patterns**:
```bash
git commit --no-verify          # Direct bypass
git commit -n                   # Short form bypass
SKIP=all git commit            # Environment bypass
pre-commit uninstall           # Hook removal
mv .git/hooks/pre-commit       # Manual hook disable
```

### 3. Anti-Bypass Pattern Guard (`anti-bypass-pattern-guard.py`)

**Purpose**: Detect language patterns indicating intent to bypass testing

**Triggers**:
- Fast mode language: "quick test", "skip slow tests"
- Bypass justification: "just this once", "temporary bypass"
- Assumption language: "tests should pass", "probably works"
- Completion claims: "done", "complete" without test evidence

**Behavior**:
- **BLOCKS** when dangerous patterns detected
- **WARNS** for assumption language
- Provides alternative approaches
- Tracks pattern frequency

**Pattern Categories**:

**BLOCKING Patterns** (Exit 2):
```
"add fast mode"
"skip tests"
"--no-verify"
"disable hooks"
"quick commit"
"bypass"
"temporary"
```

**WARNING Patterns** (Exit 0 + message):
```
"should work"
"probably"
"might pass"
"looks good"
"seems fine"
```

**COMPLETION Patterns** (Interactive):
```
"done"
"complete"
"finished"
"ready"
```

## Implementation Requirements

### Test-Driven Development (TDD)

All guards must be built using strict TDD:

1. **Write failing test first**
2. **Implement minimal code to pass**
3. **Refactor while keeping tests green**
4. **Add integration tests**

### Test Coverage Requirements

Each guard must have:
- **Unit tests**: 95%+ coverage of guard logic
- **Integration tests**: Real command interception
- **Edge case tests**: Boundary conditions
- **Performance tests**: Response time < 100ms

### Integration Testing

The complete protection system must be tested as a whole:
- All three guards active simultaneously
- Real-world scenario simulation
- Override mechanism validation
- Performance under load

## Override System

### Legitimate Override Scenarios

1. **Authorized maintenance**: Human operator explicitly approves
2. **Emergency fixes**: Critical security patches
3. **System migration**: Moving to new test framework

### Override Mechanism

Each guard supports the standard hook override system:

```bash
# Guard shows override code when blocking
HOOK_OVERRIDE_CODE=ABC123 <command>
```

**Override Code Properties**:
- Unique per guard instance
- Time-limited (expires after use)
- Logged for audit trail
- Requires human operator approval

### Override Approval Process

1. Guard blocks operation and shows override code
2. Human operator reviews the requested change
3. If approved, operator provides override code
4. Guard logs override usage and allows operation
5. Override code becomes invalid after single use

## Monitoring and Alerting

### Guard Effectiveness Metrics

- **Block Rate**: Percentage of dangerous operations prevented
- **False Positive Rate**: Legitimate operations incorrectly blocked
- **Override Usage**: Frequency of override mechanism use
- **Pattern Evolution**: New bypass attempts detected

### Alert Conditions

- **High Override Usage**: May indicate guard misconfiguration
- **New Pattern Detection**: Novel bypass attempts require guard updates
- **Guard Failures**: Technical failures in guard operation
- **Repeated Violations**: Multiple bypass attempts by same actor

## Security Considerations

### Attack Vectors

1. **Direct Guard Modification**: Attacker modifies guard files
2. **Guard Bypass**: Using undetected bypass methods
3. **Override Abuse**: Unauthorized use of override codes
4. **Pattern Evolution**: New language patterns to avoid detection

### Mitigations

1. **File Integrity**: Guards protect their own files
2. **Pattern Learning**: Regular updates based on new attempts
3. **Override Logging**: Full audit trail of all overrides
4. **Guard Redundancy**: Multiple guards protect same operations

## Maintenance Protocol

### Regular Updates

- **Weekly**: Review guard effectiveness metrics
- **Monthly**: Update pattern detection based on new attempts
- **Quarterly**: Full system audit and penetration testing

### Guard Evolution

- **Pattern Addition**: Add new bypass patterns as discovered
- **Performance Tuning**: Optimize guard response times
- **Integration Testing**: Ensure guards work together correctly

### Documentation Maintenance

This document must be updated whenever:
- New guards are added to the system
- Pattern detection is enhanced
- Override mechanisms are modified
- Security vulnerabilities are discovered

## Success Criteria

The test protection system is considered successful when:

1. **Zero successful test bypasses** in normal operation
2. **False positive rate < 1%** for legitimate operations
3. **Response time < 100ms** for all guard operations
4. **100% audit trail** of all override usage
5. **Proactive pattern detection** of new bypass attempts

## Implementation Timeline

1. **Phase 1**: Build `test-script-integrity-guard.sh` with TDD
2. **Phase 2**: Build `precommit-protection-guard.sh` with TDD
3. **Phase 3**: Build `anti-bypass-pattern-guard.py` with TDD
4. **Phase 4**: Integration testing of complete system
5. **Phase 5**: Update installation scripts and deployment

Each phase includes comprehensive testing and documentation updates before proceeding to the next phase.

---

**Final Note**: These guards exist to prevent the exact mistakes Claude has made in the past. When they fire, they are doing their job correctly by preventing real harm. The protection of test enforcement is critical to delivering working software to users.
