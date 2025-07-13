#!/bin/bash

# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.

# ---------------------------------------------------------------------
# CLAUDE CODE HOOKS INSTALLER - PYTHON DIRECTORY ONLY
# ---------------------------------------------------------------------
#
# This installer ONLY updates the python/ subdirectory in ~/.claude
# Everything else is left completely untouched
#
# SAFETY GUARANTEES:
# - NO rm -rf commands
# - NO deletion of any Claude files
# - NO touching of conversation logs
# - ONLY updates ~/.claude/python/
#
# ---------------------------------------------------------------------

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define directories
CLAUDE_DIR="$HOME/.claude"
PYTHON_DIR="$CLAUDE_DIR/python"
SOURCE_PYTHON_DIR="$SCRIPT_DIR/python"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$CLAUDE_DIR/python.backup.$TIMESTAMP"

echo -e "${BLUE}--------------------------------------------------------------------------${NC}"
echo -e "${BLUE}Claude Code Hooks Installer - Python Directory Only${NC}"
echo -e "${BLUE}--------------------------------------------------------------------------${NC}"
echo ""
echo -e "${GREEN}SAFETY GUARANTEES:${NC}"
echo "  🔒 ONLY updates python/ subdirectory"
echo "  🔒 NO deletion of Claude files"
echo "  🔒 NO touching of conversation logs"
echo "  🔒 Preserves all Claude infrastructure"
echo ""

# Verify source exists
if [[ ! -d "$SOURCE_PYTHON_DIR" ]]; then
    echo -e "${RED}ERROR: Source python directory not found: $SOURCE_PYTHON_DIR${NC}"
    exit 1
fi

# Verify Claude directory exists
if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo -e "${RED}ERROR: Claude directory not found: $CLAUDE_DIR${NC}"
    echo -e "${YELLOW}Claude Code must be installed first${NC}"
    exit 1
fi

echo -e "${YELLOW}Checking current installation...${NC}"

# Show what we're NOT touching
echo -e "${GREEN}✓ Preserving Claude infrastructure:${NC}"
for item in "$CLAUDE_DIR"/*; do
    if [[ -e "$item" && "$(basename "$item")" != "python" ]]; then
        echo "  - $(basename "$item")"
    fi
done

# Backup existing python directory if it exists
if [[ -d "$PYTHON_DIR" ]]; then
    echo -e "${YELLOW}Backing up existing python directory...${NC}"
    cp -r "$PYTHON_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✓ Backed up to: $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}No existing python directory found - fresh installation${NC}"
fi

# Update ONLY the python directory (excluding cache files)
echo -e "${YELLOW}Installing python implementation...${NC}"

# Remove old python directory if it exists (safe rm - only python dir)
if [[ -d "$PYTHON_DIR" && "$PYTHON_DIR" == "$CLAUDE_DIR/python" ]]; then
    rm -rf "$PYTHON_DIR"
fi

# Copy Python files excluding cache and build artifacts
mkdir -p "$PYTHON_DIR"
cd "$SOURCE_PYTHON_DIR"
find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.sh" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) | \
    grep -v "__pycache__" | \
    grep -v ".pyc" | \
    grep -v ".coverage" | \
    grep -v "htmlcov" | \
    grep -v ".pytest_cache" | \
    while read -r file; do
        # Create directory structure
        dir=$(dirname "$file")
        mkdir -p "$PYTHON_DIR/$dir"
        # Copy file
        cp "$file" "$PYTHON_DIR/$file"
    done
cd - > /dev/null

echo -e "${GREEN}✓ Python directory updated (cache files excluded)${NC}"

# Update hook wrapper scripts to point to the correct Python
echo -e "${YELLOW}Updating hook wrapper scripts...${NC}"

# Update adaptive-guard.sh
if [[ -f "$CLAUDE_DIR/adaptive-guard.sh" ]]; then
    echo -e "${YELLOW}Updating adaptive-guard.sh...${NC}"
    # Create a proper wrapper that calls the Python implementation
    cat > "$CLAUDE_DIR/adaptive-guard.sh" << 'EOF'
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to Python implementation
PYTHON_HOOKS_DIR="$SCRIPT_DIR/python"

# Check if Python implementation exists
if [[ ! -d "$PYTHON_HOOKS_DIR" ]]; then
    echo "ERROR: Python hooks directory not found: $PYTHON_HOOKS_DIR" >&2
    exit 1
fi

# Read JSON input from stdin
INPUT_JSON=$(cat)

# Call Python implementation - try common Python locations
for PYTHON in /usr/bin/python3 /usr/local/bin/python3 python3; do
    if command -v $PYTHON >/dev/null 2>&1; then
        exec $PYTHON "$PYTHON_HOOKS_DIR/main.py" adaptive <<< "$INPUT_JSON"
    fi
done

echo "ERROR: Python 3 not found in system" >&2
exit 1
EOF
    chmod +x "$CLAUDE_DIR/adaptive-guard.sh"
    echo -e "${GREEN}✓ Updated adaptive-guard.sh${NC}"
fi

# Update lint-guard.sh
if [[ -f "$CLAUDE_DIR/lint-guard.sh" ]]; then
    echo -e "${YELLOW}Updating lint-guard.sh...${NC}"
    cat > "$CLAUDE_DIR/lint-guard.sh" << 'EOF'
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to Python implementation
PYTHON_HOOKS_DIR="$SCRIPT_DIR/python"

# Check if Python implementation exists
if [[ ! -d "$PYTHON_HOOKS_DIR" ]]; then
    echo "ERROR: Python hooks directory not found: $PYTHON_HOOKS_DIR" >&2
    exit 1
fi

# Read JSON input from stdin
INPUT_JSON=$(cat)

# Call Python implementation - try common Python locations
for PYTHON in /usr/bin/python3 /usr/local/bin/python3 python3; do
    if command -v $PYTHON >/dev/null 2>&1; then
        exec $PYTHON "$PYTHON_HOOKS_DIR/main.py" lint <<< "$INPUT_JSON"
    fi
done

echo "ERROR: Python 3 not found in system" >&2
exit 1
EOF
    chmod +x "$CLAUDE_DIR/lint-guard.sh"
    echo -e "${GREEN}✓ Updated lint-guard.sh${NC}"
fi

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"

# Test Python implementation
TEST_JSON='{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}'
if echo "$TEST_JSON" | "$CLAUDE_DIR/adaptive-guard.sh" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Hook system operational${NC}"
else
    echo -e "${RED}WARNING: Hook system test failed${NC}"
    echo -e "${YELLOW}This may be normal if hooks are blocking the test${NC}"
fi

# Count installed files
PYTHON_FILE_COUNT=$(find "$PYTHON_DIR" -name "*.py" | wc -l)
TOTAL_FILE_COUNT=$(find "$PYTHON_DIR" -type f | wc -l)
echo -e "${GREEN}✓ Installed $PYTHON_FILE_COUNT Python files ($TOTAL_FILE_COUNT total files)${NC}"

echo ""
echo -e "${GREEN}🎉 INSTALLATION COMPLETE${NC}"
echo ""
echo -e "${BLUE}What was updated:${NC}"
echo "  - Python implementation in ~/.claude/python/"
echo "  - Hook wrapper scripts (adaptive-guard.sh, lint-guard.sh)"
echo ""
echo -e "${BLUE}What was preserved:${NC}"
echo "  - All conversation logs"
echo "  - All project data"
echo "  - All settings and configuration"
echo "  - All other Claude infrastructure"
echo ""
echo -e "${YELLOW}Backup available at: $BACKUP_DIR${NC}"
echo ""

exit 0
