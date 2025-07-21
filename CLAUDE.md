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

## 📋 MANDATORY POSTMORTEMS TO READ
**These postmortems document real failures. READ THEM to avoid repeating these mistakes:**
- **[MCP Test Failure Postmortem](POSTMORTEM_MCP_TEST_FAILURE_20250119.md)** - Critical lesson: ALWAYS run full test suite (`./run_tests.sh`), not just subset
- **[Claude Installation Failure Postmortem](POSTMORTEM_CLAUDE_INSTALLATION_FAILURE_20250120.md)** - Critical lesson: NEVER create multiple install scripts, ALWAYS use safe_install.sh
- **[Fast Mode Violation Postmortem](POSTMORTEM_FAST_MODE_VIOLATION_20250120.md)** - Critical lesson: NEVER implement test shortcuts, fix root cause instead

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

## 🚨 INSTALLATION SAFETY - USE ONLY safe_install.sh
**CRITICAL: ONLY ONE INSTALL SCRIPT SHOULD EXIST**

**THE ONLY INSTALL SCRIPT**: `./safe_install.sh`
- **NEVER create more install scripts**
- **NEVER modify .claude directory without backup**
- **ALWAYS use safe_install.sh for ALL installations**

**WHY THIS RULE EXISTS:**
- Multiple install scripts caused confusion and system damage
- Direct .claude modifications destroyed Claude installations
- Lack of backups made recovery impossible
- Users lost work due to careless installation procedures

**safe_install.sh GUARANTEES:**
1. **MANDATORY BACKUP** of entire .claude directory with timestamp
2. **SAFE INSTALLATION** of hooks (python-only approach)
3. **CENTRAL MCP SERVERS** properly configured
4. **ROLLBACK INSTRUCTIONS** if anything goes wrong
5. **USER CONFIRMATION** before any changes

**FORBIDDEN ACTIONS:**
- Creating new install scripts (install-*.sh)
- Directly modifying ~/.claude without backup
- Using rm -rf on Claude directories
- Installing without user confirmation
- Bypassing safe_install.sh

**ENFORCEMENT:**
- InstallScriptPreventionGuard blocks creation of any install scripts except safe_install.sh
- Pre-commit hook scans for and blocks unauthorized install scripts
- Violations result in immediate blocking with clear error messages

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

### 🚨 MANDATORY COMMIT MONITORING PROTOCOL
**CRITICAL: NEVER assume a commit succeeded without verification**

**REQUIRED ACTIONS for EVERY commit attempt:**

1. **WATCH THE ENTIRE COMMIT PROCESS** - Do not move on until complete
2. **READ ALL OUTPUT** - Understand what's happening, where it fails
3. **IDENTIFY SPECIFIC FAILURE POINT** - Pre-commit hook? Which test? Why?
4. **VERIFY COMPLETION** with `git log --oneline -1`
5. **IF TIMEOUT/HANG**: Investigate the specific hanging component

**COMMON HANGING POINTS:**
- Full test suite in pre-commit (`./run_tests.sh`)
- MCP integration tests (subprocess pipe deadlock)
- Long-running tests without proper timeout handling
- Environment differences between manual and pre-commit execution

**DEBUGGING HANGING COMMITS:**
```bash
# Test the exact pre-commit command manually:
PRE_COMMIT=1 timeout 600 ./run_tests.sh

# If that hangs, isolate the hanging test:
PRE_COMMIT=1 ./run_tests.sh 2>&1 | tee commit_debug.log

# Check what the pre-commit hook is actually running:
cat .pre-commit-config.yaml | grep -A5 "MANDATORY FULL TEST"

# Debug specific test components:
./run_tests.sh  # Run manually first
pytest tests/test_mcp_integration.py -v  # Check MCP tests specifically
```

**NEVER proceed with additional changes until you understand why a commit failed or hung.**

### 🚨 MANDATORY FULL TEST SUITE RULE (ZERO EXCEPTIONS)
**ABSOLUTE REQUIREMENT - NO NEGOTIATIONS, NO SHORTCUTS:**

1. **ALL TESTS MUST RUN EVERY TIME**: `./run_tests.sh` runs EVERY test in the project
2. **NO COMMAND LINE OPTIONS**: Script rejects ANY flags or options - full test suite only
3. **PRE-COMMIT ENFORCEMENT**: Pre-commit hooks run `./run_tests.sh` and BLOCK commits if ANY test fails
4. **ZERO BYPASSING**: Never use `--no-verify`, never disable hooks, never skip tests
5. **ALL TESTS MUST PASS**: Indexing tests, main project tests, MCP integration tests - ALL must pass

