#!/bin/bash

# --------------------------------------------------------------------------
# CLAUDE CODE SAFETY HOOKS INSTALLER - PYTHON ENHANCED VERSION
# --------------------------------------------------------------------------
#
# This script installs the comprehensive safety hook system for Claude Code.
# It enforces critical rules from CLAUDE.md to prevent costly mistakes.
#
# WHAT THIS INSTALLS:
# - ~/.claude/adaptive-guard.sh (main safety guard - Python wrapper)
# - ~/.claude/lint-guard.sh (linting guard - Python wrapper)
# - ~/.claude/python/ (Python implementation directory)
# - ~/.claude/settings.json (hook configuration)
# - Backup of existing settings (if any)
#
# PYTHON MIGRATION:
# - Shell scripts are now wrappers that call Python implementations
# - Python provides enhanced functionality, better error handling, comprehensive testing
# - Original shell implementations archived for reference
#
# USAGE:
#   cd hooks
#   ./install-hooks.sh
#
# --------------------------------------------------------------------------

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}--------------------------------------------------------------------------${NC}"
echo -e "${BLUE}Claude Code Safety Hooks Installation (Python Enhanced)${NC}"
echo -e "${BLUE}--------------------------------------------------------------------------${NC}"
echo ""

# Validate prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}ERROR: jq is required but not installed.${NC}"
    echo ""
    echo "Install jq:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  macOS: brew install jq"
    echo "  RHEL/CentOS: sudo yum install jq"
    echo ""
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is required but not installed.${NC}"
    echo ""
    echo "Install Python 3:"
    echo "  Ubuntu/Debian: sudo apt-get install python3"
    echo "  macOS: brew install python3"
    echo "  RHEL/CentOS: sudo yum install python3"
    echo ""
    exit 1
fi

# Check Python version (require 3.7+)
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 7 ]]; then
    echo -e "${RED}ERROR: Python 3.7+ is required, found Python $PYTHON_VERSION${NC}"
    echo ""
    echo "Please upgrade Python to version 3.7 or higher."
    exit 1
fi

# Check if source files exist
REQUIRED_FILES=("settings.json" "HOOKS.md" "python/main.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$SCRIPT_DIR/$file" ]] && [[ ! -d "$SCRIPT_DIR/$(dirname "$file")" ]]; then
        echo -e "${RED}ERROR: Required file/directory missing: $file${NC}"
        echo "Ensure you're running this script from the hooks directory with all files present."
        exit 1
    fi
done

# Check wrapper scripts exist
WRAPPER_SCRIPTS=("adaptive-guard.sh" "lint-guard.sh")
for script in "${WRAPPER_SCRIPTS[@]}"; do
    if [[ ! -f "$SCRIPT_DIR/$script" ]]; then
        echo -e "${RED}ERROR: Required wrapper script missing: $script${NC}"
        echo "Ensure the Python wrapper scripts have been created."
        exit 1
    fi
done

# Check Python implementation structure
PYTHON_FILES=("python/main.py" "python/base_guard.py" "python/registry.py")
for file in "${PYTHON_FILES[@]}"; do
    if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
        echo -e "${RED}ERROR: Required Python file missing: $file${NC}"
        echo "Ensure the Python implementation is complete."
        exit 1
    fi
done

echo -e "${GREEN}✓ Prerequisites validated${NC}"
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
echo -e "${GREEN}✓ Python implementation structure verified${NC}"
echo ""

# Create Claude config directory if it doesn't exist
CLAUDE_DIR="$HOME/.claude"
echo -e "${YELLOW}Setting up Claude configuration directory...${NC}"

if [[ ! -d "$CLAUDE_DIR" ]]; then
    mkdir -p "$CLAUDE_DIR"
    echo -e "${GREEN}✓ Created $CLAUDE_DIR${NC}"
else
    echo -e "${GREEN}✓ $CLAUDE_DIR already exists${NC}"
