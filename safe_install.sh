#!/bin/bash

# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# ============================================================================
# SAFE CLAUDE TEMPLATE INSTALLER - THE ONLY INSTALL SCRIPT YOU SHOULD USE
# ============================================================================
#
# This is the ONLY install script that should exist in this project.
# DO NOT CREATE MORE INSTALL SCRIPTS. USE THIS ONE.
#
# What this script does:
# 1. BACKS UP the entire .claude directory with timestamp
# 2. Installs hooks safely (python-only approach)
# 3. Installs MCP servers to central location
# 4. Configures Claude Desktop and CLI properly
# 5. Can rollback if anything goes wrong
#
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Critical directories
CLAUDE_DIR="$HOME/.claude"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/.claude_backup_$TIMESTAMP"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}                    SAFE CLAUDE TEMPLATE INSTALLER                          ${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${CYAN}This is the ONLY install script you should use.${NC}"
echo -e "${CYAN}DO NOT CREATE MORE INSTALL SCRIPTS.${NC}"
echo ""

# ============================================================================
# SAFETY CHECK: Warn user about what we're doing
# ============================================================================
echo -e "${YELLOW}⚠️  IMPORTANT: This script will:${NC}"
echo "  1. Back up your entire .claude directory to $BACKUP_DIR"
echo "  2. Install hooks to $CLAUDE_DIR/python/ and $CLAUDE_DIR/guards/"
echo "  3. Install MCP servers to $CLAUDE_DIR/mcp/central/"
echo "  4. Update Claude configuration files"
echo ""
echo -e "${YELLOW}Do you want to continue? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Installation cancelled by user.${NC}"
    exit 0
fi

# ============================================================================
# STEP 1: MANDATORY BACKUP OF .claude DIRECTORY
# ============================================================================
echo ""
echo -e "${BLUE}Step 1: Creating backup of .claude directory...${NC}"

if [[ -d "$CLAUDE_DIR" ]]; then
    echo -e "${YELLOW}Backing up $CLAUDE_DIR to $BACKUP_DIR...${NC}"
    cp -r "$CLAUDE_DIR" "$BACKUP_DIR"

    # Verify backup
    if [[ -d "$BACKUP_DIR" ]]; then
        BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
        echo -e "${GREEN}✓ Backup created successfully ($BACKUP_SIZE)${NC}"
        echo -e "${GREEN}  Location: $BACKUP_DIR${NC}"
    else
        echo -e "${RED}ERROR: Backup failed! Aborting installation.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}No existing .claude directory found - skipping backup${NC}"
    mkdir -p "$CLAUDE_DIR"
fi

# ============================================================================
# STEP 2: VALIDATE PREREQUISITES
# ============================================================================
echo ""
echo -e "${BLUE}Step 2: Validating prerequisites...${NC}"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is required but not installed.${NC}"
    echo "Install Python 3 and try again."
    exit 1
fi

# Check Python version (require 3.7+)
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 7 ]]; then
    echo -e "${RED}ERROR: Python 3.7+ is required, found Python $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Check jq for JSON manipulation
if ! command -v jq &> /dev/null; then
    echo -e "${RED}ERROR: jq is required but not installed.${NC}"
    echo "Install jq:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  macOS: brew install jq"
    exit 1
fi

echo -e "${GREEN}✓ jq is installed${NC}"

# Verify source directories exist
REQUIRED_DIRS=("hooks" "hooks/python" "indexing")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
        echo -e "${RED}ERROR: Required directory missing: $dir${NC}"
        echo "Ensure you're running this from the project root."
        exit 1
    fi
done

echo -e "${GREEN}✓ All required directories found${NC}"

# ============================================================================
# STEP 3: INSTALL HOOKS (Python-only safe approach)
# ============================================================================
echo ""
echo -e "${BLUE}Step 3: Installing hooks...${NC}"

