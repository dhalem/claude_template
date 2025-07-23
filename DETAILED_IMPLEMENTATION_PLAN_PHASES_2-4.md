# Detailed Implementation Plan: Phases 2-4
# Hooks Directory Quality & Architecture Improvements

**Generated:** 2025-01-21
**Scope:** Post-security fixes implementation
**Timeline:** 3 weeks total

---

## Phase 2: Path Portability & Environment Independence
**Duration:** 3 days
**Goal:** Eliminate hardcoded paths and make system portable across users/environments

### Phase 2A: Shell Script Path Standardization
**Duration:** 1.5 days
**Priority:** High - Foundation for all other work

#### 2A.1: Establish Path Resolution Standards
**Timeline:** 4 hours
**Files affected:** All shell scripts

**Tasks:**
1. **Create standard path resolution pattern**
   ```bash
   # Standard header for all shell scripts:
   #!/bin/bash
   set -euo pipefail

   # Path resolution (add to every shell script)
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"  # Adjust depth as needed
   HOOKS_DIR="$SCRIPT_DIR"
   CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
   ```

2. **Update core wrapper scripts**
   - `adaptive-guard.sh`
   - `lint-guard.sh`
   - `parse_claude_input.py` (shebang path resolution)

3. **Test path resolution in different environments**
   ```bash
   # Test script for validation
   ./test-path-resolution.sh
   ```

**Deliverables:**
- [ ] Standard path header template
- [ ] Updated core wrapper scripts
- [ ] Path resolution test script

#### 2A.2: Replace Hardcoded User Paths
**Timeline:** 8 hours
**Files affected:** 15+ shell scripts

**Tasks:**
1. **Audit and catalog all hardcoded paths**
   ```bash
   # Find all hardcoded paths
   grep -r "/home/dhalem" hooks/ > hardcoded_paths_audit.txt
   grep -r "~/.claude" hooks/ >> hardcoded_paths_audit.txt
   ```

2. **Replace paths systematically by category:**

   **Category 1: Claude Home Directory**
   ```bash
   # OLD: /home/dhalem/.claude/
   # NEW: "$CLAUDE_HOME/"

   # Files to update:
   - test_debug.sh
   - adaptive-guard.sh
   - comprehensive-guard.sh
   - claude-output-guard.sh
   ```

   **Category 2: Project Root Paths**
   ```bash
   # OLD: /home/dhalem/github/claude_template/
   # NEW: "$PROJECT_ROOT/"

   # Files to update:
   - test-hooks.sh
   - test-claude-hooks.sh
   - python wrapper scripts
   ```

   **Category 3: Relative Path References**
   ```bash
   # OLD: ../python/main.py
   # NEW: "$HOOKS_DIR/python/main.py"
   ```

3. **Update each file with proper path variables**

**Deliverables:**
- [ ] Hardcoded paths audit report
- [ ] 15+ shell scripts updated with dynamic paths
- [ ] Path variable consistency across all scripts

### Phase 2B: Python Code Path Abstraction
**Duration:** 1.5 days
**Priority:** High - Affects guard behavior

#### 2B.1: Abstract Hardcoded Paths in Guard Messages
**Timeline:** 6 hours
**Files affected:** `python/guards/*.py`

**Tasks:**
1. **Update awareness_guards.py**
   ```python
   # File: python/guards/awareness_guards.py
   import os

   class PythonVenvGuard(BaseGuard):
       def get_message(self) -> str:
           # Dynamic path resolution
           project_root = os.environ.get("PROJECT_ROOT") or os.getcwd()

           return f"""
   🐍 PYTHON VENV ENFORCEMENT: Use venv Python binary!

   1. ACTIVATE VENV FIRST (MANDATORY):
      cd {project_root}
      [ ! -d "venv" ] && ./setup-venv.sh
      source venv/bin/activate
      which python3  # Should show: {project_root}/venv/bin/python3
   """
   ```

2. **Update DirectoryAwarenessGuard paths**
   ```python
   def get_message(self) -> str:
       current_dir = os.getcwd()
       project_name = os.path.basename(current_dir)

       return f"""
   🧭 DIRECTORY AWARENESS: Know where you are!

   Current directory: {current_dir}
   Project: {project_name}
   """
   ```

