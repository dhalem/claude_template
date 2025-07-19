"""Code search functionality for MCP server."""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CodeSearcher:
    """Handles code search operations using the existing .code_index.db"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the code searcher.

        Args:
            db_path: Path to the database file. If None, searches for .code_index.db
        """
        self.db_path = self._find_database(db_path)
        logger.info(f"Using database at: {self.db_path}")

    def _find_database(self, db_path: Optional[str] = None) -> str:
        """Find the code index database."""
        if db_path and os.path.exists(db_path):
            return db_path

        # Search for .code_index.db in common locations
        search_paths = [
            Path.cwd() / ".code_index.db",
            Path.home() / ".code_index.db",
            Path("/app/.code_index.db"),  # Docker container path
        ]

        # Also check parent directories up to 3 levels
        current = Path.cwd()
        for _ in range(3):
            search_paths.append(current / ".code_index.db")
            current = current.parent

        for path in search_paths:
            if path.exists():
                return str(path)

        raise FileNotFoundError(
            "No .code_index.db found. Please run the code indexer first.\n"
            "You can start it with: ./start-indexer.sh"
        )

    def search(self, query: str, search_type: str = "name",
               symbol_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Search for code symbols.

        Args:
            query: Search query (supports * and ? wildcards)
            search_type: Type of search - 'name', 'content', or 'file'
            symbol_type: Filter by symbol type - 'function', 'class', 'method', or 'variable'
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Convert wildcards to SQL LIKE pattern
            pattern = query.replace('*', '%').replace('?', '_')

            # Build SQL query based on search type
            if search_type == "file":
                sql = """
                    SELECT DISTINCT file_path, COUNT(*) as symbol_count
                    FROM symbols
                    WHERE file_path LIKE ?
                    GROUP BY file_path
                    ORDER BY file_path
                    LIMIT ?
                """
                params = [f"%{pattern}%", limit]

            else:
                sql = """
                    SELECT name, type, file_path, line_number, column,
                           parent, signature, docstring
                    FROM symbols
                    WHERE 1=1
                """
                params = []

                if search_type == "name":
                    sql += " AND name LIKE ?"
                    params.append(pattern)
                elif search_type == "content":
                    sql += " AND (name LIKE ? OR docstring LIKE ? OR signature LIKE ?)"
                    params.extend([f"%{pattern}%", f"%{pattern}%", f"%{pattern}%"])

                if symbol_type:
                    sql += " AND type = ?"
                    params.append(symbol_type)

                sql += " ORDER BY name, file_path LIMIT ?"
                params.append(limit)

            cursor = conn.execute(sql, params)
            results = []

            if search_type == "file":
                for row in cursor:
                    results.append({
                        "file_path": row["file_path"],
                        "symbol_count": row["symbol_count"]
                    })
            else:
                for row in cursor:
                    results.append({
                        "name": row["name"],
                        "type": row["type"],
                        "file_path": row["file_path"],
                        "line_number": row["line_number"],
                        "column": row["column"],
                        "parent": row["parent"],
                        "signature": row["signature"],
                        "docstring": row["docstring"],
                        "location": f"{row['file_path']}:{row['line_number']}"
                    })

            conn.close()

            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "symbol_type": symbol_type,
                "count": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "search_type": search_type
            }

    def list_symbols(self, symbol_type: str, limit: int = 100) -> Dict[str, Any]:
        """List all symbols of a specific type.

        Args:
            symbol_type: Type of symbol - 'function', 'class', 'method', or 'variable'
            limit: Maximum number of results

        Returns:
            Dictionary with symbol list
        """
        return self.search("*", search_type="name", symbol_type=symbol_type, limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database stats
        """
        try:
            conn = sqlite3.connect(self.db_path)

            stats = {}

            # Total symbols
            cursor = conn.execute("SELECT COUNT(*) FROM symbols")
            stats["total_symbols"] = cursor.fetchone()[0]

            # Symbols by type
            cursor = conn.execute("""
                SELECT type, COUNT(*) as count
                FROM symbols
                GROUP BY type
            """)
            stats["by_type"] = {row[0]: row[1] for row in cursor}

            # Total files
            cursor = conn.execute("SELECT COUNT(DISTINCT file_path) FROM symbols")
            stats["total_files"] = cursor.fetchone()[0]

            # Get last indexed time from symbols table
            cursor = conn.execute("SELECT MAX(indexed_at) FROM symbols")
            row = cursor.fetchone()
            if row and row[0]:
                stats["last_indexed"] = row[0]

            conn.close()

            return {
                "success": True,
                "stats": stats
            }

        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # Convenience methods for cleaner API usage
    def search_by_name(self, query: str, symbol_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Search for symbols by name.

        Args:
            query: Search query (supports * and ? wildcards)
            symbol_type: Filter by symbol type - 'function', 'class', 'method', or 'variable'
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        return self.search(query, "name", symbol_type, limit)

    def search_by_content(self, query: str, symbol_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Search for symbols by content (name, docstring, signature).

        Args:
            query: Search query (supports * and ? wildcards)
            symbol_type: Filter by symbol type - 'function', 'class', 'method', or 'variable'
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        return self.search(query, "content", symbol_type, limit)

    def search_by_file(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search for files by path pattern.

        Args:
            query: File path pattern (supports * and ? wildcards)
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        return self.search(query, "file", None, limit)

    def search_in_file(self, file_path: str, name_pattern: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Search for symbols within a specific file.

        Args:
            file_path: Path to the file to search in
            name_pattern: Optional pattern to filter symbol names
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        # Search by content and filter by file path
        if name_pattern:
            query = name_pattern
        else:
            query = "*"  # Match all symbols in the file

        result = self.search(query, "content", None, limit)

        if result.get("success") and result.get("results"):
            # Filter results to only include symbols from the specified file
            filtered_results = [
                r for r in result["results"]
                if r.get("file_path") == file_path
            ]
            result["results"] = filtered_results
            result["count"] = len(filtered_results)

        return result

    def get_file_symbols(self, file_path: str) -> Dict[str, Any]:
        """Get all symbols from a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with search results
        """
        return self.search_in_file(file_path)

    def search_by_type(self, symbol_type: str, limit: int = 50) -> Dict[str, Any]:
        """Search for symbols by type only (alias for list_symbols).

        Args:
            symbol_type: Type of symbol - 'function', 'class', 'method', or 'variable'
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        return self.list_symbols(symbol_type, limit)