**If tests fail: FIX THE TESTS, don't bypass them**
**This rule exists because partial testing has caused production failures**

### 🚨 NO SKIPPING TESTS (MANDATORY)
**WE ARE PATIENT AND CAREFUL, NOT RUSHED AND DANGEROUS**
- **NEVER add @pytest.mark.skip or @pytest.mark.slow to avoid running tests**
- **NEVER use -k "not slow" or similar to exclude tests**
- **NEVER bypass tests with timeouts or workarounds**
- **If tests take time, that's FINE - quality over speed**
- **Tests exist to ensure our software works correctly**
- **Skipping tests = shipping broken software to users**

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

### 🔧 DEBUGGING HANGING TESTS (SPECIFIC PATTERNS)
**When tests hang, debug systematically:**

**Subprocess Hanging Checklist:**
1. **Test command directly**: `command --args` to verify it works
2. **Test without TTY**: `echo "" | command --args` (simulates pre-commit)
3. **Check output size**: `command --args 2>&1 | wc -c` (if >64KB, use temp files)
4. **Environment differences**: Compare `env` between terminal and pre-commit
5. **Pipe buffer issues**: Look for `subprocess.run(capture_output=True)` with verbose commands

**Network/External Service Hanging:**
1. **Check service availability**: `curl -I service-url`
2. **Use short timeouts**: `timeout=30` for external calls
3. **Mock in tests**: Don't rely on external services in test suite
4. **Check rate limits**: API services may throttle requests

**Import/Module Hanging:**
1. **Circular imports**: Check for `import A; import B` where B imports A
2. **Heavy computations**: Look for expensive operations at module level
3. **Network calls in imports**: Some modules make network calls when imported

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

### 🚨 SUBPROCESS IN PRE-COMMIT HOOKS (CRITICAL)
**PRE-COMMIT ENVIRONMENT IS DIFFERENT - ACCOUNT FOR THIS**

**PIPE BUFFER DEADLOCK PREVENTION:**
```python
# ❌ WRONG - Can cause deadlock with verbose output
result = subprocess.run(cmd, capture_output=True, text=True)

# ✅ CORRECT - Use temp files for large output
with tempfile.NamedTemporaryFile(mode='w+', delete=False) as stdout_file, \
     tempfile.NamedTemporaryFile(mode='w+', delete=False) as stderr_file:

    result = subprocess.run(cmd, stdout=stdout_file, stderr=stderr_file, text=True)
    stdout_content = Path(stdout_file.name).read_text()
    stderr_content = Path(stderr_file.name).read_text()
```

**ENVIRONMENT-AWARE VERBOSITY:**
```python
# Reduce output in pre-commit environment
cmd_args = ["program", "args"]
if not os.environ.get('PRE_COMMIT'):
    cmd_args.insert(1, "--debug")  # Only add verbose flags in terminal
```

**WHY THIS MATTERS:**
- Pre-commit runs without TTY, affecting subprocess behavior
- `capture_output=True` uses PIPE which has limited buffer size
- Verbose programs (like `claude --debug`) can overflow pipe buffers
- When buffer fills, subprocess blocks waiting to write, parent blocks waiting to read = DEADLOCK
- Git hooks have different environment variables and restrictions

**DEBUGGING HANGING SUBPROCESS:**
1. Test command directly: `command --debug`
2. Test in non-TTY: `echo "" | command --debug`
3. Check output size: `command --debug 2>&1 | wc -c`
4. If output >64KB, use temp files instead of PIPE

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

**📚 MANDATORY: Read `hooks/HOOKS.md` BEFORE working with hooks!**

This template includes a comprehensive hook system that:
- Prevents dangerous operations (git --no-verify, docker restart)
- Enforces best practices (venv usage, code search)
- Detects assumption-based language
- Blocks false success claims
- Requires Rule #0 comments in new files

**Before modifying, installing, or debugging hooks:**
1. **READ `hooks/HOOKS.md`** - Complete documentation of hook system
2. **UNDERSTAND hook events** - PreToolUse, PostToolUse, etc.
3. **KNOW exit codes** - 0=allow, 2=block, other=error
4. **TEST thoroughly** - Hooks are critical safety infrastructure