3. **Create environment configuration system**
   ```python
   # File: python/config.py
   import os
   from pathlib import Path

   class Config:
       @property
       def project_root(self) -> Path:
           return Path(os.environ.get("PROJECT_ROOT", os.getcwd()))

       @property
       def claude_home(self) -> Path:
           return Path(os.environ.get("CLAUDE_HOME", "~/.claude")).expanduser()
   ```

**Deliverables:**
- [ ] Updated awareness_guards.py with dynamic paths
- [ ] New config.py for centralized path management
- [ ] All guard messages use configurable paths

#### 2B.2: Environment Variable Integration
**Timeline:** 6 hours
**Files affected:** `python/main.py`, wrapper scripts

**Tasks:**
1. **Create environment detection in main.py**
   ```python
   # File: python/main.py
   import os
   from pathlib import Path

   def setup_environment():
       """Setup environment variables for portable execution"""
       # Auto-detect project root if not set
       if not os.environ.get("PROJECT_ROOT"):
           current_file = Path(__file__).parent
           project_root = current_file.parent.parent  # hooks/python -> hooks -> project
           os.environ["PROJECT_ROOT"] = str(project_root)

       # Set Claude home if not specified
       if not os.environ.get("CLAUDE_HOME"):
           os.environ["CLAUDE_HOME"] = str(Path.home() / ".claude")

   def main():
       setup_environment()
       # ... rest of main function
   ```

2. **Update shell wrappers to pass environment**
   ```bash
   # In adaptive-guard.sh
   export PROJECT_ROOT="$PROJECT_ROOT"
   export CLAUDE_HOME="$CLAUDE_HOME"
   export HOOKS_DIR="$HOOKS_DIR"

   # Pass to Python
   "$HOOKS_DIR/python/main.py" "$@"
   ```

3. **Create environment validation**
   ```python
   def validate_environment():
       """Ensure all required paths exist and are accessible"""
       required_paths = [
           os.environ.get("PROJECT_ROOT"),
           os.environ.get("CLAUDE_HOME"),
           os.environ.get("HOOKS_DIR")
       ]

       for path in required_paths:
           if not path or not Path(path).exists():
               raise EnvironmentError(f"Required path not found: {path}")
   ```

**Deliverables:**
- [ ] Environment setup in main.py
- [ ] Updated shell wrappers with environment passing
- [ ] Environment validation system

---

## Phase 3: Architecture Cleanup & Consolidation
**Duration:** 1 week
**Goal:** Eliminate redundancy and standardize on unified architecture

### Phase 3A: Script Consolidation & Standardization
**Duration:** 3 days
**Priority:** High - Reduces maintenance burden

#### 3A.1: Archive Redundant Guard Scripts
**Timeline:** 1 day
**Files affected:** Multiple top-level guard scripts

**Tasks:**
1. **Create archive structure**
   ```bash
   mkdir -p hooks/archive/legacy-guards
   mkdir -p hooks/archive/legacy-tests
   mkdir -p hooks/archive/documentation
   ```

2. **Identify scripts to archive**
   ```bash
   # KEEP (Active - Python wrappers):
   - adaptive-guard.sh
   - lint-guard.sh
   - parse_claude_input.py

   # ARCHIVE (Legacy shell-only):
   - comprehensive-guard.sh
   - claude-output-guard.sh
   - test-script-integrity-guard.sh (if not used by pre-commit)
   - precommit-protection-guard.sh (if not used by pre-commit)
   ```

3. **Move files systematically**
   ```bash
   # Archive with documentation
   mv comprehensive-guard.sh hooks/archive/legacy-guards/
   echo "Moved to archive: $(date)" > hooks/archive/legacy-guards/comprehensive-guard.sh.ARCHIVED

   # Update any references to archived scripts
   grep -r "comprehensive-guard.sh" hooks/ | tee archive-references.txt
   ```

4. **Update pre-commit hooks if needed**
   ```yaml
   # .pre-commit-config.yaml
   # Update any references to archived scripts
   ```

**Deliverables:**
- [ ] Archive directory structure created
- [ ] Legacy scripts moved to archive with documentation
- [ ] References to archived scripts updated
- [ ] Archive migration log

#### 3A.2: Standardize JSON Parsing
**Timeline:** 1 day
**Files affected:** Remaining shell scripts using `jq`

**Tasks:**
1. **Audit remaining jq usage**
   ```bash
   grep -r "jq" hooks/ --exclude-dir=archive > jq_usage_audit.txt
   ```

