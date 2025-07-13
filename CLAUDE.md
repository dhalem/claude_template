# CLAUDE.md - AI Assistant Guidelines

## 🚨 RULE #0: FOLLOW ALL RULES! CHECK THIS FILE BEFORE ACTING!

**MANDATORY FIRST ACTION FOR EVERY REQUEST:**
1. Read this file COMPLETELY before responding
2. Check for project-specific rules in CLAUDE.local.md
3. Only proceed after confirming no violations

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
source venv/bin/activate
which python3  # Must show ./venv/bin/python3
```

### Code Search Before Creation (MANDATORY)
```bash
# ALWAYS search existing code before writing new:
python3 indexing/claude_code_search.py search 'function_name'
python3 indexing/claude_code_search.py list_type 'class'
```

### Pre-commit Verification
```bash
# Before committing:
pre-commit run --all-files
git status  # Ensure clean
```

## 📋 Development Workflow

1. **Activate virtual environment**
2. **Search for existing implementations**
3. **Write tests first (TDD)**
4. **Implement feature**
5. **Run tests**
6. **Run pre-commit checks**
7. **Commit with descriptive message**

## 🚫 Absolute Prohibitions

- **NO MOCKS** without permission
- **NO bypassing pre-commit** without permission
- **NO force pushing** without permission
- **NO production credentials** in code

## Project-Specific Rules

See `CLAUDE.local.md` for project-specific guidelines.

---

Created from Spotidal best practices. Customize for your project needs.
