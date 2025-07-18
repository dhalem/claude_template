# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for CodeIndexer class."""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from code_indexer import CodeIndexer, Symbol


class TestCodeIndexer(unittest.TestCase):
    """Test CodeIndexer functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        self.indexer = CodeIndexer(project_root=self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_symbol_dataclass(self):
        """Test Symbol dataclass creation."""
        symbol = Symbol(
            name="test_function",
            type="function",
            file_path="/path/to/file.py",
            line_number=10,
            column=4,
            signature="(arg1, arg2)",
            docstring="Test function"
        )

        self.assertEqual(symbol.name, "test_function")
        self.assertEqual(symbol.type, "function")
        self.assertEqual(symbol.line_number, 10)
        self.assertIsNone(symbol.parent)

    def test_database_initialization(self):
        """Test that database is properly initialized."""
        db_path = self.indexer.db_path
        self.assertTrue(db_path.exists())

        # Check that tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check symbols table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symbols'")
        self.assertIsNotNone(cursor.fetchone())

        # Check file_hashes table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_hashes'")
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_extract_symbols_from_python_simple_function(self):
        """Test extracting a simple function."""
        python_code = '''
def hello_world():
    """Simple greeting function."""
    print("Hello, World!")
    return "greeting"
'''

        # Create temporary file
        test_file = self.test_dir / "test.py"
        test_file.write_text(python_code)

        symbols = self.indexer.extract_symbols_from_python(test_file)

        self.assertEqual(len(symbols), 1)
        symbol = symbols[0]
        self.assertEqual(symbol.name, "hello_world")
        self.assertEqual(symbol.type, "function")
        self.assertEqual(symbol.file_path, str(test_file))
        self.assertEqual(symbol.line_number, 2)  # def line
        self.assertIn("Simple greeting function", symbol.docstring or "")

    def test_extract_symbols_from_python_class_with_methods(self):
        """Test extracting a class with methods."""
        python_code = '''
class Calculator:
    """A simple calculator class."""

    def __init__(self, initial_value=0):
        """Initialize calculator."""
        self.value = initial_value

    def add(self, x):
        """Add a number."""
        self.value += x
        return self.value

    @staticmethod
    def multiply(a, b):
        """Multiply two numbers."""
        return a * b
'''

        test_file = self.test_dir / "calculator.py"
        test_file.write_text(python_code)

        symbols = self.indexer.extract_symbols_from_python(test_file)

        # Should have: class + 3 methods
        self.assertEqual(len(symbols), 4)

        # Check class
        class_symbol = next(s for s in symbols if s.type == "class")
        self.assertEqual(class_symbol.name, "Calculator")
        self.assertIn("simple calculator", class_symbol.docstring.lower())

        # Check methods
        method_names = {s.name for s in symbols if s.type == "method"}
        expected_methods = {"__init__", "add", "multiply"}
        self.assertEqual(method_names, expected_methods)

        # Check parent relationships
        for symbol in symbols:
            if symbol.type == "method":
                self.assertEqual(symbol.parent, "Calculator")

    def test_extract_symbols_from_python_nested_classes(self):
        """Test extracting nested classes."""
        python_code = '''
class Outer:
    """Outer class."""

    class Inner:
        """Inner class."""

        def inner_method(self):
            """Method in inner class."""
            pass

    def outer_method(self):
        """Method in outer class."""
        pass
'''

        test_file = self.test_dir / "nested.py"
        test_file.write_text(python_code)

        symbols = self.indexer.extract_symbols_from_python(test_file)

        # Should have: 2 classes + 2 methods
        self.assertEqual(len(symbols), 4)

        # Check that Inner class has Outer as parent
        inner_class = next(s for s in symbols if s.name == "Inner")
        self.assertEqual(inner_class.parent, "Outer")

        # Check that inner_method has Inner as parent
        inner_method = next(s for s in symbols if s.name == "inner_method")
        self.assertEqual(inner_method.parent, "Inner")

    def test_extract_symbols_regex_fallback(self):
        """Test regex fallback for syntax errors."""
        # Malformed Python that will cause AST to fail
        python_code = '''
def valid_function():
    return "ok"

def broken_function(
    # Missing closing parenthesis and other syntax errors
    print("this will break AST")

class ValidClass:
    def method(self):
        pass
'''

        test_file = self.test_dir / "broken.py"
        test_file.write_text(python_code)

        symbols = self.indexer.extract_symbols_from_python(test_file)

        # Should still find some symbols via regex fallback
        self.assertGreater(len(symbols), 0)

        symbol_names = {s.name for s in symbols}
        self.assertIn("valid_function", symbol_names)
        self.assertIn("ValidClass", symbol_names)

    def test_should_reindex_file_new_file(self):
        """Test that new files are marked for reindexing."""
        test_file = self.test_dir / "new_file.py"
        test_file.write_text("def new_function(): pass")

        self.assertTrue(self.indexer.should_reindex_file(test_file))

    def test_should_reindex_file_unchanged(self):
        """Test that unchanged files are not reindexed."""
        test_file = self.test_dir / "unchanged.py"
        content = "def unchanged_function(): pass"
        test_file.write_text(content)

        # Index the file first
        self.indexer.index_file(test_file)

        # Should not need reindexing
        self.assertFalse(self.indexer.should_reindex_file(test_file))

    def test_should_reindex_file_modified(self):
        """Test that modified files are marked for reindexing."""
        test_file = self.test_dir / "modified.py"

        # Write initial content and index
        test_file.write_text("def original_function(): pass")
        self.indexer.index_file(test_file)

        # Modify the file
        test_file.write_text("def modified_function(): pass")

        # Should need reindexing
        self.assertTrue(self.indexer.should_reindex_file(test_file))

    def test_index_file_complete_workflow(self):
        """Test complete file indexing workflow."""
        python_code = '''
def standalone_function():
    """A standalone function."""
    return "standalone"

class TestClass:
    """Test class for indexing."""

    def test_method(self):
        """Test method."""
        return "method"
'''

        test_file = self.test_dir / "complete.py"
        test_file.write_text(python_code)

        # Index the file
        self.indexer.index_file(test_file)

        # Verify symbols were stored in database
        conn = sqlite3.connect(self.indexer.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name, type, parent FROM symbols WHERE file_path = ?", (str(test_file),))
        results = cursor.fetchall()

        self.assertEqual(len(results), 3)  # function + class + method

        # Convert to dict for easier checking
        symbols_data = {row[0]: {"type": row[1], "parent": row[2]} for row in results}

        self.assertIn("standalone_function", symbols_data)
        self.assertEqual(symbols_data["standalone_function"]["type"], "function")
        self.assertIsNone(symbols_data["standalone_function"]["parent"])

        self.assertIn("TestClass", symbols_data)
        self.assertEqual(symbols_data["TestClass"]["type"], "class")

        self.assertIn("test_method", symbols_data)
        self.assertEqual(symbols_data["test_method"]["type"], "method")
        self.assertEqual(symbols_data["test_method"]["parent"], "TestClass")

        conn.close()

    def test_get_stats(self):
        """Test getting indexing statistics."""
        # Create and index multiple files
        files_content = {
            "file1.py": "def func1(): pass\nclass Class1: pass",
            "file2.py": "def func2(): pass\ndef func3(): pass",
            "file3.py": "class Class2:\n    def method1(self): pass"
        }

        for filename, content in files_content.items():
            test_file = self.test_dir / filename
            test_file.write_text(content)
            self.indexer.index_file(test_file)

        stats = self.indexer.get_stats()

        self.assertIn("total_symbols", stats)
        self.assertIn("total_files", stats)
        self.assertIn("type_counts", stats)

        # Should have indexed 3 files
        self.assertEqual(stats["total_files"], 3)

        # Should have multiple symbols
        self.assertGreater(stats["total_symbols"], 0)

        # Should have type breakdown
        self.assertIn("function", stats["type_counts"])
        self.assertIn("class", stats["type_counts"])
        self.assertIn("method", stats["type_counts"])

    def test_extract_symbols_edge_cases(self):
        """Test edge cases in symbol extraction."""
        edge_cases = [
            # Empty file
            "",

            # Only comments
            "# Just a comment\n# Another comment",

            # Only imports
            "import os\nfrom pathlib import Path",

            # Function with complex signature
            "def complex_func(a: int, b: str = 'default', *args, **kwargs) -> bool:\n    return True",

            # Async function
            "async def async_func():\n    await something()",

            # Lambda (should not be captured)
            "lambda_func = lambda x: x * 2",
        ]

        for i, code in enumerate(edge_cases):
            with self.subTest(case=i):
                test_file = self.test_dir / f"edge_case_{i}.py"
                test_file.write_text(code)

                # Should not crash
                symbols = self.indexer.extract_symbols_from_python(test_file)
                self.assertIsInstance(symbols, list)

    def test_docstring_extraction(self):
        """Test that docstrings are properly extracted."""
        python_code = '''
def func_with_docstring():
    """
    This is a multi-line docstring.
    It has multiple lines.
    """
    pass

class ClassWithDocstring:
    """Single line class docstring."""

    def method_with_docstring(self):
        """Method docstring here."""
        pass

def func_no_docstring():
    print("No docstring")
'''

        test_file = self.test_dir / "docstrings.py"
        test_file.write_text(python_code)

        symbols = self.indexer.extract_symbols_from_python(test_file)

        # Check docstring extraction
        docstring_symbols = {s.name: s.docstring for s in symbols if s.docstring}

        self.assertIn("func_with_docstring", docstring_symbols)
        self.assertIn("multi-line docstring", docstring_symbols["func_with_docstring"])

        self.assertIn("ClassWithDocstring", docstring_symbols)
        self.assertIn("Single line class docstring", docstring_symbols["ClassWithDocstring"])

        self.assertIn("method_with_docstring", docstring_symbols)
        self.assertIn("Method docstring here", docstring_symbols["method_with_docstring"])


if __name__ == '__main__':
    unittest.main()