2. **Convert scripts to use centralized parser**
   ```bash
   # For each script using jq:

   # OLD:
   command=$(echo "$input" | jq -r '.tool_input.command // empty')

   # NEW:
   command=$(echo "$input" | "$SCRIPT_DIR/parse_claude_input.py" --field "tool_input.command")
   ```

3. **Update scripts systematically:**
   - `claude-output-guard.sh` (if not archived)
   - Any remaining shell guards
   - Test scripts using jq

4. **Remove jq dependencies**
   ```bash
   # Update any installation docs that mention jq
   # Remove jq from requirements lists
   ```

**Deliverables:**
- [ ] JQ usage audit completed
- [ ] All scripts converted to centralized parser
- [ ] JQ dependencies removed from documentation

#### 3A.3: Test Runner Consolidation
**Timeline:** 1 day
**Files affected:** Multiple test runners

**Tasks:**
1. **Designate run_tests.sh as single entry point**
   ```bash
   # File: run_tests.sh
   # Ensure it calls ALL test categories:

   # 1. Shell script tests
   test_shell_guards() {
       # Hook pre-install tests
       ./hooks/tests/test_hooks_pre_install.sh
   }

   # 2. Python tests
   test_python_guards() {
       cd hooks/python
       ../../venv/bin/python -m pytest tests/ -v
   }

   # 3. Integration tests
   test_integration() {
       # MCP tests, etc.
   }
   ```

2. **Archive redundant test runners**
   ```bash
   # ARCHIVE:
   mv test-hooks.sh hooks/archive/legacy-tests/
   mv test-claude-hooks.sh hooks/archive/legacy-tests/
   mv hooks/python/tests/run_tests.py hooks/archive/legacy-tests/
   ```

3. **Update all documentation to reference single runner**
   ```markdown
   # Update HOOKS.md, README.md, etc.

   ## Running Tests

   ```bash
   # Run all tests (ONLY way to run tests)
   ./run_tests.sh
   ```
   ```

**Deliverables:**
- [ ] run_tests.sh enhanced as single entry point
- [ ] Redundant test runners archived
- [ ] Documentation updated to reference single runner

### Phase 3B: Documentation Synchronization
**Duration:** 4 days
**Priority:** Medium - Critical for maintainability

#### 3B.1: Guard Registry Documentation Audit
**Timeline:** 1 day
**Files affected:** `HOOKS.md`, `python/main.py`

**Tasks:**
1. **Create comprehensive audit**
   ```python
   # Script: audit_guard_registry.py
   import ast
   import re

   def extract_registered_guards(main_py_path):
       """Extract guards from create_registry() function"""
       # Parse main.py and extract registry.register() calls
       pass

   def extract_documented_guards(hooks_md_path):
       """Extract guards listed in HOOKS.md"""
       # Parse markdown and extract guard names
       pass

   def compare_and_report():
       """Generate discrepancy report"""
       pass
   ```

2. **Generate detailed discrepancy report**
   ```markdown
   # Guard Registry Audit Report

   ## Implemented & Registered (✅)
   - GitNoVerifyGuard
   - DockerRestartGuard
   [... list all active guards]

   ## Documented but NOT Registered (❌)
   - AssumptionDetectionGuard
   - FalseSuccessGuard

   ## Registered but NOT Documented (⚠️)
   - [Any guards in code but not in docs]

   ## Implemented but Commented Out (🚧)
   - TestSuiteEnforcementGuard (line 89 in main.py)
   ```

3. **Create resolution plan for each discrepancy**

**Deliverables:**
- [ ] Guard registry audit script
- [ ] Detailed discrepancy report
- [ ] Resolution plan for each guard

#### 3B.2: Implement Documentation Fixes
**Timeline:** 2 days
**Files affected:** `HOOKS.md`, `python/main.py`, guard files

**Tasks:**
1. **Add status indicators to HOOKS.md**
   ```markdown
   # File: HOOKS.md

   ## Current Guards Reference

   ### ✅ Active Guards (Implemented & Registered)
   #### Git Safety Guards
   - **GitNoVerifyGuard** - Prevents `git --no-verify` bypass
     - Status: ✅ Active
     - File: `python/guards/git_guards.py`
     - Tests: `python/tests/test_git_guards.py`

   ### 🚧 Planned Guards (Documented but not implemented)
   - **AssumptionDetectionGuard** - Detects assumption-based language
     - Status: 🚧 Planned
     - Implementation: TBD

   ### ⚠️ Disabled Guards (Implemented but not registered)
   - **TestSuiteEnforcementGuard** - Enforces running full test suite
     - Status: ⚠️ Disabled (debugging needed)
     - File: `python/guards/awareness_guards.py:65`
     - Issue: Constructor conflict with pytest
   ```

