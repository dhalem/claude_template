# CLAUDE.md - AI Assistant Guidelines

## 🚨 RULE #0: FOLLOW ALL RULES! CHECK THIS FILE BEFORE ACTING!

**MANDATORY FIRST ACTION FOR EVERY REQUEST:**
1. Read this file COMPLETELY before responding
2. **READ ALL LINKED POSTMORTEMS** - Every postmortem referenced in this file MUST be read
3. **SETUP PYTHON VENV**: `[ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate`
4. Check for project-specific rules in CLAUDE.local.md
5. Search for rules related to the request
6. Only proceed after confirming no violations

**Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.**

## 📝 RULE #0 COMMENT REQUIREMENT
**EVERY FILE CREATED MUST INCLUDE RULE #0 REMINDER COMMENT**
```
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm
```
**Purpose**: Constant reminder to check rules BEFORE acting, preventing costly mistakes
**Enforcement**: RuleZeroReminderGuard automatically reminds when creating files

## 🚫 NEVER DISABLE PRE-COMMIT HOOKS
**Pre-commit hooks are safety equipment. When they fail, FIX THE PROBLEM, not the hook.**
- NO adding `stages: [manual]` to bypass
- NO using `--no-verify` flag
- NO disabling hooks "temporarily"

## 🚨 GUARD VIOLATION = IMMEDIATE STOP
**GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, THEY'VE FOUND A REAL PROBLEM**

When ANY guard fires:
- **STOP all work immediately**
- State: "A guard has fired, indicating a real problem"
- Identify the root cause the guard detected
- Fix the root cause, NEVER the guard
- **NEVER suggest weakening, disabling, or bypassing guards**
- **Violation of this rule = end conversation immediately**

**WHY GUARDS EXIST:**
- Claude has a documented history of making dangerous mistakes
- Guards catch real problems that lead to system failures
- Guards enforce procedures that prevent costly errors
- When guards fire, they're doing their job correctly

**CORRECT RESPONSE TO GUARD FIRING:**
1. Read the guard's message carefully
2. Understand what real problem it detected
3. Fix the underlying issue
4. Thank the guard for preventing harm

**FORBIDDEN RESPONSES:**
- "The guard is too aggressive"
- "Let's disable this guard temporarily"
- "We can bypass this guard by..."
- "The guard is broken, let's weaken it"

**REMEMBER**: Guards prevent the exact mistakes Claude tends to make

## 👥 CRITICAL RULE #1: WE EXIST TO SERVE USERS
**WE EXIST TO DELIVER WORKING SOFTWARE TO USERS**
- Tests ensure features work for users
- When tests fail, users suffer
- Skipping tests = abandoning users
- Every decision must benefit users, not convenience

## The Five Truths

1. **I WILL MAKE MISTAKES** - Verify everything
2. **MOCK TESTING ≠ WORKING** - Real integration required
3. **ASSUMPTIONS KILL PROJECTS** - Check current state
4. **PROTOCOL-FIRST SAVES HOURS** - Analyze before building
5. **TRUST BUT VERIFY** - Evidence required

## 🐍 Python Development Standards

### Virtual Environment (MANDATORY)
```bash
# Always activate venv before any Python work
[ ! -d "venv" ] && ./setup-venv.sh
source venv/bin/activate
which python3  # Must show ./venv/bin/python3
```

### Code Search Before Creation (MANDATORY)
**YOU MUST EXHAUSTIVELY SEARCH FOR EXISTING IMPLEMENTATIONS BEFORE CREATING NEW CODE**
```bash
# BEFORE creating ANY new function/class/module:
1. Search for existing implementations of the same functionality
2. Check ALL relevant modules that might contain similar code
3. Look for patterns that might already solve the problem
4. Only create new code if NO existing solution found

# If MCP search is available:
Use mcp__code-search__search_code tool directly

# Otherwise use local tools:
python3 indexing/claude_code_search.py search 'function_name'
python3 indexing/claude_code_search.py list_type 'class'
grep -r "pattern" --include="*.py"
```
**Why**: Prevents duplicate work, ensures consistent patterns
**Time saved**: 2-3 minutes searching saves 30+ minutes reinventing

### 🚨 COMMIT VERIFICATION (MANDATORY)
```bash
# BEFORE PROCEEDING AFTER ANY COMMIT:
git status                    # Ensure clean working directory
git log --oneline -1         # Verify commit went through
git show --name-only HEAD    # Confirm files actually committed

# IF COMMIT FAILED:
# 1. Fix the underlying issue causing failure
# 2. Do NOT use --no-verify without explicit permission
# 3. Address test failures or pre-commit hook issues
```
**Why**: Multiple incidents caused by assuming commits succeeded when they failed.
**YOU MUST CHECK THAT COMMIT WENT THROUGH BEFORE PROCEEDING!**

### 🚨 TEST BEFORE COMMIT RULE (MANDATORY)
**BEFORE EVERY COMMIT:**
1. Run tests FIRST: `./run_tests.sh` or `pytest`
2. ONLY commit if tests pass
3. If tests fail, fix immediately - do NOT skip or defer
**This is basic software engineering.**

