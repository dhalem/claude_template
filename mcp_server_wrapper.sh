#!/bin/bash
# MCP Server Wrapper - ensures proper venv usage

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$DIR")"

# Log startup
LOG_FILE="$PARENT_DIR/logs/wrapper.log"
mkdir -p "$PARENT_DIR/logs"
echo "[$(date)] Starting wrapper: $0 $*" >> "$LOG_FILE"
echo "[$(date)] DIR=$DIR" >> "$LOG_FILE"
echo "[$(date)] PARENT_DIR=$PARENT_DIR" >> "$LOG_FILE"
echo "[$(date)] PWD=$PWD" >> "$LOG_FILE"

# Activate venv and run the actual Python server
if [ -f "$PARENT_DIR/venv/bin/activate" ]; then
    echo "[$(date)] Activating venv at $PARENT_DIR/venv" >> "$LOG_FILE"
    source "$PARENT_DIR/venv/bin/activate"
    echo "[$(date)] Python: $(which python)" >> "$LOG_FILE"
    echo "[$(date)] Executing: python $DIR/server_actual.py" >> "$LOG_FILE"
    exec python "$DIR/server_actual.py"
else
    echo "[$(date)] ERROR: No venv found at $PARENT_DIR/venv" >> "$LOG_FILE"
    # Try to use system python with the actual server
    exec python3 "$DIR/server_actual.py"
fi