2. **Sync python/main.py with decisions**
   ```python
   def create_registry() -> GuardRegistry:
       registry = GuardRegistry()

       # Git Guards - ✅ All active
       registry.register(GitNoVerifyGuard())
       registry.register(GitForcePushGuard())
       # ... other active guards

       # Disabled guards with reasoning:
       # registry.register(TestSuiteEnforcementGuard())  # DISABLED: pytest conflict

       # Planned guards (not yet implemented):
       # registry.register(AssumptionDetectionGuard())   # PLANNED: TBD
       # registry.register(FalseSuccessGuard())          # PLANNED: TBD

       return registry
   ```

3. **Update guard file docstrings**
   ```python
   class TestSuiteEnforcementGuard(BaseGuard):
       """
       DISABLED: Guard that enforces running full test suite

       Status: ⚠️ Disabled due to pytest constructor conflict
       Issue: https://github.com/project/issues/123

       When enabled, prevents claims of test completion without
       actually running the full test suite.
       """
   ```

**Deliverables:**
- [ ] HOOKS.md updated with status indicators
- [ ] python/main.py synchronized with documentation
- [ ] Guard docstrings updated with status information

#### 3B.3: Create Living Documentation System
**Timeline:** 1 day
**Files affected:** New documentation automation

**Tasks:**
1. **Create automated sync checking**
   ```python
   # File: scripts/check_doc_sync.py
   def main():
       """Daily/CI check that docs match implementation"""
       discrepancies = audit_guard_registry()
       if discrepancies:
           print("❌ Documentation out of sync!")
           print(discrepancies)
           sys.exit(1)
       print("✅ Documentation synchronized")
   ```

2. **Add to pre-commit hooks**
   ```yaml
   # .pre-commit-config.yaml
   - repo: local
     hooks:
     - id: check-documentation-sync
       name: Check guard documentation sync
       entry: python scripts/check_doc_sync.py
       language: python
       files: ^(python/main\.py|HOOKS\.md)$
   ```

3. **Create documentation update templates**
   ```markdown
   # File: .github/GUARD_TEMPLATE.md

   ## Adding a New Guard

   1. Implement guard in `python/guards/`
   2. Add tests in `python/tests/`
   3. Register in `python/main.py`
   4. Document in `HOOKS.md` with ✅ status
   5. Run `python scripts/check_doc_sync.py`
   ```

**Deliverables:**
- [ ] Automated documentation sync checker
- [ ] Pre-commit hook for documentation validation
- [ ] Documentation templates for contributors

---

## Phase 4: Code Quality & Final Validation
**Duration:** 2 weeks
**Goal:** Polish code quality and ensure everything works perfectly

### Phase 4A: Code Quality Improvements
**Duration:** 1 week
**Priority:** Medium - Improves maintainability

#### 4A.1: Remove Eval Usage & Improve Shell Safety
**Timeline:** 2 days
**Files affected:** Shell test scripts

**Tasks:**
1. **Audit and fix eval usage**
   ```bash
   # Find all eval usage
   grep -r "eval" hooks/ --exclude-dir=archive > eval_usage.txt
   ```

2. **Refactor test-hooks.sh (if not archived)**
   ```bash
   # OLD:
   run_test() {
       local test_name="$1"
       local test_command="$2"
       eval "$test_command"
   }

   # NEW:
   run_test() {
       local test_name="$1"
       local command="$2"
       shift 2
       # Direct execution instead of eval
       "$command" "$@"
   }
   ```

3. **Enhance shell script safety**
   ```bash
   # Add to all shell scripts:
   set -euo pipefail

   # Add trap for cleanup:
   cleanup() {
       local exit_code=$?
       # Cleanup temporary files
       exit $exit_code
   }
   trap cleanup EXIT
   ```

**Deliverables:**
- [ ] Eval usage audit and removal
- [ ] Enhanced shell script safety patterns
- [ ] Improved error handling

