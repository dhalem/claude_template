# Claude Development Template

**🤖 Copy and paste this prompt to get started:**

```
Please install the Claude development template from https://github.com/dhalem/claude_template into my current project. Follow the Agent Setup section in the README to automatically install all development tools, hooks, and configurations.
```

**🔧 For MCP server setup in existing projects, use this prompt:**

```
Please install the MCP server usage instructions from https://github.com/dhalem/claude_template/blob/main/indexing/MCP_SERVER_USAGE.md into my CLAUDE.md file. Add a section referencing the complete MCP server installation and usage guide. Include instructions for both code-search and code-review MCP servers with their installation commands and troubleshooting steps.
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

## ⚠️ INSTALLATION SAFETY WARNING

**CRITICAL: USE ONLY THE OFFICIAL INSTALLATION METHOD**

### The ONLY Safe Installation Script: `./safe_install.sh`
- **NEVER create additional install scripts**
- **NEVER modify ~/.claude directory without backup**
- **ALWAYS use safe_install.sh for ALL component installations**

### Why This Warning Exists
Multiple install scripts and careless .claude modifications have destroyed Claude installations and caused data loss. The `safe_install.sh` script provides:
- ✅ **Mandatory backup** of .claude directory before any changes
- ✅ **Safe installation** with proper error handling
- ✅ **Rollback instructions** if anything goes wrong
- ✅ **User confirmation** before making changes

### Installation Command
```bash
# For hooks and MCP servers installation:
./safe_install.sh
```

**DO NOT use any other install-*.sh scripts you may find in subdirectories!**

---

## What This Template Provides

### 🤖 AI Development Integration
- **Claude Code hooks** - Safety guards and development best practices
- **CLAUDE.md guidelines** - Battle-tested AI development rules
- **Meta-cognitive guards** - Prevent common AI assistant mistakes
- **Development workflow automation** - Streamlined AI-assisted coding

### 🔍 Code Intelligence & MCP Servers
- **Fast code search** - Find functions, classes, and patterns instantly across any codebase
- **MCP server integration** - Two powerful Claude Code workspace tools:
  - **code-search**: Search symbols, content, and files using indexed database
  - **code-review**: AI-powered code review using Google Gemini with usage tracking
- **Cross-workspace support** - MCP servers work from any directory once installed
- **Real-time indexing** - Automatic code discovery and cataloging
- **Pattern matching** - Find similar implementations with wildcards
- **Comprehensive MCP testing** - Automated test suite for MCP server verification

### 🚫 Duplicate Prevention System
- **AI-powered similarity detection** - Prevents creation of duplicate code using semantic embeddings
- **Real-time code analysis** - Checks new code against existing codebase before creation
- **Workspace-specific isolation** - Each project maintains its own similarity database
- **Smart threshold detection** - 70%+ similarity triggers protective blocking
- **Pre-commit integration** - Automatically prevents duplicate code from being committed
- **Override capability** - TOTP-based override system for legitimate similar code

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

# For Claude Code CLI (cross-workspace setup)
./install-mcp-central.sh
claude mcp add code-search ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-search/server.py
claude mcp add code-review ~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-review/server.py

# Test MCP server connection
claude --debug -p 'hello world'
# Look for: "MCP server 'code-search': Connected successfully"
#           "MCP server 'code-review': Connected successfully"

# Verify servers are registered (CLI only)
claude mcp list

# Manual server testing (for debugging)
~/.claude/mcp/central/venv/bin/python ~/.claude/mcp/central/code-search/server.py
```

**Available MCP servers:**
- **code-search**: Search symbols, content, and files across any workspace
  - Tools: `search_code`, `list_symbols`, `get_search_stats`
  - Requirements: Code index database (`.code_index.db`)
- **code-review**: AI-powered comprehensive code review with Google Gemini
  - Tools: `review_code` with focus areas, model selection, and usage tracking
  - Requirements: `GEMINI_API_KEY` environment variable

**Key Features:**
- **Cross-workspace support**: Work from any directory once installed
- **Protocol compliance**: Uses MCP 2024-11-05 standard
- **Comprehensive logging**: Debug logs in `~/.claude/mcp/central/*/logs/`
- **Usage tracking**: Cost estimation and token counting for Gemini reviews

**Troubleshooting MCP:**
- Check connection: Run `claude --debug -p 'test'` and look for MCP messages
- Verify registration: `claude mcp list` should show both servers (CLI only)
- Check logs: `~/.claude/mcp/central/*/logs/server_*.log`
- Environment: `GEMINI_API_KEY` required for code-review server
- Reinstall: Run `./install-mcp-servers.sh` or `./install-mcp-central.sh`

**📖 Complete documentation: [`indexing/MCP_SERVER_USAGE.md`](indexing/MCP_SERVER_USAGE.md)**

