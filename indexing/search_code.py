#!/usr/bin/env python3
"""
Code search interface using the Tree-sitter index
Provides fast function/symbol search across the codebase
"""

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class SearchResult:
    name: str
    type: str
    file_path: str
    line_number: int
    column: int
    parent: Optional[str]
    signature: Optional[str]
    docstring: Optional[str]
    score: float = 1.0

    def format(self, show_signature: bool = True, show_docstring: bool = False) -> str:
        """Format the search result for display"""
        location = f"{self.file_path}:{self.line_number}"

        if self.parent:
            full_name = f"{self.parent}.{self.name}"
        else:
            full_name = self.name

        result = f"{location} - {self.type} {full_name}"

        if show_signature and self.signature:
            result += f"\n    {self.name}{self.signature}"

        if show_docstring and self.docstring:
            # Truncate long docstrings
            doc = self.docstring.strip()
            if doc.startswith('"""') and doc.endswith('"""') or doc.startswith("'''") and doc.endswith("'''"):
                doc = doc[3:-3].strip()
            if len(doc) > 80:
                doc = doc[:77] + "..."
            result += f"\n    {doc}"

        return result


class CodeSearcher:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to parent directory of indexing/
            project_root = Path(__file__).parent.parent.resolve()
            self.db_path = project_root / ".code_index.db"
        else:
            self.db_path = Path(db_path)
        if not self.db_path.exists():
            print(f"❌ Error: Index database not found at {self.db_path}")
            print()
            print("🔍 The code indexing system is not set up for this repository.")
            print()
            print("📚 To enable fast code search, run the following commands:")
            print()
            print("   # 🐳 Recommended: Start Docker indexer (automatic updates)")
            print("   cd indexing")
            print("   ./start-indexer.sh")
            print()
            print("   # 📖 Manual: Build index once")
            print("   python3 indexing/code_indexer.py")
            print()
            print("🚀 The Docker indexer will:")
            print("   ✅ Watch for file changes automatically")
            print("   ✅ Update the index in real-time")
            print("   ✅ Run health checks every 30 seconds")
            print("   ✅ Create unique container names for multiple repos")
            print("   ✅ Run completely locally (no remote dependencies)")
            print()
            print("📋 After setup, you can search with:")
            print("   # 🤖 For AI assistants (JSON output):")
            print("   python3 indexing/claude_code_search.py search 'function_name'")
            print("   python3 indexing/claude_code_search.py list_type 'class'")
            print("   python3 indexing/claude_code_search.py file_symbols 'path/to/file.py'")
            print("   # 👤 For human users (formatted output):")
            print("   python3 indexing/search_code.py 'function_name'")
            print("   python3 indexing/search_code.py 'get_*' -t function")
            print("   python3 indexing/search_code.py --list-classes")
            print()
            sys.exit(1)

    def search_by_name(self, query: str, symbol_type: Optional[str] = None, limit: int = 20) -> List[SearchResult]:
        """Search for symbols by name (supports wildcards)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Convert query to SQL LIKE pattern
        sql_pattern = query.replace("*", "%").replace("?", "_")

        if symbol_type:
            cursor.execute(
                """
                SELECT name, type, file_path, line_number, column, parent, signature, docstring
                FROM symbols
                WHERE name LIKE ? AND type = ?
                ORDER BY
                    CASE WHEN name = ? THEN 0 ELSE 1 END,
                    length(name),
                    name
                LIMIT ?
            """,
                (sql_pattern, symbol_type, query, limit),
            )
        else:
            cursor.execute(
                """
                SELECT name, type, file_path, line_number, column, parent, signature, docstring
                FROM symbols
                WHERE name LIKE ?
                ORDER BY
                    CASE WHEN name = ? THEN 0 ELSE 1 END,
                    CASE type
                        WHEN 'class' THEN 0
                        WHEN 'function' THEN 1
                        WHEN 'method' THEN 2
                        ELSE 3
                    END,
                    length(name),
                    name
                LIMIT ?
            """,
                (sql_pattern, query, limit),
            )

        results = []
        for row in cursor.fetchall():
            results.append(SearchResult(*row))

        conn.close()
        return results

    def search_in_file(self, file_pattern: str, name_pattern: Optional[str] = None) -> List[SearchResult]:
        """Search for symbols in specific files"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        file_sql_pattern = file_pattern.replace("*", "%").replace("?", "_")

        if name_pattern:
            name_sql_pattern = name_pattern.replace("*", "%").replace("?", "_")
            cursor.execute(
                """
                SELECT name, type, file_path, line_number, column, parent, signature, docstring
                FROM symbols
                WHERE file_path LIKE ? AND name LIKE ?
                ORDER BY file_path, line_number
            """,
                (f"%{file_sql_pattern}%", name_sql_pattern),
            )
        else:
            cursor.execute(
                """
                SELECT name, type, file_path, line_number, column, parent, signature, docstring
                FROM symbols
                WHERE file_path LIKE ?
                ORDER BY file_path, line_number
            """,
                (f"%{file_sql_pattern}%",),
            )

        results = []
        for row in cursor.fetchall():
            results.append(SearchResult(*row))

        conn.close()
        return results

    def find_references(self, symbol_name: str) -> List[Tuple[str, int]]:
        """Find potential references to a symbol (requires full text search)"""
        # This is a placeholder - full implementation would require
        # parsing all files and looking for uses of the symbol
        print(f"Note: Reference search not yet implemented. Use 'rg {symbol_name}' for now.")
        return []

    def get_file_symbols(self, file_path: str) -> List[SearchResult]:
        """Get all symbols in a specific file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name, type, file_path, line_number, column, parent, signature, docstring
            FROM symbols
            WHERE file_path = ?
            ORDER BY line_number
        """,
            (file_path,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(SearchResult(*row))

        conn.close()
        return results

    def search_by_type(self, symbol_type: str, limit: int = 50) -> List[SearchResult]:
        """Get all symbols of a specific type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name, type, file_path, line_number, column, parent, signature, docstring
            FROM symbols
            WHERE type = ?
            ORDER BY name
            LIMIT ?
        """,
            (symbol_type, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(SearchResult(*row))

        conn.close()
        return results


def main():
    parser = argparse.ArgumentParser(description="Search code symbols in the project")
    parser.add_argument("query", nargs="?", help="Search query (supports * and ? wildcards)")
    parser.add_argument(
        "-t", "--type", choices=["function", "class", "method", "variable"], help="Filter by symbol type"
    )
    parser.add_argument("-f", "--file", help="Search within specific file pattern")
    parser.add_argument("-l", "--limit", type=int, default=20, help="Maximum results (default: 20)")
    parser.add_argument("--show-docstrings", action="store_true", help="Show docstrings in results")
    parser.add_argument("--list-classes", action="store_true", help="List all classes")
    parser.add_argument("--list-functions", action="store_true", help="List all functions")
    parser.add_argument("--file-symbols", help="List all symbols in a specific file")

    args = parser.parse_args()

    searcher = CodeSearcher()

    if args.file_symbols:
        results = searcher.get_file_symbols(args.file_symbols)
        print(f"\nSymbols in {args.file_symbols}:")
        for result in results:
            print(f"  {result.format(show_signature=True, show_docstring=args.show_docstrings)}")

    elif args.list_classes:
        results = searcher.search_by_type("class", limit=args.limit)
        print(f"\nClasses ({len(results)} found):")
        for result in results:
            print(f"  {result.format(show_signature=False)}")

    elif args.list_functions:
        results = searcher.search_by_type("function", limit=args.limit)
        print(f"\nFunctions ({len(results)} found):")
        for result in results:
            print(f"  {result.format(show_signature=True)}")

    elif args.file and args.query:
        results = searcher.search_in_file(args.file, args.query)
        print(f"\nSearching for '{args.query}' in files matching '{args.file}':")
        for result in results:
            print(f"  {result.format(show_signature=True, show_docstring=args.show_docstrings)}")

    elif args.query:
        results = searcher.search_by_name(args.query, symbol_type=args.type, limit=args.limit)
        print(f"\nSearch results for '{args.query}':")
        for result in results:
            print(f"  {result.format(show_signature=True, show_docstring=args.show_docstrings)}")

    else:
        parser.print_help()
        print("\nExamples:")
        print("  python3 search_code.py MediaContainer     # Find all symbols with MediaContainer")
        print("  python3 search_code.py 'get_*' -t function  # Find functions starting with get_")
        print("  python3 search_code.py '*_handler'        # Find all handlers")
        print("  python3 search_code.py -f sonos_server '*' # All symbols in sonos_server files")
        print("  python3 search_code.py --list-classes     # List all classes")


if __name__ == "__main__":
    main()