To install hooks safely:
```bash
# ALWAYS use safe_install.sh for complete installation
./safe_install.sh  # Backs up .claude before ANY changes

# Or for hooks only:
cd hooks
./install-hooks-python-only.sh  # SAFE - only updates Python directory
```

### Critical Hook Troubleshooting

**VERIFY HOOKS ARE WORKING:**
```bash
# Quick test - this SHOULD be blocked:
echo "test" > ~/.claude/test.txt
# If you see "DIRECT HOOK MODIFICATION BLOCKED", hooks are active!

# Test specific guard:
git commit --no-verify -m "test"
# Should see "SECURITY ALERT: Git --no-verify detected!"
```

**COMMON ISSUES:**
1. **Settings Location**: Must be `~/.claude/settings.json` (NOT userSettings.json)
2. **Invalid Keys**: Remove `_documentation` or other non-standard keys
3. **Debug Mode**: Use `claude --debug -p "test" 2>&1 | grep -i "hook"`
4. **Direct Test**: `echo '{"tool": "Bash", "toolInput": {"command": "git commit --no-verify"}}' | ~/.claude/adaptive-guard.sh`

## Override System

If a hook blocks a legitimate operation:
1. The hook will show an override message
2. Request an override code from the human operator
3. Use: `HOOK_OVERRIDE_CODE=<code> <your command>`

See `hooks/OVERRIDE_SYSTEM.md` for details.

## 🔧 MCP Server Installation and Usage

