#!/usr/bin/env python3
"""Tree-sitter based code indexer for Spotidal project.

Provides fast function/class/symbol search with automatic updates.
"""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import tree_sitter
    import tree_sitter_languages

    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    print("Warning: tree-sitter not installed. Run setup_code_indexing.sh first.")


@dataclass
class Symbol:
    """Represents a code symbol (function, class, method, etc.)."""

    name: str
    type: str  # function, class, method, variable
    file_path: str
    line_number: int
    column: int
    parent: Optional[str] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None


class CodeIndexer:
    """Main code indexing class that uses tree-sitter for parsing."""

    def __init__(self, project_root: str = "."):
        """Initialize the code indexer with a project root directory."""
        self.project_root = Path(project_root).resolve()
        self.db_path = self.project_root / ".code_index.db"
        self.init_database()

        if HAS_TREE_SITTER:
            self.parser = tree_sitter.Parser()
            self.parser.set_language(tree_sitter_languages.get_language("python"))

        # Directories to index
        self.index_dirs = ["sonos_server", "syncer", "syncer_v2", "gemini_playlist_suggester", "monitoring"]

        # File extensions to index
        self.extensions = {".py", ".pyx", ".pyi"}

    def init_database(self):
        """Initialize SQLite database for symbol storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                column INTEGER NOT NULL,
                parent TEXT,
                signature TEXT,
                docstring TEXT,
                file_hash TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, type, file_path, line_number)
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_symbol_name ON symbols(name)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_symbol_type ON symbols(type)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_file_path ON symbols(file_path)
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_hashes (
                file_path TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                last_modified TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def get_file_hash(self, file_path: Path) -> str:
        """Get hash of file contents"""
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def should_reindex_file(self, file_path: Path) -> bool:
        """Check if file needs reindexing based on hash"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT hash FROM file_hashes WHERE file_path = ?", (str(file_path),))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return True

        current_hash = self.get_file_hash(file_path)
        return current_hash != result[0]

    def extract_symbols_from_python(self, file_path: Path) -> List[Symbol]:
        """Extract symbols from Python file using tree-sitter"""
        if not HAS_TREE_SITTER:
            return []

        symbols = []

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            tree = self.parser.parse(content)

            # Query for functions, classes, and methods
            # Note: query would be used with tree-sitter's query language,
            # but for now we'll walk the tree manually
            # query = """
            # (function_definition
            #     name: (identifier) @function.name
            # ) @function
            #
            # (class_definition
            #     name: (identifier) @class.name
            # ) @class
            #
            # (assignment
            #     left: (identifier) @variable.name
            #     right: (_)
            # ) @variable
            # """

            # Walk the tree and extract symbols
            def walk_tree(node, parent_class=None):
                if node.type == "function_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = content[name_node.start_byte : name_node.end_byte].decode("utf-8")

                        # Get signature
                        params_node = node.child_by_field_name("parameters")
                        signature = None
                        if params_node:
                            signature = content[params_node.start_byte : params_node.end_byte].decode("utf-8")

                        # Get docstring
                        docstring = None
                        body_node = node.child_by_field_name("body")
                        if body_node and body_node.child_count > 0:
                            first_stmt = body_node.children[0]
                            if first_stmt.type == "expression_statement":
                                expr = first_stmt.children[0]
                                if expr.type == "string":
                                    docstring = content[expr.start_byte : expr.end_byte].decode("utf-8")

                        symbol = Symbol(
                            name=name,
                            type="method" if parent_class else "function",
                            file_path=str(file_path),
                            line_number=name_node.start_point[0] + 1,
                            column=name_node.start_point[1],
                            parent=parent_class,
                            signature=signature,
                            docstring=docstring,
                        )
                        symbols.append(symbol)

                elif node.type == "class_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = content[name_node.start_byte : name_node.end_byte].decode("utf-8")

                        symbol = Symbol(
                            name=name,
                            type="class",
                            file_path=str(file_path),
                            line_number=name_node.start_point[0] + 1,
                            column=name_node.start_point[1],
                        )
                        symbols.append(symbol)

                        # Walk class body for methods
                        body_node = node.child_by_field_name("body")
                        if body_node:
                            for child in body_node.children:
                                walk_tree(child, parent_class=name)
                        return

                # Recurse through children
                for child in node.children:
                    walk_tree(child, parent_class)

            walk_tree(tree.root_node)

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return symbols

    def index_file(self, file_path: Path):
        """Index a single file"""
        if file_path.suffix not in self.extensions:
            return

        print(f"Indexing {file_path}...")

        symbols = self.extract_symbols_from_python(file_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Remove old symbols for this file
        cursor.execute("DELETE FROM symbols WHERE file_path = ?", (str(file_path),))

        # Insert new symbols
        for symbol in symbols:
            cursor.execute(
                """
                INSERT OR REPLACE INTO symbols
                (name, type, file_path, line_number, column, parent, signature, docstring, file_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    symbol.name,
                    symbol.type,
                    symbol.file_path,
                    symbol.line_number,
                    symbol.column,
                    symbol.parent,
                    symbol.signature,
                    symbol.docstring,
                    self.get_file_hash(file_path),
                ),
            )

        # Update file hash
        cursor.execute(
            """
            INSERT OR REPLACE INTO file_hashes (file_path, hash, last_modified)
            VALUES (?, ?, ?)
        """,
            (str(file_path), self.get_file_hash(file_path), datetime.now()),
        )

        conn.commit()
        conn.close()

    def index_directory(self, directory: str):
        """Index all Python files in a directory"""
        dir_path = self.project_root / directory
        if not dir_path.exists():
            print(f"Directory {directory} not found")
            return

        for file_path in dir_path.rglob("*.py"):
            if "__pycache__" in str(file_path):
                continue
            if self.should_reindex_file(file_path):
                self.index_file(file_path)

    def index_all(self):
        """Index all configured directories"""
        print("Starting full index...")
        for directory in self.index_dirs:
            self.index_directory(directory)
        print("Indexing complete!")

    def get_stats(self):
        """Get indexing statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM symbols")
        total_symbols = cursor.fetchone()[0]

        cursor.execute("SELECT type, COUNT(*) FROM symbols GROUP BY type")
        type_counts = dict(cursor.fetchall())

        cursor.execute("SELECT COUNT(DISTINCT file_path) FROM symbols")
        total_files = cursor.fetchone()[0]

        conn.close()

        return {"total_symbols": total_symbols, "total_files": total_files, "type_counts": type_counts}


if __name__ == "__main__":
    indexer = CodeIndexer()
    indexer.index_all()

    stats = indexer.get_stats()
    print("\nIndexing Statistics:")
    print(f"Total symbols: {stats['total_symbols']}")
    print(f"Total files: {stats['total_files']}")
    print(f"Symbol types: {stats['type_counts']}")
