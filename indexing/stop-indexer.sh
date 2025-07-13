#!/usr/bin/env bash
# Stop the code indexer Docker container

set -e

# Get the absolute path to the indexing directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get the parent directory name for the project
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Generate the same unique project name
PROJECT_HASH=$(echo "$PROJECT_DIR" | sha256sum | cut -c1-8)
COMPOSE_PROJECT_NAME="${PROJECT_NAME}-${PROJECT_HASH}"

echo "Stopping code indexer for: $PROJECT_DIR"

# Stop the indexer
export COMPOSE_PROJECT_NAME
docker -c default compose down

echo "✅ Code indexer stopped"