#### 4A.2: Python Code Quality Improvements
**Timeline:** 2 days
**Files affected:** Python guard implementations

**Tasks:**
1. **Standardize Python imports and structure**
   ```python
   # Standard import order for all guard files:
   # 1. Standard library
   import os
   import re
   from pathlib import Path
   from typing import Optional

   # 2. Local imports
   from .base_guard import BaseGuard, GuardContext, GuardResult
   ```

2. **Add type hints throughout**
   ```python
   class GitNoVerifyGuard(BaseGuard):
       def should_trigger(self, context: GuardContext) -> bool:
           """Check if guard should trigger with proper typing"""
           pass

       def get_message(self) -> str:
           """Get guard message with proper return type"""
           pass
   ```

3. **Improve error handling**
   ```python
   class BaseGuard:
       def check(self, context: GuardContext) -> GuardResult:
           try:
               should_trigger = self.should_trigger(context)
               if should_trigger:
                   message = self.get_message()
                   return GuardResult.blocking(message)
               return GuardResult.allowing()
           except Exception as e:
               # Log error and fail safely
               return GuardResult.blocking(f"Guard error: {str(e)}")
   ```

**Deliverables:**
- [ ] Standardized Python code structure
- [ ] Complete type hint coverage
- [ ] Improved error handling throughout

#### 4A.3: Environment Loading Consolidation
**Timeline:** 2 days
**Files affected:** Shell wrappers, Python main

**Tasks:**
1. **Create centralized environment loading**
   ```python
   # File: python/environment.py
   import os
   from pathlib import Path
   from typing import Optional

   class Environment:
       def __init__(self):
           self.load_environment_files()
           self.setup_paths()

       def load_environment_files(self):
           """Load .env files in priority order"""
           env_files = [
               Path.home() / ".claude" / ".env",  # Global
               Path.cwd() / ".env",               # Project
               Path.cwd() / ".env.local"          # Local overrides
           ]

           for env_file in env_files:
               if env_file.exists():
                   self.load_env_file(env_file)
   ```

2. **Update shell wrappers to use consistent loading**
   ```bash
   # Standard pattern for all shell wrappers:
   load_environment() {
       # Load Claude environment
       if [[ -f "$CLAUDE_HOME/.env" ]]; then
           set -a  # Mark variables for export
           source "$CLAUDE_HOME/.env"
           set +a  # Stop auto-export
       fi

       # Load project environment
       if [[ -f "$PROJECT_ROOT/.env" ]]; then
           set -a
           source "$PROJECT_ROOT/.env"
           set +a
       fi
   }
   ```

3. **Remove redundant environment logic**
   ```bash
   # Remove custom .env loading from:
   - adaptive-guard.sh
   - lint-guard.sh
   # Replace with centralized load_environment()
   ```

**Deliverables:**
- [ ] Centralized environment loading system
- [ ] Consistent .env handling across all scripts
- [ ] Removed redundant environment code

### Phase 4B: Comprehensive Testing & Validation
**Duration:** 1 week
**Priority:** High - Ensures everything works

#### 4B.1: Create Fresh Environment Testing
**Timeline:** 2 days
**Files affected:** New test infrastructure

**Tasks:**
1. **Create clean environment test script**
   ```bash
   # File: test_fresh_environment.sh
   #!/bin/bash

   # Test in completely fresh environment
   create_test_user() {
       # Create temporary user for testing
       sudo useradd -m -s /bin/bash testuser_$(date +%s)
   }

   test_installation() {
       # Test complete installation as different user
       sudo -u "$test_user" bash -c "
           cd /tmp
           git clone /path/to/repo test_repo
           cd test_repo
           ./safe_install.sh
           ./run_tests.sh
       "
   }
   ```

2. **Test different operating systems**
   ```bash
   # Create Docker test environments
   # File: docker/test-environments/
   - ubuntu-20.04/
   - ubuntu-22.04/
   - centos-8/
   - alpine/
   ```

3. **Automated portability testing**
   ```yaml
   # File: .github/workflows/portability-test.yml
   name: Portability Test
   on: [push, pull_request]
   jobs:
     test-environments:
       strategy:
         matrix:
           os: [ubuntu-20.04, ubuntu-22.04, centos-8]
           user: [testuser1, testuser2]
   ```

**Deliverables:**
- [ ] Fresh environment test script
- [ ] Multi-OS Docker test environments
- [ ] Automated portability testing

