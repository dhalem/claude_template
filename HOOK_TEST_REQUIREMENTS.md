# Hook Test Requirements

## 🚨 MANDATORY HOOK TESTING REQUIREMENTS 🚨

**ALL HOOKS MUST HAVE COMPREHENSIVE TESTS - NO EXCEPTIONS**

## Test Categories Required

### 1. Pre-Install Tests
- **Location**: `hooks/tests/test_hooks_pre_install.sh`
- **Purpose**: Verify hooks work correctly in development environment
- **Requirements**:
  - Test each hook with valid input
  - Test each hook with invalid input
  - Test each hook with empty input
  - Test stdin handling
  - Test exit codes (0=allow, 1=error, 2=block)

### 2. Installation Tests
- **Location**: `hooks/tests/test_installation.sh`
- **Purpose**: Verify installation process works correctly
- **Requirements**:
  - Test backup creation
  - Test file copying
  - Test permission setting
  - Test wrapper script generation
  - Test Python dependencies

### 3. Post-Install Tests
- **Location**: `hooks/tests/test_hooks_post_install.sh`
- **Purpose**: Verify hooks work after installation
- **Requirements**:
  - Test installed hooks in ~/.claude
  - Test stdin handling after install
  - Test all guards work correctly
  - Test override mechanisms
  - Test logging functionality

## Hook Coverage Requirements

### Python Hooks (hooks/python/)
1. **adaptive-guard.sh** → test_adaptive_guard.py
2. **lint-guard.sh** → test_lint_guard.py
3. **All Python guards** → Individual test files in hooks/python/tests/

### Protection Guards (hooks/)
1. **test-script-integrity-guard.sh** → test_test_script_integrity_guard.sh
2. **precommit-protection-guard.sh** → test_precommit_protection_guard.sh
3. **anti-bypass-pattern-guard.py** → test_anti_bypass_pattern_guard.py

### Shell Wrappers
1. **adaptive-guard.sh** → Must test stdin piping to Python
2. **lint-guard.sh** → Must test stdin piping to Python

## Integration with run_tests.sh

The following section MUST be added to run_tests.sh:

```bash
# Run hook tests
test_hooks() {
    log_info "Running hook system tests..."

    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"

    # Pre-install tests
    if [ -f "hooks/tests/test_hooks_pre_install.sh" ]; then
        log_info "Running pre-install hook tests..."
        if ! ./hooks/tests/test_hooks_pre_install.sh; then
            log_error "Pre-install hook tests FAILED"
            return 1
        fi
    fi

    # Python hook tests
    log_info "Running Python hook tests..."
    if ! "$VENV_PATH/bin/python" -m pytest hooks/python/tests/ -v; then
        log_error "Python hook tests FAILED"
        return 1
    fi

    # Post-install tests (if hooks are installed)
    if [ -d "$HOME/.claude/python" ]; then
        log_info "Running post-install hook tests..."
        if [ -f "hooks/tests/test_hooks_post_install.sh" ]; then
            if ! ./hooks/tests/test_hooks_post_install.sh; then
                log_error "Post-install hook tests FAILED"
                return 1
            fi
        fi
    fi

    log_success "Hook tests passed"
    return 0
}
```

## Test Maintenance Rules

1. **NEVER SKIP HOOK TESTS** - They protect critical functionality
2. **ADD TEST FOR EVERY NEW HOOK** - No hook without a test
3. **TEST STDIN HANDLING** - The #1 cause of hook failures
4. **TEST BOTH SUCCESS AND FAILURE** - Ensure proper exit codes
5. **TEST AFTER CHANGES** - Any hook modification requires test run

## Common Test Patterns

### Testing Shell Hook with Stdin
```bash
test_hook_stdin() {
    local input='{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}'
    echo "$input" | /path/to/hook.sh
    [ $? -eq 0 ] || fail "Hook should allow valid input"
}
```

### Testing Python Guard
```python
def test_guard_blocks_pattern(self):
    input_json = {
        "tool_name": "Edit",
        "tool_input": {"new_string": "blocked_pattern"}
    }
    result = subprocess.run(
        [sys.executable, "guard.py"],
        input=json.dumps(input_json),
        capture_output=True,
        text=True
    )
    self.assertEqual(result.returncode, 2)  # Should block
```

## Failure Consequences

If hook tests fail:
1. **Pre-commit will block the commit**
2. **CI/CD will fail the build**
3. **The issue MUST be fixed immediately**
4. **NO bypassing with --no-verify**

## Historical Context

Hook stdin handling was broken in commit [commit_id] because:
- Python main.py expected stdin but got empty string
- No tests caught this regression
- Hooks failed silently in production

This MUST NEVER happen again.

## Enforcement

1. **test-script-integrity-guard.sh** protects this file
2. **precommit-protection-guard.sh** prevents bypassing tests
3. **anti-bypass-pattern-guard.py** blocks test skipping patterns
4. **Pre-commit hooks** run tests automatically

---

**Remember**: Hooks are critical safety infrastructure. Test them thoroughly.
