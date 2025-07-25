#!/usr/bin/env python3
"""Code search interface designed for Claude Code to use.

Provides structured output that's easy to parse.
"""

import json
import os
import sys
from typing import Any, Dict

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from code_searcher import CodeSearcher


class ClaudeCodeSearcher:
    """Search interface for Claude Code."""

    def __init__(self):
        """Initialize the Claude Code searcher."""
        self.searcher = CodeSearcher()

    def search(self, query: str, search_type: str = "name", **kwargs) -> Dict[str, Any]:
        """Unified search interface that returns structured JSON.

        Args:
            query: Search query
            search_type: One of "name", "file", "type", "file_symbols"
            **kwargs: Additional parameters like limit, symbol_type, etc.
        """
        try:
            if search_type == "name":
                results = self.searcher.search_by_name(
                    query, symbol_type=kwargs.get("symbol_type"), limit=kwargs.get("limit", 20)
                )
            elif search_type == "file":
                results = self.searcher.search_by_file(query, limit=kwargs.get("limit", 50))
            elif search_type == "type":
                results = self.searcher.search_by_type(query, limit=kwargs.get("limit", 50))
            elif search_type == "file_symbols":
                results = self.searcher.get_file_symbols(query)
            else:
                return {"success": False, "error": f"Unknown search type: {search_type}", "results": []}

            # The searcher methods return a dict with "success", "results", etc.
            if not results.get("success"):
                return {"success": False, "error": results.get("error", "Search failed"), "results": []}

            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "count": results.get("count", len(results.get("results", []))),
                "results": results.get("results", []),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "results": []}


def main():
    """CLI interface for Claude Code."""
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Usage: claude_code_search.py <command> [args]",
                    "commands": {
                        "search": "Search by symbol name",
                        "search_file": "Search in specific files",
                        "list_type": "List all symbols of a type",
                        "file_symbols": "Get all symbols in a file",
                    },
                },
                indent=2,
            )
        )
        sys.exit(1)

    command = sys.argv[1]
    searcher = ClaudeCodeSearcher()

    if command == "search" and len(sys.argv) >= 3:
        query = sys.argv[2]
        symbol_type = sys.argv[3] if len(sys.argv) > 3 else None
        result = searcher.search(query, "name", symbol_type=symbol_type)

    elif command == "search_file" and len(sys.argv) >= 3:
        file_pattern = sys.argv[2]
        name_pattern = sys.argv[3] if len(sys.argv) > 3 else None
        result = searcher.search(file_pattern, "file", name_pattern=name_pattern)

    elif command == "list_type" and len(sys.argv) >= 3:
        symbol_type = sys.argv[2]
        result = searcher.search(symbol_type, "type")

    elif command == "file_symbols" and len(sys.argv) >= 3:
        file_path = sys.argv[2]
        result = searcher.search(file_path, "file_symbols")

    else:
        result = {"success": False, "error": f"Unknown command or missing arguments: {command}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