# Create necessary directories
mkdir -p "$CLAUDE_DIR/python"
mkdir -p "$CLAUDE_DIR/guards"

# Copy Python implementation
echo -e "${YELLOW}Installing Python hook implementation...${NC}"
cp -r "$SCRIPT_DIR/hooks/python/"* "$CLAUDE_DIR/python/"

# Copy wrapper scripts and Discord Stop hook
for script in adaptive-guard.sh lint-guard.sh discord-stop-hook.py; do
    if [[ -f "$SCRIPT_DIR/hooks/$script" ]]; then
        cp "$SCRIPT_DIR/hooks/$script" "$CLAUDE_DIR/$script"
        chmod +x "$CLAUDE_DIR/$script"
        echo -e "${GREEN}✓ Installed $script${NC}"
    fi
done

# Copy protection guards
for guard in test-script-integrity-guard.sh precommit-protection-guard.sh anti-bypass-pattern-guard.py; do
    if [[ -f "$SCRIPT_DIR/hooks/$guard" ]]; then
        cp "$SCRIPT_DIR/hooks/$guard" "$CLAUDE_DIR/guards/$guard"
        chmod +x "$CLAUDE_DIR/guards/$guard"
        echo -e "${GREEN}✓ Installed $guard${NC}"
    fi
done

# Copy settings.json
if [[ -f "$SCRIPT_DIR/hooks/settings.json" ]]; then
    cp "$SCRIPT_DIR/hooks/settings.json" "$CLAUDE_DIR/settings.json"
    echo -e "${GREEN}✓ Installed settings.json${NC}"
fi

# Test hook functionality
echo -e "${YELLOW}Testing hook system...${NC}"
TEST_JSON='{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}'
if echo "$TEST_JSON" | "$CLAUDE_DIR/adaptive-guard.sh" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Hook system operational${NC}"
else
    echo -e "${RED}WARNING: Hook test failed - continuing anyway${NC}"
fi

# ============================================================================
# STEP 4: INSTALL MCP SERVERS
# ============================================================================
echo ""
echo -e "${BLUE}Step 4: Installing MCP servers...${NC}"

# Create MCP directories
CENTRAL_DIR="$CLAUDE_DIR/mcp/central"
mkdir -p "$CENTRAL_DIR/code-search"
mkdir -p "$CENTRAL_DIR/code-review"

# Copy MCP servers
echo -e "${YELLOW}Installing code-search server...${NC}"
cp "$SCRIPT_DIR/indexing/mcp_search_server.py" "$CENTRAL_DIR/code-search/server.py"
cp -r "$SCRIPT_DIR/indexing/src" "$CENTRAL_DIR/code-search/"
chmod +x "$CENTRAL_DIR/code-search/server.py"
echo -e "${GREEN}✓ code-search server installed${NC}"

echo -e "${YELLOW}Installing code-review server...${NC}"
cp "$SCRIPT_DIR/indexing/mcp_review_server.py" "$CENTRAL_DIR/code-review/server.py"
cp -r "$SCRIPT_DIR/indexing/src" "$CENTRAL_DIR/code-review/"
chmod +x "$CENTRAL_DIR/code-review/server.py"
echo -e "${GREEN}✓ code-review server installed${NC}"

# Create Python virtual environment for MCP
echo -e "${YELLOW}Setting up Python environment for MCP...${NC}"
cd "$CENTRAL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip >/dev/null 2>&1
pip install -r "$SCRIPT_DIR/indexing/requirements.txt" >/dev/null 2>&1
deactivate
cd "$SCRIPT_DIR"
echo -e "${GREEN}✓ MCP Python environment ready${NC}"

# ============================================================================
# STEP 5: CONFIGURE CLAUDE
# ============================================================================
echo ""
echo -e "${BLUE}Step 5: Configuring Claude...${NC}"