This project includes two MCP (Model Context Protocol) servers for Claude Code integration from [github.com/dhalem/claude_template](https://github.com/dhalem/claude_template):

1. **code-search**: Search code symbols, content, and files using indexed database
2. **code-review**: AI-powered code review using Google Gemini

### Installation and Setup

**Prerequisites:**
- Python virtual environment activated (`source venv/bin/activate`)
- For code-review: `GEMINI_API_KEY` environment variable set

**Installation:**
```bash
# For Claude Desktop (automatic .mcp.json detection)
./install-mcp-servers.sh

# For Claude Code CLI (requires manual registration)
./install-mcp-central.sh
claude mcp add code-search /home/$USER/.claude/mcp/central/venv/bin/python /home/$USER/.claude/mcp/central/code-search/server.py
claude mcp add code-review /home/$USER/.claude/mcp/central/venv/bin/python /home/$USER/.claude/mcp/central/code-review/server.py
```

### Code Search Server (`code-search`)

**Purpose**: Search through indexed codebase for symbols, content, and files

**Available Tools:**

#### 1. `search_code` - Search for code symbols by name, content, or file path
**Parameters:**
- `query` (required): Search query (supports * and ? wildcards)
- `search_type` (optional): "name" (default), "content", or "file"
- `symbol_type` (optional): "function", "class", "method", or "variable"
- `limit` (optional): Maximum results (default: 50)

**Examples:**
```bash
# Search for functions containing "parse"
search_code query="parse*" search_type="name" symbol_type="function"

# Search file content for "TODO"
search_code query="TODO" search_type="content"

# Find files with "config" in name
search_code query="*config*" search_type="file"
```

#### 2. `list_symbols` - List all symbols of a specific type
**Parameters:**
- `symbol_type` (required): "function", "class", "method", or "variable"
- `limit` (optional): Maximum results (default: 100)

**Examples:**
```bash
# List all classes
list_symbols symbol_type="class"

# List first 20 functions
list_symbols symbol_type="function" limit=20
```

#### 3. `get_search_stats` - Get statistics about the code index database
**Parameters:** None required

**Returns:** Database statistics including total symbols, files, and breakdown by type

**Requirements:**
- Code index database (`.code_index.db`) must exist
- Run `./start-indexer.sh` if database missing
- Server searches for database in: current directory, parent directories (3 levels), home directory, `/app/`

### Code Review Server (`code-review`)

**Purpose**: Perform comprehensive AI-powered code review using Google Gemini

**Available Tools:**

#### 1. `review_code` - Perform comprehensive code review of a directory
**Parameters:**
- `directory` (required): Absolute path to directory to review
- `focus_areas` (optional): Array of specific focus areas (e.g., ["security", "performance"])
- `model` (optional): Gemini model - "gemini-1.5-flash" or "gemini-2.5-pro" (default)
- `max_file_size` (optional): Maximum file size in bytes (default: 1048576)

**Examples:**
```bash
# Basic code review
review_code directory="/path/to/project"

# Security-focused review
review_code directory="/path/to/project" focus_areas=["security", "error_handling"]

# Use different model with larger file limit
review_code directory="/path/to/project" model="gemini-2.5-pro" max_file_size=2097152
```

**Features:**
- Automatic file collection (respects gitignore patterns)
- Supports multiple programming languages (.py, .js, .ts, .go, .rs, etc.)
- Includes project context (CLAUDE.md file if present)
- Usage tracking and cost estimation
- Comprehensive file tree analysis

**Requirements:**
- `GEMINI_API_KEY` environment variable
- Directory must exist and be readable
- Files must be under max_file_size limit

### Testing MCP Server Connection
```bash
# Test if MCP servers are connecting properly
claude --debug -p 'hello world'

# For automated testing or CI environments, use:
claude --debug --dangerously-skip-permissions -p 'hello world'

# Verify servers are registered (CLI only)
claude mcp list
```

**Expected output in debug logs:**
- ✅ `MCP server "code-search": Connected successfully`
- ✅ `MCP server "code-review": Connected successfully`

**Note**: The `--dangerously-skip-permissions` flag bypasses permission checks and should only be used for testing purposes, not in normal usage.

### Troubleshooting MCP Connection Issues

#### Critical Discovery: Claude Code CLI vs Desktop Differences

**IMPORTANT**: Claude Code CLI and Claude Desktop handle MCP servers completely differently:

- **Claude Desktop**: Automatically loads `.mcp.json` from project root
- **Claude Code CLI**: Requires manual server registration using `claude mcp add`
- **Project config (.mcp.json) takes precedence over global config**

If using Claude Code CLI, you MUST first register servers:
```bash
# Check if servers are already configured
claude mcp list

# If not listed, add them from .mcp.json automatically:
cat .mcp.json | jq -r '.mcpServers | to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"' | bash

# Or add them manually:
claude mcp add code-search ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-search/server.py
claude mcp add code-review ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-review/server.py

# Verify they were added
claude mcp list
```

#### CRITICAL: Environment Variable Issues

**GEMINI_API_KEY vs GOOGLE_API_KEY**:
- MCP servers expect `GEMINI_API_KEY`
- If you only have `GOOGLE_API_KEY`, create wrapper script:
```bash
#!/bin/bash
export GEMINI_API_KEY="${GOOGLE_API_KEY}"
exec /path/to/venv/bin/python /path/to/server.py "$@"
```

#### Common Problems and Solutions

**1. "Connection closed" errors (MCP error -32000)**
- **Cause**: Server exits immediately after startup
- **Debug**: Check server logs for startup errors
- **Solution**: Verify Python environment and dependencies

**2. No MCP messages in debug output**
- **Cause**: Servers not registered with Claude Code CLI
- **Solution**: Run `claude mcp add` commands (see above)
- **Note**: `.mcp.json` is NOT automatically loaded by CLI

**3. Protocol handshake failures**
- **Cause**: Wrong protocol version or initialization options
- **Current Protocol**: `2024-11-05` (as of 2025)
- **Solution**: Ensure servers use correct MCP library version

**4. STDIO communication corruption**
- **Cause**: Server writing to stdout (breaks JSON-RPC)
- **Rule**: Never use `print()` or `console.log()` in MCP servers
- **Solution**: Use stderr for debugging or log files only

**5. Environment path issues**
- **Cause**: Claude Code cannot find Python/Node binaries
- **Solution**: Use absolute paths in configuration
- **Example**: `/home/user/.claude/mcp/central/venv/bin/python`

#### Debugging Steps
1. **Enable debug mode and read FULL output**:
   ```bash
   claude --debug --dangerously-skip-permissions -p 'test' 2>&1 | tee debug.log
   # Read the ENTIRE log - do not grep initially
   ```

2. **Look for MCP indicators**:
   - `[DEBUG] MCP server "name": Calling MCP tool` - Server working
   - `[DEBUG] MCP server "name": Tool call succeeded` - Success
   - No MCP messages at all - Servers not loaded

3. **Test servers manually**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05"},"id":1}' | \
     ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-search/server.py
   ```

4. **Run MCP test suite**:
   ```bash
   # Quick test (30 seconds)
   ./test_mcp_quick.sh

   # Comprehensive test
   ./test_mcp_servers.py

   # Pytest integration
   pytest tests/test_mcp_integration.py -v
   ```

#### MCP Server Requirements (Critical)
- **Protocol Version**: Must use `2024-11-05`
- **Return Types**: `list[Tool]` not `ListToolsResult`
- **Transport**: STDIO only (no HTTP for Claude Desktop)
- **Logging**: File-based only, never stdout/stderr during operation
- **Path**: Absolute paths required in configuration
- **Dependencies**: Isolated venv per server
- **Registration**: Must use `claude mcp add` for CLI

#### Log Locations
- Code Search: `~/.claude/mcp/code-search/logs/server_YYYYMMDD.log`
- Code Review: `~/.claude/mcp/code-review/logs/server_YYYYMMDD.log`

### Best Practices for MCP Usage

1. **Always activate virtual environment** before using MCP servers
2. **Check logs** when troubleshooting connection issues
3. **Use absolute paths** in all configurations
4. **Test connectivity** with debug mode before important operations
5. **Monitor usage** for code-review server (tracks tokens and cost)
6. **Keep index updated** by running indexer regularly
7. **Use appropriate models** - flash for quick reviews, pro for comprehensive analysis
8. **Set reasonable limits** to avoid API rate limits and costs

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

### Troubleshooting MCP Connection Issues

#### Critical Discovery: Claude Code CLI vs Desktop Differences

**IMPORTANT**: Claude Code CLI and Claude Desktop handle MCP servers completely differently:

- **Claude Desktop**: Automatically loads `.mcp.json` from project root
- **Claude Code CLI**: Requires manual server registration using `claude mcp add`
- **Project config (.mcp.json) takes precedence over global config**

If using Claude Code CLI, you MUST first register servers:
```bash
# Check if servers are already configured
claude mcp list

# If not listed, add them from .mcp.json
cat .mcp.json | jq -r '.mcpServers | to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"' | bash

# Verify they were added
claude mcp list
```

#### Common Problems and Solutions

**1. "Connection closed" errors (MCP error -32000)**
- **Cause**: Server exits immediately after startup
- **Debug**: Check server logs for startup errors
- **Solution**: Verify Python environment and dependencies

**2. No MCP messages in debug output**
- **Cause**: Servers not registered with Claude Code CLI
- **Solution**: Run `claude mcp add` commands (see above)
- **Note**: `.mcp.json` is NOT automatically loaded by CLI

**3. Protocol handshake failures**
- **Cause**: Wrong protocol version or initialization options
- **Current Protocol**: `2024-11-05` (as of 2025)
- **Solution**: Ensure servers use correct MCP library version

**4. STDIO communication corruption**
- **Cause**: Server writing to stdout (breaks JSON-RPC)
- **Rule**: Never use `print()` or `console.log()` in MCP servers
- **Solution**: Use stderr for debugging or log files only

**5. Environment path issues**
- **Cause**: Claude Code cannot find Python/Node binaries
- **Solution**: Use absolute paths in configuration
- **Example**: `/home/user/.claude/mcp/central/venv/bin/python`

#### Debugging Steps
1. **Enable debug mode and read FULL output**:
   ```bash
   claude --debug --dangerously-skip-permissions -p 'test' 2>&1 | tee debug.log
   # Read the ENTIRE log - do not grep initially
   ```

2. **Look for MCP indicators**:
   - `[DEBUG] MCP server "name": Calling MCP tool` - Server working
   - `[DEBUG] MCP server "name": Tool call succeeded` - Success
   - No MCP messages at all - Servers not loaded

3. **Test servers manually**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05"},"id":1}' | \
     /path/to/python /path/to/server.py
   ```

4. **Run MCP test suite**:
   ```bash
   # Quick test (30 seconds)
   ./test_mcp_quick.sh

   # Comprehensive test
   ./test_mcp_servers.py

   # Pytest integration
   pytest tests/test_mcp_integration.py -v
   ```

#### MCP Server Requirements (Critical)
- **Protocol Version**: Must use `2024-11-05`
- **Return Types**: `list[Tool]` not `ListToolsResult`
- **Transport**: STDIO only (no HTTP for Claude Desktop)
- **Logging**: File-based only, never stdout/stderr during operation
- **Path**: Absolute paths required in configuration
- **Dependencies**: Isolated venv per server
- **Registration**: Must use `claude mcp add` for CLI

#### Testing MCP Servers

The project includes comprehensive MCP tests:
- `test_mcp_quick.sh` - Quick 30-second verification
- `test_mcp_servers.py` - Detailed test suite with diagnostics
- `tests/test_mcp_integration.py` - Pytest integration tests

Tests are automatically run by:
- `./run_tests.sh` - Includes ALL MCP tests (full integration suite)
- Pre-commit hooks - Runs FULL test suite (no exclusions, no shortcuts)

#### MCP Tests in Pre-commit Environment

**CRITICAL**: MCP tests run differently in pre-commit hooks due to environment differences:

**Environment Detection**:
- Tests detect `PRE_COMMIT=1` environment variable
- In pre-commit: Uses `claude --dangerously-skip-permissions` (no --debug)
- In terminal: Uses `claude --debug --dangerously-skip-permissions`

**Why This Matters**:
- `--debug` flag produces excessive output (~10x more verbose)
- Pre-commit runs without TTY, affecting subprocess behavior
- Large output can cause subprocess pipe buffer deadlock
- Solution: Environment-aware verbosity control

**Performance**:
- Pre-commit MCP tests: ~60-90 seconds (without --debug)
- Direct execution: ~90-120 seconds (with --debug for debugging)
- Both run FULL test suite - no shortcuts or exclusions

**Documentation:**
- `indexing/MCP_SERVER_USAGE.md` - **Complete usage guide and API reference**
- `MCP_TESTING_GUIDE.md` - How to test MCP servers
- `MCP_SERVER_TROUBLESHOOTING.md` - Debug connection issues
- `MCP_CROSS_WORKSPACE_SETUP.md` - Set up servers for all workspaces
- `MCP_KEY_LEARNINGS.md` - Critical discoveries and lessons learned
- `indexing/MCP_SERVER_GUIDE.md` - Implementation details

## 🧪 MANDATORY HOOK TESTING REQUIREMENTS

**ALL HOOKS MUST HAVE COMPREHENSIVE TESTS - NO EXCEPTIONS**

**📚 FIRST: Read `hooks/HOOKS.md` for complete hook documentation**

### Critical Testing Mandate
1. **EVERY HOOK MUST BE TESTED** - No hook without comprehensive tests
2. **TESTS MUST RUN IN EVERY BUILD** - Integrated into `run_tests.sh`
3. **NEVER SKIP HOOK TESTS** - They protect critical safety infrastructure
4. **TEST STDIN HANDLING** - The #1 cause of hook failures
5. **ADD TEST FOR EVERY NEW HOOK** - No exceptions
6. **UNDERSTAND HOOK ARCHITECTURE** - Read `hooks/HOOKS.md` before making changes

### Required Test Categories

#### Pre-Install Tests (`hooks/tests/test_hooks_pre_install.sh`)
- Test each hook with valid input
- Test each hook with invalid input
- Test each hook with empty input
- Test stdin handling with heredoc
- Test exit codes (0=allow, 1=error, 2=block)

#### Python Hook Tests (`hooks/python/tests/`)
- Unit tests for all Python guards
- Integration tests for guard system
- Mock testing for Claude input parsing
- Exit code verification

#### Protection Guard Tests
- `test-script-integrity-guard.sh` - Protects test scripts
- `precommit-protection-guard.sh` - Prevents bypass attempts
- `anti-bypass-pattern-guard.py` - Blocks test skipping patterns

#### Post-Install Tests (if hooks installed)
- Test installed hooks in `~/.claude`
- Test stdin handling after installation
- Test override mechanisms
- Test logging functionality

### Integration with run_tests.sh

Hook tests are **MANDATORY** and run as part of the full test suite:

```bash
# Run hook tests - MUST PASS (critical safety infrastructure)
if ! test_hooks; then
    log_error "Hook tests FAILED - blocking commit"
    exit 1
fi
```

### Enforcement
- **test-script-integrity-guard.sh** protects hook test files
- **precommit-protection-guard.sh** prevents bypassing tests
- **anti-bypass-pattern-guard.py** blocks test skipping patterns
- **Pre-commit hooks** run tests automatically

### Historical Context
Hook stdin handling was broken because:
- Python main.py expected stdin but got empty string
- No tests caught this regression
- Hooks failed silently in production

**This MUST NEVER happen again.**

### Documentation
- `HOOK_TEST_REQUIREMENTS.md` - Complete testing requirements
- `hooks/tests/` - All test implementations
- Hook tests are **critical safety infrastructure**

---

Created from Spotidal production best practices. These rules prevent real harm.
