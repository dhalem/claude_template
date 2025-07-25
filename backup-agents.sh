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
# CLAUDE AGENTS BACKUP SCRIPT
# ============================================================================
#
# This script backs up ONLY the agents directory from ~/.claude to the
# local claude-agents-backup directory for version control with git.
#
# What this script does:
# 1. Checks if ~/.claude/agents directory exists
# 2. Copies ~/.claude/agents to ./claude-agents-backup/
# 3. Preserves file permissions and timestamps
# 4. Provides clear status feedback
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

# Critical directories
CLAUDE_DIR="$HOME/.claude"
AGENTS_SOURCE="$CLAUDE_DIR/agents"
BACKUP_TARGET="./claude-agents-backup"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}                        CLAUDE AGENTS BACKUP                                ${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# STEP 1: VALIDATE SOURCE DIRECTORY
# ============================================================================
echo -e "${BLUE}Step 1: Checking source directory...${NC}"

if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo -e "${RED}ERROR: Claude directory not found at $CLAUDE_DIR${NC}"
    echo -e "${YELLOW}Have you installed Claude yet?${NC}"
    exit 1
fi

if [[ ! -d "$AGENTS_SOURCE" ]]; then
    echo -e "${RED}ERROR: Agents directory not found at $AGENTS_SOURCE${NC}"
    echo -e "${YELLOW}No agents to backup.${NC}"
    exit 1
fi

AGENT_COUNT=$(find "$AGENTS_SOURCE" -type f -name "*.py" | wc -l)
SOURCE_SIZE=$(du -sh "$AGENTS_SOURCE" | cut -f1)
echo -e "${GREEN}✓ Found agents directory ($SOURCE_SIZE, $AGENT_COUNT Python files)${NC}"

# ============================================================================
# STEP 2: PREPARE BACKUP TARGET
# ============================================================================
echo ""
echo -e "${BLUE}Step 2: Preparing backup target...${NC}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_TARGET"

# If backup target has existing content, show what will be overwritten
if [[ -d "$BACKUP_TARGET" ]] && [[ -n "$(ls -A "$BACKUP_TARGET" 2>/dev/null)" ]]; then
    EXISTING_COUNT=$(find "$BACKUP_TARGET" -type f -name "*.py" | wc -l)
    echo -e "${YELLOW}⚠️  Existing backup found ($EXISTING_COUNT Python files)${NC}"
    echo -e "${YELLOW}This will be overwritten. Continue? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Backup cancelled by user.${NC}"
        exit 0
    fi

    # Clear existing backup
    rm -rf "$BACKUP_TARGET"/*
fi

echo -e "${GREEN}✓ Backup target prepared${NC}"

# ============================================================================
# STEP 3: BACKUP AGENTS
# ============================================================================
echo ""
echo -e "${BLUE}Step 3: Backing up agents...${NC}"

echo -e "${YELLOW}Copying $AGENTS_SOURCE to $BACKUP_TARGET...${NC}"

# Copy agents directory contents (not the directory itself)
cp -r "$AGENTS_SOURCE"/* "$BACKUP_TARGET/"

# Verify backup
if [[ -d "$BACKUP_TARGET" ]] && [[ -n "$(ls -A "$BACKUP_TARGET" 2>/dev/null)" ]]; then
    BACKUP_COUNT=$(find "$BACKUP_TARGET" -type f -name "*.py" | wc -l)
    BACKUP_SIZE=$(du -sh "$BACKUP_TARGET" | cut -f1)
    echo -e "${GREEN}✓ Backup completed successfully ($BACKUP_SIZE, $BACKUP_COUNT Python files)${NC}"
    echo -e "${GREEN}  Location: $BACKUP_TARGET${NC}"
else
    echo -e "${RED}ERROR: Backup failed!${NC}"
    exit 1
fi

# ============================================================================
# BACKUP COMPLETE
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}                        BACKUP COMPLETE!                                   ${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${CYAN}What was backed up:${NC}"
echo "  ✓ Agents from $AGENTS_SOURCE"
echo "  ✓ Saved to $BACKUP_TARGET"
echo "  ✓ $BACKUP_COUNT Python files ($BACKUP_SIZE total)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Add changes to git: git add claude-agents-backup/"
echo "  2. Commit changes: git commit -m 'backup: update Claude agents'"
echo "  3. Push to remote: git push"
echo ""
echo -e "${GREEN}Your Claude agents are now backed up for version control!${NC}"
