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
# CLAUDE AGENTS RESTORE SCRIPT
# ============================================================================
#
# This script safely restores agents from the local backup to ~/.claude/agents
# following the same safety patterns as safe_install.sh.
#
# What this script does:
# 1. Creates timestamped backup of ENTIRE ~/.claude directory (safety)
# 2. Restores ONLY the agents directory from ./claude-agents-backup
# 3. Preserves file permissions and timestamps
# 4. Provides rollback instructions if something goes wrong
#
# SAFETY FIRST: This script creates a full backup before making ANY changes
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
AGENTS_TARGET="$CLAUDE_DIR/agents"
BACKUP_SOURCE="./claude-agents-backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFETY_BACKUP="$HOME/.claude_backup_$TIMESTAMP"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}                        CLAUDE AGENTS RESTORE                               ${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${CYAN}This script will safely restore your Claude agents.${NC}"
echo -e "${CYAN}A full backup will be created before making ANY changes.${NC}"
echo ""

# ============================================================================
# SAFETY CHECK: Warn user about what we're doing
# ============================================================================
echo -e "${YELLOW}⚠️  IMPORTANT: This script will:${NC}"
echo "  1. Back up your ENTIRE .claude directory to $SAFETY_BACKUP"
echo "  2. Restore agents from $BACKUP_SOURCE to $AGENTS_TARGET"
echo "  3. ONLY touch the agents directory (everything else stays safe)"
echo ""
echo -e "${YELLOW}Do you want to continue? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Restore cancelled by user.${NC}"
    exit 0
fi

# ============================================================================
# STEP 1: VALIDATE BACKUP SOURCE
# ============================================================================
echo ""
echo -e "${BLUE}Step 1: Validating backup source...${NC}"

if [[ ! -d "$BACKUP_SOURCE" ]]; then
    echo -e "${RED}ERROR: Backup source not found at $BACKUP_SOURCE${NC}"
    echo -e "${YELLOW}Run ./backup-agents.sh first to create a backup.${NC}"
    exit 1
fi

if [[ ! -n "$(ls -A "$BACKUP_SOURCE" 2>/dev/null)" ]]; then
    echo -e "${RED}ERROR: Backup source is empty at $BACKUP_SOURCE${NC}"
    echo -e "${YELLOW}Run ./backup-agents.sh first to create a backup.${NC}"
    exit 1
fi

BACKUP_COUNT=$(find "$BACKUP_SOURCE" -type f -name "*.py" | wc -l)
BACKUP_SIZE=$(du -sh "$BACKUP_SOURCE" | cut -f1)
echo -e "${GREEN}✓ Found backup source ($BACKUP_SIZE, $BACKUP_COUNT Python files)${NC}"

# ============================================================================
# STEP 2: MANDATORY SAFETY BACKUP OF ENTIRE .claude DIRECTORY
# ============================================================================
echo ""
echo -e "${BLUE}Step 2: Creating safety backup of entire .claude directory...${NC}"

if [[ -d "$CLAUDE_DIR" ]]; then
    echo -e "${YELLOW}Backing up $CLAUDE_DIR to $SAFETY_BACKUP...${NC}"
    cp -r "$CLAUDE_DIR" "$SAFETY_BACKUP"

    # Verify safety backup
    if [[ -d "$SAFETY_BACKUP" ]]; then
        SAFETY_SIZE=$(du -sh "$SAFETY_BACKUP" | cut -f1)
        echo -e "${GREEN}✓ Safety backup created successfully ($SAFETY_SIZE)${NC}"
        echo -e "${GREEN}  Location: $SAFETY_BACKUP${NC}"
    else
        echo -e "${RED}ERROR: Safety backup failed! Aborting restore.${NC}"
        exit 1
    fi
else
    echo -e "${RED}ERROR: Claude directory not found at $CLAUDE_DIR${NC}"
    echo -e "${YELLOW}Install Claude first before restoring agents.${NC}"
    exit 1
fi

# ============================================================================
# STEP 3: PREPARE AGENTS TARGET DIRECTORY
# ============================================================================
echo ""
echo -e "${BLUE}Step 3: Preparing agents target directory...${NC}"

# Create agents directory if it doesn't exist
mkdir -p "$AGENTS_TARGET"

# If agents directory has existing content, show what will be overwritten
if [[ -d "$AGENTS_TARGET" ]] && [[ -n "$(ls -A "$AGENTS_TARGET" 2>/dev/null)" ]]; then
    EXISTING_COUNT=$(find "$AGENTS_TARGET" -type f -name "*.py" | wc -l)
    EXISTING_SIZE=$(du -sh "$AGENTS_TARGET" | cut -f1)
    echo -e "${YELLOW}⚠️  Existing agents found ($EXISTING_SIZE, $EXISTING_COUNT Python files)${NC}"
    echo -e "${YELLOW}These will be replaced. Continue? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Restore cancelled by user.${NC}"
        echo -e "${CYAN}Your safety backup remains at: $SAFETY_BACKUP${NC}"
        exit 0
    fi

    # Clear existing agents
    rm -rf "$AGENTS_TARGET"/*
fi

echo -e "${GREEN}✓ Agents target directory prepared${NC}"

# ============================================================================
# STEP 4: RESTORE AGENTS
# ============================================================================
echo ""
echo -e "${BLUE}Step 4: Restoring agents...${NC}"

echo -e "${YELLOW}Copying $BACKUP_SOURCE to $AGENTS_TARGET...${NC}"

# Copy backup contents to agents directory
cp -r "$BACKUP_SOURCE"/* "$AGENTS_TARGET/"

# Verify restore
if [[ -d "$AGENTS_TARGET" ]] && [[ -n "$(ls -A "$AGENTS_TARGET" 2>/dev/null)" ]]; then
    RESTORED_COUNT=$(find "$AGENTS_TARGET" -type f -name "*.py" | wc -l)
    RESTORED_SIZE=$(du -sh "$AGENTS_TARGET" | cut -f1)
    echo -e "${GREEN}✓ Restore completed successfully ($RESTORED_SIZE, $RESTORED_COUNT Python files)${NC}"
    echo -e "${GREEN}  Location: $AGENTS_TARGET${NC}"
else
    echo -e "${RED}ERROR: Restore failed!${NC}"
    echo -e "${YELLOW}To rollback:${NC}"
    echo "  rm -rf $CLAUDE_DIR"
    echo "  mv $SAFETY_BACKUP $CLAUDE_DIR"
    exit 1
fi

# ============================================================================
# RESTORE COMPLETE
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}                        RESTORE COMPLETE!                                  ${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${CYAN}What was restored:${NC}"
echo "  ✓ Agents from $BACKUP_SOURCE"
echo "  ✓ Restored to $AGENTS_TARGET"
echo "  ✓ $RESTORED_COUNT Python files ($RESTORED_SIZE total)"
echo ""
echo -e "${CYAN}Safety backup location:${NC}"
echo "  $SAFETY_BACKUP"
echo ""
echo -e "${YELLOW}Important notes:${NC}"
echo "  1. Only the agents directory was modified"
echo "  2. All other Claude configuration remains unchanged"
echo "  3. Restart Claude Code to load the restored agents"
echo ""
echo -e "${YELLOW}If something went wrong, you can rollback:${NC}"
echo "  rm -rf $CLAUDE_DIR"
echo "  mv $SAFETY_BACKUP $CLAUDE_DIR"
echo ""
echo -e "${GREEN}Your Claude agents have been successfully restored!${NC}"