fi

# Backup existing settings if they exist
if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
    BACKUP_FILE="$CLAUDE_DIR/settings.json.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CLAUDE_DIR/settings.json" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backed up existing settings to: $BACKUP_FILE${NC}"
fi

# Function to install a hook file with backup
install_hook() {
    local filename="$1"
    local source_file="$SCRIPT_DIR/$filename"
    local dest_file="$CLAUDE_DIR/$filename"

    if [[ ! -f "$source_file" ]]; then
        echo -e "${YELLOW}⚠️  Skipping $filename (not found in source)${NC}"
        return
    fi

    if [[ -f "$dest_file" ]]; then
        BACKUP_FILE="$dest_file.backup.$(date +%Y%m%d_%H%M%S)"
        mv "$dest_file" "$BACKUP_FILE"
        echo -e "${GREEN}✓ Backed up existing $filename to: $(basename "$BACKUP_FILE")${NC}"
    fi

    cp "$source_file" "$dest_file"
    chmod +x "$dest_file"
    echo -e "${GREEN}✓ Installed: $dest_file${NC}"
}

# Function to copy Python implementation
install_python_implementation() {
    local python_dest="$CLAUDE_DIR/python"

    echo -e "${YELLOW}Installing Python implementation...${NC}"

    # Remove existing Python directory if it exists (with backup)
    if [[ -d "$python_dest" ]]; then
        BACKUP_DIR="$python_dest.backup.$(date +%Y%m%d_%H%M%S)"
        mv "$python_dest" "$BACKUP_DIR"
        echo -e "${GREEN}✓ Backed up existing Python implementation to: $(basename "$BACKUP_DIR")${NC}"
    fi

    # Copy Python implementation
    cp -r "$SCRIPT_DIR/python" "$python_dest"

    # Make main.py executable
    chmod +x "$python_dest/main.py"

    # Count Python files for reporting
    PYTHON_FILE_COUNT=$(find "$python_dest" -name "*.py" | wc -l)
    echo -e "${GREEN}✓ Installed Python implementation ($PYTHON_FILE_COUNT Python files)${NC}"

    # Test Python implementation
    if python3 "$python_dest/main.py" adaptive '{"tool_name":"Bash","tool_input":{"command":"echo test"}}' >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Python implementation test successful${NC}"
    else
        echo -e "${RED}ERROR: Python implementation test failed${NC}"
        return 1
    fi
}

# Install Python implementation first
install_python_implementation

# Install environment files if they exist
echo -e "${YELLOW}Installing environment configuration...${NC}"

# Copy main project .env if it exists
if [[ -f "$SCRIPT_DIR/../.env" ]]; then
    cp "$SCRIPT_DIR/../.env" "$CLAUDE_DIR/.env"
    chmod 600 "$CLAUDE_DIR/.env"  # Secure permissions
    echo -e "${GREEN}✓ Installed: $CLAUDE_DIR/.env (main project environment)${NC}"
else
    echo -e "${YELLOW}⚠️  No main .env file found in parent directory${NC}"
fi

# Copy hooks-specific .env if it exists
if [[ -f "$SCRIPT_DIR/python/.env" ]]; then
    cp "$SCRIPT_DIR/python/.env" "$CLAUDE_DIR/.env.hooks"
    chmod 600 "$CLAUDE_DIR/.env.hooks"  # Secure permissions
    echo -e "${GREEN}✓ Installed: $CLAUDE_DIR/.env.hooks (hooks-specific environment)${NC}"
else
    echo -e "${YELLOW}⚠️  No hooks-specific .env file found${NC}"
fi

# Install wrapper scripts (these now call Python implementation)
echo -e "${YELLOW}Installing hook wrapper scripts...${NC}"
install_hook "adaptive-guard.sh"
install_hook "lint-guard.sh"

