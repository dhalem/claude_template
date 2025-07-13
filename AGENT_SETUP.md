# Agent Setup Guide - Claude Development Template

**This guide is designed for AI agents to set up the Claude development template in new repositories.**

## Quick Setup Commands

### Method 1: Full Template Setup (Recommended)
```bash
# Download and run the setup script
curl -sL https://raw.githubusercontent.com/dhalem/claude_template/main/scripts/agent-setup.sh | bash
```

### Method 2: Manual Step-by-Step

1. **Download the pull script**:
   ```bash
   curl -sO https://raw.githubusercontent.com/dhalem/claude_template/main/pull-templates.sh
   chmod +x pull-templates.sh
   ```

2. **Install everything automatically**:
   ```bash
   echo "1" | ./pull-templates.sh  # Option 1 = Full setup
   ```

3. **Set up Python environment**:
   ```bash
   ./scripts/setup-venv.sh
   source venv/bin/activate
   ./scripts/setup-pre-commit.sh
   ```

4. **Set up code indexing** (optional but recommended):
   ```bash
   cd indexing && ./setup_code_indexing.sh && cd ..
   ```

5. **Create local configuration**:
   ```bash
   cp CLAUDE.local.md.template CLAUDE.local.md
   ```

### Method 3: Selective Installation

For existing projects, install only specific components:

```bash
# Download pull script
curl -sO https://raw.githubusercontent.com/dhalem/claude_template/main/pull-templates.sh
chmod +x pull-templates.sh

# Install specific components:
echo "2" | ./pull-templates.sh  # Pre-commit hooks only
echo "3" | ./pull-templates.sh  # Python config only
echo "4" | ./pull-templates.sh  # Scripts only
echo "5" | ./pull-templates.sh  # Claude integration only
echo "6" | ./pull-templates.sh  # Code indexing only
```

## What Gets Installed

### Core Development Tools
- `.pre-commit-config.yaml` - 15+ automated quality checks
- `pyproject.toml` - Python tool configurations
- `pytest.ini` - Test configuration
- `.flake8`, `.gitignore`, `.secrets.baseline` - Additional configs

### Scripts Directory
- `setup-venv.sh` - Python virtual environment setup
- `setup-pre-commit.sh` - Pre-commit hook installation
- `run_tests.sh` - Smart test runner
- `smart_test_runner.py` - Intelligent test selection

### Claude Code Integration
- `hooks/` - AI safety guards and best practices
- `CLAUDE.md` - AI assistant guidelines
- `CLAUDE.local.md.template` - Project-specific customization template

### Code Search System
- `indexing/` - Fast code search with MCP support
- `indexing/claude_code_search.py` - Search interface
- `indexing/mcp/` - Model Context Protocol server

## Agent Workflow

When setting up a new repository, follow this sequence:

1. **Initial Setup**:
   ```bash
   # Ensure we're in the project root
   pwd
   git status  # Verify it's a git repository

   # Install template
   curl -sL https://raw.githubusercontent.com/dhalem/claude_template/main/scripts/agent-setup.sh | bash
   ```

2. **Verify Installation**:
   ```bash
   # Check that key files exist
   ls -la .pre-commit-config.yaml pyproject.toml CLAUDE.md
   ls -la scripts/ hooks/ indexing/
   ```

3. **Activate Environment**:
   ```bash
   source venv/bin/activate
   which python3  # Should show ./venv/bin/python3
   ```

4. **Test the Setup**:
   ```bash
   # Run a basic test
   pre-commit run --all-files

   # Test code search (if files exist)
   python3 indexing/claude_code_search.py --help
   ```

5. **Customize for Project**:
   ```bash
   # Edit project-specific rules
   # Update CLAUDE.local.md with project context
   ```

## Agent Commands Reference

### Code Search Commands
```bash
# Search for functions
python3 indexing/claude_code_search.py search 'function_name'

# List all classes
python3 indexing/claude_code_search.py list_type 'class'

# Search with patterns
python3 indexing/claude_code_search.py search 'get_*' function

# Search in specific files
python3 indexing/claude_code_search.py file_symbols "path/to/file.py"
```

### Testing Commands
```bash
# Run all tests
pytest

# Run specific categories
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Smart test runner
./scripts/run_tests.sh
```

### Quality Checks
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific tools
black .
ruff check .
mypy src/
bandit -r src/
```

## Error Handling

### Common Issues and Solutions

1. **"Permission denied" errors**:
   ```bash
   chmod +x scripts/*.sh
   chmod +x pull-templates.sh
   ```

2. **Python virtual environment issues**:
   ```bash
   # Remove and recreate venv
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

3. **Pre-commit installation fails**:
   ```bash
   # Install pre-commit manually
   pip install pre-commit
   pre-commit install
   ```

4. **Code indexing setup fails**:
   ```bash
   # Skip indexing for now, can be set up later
   echo "Skipping code indexing setup"
   ```

## Agent Safety Checks

Before proceeding with setup, verify:

1. **Correct directory**: `pwd` shows the intended project directory
2. **Git repository**: `git status` works without errors
3. **No conflicts**: Check if files already exist before overwriting
4. **Python available**: `python3 --version` works
5. **Write permissions**: Can create files in current directory

## Success Verification

After setup, these should all work:

```bash
# Environment check
source venv/bin/activate && which python3 | grep venv

# Tools check
pre-commit --version
black --version
ruff --version

# Template files exist
test -f CLAUDE.md && test -f .pre-commit-config.yaml && echo "Core files OK"

# Scripts are executable
test -x scripts/setup-venv.sh && echo "Scripts OK"
```

## Integration with Existing Projects

For projects that already have some of these tools:

1. **Backup existing files** before installation
2. **Review differences** after installation
3. **Merge configurations** manually if needed
4. **Test thoroughly** before committing changes

Example backup and merge workflow:
```bash
# Backup existing configs
cp .pre-commit-config.yaml .pre-commit-config.yaml.backup 2>/dev/null || true
cp pyproject.toml pyproject.toml.backup 2>/dev/null || true

# Install template
echo "1" | ./pull-templates.sh

# Compare and merge if needed
diff .pre-commit-config.yaml.backup .pre-commit-config.yaml || true
```

---

**This guide enables AI agents to quickly and reliably set up the Claude development template in any Python project.**