### 🧪 WHEN TESTS FAIL OR HANG (MANDATORY DEBUGGING)
**When pre-commit hooks fail/timeout, NEVER assume it's a "timeout issue":**
1. **YOU PROBABLY BROKE SOMETHING** - Tests don't randomly fail
2. **TIMEOUTS = HANGING TESTS** - It's not because the suite is "large", a test is stuck
3. **Check for import errors first** - `grep -r "from module.name" .`
4. **Run specific test that's failing** - `./venv/bin/python -m pytest path/to/test.py -v`
5. **Common breaks when moving files:**
   - Tests importing moved/deleted modules
   - Hardcoded paths that no longer exist
   - DNS lookups on nonexistent hosts (use localhost:1 instead)
   - Missing dependencies after cleanup
6. **The hook is your friend** - It caught a real break, be grateful

### 🚨 READ THE ACTUAL ERROR MESSAGES (MANDATORY)
**THE MOST COMMON MISTAKE: IGNORING ACTUAL ERROR MESSAGES**

**WHEN COMMITS FAIL:**
1. **READ EVERY ERROR MESSAGE** - Don't just look at test results
2. **PRE-COMMIT HOOKS CAN FAIL** - Even if tests pass, other checks may fail
3. **LOOK FOR SPECIFIC FAILURES:**
   - `Check for merge conflict markers` - Files with `====` patterns
   - `Check for empty files` - Empty files cause failures
   - `yamllint`, `flake8`, `shellcheck` - Code quality issues
   - Any hook showing `Failed` status
4. **FIX ALL FAILURES SYSTEMATICALLY** - Don't skip any errors
5. **NEVER ASSUME SUCCESS** - Verify with git status/log after every commit

## 📋 Development Workflow

1. **Activate virtual environment**
2. **Read CLAUDE.md and project rules**
3. **Search for existing implementations**
4. **Write tests first (TDD)**
5. **Implement feature**
6. **Run tests**
7. **Run pre-commit checks**
8. **Verify commit success**

## 🚫 Absolute Prohibitions

- **NO MOCKS** without written permission
- **NO config.py changes** without permission
- **NO pre-commit bypassing** without permission
- **NO network config changes** without permission
- **NO HOOK INSTALLATION** without following safety protocol
  - ✅ SAFE: `./hooks/install-hooks-python-only.sh` (only updates python/ directory)
  - ❌ DANGEROUS: `./hooks/install-hooks.sh` (can destroy Claude installation)
- **NO NEW SCRIPTS** when existing ones can be reused - clean up after yourself
- **NO PRODUCTION CHANGES** without explicit permission
- **NO ECHO TESTS** - Always use proper test suites
- **NO CREATING BRANCHES** - Work on main/master unless explicitly told otherwise

## 🔧 INSTALLATION DISCIPLINE (VIOLATION = SYSTEM FAILURE)
**NEVER install without comprehensive testing**

**REQUIRED before ANY hook installation**:
1. All unit tests pass
2. Integration tests pass
3. Installation dry-run succeeds
4. Rollback plan prepared
5. Single incremental change only

**INSTALLATION MUST FAIL FAST on any error**

## Project-Specific Rules

See `CLAUDE.local.md` for project-specific guidelines.

## Hook System Safety

This template includes a comprehensive hook system that:
- Prevents dangerous operations (git --no-verify, docker restart)
- Enforces best practices (venv usage, code search)
- Detects assumption-based language
- Blocks false success claims
- Requires Rule #0 comments in new files

To install hooks safely:
```bash
cd hooks
./install-hooks-python-only.sh  # SAFE - only updates Python directory
```

## Override System

If a hook blocks a legitimate operation:
1. The hook will show an override message
2. Request an override code from the human operator
3. Use: `HOOK_OVERRIDE_CODE=<code> <your command>`

See `hooks/OVERRIDE_SYSTEM.md` for details.

## 🔧 MCP Server Installation and Testing

This project includes two MCP (Model Context Protocol) servers for Claude Code integration:

### Installation
```bash
# Install MCP servers to central location
./install-mcp-servers.sh
```

This installs:
- **code-search**: Search code symbols and content across workspaces
- **code-review**: AI-powered code review using Gemini

### Testing MCP Server Connection
```bash
# Test if MCP servers are connecting properly
claude --debug -p 'hello world'
```

**Expected output in debug logs:**
- ✅ `MCP server "code-search": Connected successfully`
- ✅ `MCP server "code-review": Connected successfully`

**Common connection issues:**
- ❌ `Connection closed` - Server startup failure
- ❌ `MCP error -32000` - Protocol communication issue

### Manual Server Testing
```bash
# Test individual server startup (for debugging)
/home/dhalem/.claude/mcp/central/venv/bin/python \
  /home/dhalem/.claude/mcp/central/code-search/server.py

# Server should log: "Code Search MCP Server starting"
# Press Ctrl+C to stop
```

### Configuration
Servers are automatically configured in `~/.config/claude/claude_desktop_config.json`:
- Uses central Python virtual environment
- Requires `GEMINI_API_KEY` environment variable for code-review
- Logs to `~/.claude/mcp/central/{server}/logs/`

### Troubleshooting
1. **Check server logs**: `~/.claude/mcp/central/code-*/logs/server_*.log`
2. **Verify installation**: Run `./install-mcp-servers.sh` again
3. **Test connection**: Use `claude --debug` command above
4. **Check permissions**: Ensure central directory is accessible

---

Created from Spotidal production best practices. These rules prevent real harm.
