# Experimental Code

This directory contains experimental implementations that are not currently in use.

## code_indexer_treesitter.py

An alternative implementation of the code indexer using tree-sitter instead of Python's AST module.

**Status**: Complete but not integrated
**Why not used**: The AST-based indexer in `code_indexer.py` is currently sufficient and is already integrated with the watch system.

### Potential advantages of tree-sitter version:
- Can parse files with syntax errors
- Supports multiple languages (not just Python)
- More detailed parsing information

### To integrate tree-sitter version:
1. Update `watch_and_index.py` to import from `experimental.code_indexer_treesitter`
2. Update Docker image to include tree-sitter dependencies
3. Test thoroughly to ensure compatibility
