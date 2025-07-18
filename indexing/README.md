# Code Indexing and Review System

Fast AI-powered code search, indexing, and review system for intelligent code navigation and analysis.

## 🚀 Quick Start

### Docker Setup (Recommended)
```bash
# Start the indexer (runs in background)
cd indexing
./start-indexer.sh

# Stop the indexer
./stop-indexer.sh

# View logs
docker compose logs -f
```

### Manual Setup
```bash
# Install dependencies
./setup_code_indexing.sh

# Build initial index
python3 code_indexer.py

# Search for code
python3 search_code.py get_metadata
```

## 📋 Components

### Core Indexing
- **`code_indexer.py`** - AST-based Python parser and symbol extractor
- **`watch_and_index.py`** - File watcher for automatic index updates
- **`search_code.py`** - Human-friendly search interface
- **`claude_code_search.py`** - AI-optimized JSON API

### Code Review (MCP Server)
- **`mcp_review_server.py`** - MCP server for AI-powered code reviews
- **`src/`** - Review system components (file collection, Gemini client, formatting)
- **`install_mcp_code_review.sh`** - Installation script for MCP integration

### Configuration
- **`requirements.txt`** - Pinned dependencies for reproducible builds
- **`docker-compose.yml`** - Container orchestration
- **`Dockerfile`** - Containerized indexing service

## 🔧 Installation

### Prerequisites
- Python 3.11+
- Docker (for containerized deployment)
- Virtual environment recommended

### Dependencies
The system uses pinned dependencies defined in `requirements.txt`:
- `mcp` - Model Context Protocol integration
- `google-generativeai` - Gemini API for code reviews
- `watchdog` - File system monitoring
- `tree-sitter` - Alternative parsing backend

### MCP Code Review Server
Install the code review server for Claude integration:
```bash
cd indexing
./install_mcp_code_review.sh
```

The server will be installed to `~/.claude/mcp/code-review/` and can be used via:
```
mcp__code-review__review_code
```

## 🎯 Usage

### Search Examples
```bash
# Find functions by name
python3 search_code.py get_metadata

# Search with wildcards
python3 search_code.py "play*"

# Find classes
python3 search_code.py --type class Player

# Search in specific files
python3 search_code.py --file "sonos_server" connect
```

### AI-Optimized Search
```bash
# JSON output for AI consumption
python3 claude_code_search.py search "authentication methods"
python3 claude_code_search.py list_types
python3 claude_code_search.py list_files
```

### Docker Operations
```bash
# Check indexer status
docker compose ps

# Rebuild index from scratch
docker compose down
docker compose up -d --build

# Monitor resource usage
docker compose stats
```

## 🔒 Security

### Dependencies
- All dependencies are pinned to specific versions in `requirements.txt`
- Regular security updates recommended
- Virtual environment isolation enforced

### Shell Scripts
- All scripts use `set -euo pipefail` for strict error handling
- Variables properly quoted to prevent injection
- Input validation for file paths and project names

## 🏗️ Architecture

### Index Storage
- SQLite database (`.code_index.db`) for fast queries
- AST-based symbol extraction for accurate parsing
- Incremental updates via file watching

### Docker Integration
- Unique container names per project directory
- Automatic port allocation to prevent conflicts
- Persistent index storage outside containers

### MCP Integration
- Standard Model Context Protocol compliance
- Local module copying to avoid path manipulation
- Structured error handling and logging

## 📚 API Reference

### Search Functions
- `search(query, file_filter=None, type_filter=None)` - Main search interface
- `list_types()` - Enumerate all symbol types in index
- `list_files()` - Show indexed files with metadata

### Review Functions
- `review_code(directory, focus_areas=[], model="gemini-2.5-pro")` - Comprehensive code review
- File filtering by size and type
- Token usage tracking and cost estimation

## 🔧 Troubleshooting

### Common Issues
1. **Index not updating**: Check file watcher service status
2. **Import errors**: Ensure virtual environment is activated
3. **Docker conflicts**: Use unique project names via `start-indexer.sh`
4. **MCP server fails**: Check logs in `~/.claude/mcp/code-review/logs/`

### Performance
- Index size scales with codebase complexity
- Docker resources auto-configured based on project hash
- Consider excluding large directories via `.gitignore` patterns

---

This system provides the foundation for intelligent code navigation and AI-assisted development workflows.
