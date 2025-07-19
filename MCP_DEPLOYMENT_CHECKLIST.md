# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# MCP Server Development and Deployment Checklist

This comprehensive checklist ensures new MCP servers are built correctly and work across all workspaces from day one.

## 📋 Pre-Development Checklist

### Environment Setup
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] MCP dependencies installed: `pip install mcp`
- [ ] Claude Code CLI available: `which claude`
- [ ] Git repository clean: `git status`

### Planning
- [ ] Server purpose clearly defined
- [ ] Tool functions identified
- [ ] Input/output schemas designed
- [ ] Environment variables documented
- [ ] Cross-workspace requirements understood

## 🚀 Development Phase Checklist

### 1. Server Creation
- [ ] Used automated creation script: `./create_new_mcp_server.sh`
- [ ] OR copied from template: `templates/mcp_server_template.py`
- [ ] Server name follows naming convention (lowercase, hyphens)
- [ ] File created: `indexing/mcp_<servername>_server.py`

### 2. Code Implementation
- [ ] **Protocol Requirements**:
  - [ ] Returns `list[Tool]` not `ListToolsResult`
  - [ ] Uses exact MCP protocol version that works
  - [ ] No stdout/stderr output during operation
  - [ ] File-based logging only
  - [ ] Proper async/await patterns

- [ ] **Tool Implementation**:
  - [ ] All tools have proper input schemas
  - [ ] Required parameters clearly marked
  - [ ] Default values provided where appropriate
  - [ ] Input validation implemented
  - [ ] Error handling for all edge cases

- [ ] **Error Handling**:
  - [ ] Try/catch blocks around all tool logic
  - [ ] Meaningful error messages
  - [ ] Proper logging of errors
  - [ ] Graceful degradation on failures

- [ ] **Code Quality**:
  - [ ] Type hints throughout
  - [ ] Docstrings for all functions
  - [ ] Clear variable names
  - [ ] No hardcoded paths or values
  - [ ] Environment variables properly handled

### 3. Local Testing
- [ ] **Server Startup**:
  - [ ] Server starts without errors: `python3 indexing/mcp_<server>_server.py`
  - [ ] No import errors
  - [ ] No syntax errors
  - [ ] Logs created in expected location

- [ ] **Tool Registration**:
  - [ ] Tools listed correctly: Check debug output
  - [ ] Schema validation passes
  - [ ] All required parameters present

- [ ] **Tool Functionality**:
  - [ ] Each tool returns expected results
  - [ ] Error cases handled properly
  - [ ] Edge cases tested
  - [ ] Performance acceptable

## 🔧 Integration Phase Checklist

### 4. Script Updates
- [ ] **Installation Script** (`install-mcp-central.sh`):
  - [ ] Server added to SERVER_CONFIGS array
  - [ ] File path correct
  - [ ] No syntax errors in script

- [ ] **Registration Script** (`register-mcp-global.sh`):
  - [ ] Registration block added
  - [ ] User scope specified (`-s user`)
  - [ ] Central paths used
  - [ ] Error handling included

- [ ] **Test Script** (`test_mcp_cross_workspace_prevention.py`):
  - [ ] Expected server count updated
  - [ ] Server name added to checks
  - [ ] Test coverage adequate

### 5. Central Installation
- [ ] **Installation Process**:
  - [ ] Central installation successful: `./install-mcp-central.sh`
  - [ ] Directory created: `~/.claude/mcp/central/<server>/`
  - [ ] Server file copied correctly
  - [ ] Virtual environment working
  - [ ] Dependencies installed
  - [ ] No permission errors

- [ ] **Verification**:
  - [ ] Server files exist in central location
  - [ ] Python environment functional
  - [ ] Logs directory created
  - [ ] Server starts from central location

### 6. User Scope Registration
- [ ] **Registration Process**:
  - [ ] Global registration successful: `./register-mcp-global.sh`
  - [ ] User scope registration confirmed
  - [ ] No override codes needed
  - [ ] OR override codes used if hooks block

- [ ] **Verification**:
  - [ ] Server listed: `claude mcp list`
  - [ ] Central paths shown in output
  - [ ] No local/project scope registrations
  - [ ] Registration persistent across sessions

## 🧪 Testing Phase Checklist

### 7. Cross-Workspace Testing
- [ ] **Different Directory Test**:
  - [ ] Test from different directory: `./test_mcp_other_workspace.sh /tmp/test`
  - [ ] Server accessible outside project
  - [ ] Tools function correctly
  - [ ] No path dependencies

- [ ] **Clean Environment Test**:
  - [ ] Test with empty `.mcp.json`
  - [ ] Test without project-specific config
  - [ ] Server works from user scope only

### 8. Automated Testing
- [ ] **Prevention Tests**:
  - [ ] Prevention tests pass: `python3 test_mcp_cross_workspace_prevention.py`
  - [ ] No hardcoded paths detected
  - [ ] Central installation verified
  - [ ] User scope confirmed
  - [ ] Cross-workspace access working

- [ ] **Full Test Suite**:
  - [ ] All tests pass: `./run_tests.sh`
  - [ ] MCP integration tests pass
  - [ ] No test failures
  - [ ] Performance acceptable

### 9. Claude Integration Testing
- [ ] **Claude Desktop**:
  - [ ] Server appears in Claude Desktop
  - [ ] Tools accessible via chat
  - [ ] Functions work correctly
  - [ ] No connection errors

