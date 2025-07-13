FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the indexing scripts
COPY . /app/indexing/

# Set the project root as working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    watchdog==3.0.0 \
    tree-sitter==0.20.2 \
    tree-sitter-languages==1.8.0

# Create volume mount point for the codebase
VOLUME ["/app"]

# Expose healthcheck port
EXPOSE 9999

# Default to running the watcher
CMD ["python3", "-u", "indexing/watch_and_index.py"]
