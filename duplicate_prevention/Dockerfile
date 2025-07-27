# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for indexer code
WORKDIR /indexer

# Copy only the indexer and necessary code
COPY duplicate_prevention/ /indexer/duplicate_prevention/
COPY scripts/index_repository.py /indexer/scripts/

# Install Python dependencies
RUN pip install --no-cache-dir -r /indexer/duplicate_prevention/requirements.txt

# Set Python path to include indexer paths
ENV PYTHONPATH=/indexer:/indexer/duplicate_prevention:/indexer/scripts

# Create directory for workspace mount
RUN mkdir -p /workspace

# Create non-root user
RUN useradd -m -u 1000 indexer
USER indexer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:9999/health')" || exit 1

# Default command - run indexer from its own location
CMD ["python3", "/indexer/duplicate_prevention/watch_and_index.py"]
