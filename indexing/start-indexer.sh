#!/usr/bin/env bash
# Start the code indexer in Docker
# Automatically generates unique container names based on the directory

set -e

# Get the absolute path to the indexing directory
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
# Convert first 4 chars of hash to decimal and add to base port 9900
PORT_OFFSET=$((0x${PROJECT_HASH:0:4} % 1000))
INDEXER_PORT=$((9900 + PORT_OFFSET))

echo "Starting code indexer for: $PROJECT_DIR"
echo "Container name: indexer-${COMPOSE_PROJECT_NAME}"
echo "Port: ${INDEXER_PORT}"

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
    echo "✅ Code indexer started successfully!"
    echo ""
    echo "Container: indexer-${COMPOSE_PROJECT_NAME}"
    echo "Health check: http://localhost:${INDEXER_PORT}/health"
    echo "Index database: ${PROJECT_DIR}/.code_index.db"
    echo ""
    echo "To view logs: docker -c default compose logs -f"
    echo "To stop: ./stop-indexer.sh"
else
    echo "❌ Failed to start code indexer"
    docker -c default compose logs
    exit 1
fi