#### 4B.2: Performance & Load Testing
**Timeline:** 1 day
**Files affected:** Test infrastructure

**Tasks:**
1. **Create performance benchmarks**
   ```python
   # File: tests/test_performance.py
   import time
   import pytest

   def test_guard_performance():
       """Ensure guards respond within reasonable time"""
       start = time.time()
       # Run guard check
       duration = time.time() - start
       assert duration < 0.1  # Max 100ms per guard
   ```

2. **Test with large inputs**
   ```python
   def test_large_input_handling():
       """Test guards with very large command inputs"""
       large_command = "echo " + "x" * 100000
       context = GuardContext(tool="Bash", command=large_command)
       # Should not hang or crash
   ```

3. **Memory usage testing**
   ```python
   import psutil

   def test_memory_usage():
       """Ensure guards don't leak memory"""
       process = psutil.Process()
       initial_memory = process.memory_info().rss
       # Run many guard checks
       final_memory = process.memory_info().rss
       assert final_memory - initial_memory < 10 * 1024 * 1024  # Max 10MB growth
   ```

**Deliverables:**
- [ ] Performance benchmark suite
- [ ] Large input handling tests
- [ ] Memory usage validation

#### 4B.3: Final Integration Testing
**Timeline:** 4 days
**Files affected:** All systems

**Tasks:**
1. **End-to-end workflow testing**
   ```bash
   # Test complete workflows:

   # 1. Fresh installation
   test_fresh_install() {
       # Clean environment -> install -> verify
   }

   # 2. Guard activation
   test_guard_activation() {
       # Trigger each guard -> verify correct behavior
   }

   # 3. Override system
   test_override_system() {
       # Test TOTP overrides work correctly
   }

   # 4. Error scenarios
   test_error_handling() {
       # Missing files, permissions, etc.
   }
   ```

2. **Cross-platform validation**
   ```bash
   # Test on all supported platforms:
   - Linux (Ubuntu, CentOS)
   - macOS (if applicable)
   - Different shell environments (bash, zsh)
   ```

3. **Regression testing**
   ```bash
   # Ensure all original functionality still works:
   - All 405+ existing tests pass
   - No performance regressions
   - All documented features work
   ```

4. **Documentation validation**
   ```bash
   # Test that all documentation examples work:
   - Installation instructions
   - Usage examples
   - Troubleshooting guides
   ```

**Deliverables:**
- [ ] Complete end-to-end test suite
- [ ] Cross-platform validation
- [ ] Regression test confirmation
- [ ] Documentation accuracy verification

---

## Success Criteria & Validation

### Phase 2 Success Criteria:
- [ ] System works identically for any user (no hardcoded paths)
- [ ] All environment variables properly configurable
- [ ] Installation works in fresh environment
- [ ] All existing tests continue to pass

### Phase 3 Success Criteria:
- [ ] Single authoritative test runner (`run_tests.sh`)
- [ ] All scripts use centralized JSON parsing
- [ ] Documentation exactly matches implementation
- [ ] No redundant or unused code

### Phase 4 Success Criteria:
- [ ] All code quality improvements implemented
- [ ] Performance benchmarks established and passing
- [ ] Complete portability across environments
- [ ] 100% documentation accuracy

### Overall Project Success:
- [ ] **Zero breaking changes** to existing functionality
- [ ] **Improved maintainability** through consolidation
- [ ] **Enhanced portability** for any user/environment
- [ ] **Documentation accuracy** matching implementation
- [ ] **Performance maintained** or improved
- [ ] **All 405+ tests passing** after changes

---

## Risk Mitigation Strategy

### Git Strategy:
```bash
# Create feature branches for each phase
git checkout -b phase-2-path-portability
git checkout -b phase-3-architecture-cleanup
git checkout -b phase-4-quality-improvements

# Merge only after validation
git checkout main
git merge phase-2-path-portability  # Only after success criteria met
```

### Rollback Plan:
- Each subphase can be individually reverted
- Comprehensive test suite validates each change
- Archive system preserves all replaced functionality

### Testing Strategy:
- Run full test suite after each subphase
- Test in fresh environment after Phase 2
- Performance validation after each major change
- Documentation sync validation throughout

**Total Estimated Effort:** 3 weeks
**Critical Dependencies:** Each phase builds on previous phases
**Key Risk:** Ensure no breaking changes to existing guard functionality