- [ ] **Claude Code CLI**:
  - [ ] Server accessible: `claude --debug -p 'test'`
  - [ ] Tools callable via CLI
  - [ ] Debug output shows connection
  - [ ] No protocol errors

## 📚 Documentation Phase Checklist

### 10. Documentation
- [ ] **Server Documentation**:
  - [ ] Created: `docs/MCP_<SERVER>_SERVER.md`
  - [ ] Tool descriptions complete
  - [ ] Usage examples provided
  - [ ] Environment variables documented
  - [ ] Troubleshooting section included

- [ ] **Code Documentation**:
  - [ ] Docstrings for all functions
  - [ ] Schema descriptions clear
  - [ ] Parameter explanations provided
  - [ ] Error scenarios documented

- [ ] **Integration Documentation**:
  - [ ] Installation steps documented
  - [ ] Testing procedures outlined
  - [ ] Common issues listed
  - [ ] Links to related docs

## 🚀 Deployment Phase Checklist

### 11. Pre-Deployment Verification
- [ ] **Code Quality**:
  - [ ] No TODO items remaining in production code
  - [ ] All hardcoded values removed
  - [ ] Secrets properly externalized
  - [ ] No debug print statements

- [ ] **Security Review**:
  - [ ] No secrets in code
  - [ ] Input validation comprehensive
  - [ ] Error messages don't leak info
  - [ ] File access properly restricted

- [ ] **Performance**:
  - [ ] Response times acceptable
  - [ ] Memory usage reasonable
  - [ ] No blocking operations in main thread
  - [ ] Timeouts configured appropriately

### 12. Deployment Verification
- [ ] **Post-Deployment Testing**:
  - [ ] Server responds to basic requests
  - [ ] All tools functional
  - [ ] Error handling working
  - [ ] Logging operational

- [ ] **Cross-Workspace Validation**:
  - [ ] Works in multiple workspaces
  - [ ] No workspace-specific dependencies
  - [ ] User scope registration stable
  - [ ] Configuration portable

## 🔍 Maintenance Phase Checklist

### 13. Monitoring Setup
- [ ] **Logging**:
  - [ ] Log files accessible
  - [ ] Log rotation configured
  - [ ] Error logs monitored
  - [ ] Performance metrics tracked

- [ ] **Health Checks**:
  - [ ] Status tool implemented
  - [ ] Health monitoring setup
  - [ ] Failure detection configured
  - [ ] Recovery procedures documented

### 14. Update Procedures
- [ ] **Version Management**:
  - [ ] Version numbering scheme
  - [ ] Backward compatibility plan
  - [ ] Migration procedures
  - [ ] Rollback plan available

- [ ] **Testing Updates**:
  - [ ] Update testing procedures
  - [ ] Regression test suite
  - [ ] Performance benchmarks
  - [ ] User acceptance criteria

## 🚨 Common Failure Points Checklist

### Critical Issues to Avoid
- [ ] **Protocol Violations**:
  - [ ] NOT returning `ListToolsResult` instead of `list[Tool]`
  - [ ] NOT writing to stdout during operation
  - [ ] NOT using wrong protocol version

- [ ] **Path Issues**:
  - [ ] NOT using hardcoded user paths (`/home/username/`)
  - [ ] NOT using project-specific paths
  - [ ] NOT using local scope instead of user scope

- [ ] **Registration Issues**:
  - [ ] NOT forgetting to update installation scripts
  - [ ] NOT forgetting to register with user scope
  - [ ] NOT testing cross-workspace functionality

- [ ] **Code Issues**:
  - [ ] NOT missing error handling
  - [ ] NOT missing input validation
  - [ ] NOT using blocking operations

## ✅ Final Sign-off Checklist

Before considering the server "production ready":

- [ ] All checklist items completed
- [ ] Code reviewed by another developer
- [ ] Documentation reviewed and approved
- [ ] Testing completed in multiple environments
- [ ] Performance benchmarks met
- [ ] Security review passed
- [ ] Deployment procedures validated
- [ ] Monitoring and alerting configured
- [ ] Support procedures documented
- [ ] Training materials created (if needed)

## 🔗 Quick Reference Commands

```bash
# Create new server
./create_new_mcp_server.sh my-server "Description" my_tool "Tool description"

# Install centrally
./install-mcp-central.sh

# Register globally
./register-mcp-global.sh

# Test cross-workspace
./test_mcp_other_workspace.sh /tmp/test

# Run prevention tests
python3 test_mcp_cross_workspace_prevention.py

# Full test suite
./run_tests.sh

# Check registration
claude mcp list

# Test functionality
claude --debug -p 'Use my_tool to test'
```

## 📖 Related Documentation

- `MCP_SERVER_DEVELOPMENT_GUIDE.md` - Development guide
- `MCP_KEY_LEARNINGS.md` - Critical discoveries
- `MCP_SERVER_TROUBLESHOOTING.md` - Debugging guide
- `MCP_CROSS_WORKSPACE_SETUP.md` - Cross-workspace setup
- `templates/README.md` - Template usage guide

---

**Remember**: This checklist was created from real debugging experiences. Every item prevents a mistake that has actually happened. Use it religiously to avoid the same pitfalls.
