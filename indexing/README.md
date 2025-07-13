# Code Indexing Tools

Fast code search and indexing for the Spotidal project.

## 🐳 Docker Quick Start (Recommended)

The easiest way to keep the index automatically updated is using Docker:

```bash
# Start the indexer (runs in background)
cd indexing
./start-indexer.sh

# Stop the indexer
./stop-indexer.sh

# View logs
docker compose logs -f
```

The Docker setup:

- ✅ Automatically watches for file changes
- ✅ Updates the index in real-time
- ✅ Runs health checks every 30 seconds
- ✅ Restarts automatically if it crashes
- ✅ Creates unique container names for multiple repos
- ✅ Runs completely locally (no musicbot required)

## 🔍 Search Examples

Once the indexer is running, search for code symbols:

### 🤖 For AI Assistants (Recommended - JSON Output)

```bash
# Find exact matches
python3 claude_code_search.py search 'CodeIndexer'
python3 claude_code_search.py search 'get_metadata'

# Find by type
python3 claude_code_search.py list_type 'class'     # All classes
python3 claude_code_search.py list_type 'function'  # All functions

# File-specific searches
python3 claude_code_search.py file_symbols "/app/indexing/code_indexer.py"
python3 claude_code_search.py search_file "spotidal*" "*handler*"
```

### 👤 For Human Users (Interactive)

```bash
# Find exact matches
python3 search_code.py CodeIndexer
python3 search_code.py get_metadata

# Wildcard searches
python3 search_code.py 'get_*' -t function     # Functions starting with get_
python3 search_code.py '*handler*'             # All symbols containing 'handler'
python3 search_code.py 'search_*' -t method    # Methods starting with search_

# Browse by type
python3 search_code.py --list-classes -l 10    # Show first 10 classes
python3 search_code.py --list-functions -l 20  # Show first 20 functions

# File-specific searches
python3 search_code.py --file-symbols "/app/indexing/code_indexer.py"
python3 search_code.py -f "spotidal*" "*handler*"

# Show documentation
python3 search_code.py 'CodeIndexer' --show-docstrings
```

## Manual Setup

```bash
# From fresh clone:
./indexing/setup.sh

# Search for code:
./indexing/search get_metadata
```

See [INDEXING.md](INDEXING.md) for full documentation.
