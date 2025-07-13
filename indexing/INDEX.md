# Code Indexing System Index

This directory contains the **AI-powered code search and indexing system** for the Spotidal repository.

## 📋 Purpose

Provides fast, intelligent code search capabilities optimized for AI assistants (like Claude) to navigate and understand the codebase efficiently.

## 📁 Files

### Core Indexing Components

- **`code_indexer.py`** - Main AST-based Python code parser and symbol extractor
- **`code_indexer_treesitter.py`** - Alternative tree-sitter based parser (experimental)
- **`watch_and_index.py`** - File watcher service that automatically updates the index

### Search Interfaces

- **`search_code.py`** - Human-friendly command-line search interface
- **`claude_code_search.py`** - AI-optimized JSON API for code search
- **`search`** - Symlink to search_code.py for convenience

### Docker Deployment

- **`Dockerfile`** - Container definition for the indexing service
- **`docker-compose.yml`** - Service orchestration configuration
- **`start-indexer.sh`** - Script to start the containerized indexer with unique naming
- **`stop-indexer.sh`** - Script to stop the running indexer container

### Setup & Configuration

- **`setup.sh`** - Basic setup script for dependencies
- **`setup_code_indexing.sh`** - Comprehensive setup for the indexing system
- **`spotidal-indexer.service`** - Systemd service definition (optional)

### Documentation

- **`README.md`** - User guide for the code indexing system
- **`INDEXING.md`** - Technical details and AI integration guide
- **`INDEX.md`** - This file

## 🏗️ Architecture

The indexing system:

1. **Parses Python files** using AST to extract symbols (classes, functions, methods)
2. **Stores symbols** in a SQLite database (`.code_index.db`) for fast lookups
3. **Watches for changes** using watchdog library to keep index current
4. **Provides search APIs** optimized for both humans and AI assistants
5. **Runs in Docker** for consistent deployment across environments

## 🚀 Usage

### Quick Start

```bash
# Start the Docker indexer
cd indexing
./start-indexer.sh

# Search for code
./search_code.py --list-classes -l 10
./claude_code_search.py search "DatabaseService"
```

### AI Integration

The `claude_code_search.py` script provides JSON output optimized for AI consumption:

```bash
python3 claude_code_search.py search "function_name"
python3 claude_code_search.py list_type "class"
python3 claude_code_search.py file_symbols "path/to/file.py"
```

## 📊 Capabilities

- **Symbol Types**: Classes, functions, methods with full signatures
- **Search Modes**: Name search, type filtering, file-specific queries
- **Output Formats**: Human-readable or JSON for AI processing
- **Auto-updating**: File watcher keeps index current
- **Performance**: Sub-second searches across entire codebase