# Configure Claude Desktop if config directory exists
CONFIG_DIR="$HOME/.config/claude"
if [[ -d "$CONFIG_DIR" ]]; then
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

    # Backup existing config
    if [[ -f "$CONFIG_FILE" ]]; then
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$TIMESTAMP"
        echo -e "${GREEN}✓ Backed up existing Claude Desktop config${NC}"
    fi

    # Write new configuration
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "code-search": {
      "command": "$HOME/.claude/mcp/central/venv/bin/python",
      "args": ["$HOME/.claude/mcp/central/code-search/server.py"],
      "env": {
        "PYTHONPATH": "$HOME/.claude/mcp/central/code-search"
      }
    },
    "code-review": {
      "command": "$HOME/.claude/mcp/central/venv/bin/python",
      "args": ["$HOME/.claude/mcp/central/code-review/server.py"],
      "env": {
        "PYTHONPATH": "$HOME/.claude/mcp/central/code-review"
      }
    }
  }
}
EOF
    echo -e "${GREEN}✓ Claude Desktop configured${NC}"
fi

# Configure Claude CLI if available
if command -v claude &> /dev/null; then
    echo -e "${YELLOW}Registering MCP servers with Claude CLI...${NC}"

    # Clean up any existing registrations
    for server in code-search code-review; do
        claude mcp remove "$server" -s user 2>/dev/null || true
        claude mcp remove "$server" -s project 2>/dev/null || true
    done

    # Add new registrations
    claude mcp add code-search "$HOME/.claude/mcp/central/venv/bin/python" "$HOME/.claude/mcp/central/code-search/server.py" -s user
    claude mcp add code-review "$HOME/.claude/mcp/central/venv/bin/python" "$HOME/.claude/mcp/central/code-review/server.py" -s user

    echo -e "${GREEN}✓ MCP servers registered with Claude CLI${NC}"
fi

# ============================================================================
# STEP 6: CREATE/UPDATE PROJECT .mcp.json
# ============================================================================
echo ""
echo -e "${BLUE}Step 6: Creating project MCP configuration...${NC}"

MCP_CONFIG="$SCRIPT_DIR/.mcp.json"
cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
    "code-search": {
      "command": "$HOME/.claude/mcp/central/venv/bin/python",
      "args": ["$HOME/.claude/mcp/central/code-search/server.py"],
      "env": {
        "PYTHONPATH": "$HOME/.claude/mcp/central/code-search"
      }
    },
    "code-review": {
      "command": "$HOME/.claude/mcp/central/venv/bin/python",
      "args": ["$HOME/.claude/mcp/central/code-review/server.py"],
      "env": {
        "PYTHONPATH": "$HOME/.claude/mcp/central/code-review"
      }
    }
  }
}
EOF
echo -e "${GREEN}✓ Created .mcp.json for project${NC}"

# ============================================================================
# INSTALLATION COMPLETE
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}                      INSTALLATION COMPLETE!                                ${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${CYAN}What was installed:${NC}"
echo "  ✓ Hooks in $CLAUDE_DIR/python/ and $CLAUDE_DIR/guards/"
echo "  ✓ MCP servers in $CLAUDE_DIR/mcp/central/"
echo "  ✓ Configuration files updated"
echo "  ✓ Project .mcp.json created"
echo ""
echo -e "${CYAN}Backup location:${NC}"
echo "  $BACKUP_DIR"
echo ""
echo -e "${YELLOW}Important notes:${NC}"
echo "  1. Restart Claude Code to load the new configuration"
echo "  2. For code-review server: export GEMINI_API_KEY='your-key'"
echo "  3. Use this script for ALL installations - DO NOT create more install scripts"
echo ""
echo -e "${YELLOW}To restore from backup if needed:${NC}"
echo "  rm -rf $CLAUDE_DIR"
echo "  mv $BACKUP_DIR $CLAUDE_DIR"
echo ""
echo -e "${GREEN}The Claude template is now safely installed!${NC}"
