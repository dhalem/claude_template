# Claude Development Template

**🤖 Copy and paste this prompt to get started:**

```
Please install the Claude development template from https://github.com/dhalem/claude_template into my current project. Follow the Agent Setup section in the README to automatically install all development tools, hooks, and configurations.
```

**🧑‍💻 For hook development, use this prompt:**

```
Please set up the Claude template development environment from https://github.com/dhalem/claude_template for developing new Claude Code safety hooks. Run setup-development.sh and follow the DEVELOPMENT.md guide.
```

**AI Agent Instructions: Follow the [Agent Setup](#agent-setup) section below to automatically install this template.**

## Agent Setup

### Prerequisites Check
```bash
# Verify we're in a git repository
git status

# Verify Python 3 is available
python3 --version

# Check current directory
pwd
```

### Automatic Installation
Run these commands in sequence:

```bash
# Step 1: Download the template installer
curl -sO https://raw.githubusercontent.com/dhalem/claude_template/main/pull-templates.sh
chmod +x pull-templates.sh

# Step 2: Install everything automatically (option 1 = full setup)
echo "1" | ./pull-templates.sh

# Step 3: Set up Python virtual environment
./scripts/setup-venv.sh

# Step 4: Activate virtual environment
source venv/bin/activate

# Step 5: Install pre-commit hooks
./scripts/setup-pre-commit.sh

# Step 6: Set up code indexing (optional - skip if errors)
cd indexing && ./setup_code_indexing.sh && cd .. || echo "Skipping code indexing setup"

# Step 7: Create local configuration
cp CLAUDE.local.md.template CLAUDE.local.md

# Step 8: Test the installation
pre-commit run --all-files || echo "Pre-commit setup complete, some checks may fail on empty repo"
```

### Verification Commands
```bash
# Verify key files exist
ls -la .pre-commit-config.yaml pyproject.toml CLAUDE.md scripts/ hooks/

# Verify virtual environment
source venv/bin/activate && which python3 | grep venv

# Test code search (if indexing was set up)
python3 indexing/claude_code_search.py --help 2>/dev/null || echo "Code search not available"
```

### Agent Success Criteria
- ✅ `.pre-commit-config.yaml` exists
- ✅ `pyproject.toml` exists
- ✅ `CLAUDE.md` exists
- ✅ `scripts/` directory exists
- ✅ `hooks/` directory exists
- ✅ Virtual environment activated (`which python3` shows venv path)
- ✅ Pre-commit installed (`pre-commit --version` works)

---

## What This Template Provides

### 🤖 AI Development Integration
- **Claude Code hooks** - Safety guards and development best practices
- **CLAUDE.md guidelines** - Battle-tested AI development rules
- **Meta-cognitive guards** - Prevent common AI assistant mistakes
- **Development workflow automation** - Streamlined AI-assisted coding

### 🔍 Code Intelligence
- **Fast code search** - Find functions, classes, and patterns instantly
- **MCP server integration** - Claude Code workspace integration
- **Real-time indexing** - Automatic code discovery and cataloging
- **Pattern matching** - Find similar implementations with wildcards

### ✅ Quality Assurance System
- **15+ pre-commit hooks** - Automated quality and security checks
- **Smart test runner** - Dependency-aware test execution
- **Security scanning** - Secret detection and vulnerability analysis
- **Code formatting** - Black, isort, Ruff, MyPy integration

### 🧪 Intelligent Testing
- **Test categorization** - Unit, integration, slow test separation
- **Parallel execution** - Fast test runs with pytest-xdist
- **Coverage reporting** - Track and improve test coverage
- **Real integration focus** - Discourage mocking, encourage real tests

## Core Commands

### Code Search
```bash
# Find functions
python3 indexing/claude_code_search.py search 'function_name'

# Find with patterns
python3 indexing/claude_code_search.py search 'get_*' function

# List all classes
python3 indexing/claude_code_search.py list_type 'class'

# Explore file contents
python3 indexing/claude_code_search.py file_symbols "src/models.py"
```

### MCP Server Integration
```bash
# Install MCP servers for Claude Code
./install-mcp-servers.sh

# Test MCP server connection
claude --debug -p 'hello world'
# Look for: "MCP server connected successfully" in debug output

# Manual server testing (for debugging)
/home/dhalem/.claude/mcp/central/venv/bin/python \
  /home/dhalem/.claude/mcp/central/code-search/server.py
```

**Available MCP servers:**
- **code-search**: Search symbols across workspaces
- **code-review**: AI-powered code review with Gemini

**Troubleshooting MCP:**
- Check logs: `~/.claude/mcp/central/*/logs/server_*.log`
- Verify environment: `GEMINI_API_KEY` required for code-review
- Reinstall: Run `./install-mcp-servers.sh` again

### Testing
```bash
# Run all tests
pytest

# Run specific categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # Skip slow tests

# Smart test runner (dependency-aware)
./scripts/run_tests.sh
```

### Quality Checks
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Individual tools
black .              # Code formatting
ruff check .         # Linting and import sorting
mypy src/           # Type checking
bandit -r src/      # Security scanning
```

## Development Workflow

### The Five Truths (Battle-Tested Principles)
1. **I WILL MAKE MISTAKES** - Always verify and double-check
2. **MOCK TESTING ≠ WORKING** - Prefer real integration over mocks
3. **ASSUMPTIONS KILL PROJECTS** - Check current state before proceeding
4. **PROTOCOL-FIRST SAVES HOURS** - Understand interfaces before building
5. **TRUST BUT VERIFY** - Require evidence for all claims

### Recommended Agent Workflow
1. **Search before creating**: `python3 indexing/claude_code_search.py search 'similar_function'`
2. **Activate environment**: `source venv/bin/activate`
3. **Write tests first**: Create in `tests/` directory
4. **Implement feature**: Create in `src/` directory
5. **Run tests**: `pytest`
6. **Check quality**: `pre-commit run --all-files`
7. **Commit changes**: `git add . && git commit -m "feat: description"`

## Project Structure

```
├── hooks/                      # Claude Code integration
│   ├── python/                # Python-based safety guards
│   │   ├── guards/            # Individual guard modules
│   │   └── tests/             # Guard test suite
│   ├── adaptive-guard.sh       # Main safety system
│   └── settings.json          # Claude Code configuration
├── indexing/                   # Code search & MCP server
│   ├── mcp/                   # Model Context Protocol server
│   ├── claude_code_search.py  # Search interface
│   └── setup_code_indexing.sh # Setup script
├── scripts/                    # Development utilities
│   ├── run_tests.sh           # Smart test runner
│   ├── setup-venv.sh          # Python environment setup
│   └── smart_test_runner.py   # Intelligent test selection
├── src/                        # Your source code
├── tests/                      # Your test suite
├── .pre-commit-config.yaml     # Quality automation
├── pyproject.toml             # Python tool configuration
├── CLAUDE.md                  # AI assistant guidelines
├── CLAUDE.local.md            # Project-specific rules
└── setup-template.sh          # One-command setup
```

## Advanced Features

### Claude Code Safety Hooks
- **Path verification** - Ensures operations happen in correct directories
- **Virtual environment enforcement** - Prevents system-wide Python pollution
- **Git operation safety** - Protects against dangerous git commands
- **Container state awareness** - Distinguishes local vs containerized environments
- **Meta-cognitive monitoring** - Tracks AI decision-making patterns
- **TOTP override system** - Google Authenticator integration for authorized bypasses

### 🔐 Google Authenticator Override System
The template includes a secure override system for when hooks block legitimate operations:

**🚨 IMPORTANT: The installation script automatically handles all Python dependencies and requirements setup.**

#### Quick Setup
1. **Install the hook system** (handles all dependencies automatically):
   ```bash
   ./hooks/install-hooks-python-only.sh
   ```

2. **Setup Google Authenticator** (fully automated):
   ```bash
   ./hooks/setup-authenticator.sh
   ```
   This automatically:
   - Generates a secure TOTP secret
   - Guides you through Google Authenticator setup
   - **Creates .env file in hooks directory for automatic loading**
   - **Ready to use immediately - no manual configuration needed**

#### How It Works
- When hooks block commands, you'll see override instructions
- Get 6-digit code from Google Authenticator app
- Re-run command: `HOOK_OVERRIDE_CODE=123456 your-command`
- All overrides are audited and logged

#### Features
- ✅ 30-second TOTP validation with time-window tolerance
- ✅ Secure audit logging of all override attempts
- ✅ Fallback implementation when pyotp unavailable
- ✅ Integration with existing Claude Code hook system

### Code Search Capabilities
- **Symbol search**: Functions, classes, variables, imports
- **Pattern matching**: Wildcards (`get_*`, `*_handler`)
- **File filtering**: Search specific file types or patterns
- **Contextual search**: Find similar implementations
- **MCP integration**: Works seamlessly with Claude Code workspace

### Intelligent Testing System
- **Dependency detection**: Only run tests affected by changes
- **Category-based execution**: Unit, integration, slow test separation
- **Parallel execution**: Automatic parallelization for speed
- **Real integration focus**: Discourages over-mocking
- **Coverage tracking**: HTML and terminal coverage reports

## Updating the Template

### For Individual Projects (Pull Updates)
```bash
# Re-run the installer to get updates
./pull-templates.sh

# Choose update option:
# 1) Everything (full update)
# 2) Just pre-commit hooks
# 3) Just Python config
# 4) Just scripts
# 5) Just Claude integration
# 6) Just code indexing
```

### Update Template Repository (Push Changes)

**Agent Instructions**: Use these commands to update the template repository with improvements from a target project:

#### Prerequisites
```bash
# Verify we're in the target project (source of improvements)
pwd
git status

# Verify the target has the template files
ls .pre-commit-config.yaml pyproject.toml CLAUDE.md scripts/ hooks/ indexing/
```

#### Extract Improvements to Template Repository
```bash
# Step 1: Clone the template repository
git clone https://github.com/dhalem/claude_template /tmp/claude_template_update
cd /tmp/claude_template_update

# Step 2: Copy improved files from target project (replace /path/to/target with actual path)
TARGET_PROJECT="/path/to/target/project"

# Copy core configuration files
cp "$TARGET_PROJECT/.pre-commit-config.yaml" .
cp "$TARGET_PROJECT/pyproject.toml" .
cp "$TARGET_PROJECT/pytest.ini" .
cp "$TARGET_PROJECT/.flake8" .
cp "$TARGET_PROJECT/.gitignore" .
cp "$TARGET_PROJECT/.secrets.baseline" .

# Copy improved scripts
cp -r "$TARGET_PROJECT/scripts/"* scripts/

# Copy improved hooks (be careful not to overwrite project-specific settings)
cp -r "$TARGET_PROJECT/hooks/"* hooks/

# Copy improved indexing system
cp -r "$TARGET_PROJECT/indexing/"* indexing/

# Copy improved documentation (merge carefully)
cp "$TARGET_PROJECT/CLAUDE.md" CLAUDE.md

# Step 3: Review changes
git diff

# Step 4: Commit improvements
git add .
git commit -m "feat: update template with improvements from production project

- Improved pre-commit configuration
- Enhanced scripts and utilities
- Updated Claude Code integration
- Better indexing system
- Documentation improvements

Source: $TARGET_PROJECT"

# Step 5: Push updates
git push origin main
```

#### Alternative: Selective Update
```bash
# For more targeted updates, copy specific files:

# Update just pre-commit hooks
cp "$TARGET_PROJECT/.pre-commit-config.yaml" /tmp/claude_template_update/

# Update just testing framework
cp "$TARGET_PROJECT/scripts/run_tests.sh" /tmp/claude_template_update/scripts/
cp "$TARGET_PROJECT/scripts/smart_test_runner.py" /tmp/claude_template_update/scripts/

# Update just Claude integration
cp -r "$TARGET_PROJECT/hooks/"* /tmp/claude_template_update/hooks/

# Update just code search
cp -r "$TARGET_PROJECT/indexing/"* /tmp/claude_template_update/indexing/
```

#### Agent Workflow for Template Updates
```bash
# Use this when you want to improve the template based on lessons learned in a project:

# 1. Identify improvements in current project
echo "Current project improvements to extract:"
echo "- Enhanced pre-commit hooks"
echo "- Better testing scripts"
echo "- Improved Claude integration"
echo "- Updated documentation"

# 2. Set variables
CURRENT_PROJECT=$(pwd)
TEMPLATE_REPO="/tmp/claude_template_update"

# 3. Clone template repo
git clone https://github.com/dhalem/claude_template "$TEMPLATE_REPO"

# 4. Copy improvements
cd "$TEMPLATE_REPO"
cp "$CURRENT_PROJECT/.pre-commit-config.yaml" .
cp "$CURRENT_PROJECT/pyproject.toml" .
cp -r "$CURRENT_PROJECT/scripts/"* scripts/
cp -r "$CURRENT_PROJECT/hooks/"* hooks/
cp -r "$CURRENT_PROJECT/indexing/"* indexing/

# 5. Review and commit
git diff --name-only
git add .
git commit -m "feat: update template with production improvements"
git push origin main

# 6. Clean up
rm -rf "$TEMPLATE_REPO"
cd "$CURRENT_PROJECT"
```

### Template Contribution Workflow
```bash
# For contributing to the template:
git clone https://github.com/dhalem/claude_template
cd claude_template
# Make improvements
git add .
git commit -m "improvement description"
git push origin main
```

## Troubleshooting

### Common Agent Issues

**"Permission denied" on scripts:**
```bash
chmod +x scripts/*.sh pull-templates.sh
```

**Virtual environment not working:**
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

**Pre-commit hooks failing:**
```bash
# Install pre-commit manually
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

**Code indexing setup fails:**
```bash
# Skip for now, can be set up later
echo "Code indexing setup skipped - can be configured later"
```

### Success Verification Checklist

After installation, verify these work:
- [ ] `source venv/bin/activate && which python3 | grep venv`
- [ ] `pre-commit --version`
- [ ] `black --version`
- [ ] `pytest --version`
- [ ] `ls .pre-commit-config.yaml pyproject.toml CLAUDE.md`

## 🧑‍💻 Hook Development

This template also serves as a development environment for creating and improving Claude Code safety hooks:

### Quick Development Setup
```bash
# Set up development environment for hook development
./setup-development.sh

# Create a new guard
./scripts/develop-hooks.sh new-guard my_security_check

# Test hooks
./scripts/develop-hooks.sh test

# Run performance tests
./scripts/test-performance.sh
```

### Development Features
- **Complete testing framework** with pytest and coverage
- **Automated CI/CD** with GitHub Actions
- **Security scanning** with bandit and safety
- **Performance benchmarking** with pytest-benchmark
- **Code quality tools** with black, ruff, and mypy
- **Guard templates** for rapid development
- **Integration testing** with real Claude Code scenarios

📖 **Read [DEVELOPMENT.md](DEVELOPMENT.md) for the complete development guide**

## License

MIT License - Use this template for any project!

---

**🤖 Agent Note**: This template is designed for automatic installation. Follow the [Agent Setup](#agent-setup) section for reliable, hands-off installation.
