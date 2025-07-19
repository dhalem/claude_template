# Review Remediation Plan Template

## 🎯 **Remediation Planning Protocol**

**Use this template after receiving a code review to create a systematic remediation plan that ensures safety, quality, and completeness.**

---

## 📋 **Phase 0: Review Analysis & Planning**

### Step 0.1: Create Tracking Document
```markdown
# Remediation Tracking: [Review Date] - [Directory/Component]

## Review Summary
- **Directory Reviewed**: [path]
- **Review Tool**: [mcp code-review / manual / other]
- **Focus Areas**: [list]
- **Total Issues Found**: [count]

## Issue Categories
- **Critical**: [count] - [brief description]
- **Major**: [count] - [brief description]
- **Minor**: [count] - [brief description]

## Remediation Status
- [ ] Phase 1: Critical Issues
- [ ] Phase 2: Major Issues
- [ ] Phase 3: Minor Issues
- [ ] Phase 4: Validation & Documentation
```

### Step 0.2: Categorize Issues by Severity
- **Critical**: Bugs, security issues, broken functionality
- **Major**: Design flaws, significant inconsistencies, missing tests
- **Minor**: Style issues, documentation gaps, minor improvements

### Step 0.3: Plan Logical Phases
- **Phase 1**: Fix critical bugs that break functionality
- **Phase 2**: Address major design and consistency issues
- **Phase 3**: Resolve minor improvements and style issues
- **Phase 4**: Final validation and documentation updates

---

## 🔥 **Phase 1: Critical Issues Remediation**

### For Each Critical Issue:

#### Step 1.1: Update Tracking Document
```markdown
## Current Work: [Issue Description]
- **Issue Type**: Critical
- **Files Affected**: [list]
- **Expected Changes**: [description]
- **Status**: In Progress
- **Started**: [timestamp]
```

#### Step 1.2: Pre-Change Safety Check
```bash
# Verify current test status
./run_tests.sh
# OR
pytest
# Status: ✅ MUST PASS before proceeding
```

#### Step 1.3: Implement Fix
- Make minimal, focused changes
- Test locally as you go
- Follow existing code patterns

#### Step 1.4: Validate Fix
```bash
# Run relevant tests
pytest path/to/affected/tests.py -v

# Run full test suite
./run_tests.sh

# Status: ✅ MUST PASS before commit
```

#### Step 1.5: Commit with Protocol
```bash
# Check status and diff
git status
git diff

# Add changes
git add [specific files]

# Commit with descriptive message
git commit -m "fix: [brief description of critical issue fixed]

- [Detailed description of change]
- [Impact on functionality]
- Addresses critical issue from code review

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Verify commit succeeded
git status
git log --oneline -1

# Status: ✅ MUST verify commit succeeded
```

#### Step 1.6: Update Tracking Document
```markdown
## Completed: [Issue Description]
- **Status**: ✅ Completed
- **Commit**: [hash]
- **Completed**: [timestamp]
- **Test Status**: ✅ Passing
```

#### Step 1.7: Repeat for All Critical Issues

---

## 🔧 **Phase 2: Major Issues Remediation**

### For Each Major Issue:

#### Step 2.1: Update Tracking Document
```markdown
## Current Work: [Issue Description]
- **Issue Type**: Major
- **Files Affected**: [list]
- **Expected Changes**: [description]
- **Status**: In Progress
- **Started**: [timestamp]
```

#### Step 2.2: Pre-Change Safety Check
```bash
# Verify current test status
./run_tests.sh
# Status: ✅ MUST PASS before proceeding
```

#### Step 2.3: Implement Solution
- Address design issues systematically
- Add missing tests if required
- Refactor for consistency

#### Step 2.4: Validate Solution
```bash
# Run affected tests
pytest path/to/affected/tests.py -v

# Run full test suite
./run_tests.sh

# Status: ✅ MUST PASS before commit
```

#### Step 2.5: Commit with Protocol
```bash
# Follow same commit protocol as Phase 1
git status
git diff
git add [files]
git commit -m "refactor: [description of major improvement]

- [Detailed description]
- [Impact on architecture/design]
- Addresses major issue from code review

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Verify commit
git status
git log --oneline -1
```

#### Step 2.6: Update Tracking Document
```markdown
## Completed: [Issue Description]
- **Status**: ✅ Completed
- **Commit**: [hash]
- **Completed**: [timestamp]
- **Test Status**: ✅ Passing
```

#### Step 2.7: Repeat for All Major Issues

---

## ✨ **Phase 3: Minor Issues Remediation**

### For Each Minor Issue:

#### Step 3.1: Update Tracking Document
```markdown
## Current Work: [Issue Description]
- **Issue Type**: Minor
- **Files Affected**: [list]
- **Expected Changes**: [description]
- **Status**: In Progress
- **Started**: [timestamp]
```

#### Step 3.2: Pre-Change Safety Check
```bash
./run_tests.sh
# Status: ✅ MUST PASS before proceeding
```

#### Step 3.3: Implement Improvement
- Style fixes, documentation updates
- Minor consistency improvements
- Code cleanup

#### Step 3.4: Validate Improvement
```bash
# Run tests to ensure no regressions
./run_tests.sh
# Status: ✅ MUST PASS before commit
```

#### Step 3.5: Commit with Protocol
```bash
git status
git diff
git add [files]
git commit -m "style: [description of minor improvement]

- [Detailed description]
- [Impact on maintainability]
- Addresses minor issue from code review

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Verify commit
git status
git log --oneline -1
```

#### Step 3.6: Update Tracking Document
```markdown
## Completed: [Issue Description]
- **Status**: ✅ Completed
- **Commit**: [hash]
- **Completed**: [timestamp]
- **Test Status**: ✅ Passing
```

#### Step 3.7: Repeat for All Minor Issues

---

## ✅ **Phase 4: Validation & Documentation**

### Step 4.1: Update Tracking Document
```markdown
## Phase 4: Final Validation
- **Status**: In Progress
- **Started**: [timestamp]
```

### Step 4.2: Run Complete Test Suite
```bash
# Full test validation
./run_tests.sh

# If MCP tests exist
./test_mcp_quick.sh

# Status: ✅ MUST PASS completely
```

### Step 4.3: Run Follow-Up Code Review
```bash
# Re-run the MCP code review on the same directory
```

**Using MCP tool:**
```
mcp__code-review__review_code directory="[same path]" focus_areas=["[same focus areas]"] model="gemini-2.5-pro"
```

### Step 4.4: Analyze Follow-Up Review
- Compare with original review findings
- Verify all issues were addressed
- Check for any new issues introduced
- Document remaining issues (if any)

### Step 4.5: Update Documentation (if needed)
```bash
# Update any affected documentation
# README.md, API docs, etc.

# Commit documentation updates
git add [docs]
git commit -m "docs: update documentation after code review remediation

- Updated [specific docs]
- Reflects changes from review remediation
- All review findings addressed

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 4.6: Final Tracking Document Update
```markdown
## Remediation Complete ✅
- **Completed**: [timestamp]
- **Total Commits**: [count]
- **Final Test Status**: ✅ Passing
- **Follow-up Review**: [summary of results]

## Summary of Changes
- **Critical Issues Fixed**: [count] - [brief description]
- **Major Issues Fixed**: [count] - [brief description]
- **Minor Issues Fixed**: [count] - [brief description]

## Outstanding Issues (if any)
- [List any issues not addressed and why]

## Next Steps
- [Any follow-up work needed]
- [Future improvements planned]
```

### Step 4.7: Push All Changes
```bash
# Push all commits to remote
git push

# Verify push succeeded
git status
```

---

## 🛡️ **Safety Protocols**

### Required Checks at Every Step:
1. **Tests must pass** before any code changes
2. **Tests must pass** after every change
3. **Commits must succeed** and be verified
4. **Small, focused changes** only
5. **Follow existing patterns** and conventions

### Emergency Rollback:
```bash
# If something breaks, immediately rollback
git reset --hard HEAD~1

# Run tests to verify rollback worked
./run_tests.sh

# Investigate issue before retrying
```

### Commit Message Standards:
- **fix**: Critical bug fixes
- **refactor**: Major design improvements
- **style**: Minor style/consistency fixes
- **docs**: Documentation updates
- **test**: Test additions/improvements

---

## 📊 **Success Criteria**

**Phase Complete When:**
- [ ] All targeted issues addressed
- [ ] All tests passing
- [ ] All commits successful and pushed
- [ ] Tracking document updated

**Remediation Complete When:**
- [ ] All phases completed
- [ ] Follow-up review shows significant improvement
- [ ] No new critical/major issues introduced
- [ ] Documentation updated (if needed)

---

## 🔄 **Template Usage Instructions**

1. **Copy this template** to a new file: `REMEDIATION_PLAN_[DATE]_[COMPONENT].md`
2. **Fill in the tracking document** with actual review findings
3. **Work through phases sequentially** - never skip safety checks
4. **Update tracking document** at every step
5. **Commit frequently** with descriptive messages
6. **Run follow-up review** to validate remediation
7. **Archive completed plan** for future reference

**Remember**: Safety first, small changes, test everything, verify commits!
