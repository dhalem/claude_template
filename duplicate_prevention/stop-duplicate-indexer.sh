#!/usr/bin/env bash
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Stop the duplicate prevention indexer Docker container

set -euo pipefail

# Get the absolute path to the duplicate_prevention directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get the parent directory name for the project
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Generate the same unique project name used when starting
PROJECT_HASH=$(echo "$PROJECT_DIR" | sha256sum | cut -c1-8)
COMPOSE_PROJECT_NAME="${PROJECT_NAME}-${PROJECT_HASH}"

echo "Stopping duplicate prevention indexer for: $PROJECT_DIR"
echo "Container name: duplicate-indexer-${COMPOSE_PROJECT_NAME}"

# Stop the services
export COMPOSE_PROJECT_NAME
docker -c default compose down

echo "✅ Duplicate prevention indexer stopped"
