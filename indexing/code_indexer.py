#!/usr/bin/env python3
"""Simplified code indexer using AST for Python code.

Falls back to regex patterns if tree-sitter has issues.
"""

import ast
import hashlib
import logging
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


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
    """Main code indexing class that parses Python files and stores symbols."""

    def __init__(self, project_root: str = None):
        """Initialize the code indexer.

        Args:
            project_root: Root directory of the project to index. Defaults to parent of indexing/.
        """
        if project_root is None:
            # Default to parent directory of indexing/
            self.project_root = Path(__file__).parent.parent.resolve()
        else:
            self.project_root = Path(project_root).resolve()
        self.db_path = self.project_root / ".code_index.db"
        self.init_database()

        # Index the entire repository root
        self.index_dirs = ["."]

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
        """Get hash of file contents."""
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def should_reindex_file(self, file_path: Path) -> bool:
        """Check if file needs reindexing based on hash."""
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
        """Extract symbols from Python file using AST."""
        symbols = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            class SymbolVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.symbols = []
                    self.current_class = None

                def visit_ClassDef(self, node):
                    symbol = Symbol(
                        name=node.name,
                        type="class",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=node.col_offset,
                        docstring=ast.get_docstring(node),
                    )
                    self.symbols.append(symbol)

                    # Visit methods
                    old_class = self.current_class
                    self.current_class = node.name
                    self.generic_visit(node)
                    self.current_class = old_class

                def visit_FunctionDef(self, node):
                    # Get function signature
                    args = []
                    for arg in node.args.args:
                        args.append(arg.arg)
                    signature = f"({', '.join(args)})"

                    symbol = Symbol(
                        name=node.name,
                        type="method" if self.current_class else "function",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=node.col_offset,
                        parent=self.current_class,
                        signature=signature,
                        docstring=ast.get_docstring(node),
                    )
                    self.symbols.append(symbol)

                def visit_AsyncFunctionDef(self, node):
                    # Treat async functions same as regular functions
                    self.visit_FunctionDef(node)

            visitor = SymbolVisitor()
            visitor.visit(tree)
            symbols = visitor.symbols

        except SyntaxError as e:
            logger.warning("Syntax error in %s: %s", file_path, e)
            # Fall back to regex-based extraction for files with syntax errors
            symbols = self.extract_symbols_with_regex(file_path)
        except Exception as e:
            logger.error("Error parsing %s: %s", file_path, e)

        return symbols

    def extract_symbols_with_regex(self, file_path: Path) -> List[Symbol]:
        """Fallback regex-based symbol extraction."""
        symbols = []

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            current_class = None

            for i, line in enumerate(lines):
                # Match class definitions
                class_match = re.match(r"^class\s+(\w+)", line)
                if class_match:
                    current_class = class_match.group(1)
                    symbols.append(
                        Symbol(name=current_class, type="class", file_path=str(file_path), line_number=i + 1, column=0)
                    )

                # Match function/method definitions
                func_match = re.match(r"^(\s*)def\s+(\w+)\s*\((.*?)\)", line)
                if func_match:
                    indent, name, params = func_match.groups()
                    is_method = len(indent) > 0 and current_class is not None

                    symbols.append(
                        Symbol(
                            name=name,
                            type="method" if is_method else "function",
                            file_path=str(file_path),
                            line_number=i + 1,
                            column=len(indent),
                            parent=current_class if is_method else None,
                            signature=f"({params})",
                        )
                    )

                # Reset current_class if we're back at top level
                if line.strip() and not line[0].isspace():
                    if not class_match:
                        current_class = None

        except Exception as e:
            logger.error(f"Error in regex extraction for {file_path}: {e}")

        return symbols

    def index_file(self, file_path: Path):
        """Index a single file."""
        if file_path.suffix not in self.extensions:
            return

        logger.debug(f"Indexing {file_path}...")

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
        """Index all Python files in a directory."""
        dir_path = self.project_root / directory
        if not dir_path.exists():
            logger.warning(f"Directory {directory} not found")
            return

        count = 0
        for file_path in dir_path.rglob("*.py"):
            if "__pycache__" in str(file_path):
                continue
            if "venv" in str(file_path):
                continue
            if self.should_reindex_file(file_path):
                self.index_file(file_path)
                count += 1

        print(f"Indexed {count} files in {directory}")

    def index_all(self):
        """Index all configured directories."""
        print("Starting full index...")
        for directory in self.index_dirs:
            self.index_directory(directory)
        print("Indexing complete!")

    def get_stats(self):
        """Get indexing statistics."""
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
