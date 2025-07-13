# Code Indexing System

This directory contains a fast code indexing and search system for the Spotidal project.
It provides instant function/class/method search across the entire codebase using an AST-based Python parser with SQLite storage.

## Quick Start (Fresh Clone)

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/spotidal.git
cd spotidal

# 2. Run setup (builds initial index)
./indexing/setup.sh

# 3. Search for code!
python3 indexing/search_code.py get_metadata
```

## Features

- **Fast Search**: Instant symbol lookup using SQLite FTS
- **AST-Based**: Accurate parsing of Python code structure
- **Automatic Updates**: File watcher keeps index current
- **Wildcard Support**: Search patterns like `get_*` or `*_handler`
- **Type Filtering**: Search only functions, classes, or methods
- **Zero Dependencies**: Uses only Python stdlib (watchdog optional)

## Components

### 1. **code_indexer.py** - The Indexer

Parses Python files using AST (Abstract Syntax Tree) to extract:

- Functions and their signatures
- Classes and their methods
- Docstrings and documentation
- Line numbers for quick navigation

### 2. **search_code.py** - User Search Tool

Interactive search with features:

- Wildcard patterns (`*` and `?`)
- Type filtering (`-t function|class|method`)
- List all symbols of a type
- Show symbols in specific files

### 3. **claude_code_search.py** - AI Integration

JSON-based interface for Claude Code to search programmatically.

### 4. **watch_and_index.py** - Auto-Update Daemon

Monitors file changes and updates index automatically:

- Uses watchdog library if available
- Falls back to periodic scanning
- Updates on create/modify/delete

## Usage Examples

### Basic Search

```bash
# Find exact function name
python3 indexing/search_code.py get_metadata

# Wildcard search
python3 indexing/search_code.py "get_*"              # Functions starting with get_
python3 indexing/search_code.py "*_handler"          # All handlers
python3 indexing/search_code.py "get_artist*"        # get_artist, get_artists, etc.
```

### Type-Specific Search

```bash
# Only functions
python3 indexing/search_code.py "process_*" -t function

# Only classes
python3 indexing/search_code.py "*Service" -t class

# List all classes
python3 indexing/search_code.py --list-classes

# List all functions (limit 50)
python3 indexing/search_code.py --list-functions -l 50
```

### File-Specific Search

```bash
# All symbols in a file
python3 indexing/search_code.py --file-symbols sonos_server/services/database.py

# Search within files matching pattern
python3 indexing/search_code.py -f "database" "*"
```

### Advanced Search

```bash
# Show docstrings in results
python3 indexing/search_code.py DatabaseService --show-docstrings

# Increase result limit
python3 indexing/search_code.py "test_*" -l 100

# Complex searches with examples from real codebase
python3 indexing/search_code.py 'search_*' -t method  # Find all search methods
python3 indexing/search_code.py '*Service' -t class   # Find all service classes
python3 indexing/search_code.py 'get_*' -t function   # Find getter functions
```

## 🚀 Quick Reference & Examples

Based on the current Spotidal codebase, here are practical search examples:

### Finding Core Components

```bash
# Database services
python3 search_code.py 'DatabaseService' --show-docstrings
python3 search_code.py '*database*' -t class

# API endpoints
python3 search_code.py '*api*' -t function
python3 search_code.py 'search_*' -t method

# Workers and background tasks
python3 search_code.py '*Worker' -t class
python3 search_code.py '*worker*' -f "syncer*"
```

### Debugging and Development

```bash
# Find test files and methods
python3 search_code.py 'test_*' -t function -l 50
python3 search_code.py --file-symbols "tests/test_something.py"

# Explore specific modules
python3 search_code.py --file-symbols "/app/sonos_server/services/database.py"
python3 search_code.py -f "indexing*" "*"

# Find configuration and setup
python3 search_code.py '*config*' -t class
python3 search_code.py 'setup*' -t function
```

### Browse by Architecture Layer

```bash
# Services layer
python3 search_code.py '*Service' -t class -l 20

# Models and data structures
python3 search_code.py '*Model' -t class
python3 search_code.py 'Album' -t class

# Utilities and helpers
python3 search_code.py 'get_*' -t function -l 30
python3 search_code.py '*_util*'
```

## Maintaining the Index

### Manual Update

```bash
# Rebuild entire index
python3 indexing/code_indexer.py

# Keep index updated automatically
python3 indexing/watch_and_index.py
```

### Automatic Updates

The watcher monitors the entire repository including:

- All Python files in the repository root
- All subdirectories including `archive/`
- Real-time updates on file changes
- Excludes `__pycache__` and `venv` directories

## Technical Details

### Database Schema

The index uses SQLite with this structure:

```sql
symbols (
    name TEXT,
    type TEXT,           -- function, class, method
    file_path TEXT,
    line_number INTEGER,
    parent TEXT,         -- Parent class for methods
    signature TEXT,      -- Function parameters
    docstring TEXT
)
```

### Search Algorithm

1. Converts wildcards to SQL LIKE patterns
2. Prioritizes exact matches
3. Orders by symbol type (classes > functions > methods)
4. Returns results with file:line format

### Performance

- Initial indexing: ~1-2 seconds for entire codebase
- Search queries: <10ms for most patterns
- Database size: ~2-5MB for typical project

## Integration with Editors

### VS Code

Add to `settings.json`:

```json
{
    "terminal.integrated.env.linux": {
        "SPOTIDAL_INDEX": "${workspaceFolder}/.code_index.db"
    }
}
```

### Vim

Add to `.vimrc`:

```vim
command! -nargs=1 CodeSearch :!python3 indexing/search_code.py <args>
nnoremap <leader>cs :CodeSearch
```

## Troubleshooting

### "Index database not found"

Run `python3 indexing/code_indexer.py` to build the index.

### "No results found"

- Check spelling and try wildcards
- Ensure the file containing the symbol is in an indexed directory
- Rebuild index if files were added recently

### Slow searches

- Vacuum the database: `sqlite3 .code_index.db 'VACUUM;'`
- Limit search scope with type filters
- Use more specific patterns

## 🤖 For AI Assistants (Recommended Interface)

**AI assistants should use `claude_code_search.py` for structured JSON output:**

```bash
# Search for symbols (returns structured JSON)
python3 indexing/claude_code_search.py search "pattern"
python3 indexing/claude_code_search.py search "get_*" function  # With type filter

# List all symbols of a type
python3 indexing/claude_code_search.py list_type "class"
python3 indexing/claude_code_search.py list_type "function"

# Explore specific files
python3 indexing/claude_code_search.py file_symbols "path/to/file.py"

# Search within files
python3 indexing/claude_code_search.py search_file "sonos_server*" "handler"
```

**JSON Output Structure:**

```json
{
  "success": true,
  "query": "search_term",
  "count": 5,
  "results": [
    {
      "name": "function_name",
      "type": "function",
      "file_path": "/app/path/to/file.py",
      "line_number": 42,
      "column": 4,
      "parent": null,
      "signature": "(self, param1, param2)",
      "docstring": "Function description...",
      "location": "/app/path/to/file.py:42"
    }
  ]
}
```

**Benefits for AI:**

- ✅ Structured JSON output for programmatic processing
- ✅ Consistent data format across all search types
- ✅ Error handling with `success` field
- ✅ Ready-to-parse symbol information
- ✅ Location strings for direct file navigation

## 👤 For Human Users

Interactive search with `search_code.py` provides formatted output for reading.
