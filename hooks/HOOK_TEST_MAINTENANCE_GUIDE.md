# Hook Test Maintenance Guide

## 🚨 CRITICAL: Hook Tests Are Safety Infrastructure

**Hook tests protect against the exact mistakes Claude tends to make. They MUST be maintained rigorously.**

## Daily Maintenance Requirements

### 1. Before Every Commit
```bash
# MANDATORY - run full test suite
./run_tests.sh

# Hook tests are included and MUST pass
# No bypassing with --no-verify
```

### 2. After Any Hook Changes
```bash
# Test the specific hook you changed
./hooks/tests/test_hooks_pre_install.sh

# Test the protection guards
./hooks/tests/test_*_guard.sh

# Run full test suite
./run_tests.sh
```

### 3. After Installation Changes
```bash
# Test installation process
./hooks/tests/test_installation_verification.sh

# Test post-install functionality
./hooks/tests/test_hooks_post_install.sh
```

## Test Categories and Their Purpose

### Pre-Install Tests (`test_hooks_pre_install.sh`)
**Purpose**: Verify hooks work in development environment
**Critical because**: Catches issues before installation
**Maintenance**:
- Update when adding new hooks
- Update when changing stdin handling
- Add new test patterns for new guards

### Installation Verification (`test_installation_verification.sh`)
**Purpose**: Verify installation process works correctly
**Critical because**: Broken installations cause production failures
**Maintenance**:
- Update when installation script changes
- Add tests for new installation features
- Verify backup/restore functionality

### Post-Install Tests (`test_hooks_post_install.sh`)
**Purpose**: Verify hooks work after installation
**Critical because**: Installation may break hook functionality
**Maintenance**:
- Update when hook behavior changes
- Add tests for new guards in production
- Test override mechanisms remain functional

### Python Hook Tests (`hooks/python/tests/`)
**Purpose**: Unit test all Python guard logic
**Critical because**: Guards contain complex logic that must be tested
**Maintenance**:
- Add test for every new guard
- Test all code paths (allow, block, error)
- Mock Claude input parsing correctly

### Protection Guard Tests (`test_*_guard.sh`)
**Purpose**: Test individual protection guards
**Critical because**: These guards protect the test system itself
**Maintenance**:
- One test file per guard
- Test blocking behavior specifically
- Test override mechanisms

## Adding Tests for New Hooks

### For Shell Hooks:
1. **Add to pre-install tests**:
   ```bash
   # In test_hooks_pre_install.sh
   if [ -f "$HOOKS_DIR/new-hook.sh" ]; then
       run_test "Valid input" \
           "echo '{\"tool_name\":\"Read\"}' | $HOOKS_DIR/new-hook.sh" \
           0

       run_test "Empty input" \
           "echo '' | $HOOKS_DIR/new-hook.sh" \
           1
   fi
   ```

2. **Add to post-install tests**:
   ```bash
   # In test_hooks_post_install.sh
   test_hook "new-hook.sh basic functionality" \
       "$HOME/.claude/new-hook.sh" \
       '{"tool_name": "Read", "tool_input": {"file_path": "test.txt"}}' \
       "allow"
   ```

### For Python Guards:
1. **Create individual test file**:
   ```bash
   touch hooks/tests/test_new_guard.py
   chmod +x hooks/tests/test_new_guard.py
   ```

2. **Add test content**:
   ```python
   #!/usr/bin/env python3
   import subprocess
   import json
   import sys

   def test_guard_blocks_pattern():
       input_json = {"tool_name": "Edit", "tool_input": {"new_string": "bad_pattern"}}
       result = subprocess.run([sys.executable, "hooks/new-guard.py"],
                              input=json.dumps(input_json),
                              capture_output=True, text=True)
       assert result.returncode == 2, "Should block bad pattern"

   if __name__ == "__main__":
       test_guard_blocks_pattern()
       print("All tests passed!")
   ```

## Maintenance Schedules

### Weekly
- Review test coverage report
- Check for new guards without tests
- Verify all tests still pass

### After Major Changes
- Update test documentation
- Review test patterns for new requirements
- Validate backup/restore procedures

### Monthly
- Review test performance
- Clean up obsolete test files
- Update test patterns based on new threats

## Common Maintenance Issues

### Stdin Handling Breakage
**Symptoms**: Tests hang or fail with "No input data provided"
**Fix**:
1. Check Python main.py stdin handling
2. Verify shell wrappers pass stdin correctly
3. Test both pipe and heredoc input methods

### Test Skipping/Bypassing
**Symptoms**: Guards detect test bypass patterns
**Fix**:
1. Never use `@pytest.mark.skip`
2. Never use `stages: [manual]`
3. Never use `-k "not slow"`
4. Fix the underlying issue, don't skip tests

### Installation Test Failures
**Symptoms**: Installation verification fails
**Fix**:
1. Check file permissions (755 for directories, 644 for files)
2. Verify JSON syntax in settings files
3. Check Python import paths
4. Verify backup/restore functionality

## Testing Anti-Patterns (FORBIDDEN)

### ❌ Never Do This:
- Skip hook tests with command line flags
- Mock out safety-critical functionality
- Test only the "happy path"
- Assume installation works without testing
- Bypass stdin handling tests
- Create tests that always pass

### ✅ Always Do This:
- Test both success AND failure cases
- Test stdin handling with multiple methods
- Test installation and uninstallation
- Test override mechanisms work
- Test guard integration end-to-end
- Add test for every new hook/guard

## Error Recovery

### If Hook Tests Break Production:
1. **STOP all development immediately**
2. Identify the broken test case
3. Create failing test case first
4. Fix the underlying issue
5. Verify fix with test
6. Document the failure in this guide

### If Installation Tests Fail:
1. **DO NOT bypass installation tests**
2. Create backup of current state
3. Fix installation process
4. Verify with fresh environment
5. Test both install and uninstall

## Integration with CI/CD

Hook tests are integrated into:
- `run_tests.sh` - Full test suite runner
- Pre-commit hooks - Prevents broken commits
- Protection guards - Self-protecting test system

**NEVER remove hook tests from CI/CD pipeline.**

## Documentation Requirements

When adding new tests:
1. Update this maintenance guide
2. Update `HOOK_TEST_REQUIREMENTS.md`
3. Add comments explaining test purpose
4. Document expected failure modes
5. Update hook documentation with test info

## Historical Context

**Why Hook Tests Are Critical:**
- Hook stdin handling was broken due to missing tests
- Installation failures went undetected
- Guards were bypassed without detection
- Real production harm was caused

**These tests prevent repetition of documented failures.**

## Emergency Procedures

### If All Hook Tests Fail:
1. Check Python virtual environment
2. Verify run_tests.sh syntax
3. Check file permissions on test scripts
4. Validate JSON syntax in settings
5. Contact system administrator if needed

### If Only Specific Tests Fail:
1. Run the failing test in isolation
2. Check for environment dependencies
3. Verify hook installation state
4. Check for missing files or permissions
5. Fix root cause, never bypass test

---

**Remember**: Hook tests are safety equipment. When they fail, they've found a real problem that needs fixing.