# Install additional hook scripts if they exist
OTHER_HOOKS=("comprehensive-guard.sh" "claude-output-guard.sh" "stderr-output-guard.sh")
for hook in "${OTHER_HOOKS[@]}"; do
    if [[ -f "$SCRIPT_DIR/$hook" ]]; then
        install_hook "$hook"
    fi
done

# Install settings.json
echo -e "${YELLOW}Installing hook configuration...${NC}"
# Settings.json backup already handled above, just copy the new one
cp "$SCRIPT_DIR/settings.json" "$CLAUDE_DIR/"
echo -e "${GREEN}✓ Installed: $CLAUDE_DIR/settings.json${NC}"

# Validate JSON configuration
echo -e "${YELLOW}Validating configuration...${NC}"
if jq empty "$CLAUDE_DIR/settings.json" 2>/dev/null; then
    echo -e "${GREEN}✓ JSON configuration is valid${NC}"
else
    echo -e "${RED}ERROR: Invalid JSON in settings.json${NC}"
    exit 1
fi

# Validate script syntax for all installed wrapper scripts
echo -e "${YELLOW}Validating wrapper script syntax...${NC}"
SCRIPTS_VALID=true
for script in "$CLAUDE_DIR"/*.sh; do
    if [[ -f "$script" ]]; then
        if bash -n "$script" 2>/dev/null; then
            echo -e "${GREEN}✓ $(basename "$script") syntax is valid${NC}"
        else
            echo -e "${RED}ERROR: Syntax error in $(basename "$script")${NC}"
            SCRIPTS_VALID=false
        fi
    fi
done

if [[ "$SCRIPTS_VALID" == "false" ]]; then
    echo -e "${RED}ERROR: One or more wrapper scripts have syntax errors${NC}"
    exit 1
fi

# Test the complete hook system
echo -e "${YELLOW}Testing complete hook system...${NC}"
TEST_JSON='{"tool_name":"Bash","tool_input":{"command":"echo test"}}'

# Test adaptive guard
if echo "$TEST_JSON" | "$CLAUDE_DIR/adaptive-guard.sh" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Adaptive guard test successful${NC}"
else
    echo -e "${RED}ERROR: Adaptive guard test failed${NC}"
    exit 1
fi

# Test lint guard
if echo "$TEST_JSON" | "$CLAUDE_DIR/lint-guard.sh" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Lint guard test successful${NC}"
else
    echo -e "${RED}ERROR: Lint guard test failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}--------------------------------------------------------------------------${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${BLUE}--------------------------------------------------------------------------${NC}"
echo ""

# Show what was installed
echo -e "${YELLOW}Installed Files:${NC}"
echo "  🐍 $CLAUDE_DIR/python/ (Python implementation with $(find "$CLAUDE_DIR/python" -name "*.py" | wc -l) files)"
echo "  📜 $CLAUDE_DIR/adaptive-guard.sh ($(wc -l < "$CLAUDE_DIR/adaptive-guard.sh") lines)"
echo "  🔧 $CLAUDE_DIR/lint-guard.sh ($(wc -l < "$CLAUDE_DIR/lint-guard.sh") lines)"
echo "  ⚙️  $CLAUDE_DIR/settings.json ($(jq '.hooks | length' "$CLAUDE_DIR/settings.json") hook configurations)"
echo ""

# Show Python implementation features
echo -e "${YELLOW}Python Implementation Features:${NC}"
echo "  🎯 Enhanced accuracy (fixes Git force push logic bugs)"
echo "  🛡️  Comprehensive safety guards (12+ guard types)"
echo "  🔧 Advanced auto-fixing (Python, JSON, YAML, JS/TS, CSS)"
echo "  🧪 Extensive testing (500+ test cases)"
echo "  ⚡ Better performance and error handling"
echo ""

# Show installed guards
echo -e "${YELLOW}Active Safety Guards:${NC}"
if jq -e '._documentation.guards_implemented' "$CLAUDE_DIR/settings.json" >/dev/null 2>&1; then
    jq -r '._documentation.guards_implemented[]' "$CLAUDE_DIR/settings.json" | while IFS= read -r guard; do
        echo "  🛡️  $guard"
    done
else
    echo "  🛡️  Git No-Verify Prevention"
    echo "  🛡️  Docker Restart Prevention"
    echo "  🛡️  Git Force Push Prevention"
    echo "  🛡️  Mock Code Prevention"
    echo "  🛡️  Pre-commit Config Protection"
    echo "  🛡️  Hook Installation Protection"
    echo "  🛡️  Directory Awareness"
    echo "  🛡️  Test Suite Enforcement"
    echo "  🛡️  Container Rebuild Reminders"
    echo "  🛡️  Database Schema Reminders"
    echo "  🛡️  Temp File Location Guidance"
    echo "  🔧 Code Linting & Auto-fixing"
fi
echo ""

# Show next steps
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. ✅ Hooks are now active and will trigger automatically"
echo "  2. 🧪 Test the installation: cd $(basename "$SCRIPT_DIR") && ./test-python-wrappers.sh"
echo "  3. 📖 Read the documentation: cat $(basename "$SCRIPT_DIR")/HOOKS.md"
echo "  4. 🔧 View Python implementation: ls -la $CLAUDE_DIR/python/"
echo ""

# Show verification commands
echo -e "${YELLOW}Verification Commands:${NC}"
echo "  Check installation:     ls -la $CLAUDE_DIR/"
echo "  Test JSON config:       jq . $CLAUDE_DIR/settings.json"
echo "  Test wrapper syntax:    bash -n $CLAUDE_DIR/adaptive-guard.sh"
echo "  Test Python hooks:      python3 $CLAUDE_DIR/python/main.py adaptive '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"echo test\"}}'"
echo ""

echo -e "${GREEN}The enhanced Claude Code safety hook system (Python-powered) is now protecting your workflow!${NC}"
echo ""

# Show warning about what hooks will do
echo -e "${YELLOW}⚠️  IMPORTANT: These hooks will now actively prevent dangerous operations:${NC}"
echo "  • git commit --no-verify (requires permission)"
echo "  • docker restart commands (suggests proper rebuild)"
echo "  • Location-dependent commands without pwd verification"
echo "  • Completion claims without test suite execution"
echo "  • Creation of mock/simulation code (requires permission)"
echo "  • Modification of .pre-commit-config.yaml (requires permission)"
echo "  • Auto-fixes code style issues (Python, JSON, YAML, JS/TS, CSS)"
echo ""
echo -e "${BLUE}These protections exist because these mistakes have caused real harm in the past.${NC}"
echo -e "${BLUE}The Python implementation provides enhanced protection with better accuracy.${NC}"
echo ""

# Show backup management info
echo -e "${YELLOW}Backup Management:${NC}"
BACKUP_COUNT=$(find "$CLAUDE_DIR" -name "*.backup.*" 2>/dev/null | wc -l)
if [[ $BACKUP_COUNT -gt 0 ]]; then
    echo "  📦 Found $BACKUP_COUNT backup file(s) in $CLAUDE_DIR"
    echo "  To list backups: ls -la $CLAUDE_DIR/*.backup.*"
    echo "  To clean old backups: find $CLAUDE_DIR -name '*.backup.*' -mtime +7 -delete"
else
    echo "  📦 No backup files found"
fi
echo ""

# Show migration information
echo -e "${YELLOW}Migration Information:${NC}"
echo "  🔄 Shell scripts now call Python implementations"
echo "  📁 Original shell scripts archived in: $SCRIPT_DIR/archive/shell_originals/"
echo "  🐍 Python implementation location: $CLAUDE_DIR/python/"
echo "  📊 Test coverage: 500+ test cases with parallel validation"
echo "  🎯 Bug fixes: Corrected Git force push logic and exit code consistency"
echo ""

exit 0
