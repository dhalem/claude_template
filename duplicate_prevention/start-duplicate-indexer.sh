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

# Start the duplicate prevention indexer in Docker
# Automatically generates unique container names based on the directory

set -euo pipefail

# Get the absolute path to the duplicate_prevention directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get the parent directory name for the project
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Generate a unique project name based on the full path
# This ensures multiple checkouts don't conflict
PROJECT_HASH=$(echo "$PROJECT_DIR" | sha256sum | cut -c1-8)
COMPOSE_PROJECT_NAME="${PROJECT_NAME}-${PROJECT_HASH}"

# Generate a unique port based on the project hash
# Convert first 4 chars of hash to decimal and add to base port 9998
PORT_OFFSET=$((0x${PROJECT_HASH:0:4} % 1000))
INDEXER_PORT=$((9998 + PORT_OFFSET))

echo "Starting duplicate prevention indexer for: $PROJECT_DIR"
echo "Container name: duplicate-indexer-${COMPOSE_PROJECT_NAME}"
echo "Port: ${INDEXER_PORT}"

# Get absolute path to workspace (parent of duplicate_prevention directory)
WORKSPACE_PATH=$(cd "$SCRIPT_DIR/.." && pwd)
export WORKSPACE_PATH

# Build and start the indexer
export COMPOSE_PROJECT_NAME
export INDEXER_PORT
USER_ID=$(id -u)
GROUP_ID=$(id -g)
export USER_ID
export GROUP_ID
docker -c default compose up -d --build

# Check if it started successfully
if docker -c default compose ps | grep -q "running"; then
    echo "✅ Duplicate prevention indexer started successfully!"
    echo ""
    echo "Container: duplicate-indexer-${COMPOSE_PROJECT_NAME}"
    echo "Health check: http://localhost:${INDEXER_PORT}/health"
    echo "Qdrant service: http://localhost:6333"
    echo ""
    echo "To view logs: docker -c default compose logs -f duplicate-prevention-indexer"
    echo "To stop: ./stop-duplicate-indexer.sh"
else
    echo "❌ Failed to start duplicate prevention indexer"
    docker -c default compose logs
    exit 1
fi