### Testing
```bash
# Run all tests (includes MCP tests)
./run_tests.sh

# Run specific test suites
./run_tests.sh --indexing-only  # Indexing tests only
./run_tests.sh --mcp-only       # MCP tests only

# Quick MCP server verification (30 seconds)
./test_mcp_quick.sh

# Comprehensive MCP testing
./test_mcp_servers.py

# Standard pytest
pytest                           # All tests
pytest -m unit                   # Unit tests only
pytest -m integration            # Integration tests only
pytest -m "not slow"             # Skip slow tests
pytest tests/test_mcp_integration.py -v  # MCP integration tests
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

## 🚫 Duplicate Prevention System Setup

The duplicate prevention system uses AI-powered semantic similarity detection to prevent creation of duplicate code. It integrates with Claude Code to block creation of files that are too similar to existing code.

### Prerequisites

1. **Docker and Docker Compose** (for Qdrant vector database)
   ```bash
   # Check if Docker is installed
   docker --version
   docker-compose --version
   ```

2. **Python virtual environment activated**
   ```bash
   source venv/bin/activate
   ```

### Installation Instructions

1. **Start the Qdrant vector database**:
   ```bash
   cd duplicate_prevention
   docker-compose up -d

   # Verify it's running
   curl http://localhost:6333/health
   ```

2. **Install the duplicate prevention hook**:
   ```bash
   # This is already done by safe_install.sh, but can be run separately:
   ./hooks/install-hooks-python-only.sh
   ```

3. **Initialize your workspace collection**:
   ```bash
   # The system automatically creates a workspace-specific collection
   # Collection name format: {workspace_name}_duplicate_prevention
   ```

### Configuration

The duplicate prevention system can be configured in `hooks/python/guards/duplicate_prevention_guard.py`:

- **Similarity threshold**: Default 70% (0.70)
- **Minimum file size**: Default 5 lines
- **Supported languages**: Python, JavaScript, TypeScript, Java, C++, C, Go, Rust

### How It Works

1. **Real-time analysis**: When you create/edit code files, the guard:
   - Generates semantic embeddings of your code
   - Compares against all existing code in the workspace
   - Blocks creation if similarity exceeds threshold

2. **Workspace isolation**: Each project maintains its own vector database collection
   - No cross-contamination between projects
   - Automatic workspace detection
   - Clean separation of concerns

3. **Smart detection**: Uses advanced AI models to understand code semantics
   - Detects similar logic even with different variable names
   - Understands code structure and patterns
   - Language-aware processing

### Usage Example

When the system detects duplicate code, you'll see:
```
🚨 DUPLICATE CODE BLOCKED: Similar code already exists!

📍 DUPLICATE LOCATIONS FOUND:
  1. 85% similar code in: /home/user/project/utils/math_helpers.py
     Similarity score: 0.852

❌ WHY THIS IS BLOCKED:
  Creating duplicate code leads to maintenance issues, bugs, and inconsistency.

✅ RECOMMENDED ACTIONS:
  1. Edit the existing similar file to add your functionality
  2. Extract common code into a shared utility function
  3. Refactor both implementations to use shared components

🔓 TO OVERRIDE THIS BLOCK:
  If you believe this is genuinely different functionality:
  1. Ask for an override code from the human operator
  2. Re-run with: HOOK_OVERRIDE_CODE=<code> <your command>
```

### Testing the System

```bash
# Run duplicate prevention tests
cd hooks/python
pytest tests/test_duplicate_prevention_guard.py -v

# Test with a sample file
echo 'def calculate_distance(x1, y1, x2, y2):
    return ((x2-x1)**2 + (y2-y1)**2)**0.5' > test_function.py

# Try creating a similar function - should be blocked
echo 'def compute_distance(a, b, c, d):
    return ((c-a)**2 + (d-b)**2)**0.5' > similar_function.py
```

### Troubleshooting

**Qdrant not running**:
```bash
cd duplicate_prevention
docker-compose down
docker-compose up -d
docker-compose logs
```

**Collection issues**:
```bash
# Check collections
curl http://localhost:6333/collections

# Check specific collection
curl http://localhost:6333/collections/{workspace_name}_duplicate_prevention
```

**Guard not triggering**:
- Ensure hooks are installed: `ls ~/.claude/hooks/`
- Check logs: `tail -f ~/.claude/logs/*`
- Verify file size meets minimum (5 lines)
- Ensure file extension is supported

### Cross-Workspace Setup

To enable duplicate prevention in other workspaces:

1. **Copy the duplicate prevention directory**:
   ```bash
   cp -r /path/to/claude_template/duplicate_prevention /path/to/new/workspace/
   ```

2. **Start Qdrant in the new workspace**:
   ```bash
   cd /path/to/new/workspace/duplicate_prevention
   docker-compose up -d
   ```

3. **Install hooks (if not already global)**:
   ```bash
   cd /path/to/new/workspace
   ./safe_install.sh  # Or copy from claude_template
   ```

The system will automatically create a new collection for the workspace!

### Quick Setup Prompt for Other Workspaces

Copy and paste this prompt when working in a new workspace:

```
I want to enable the duplicate prevention system from claude_template in this workspace. Please:

1. Copy the duplicate_prevention directory from claude_template to this workspace
2. Start the Qdrant database using docker-compose
3. Verify the setup is working
4. The system should automatically create a workspace-specific collection

The duplicate prevention guard is already installed globally via safe_install.sh, so it should work once Qdrant is running.
```

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
