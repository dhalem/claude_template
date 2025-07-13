"""Import Validation Tests - Prevents import errors from reaching production.

This test ensures that:
1. All guards imported in main.py can actually be imported
2. All guards registered in create_registry() are properly imported
3. The registry creation succeeds without import errors
4. All guards can be instantiated without errors

CRITICAL: This test must catch import errors before they reach production.
"""

import importlib
import inspect
import sys
import unittest
from pathlib import Path

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the actual main module
import main
from registry import GuardRegistry


class TestImportValidation(unittest.TestCase):
    """Test that all imports and guard creation work correctly."""

    def test_main_module_imports_successfully(self):
        """Test that the main module can be imported without errors."""
        try:
            # Force reload to catch any import issues
            importlib.reload(main)
        except Exception as e:
            self.fail(f"Failed to import main module: {e}")

    def test_create_registry_succeeds(self):
        """Test that create_registry() succeeds without import errors."""
        try:
            registry = main.create_registry()
            self.assertIsInstance(registry, GuardRegistry)
        except Exception as e:
            self.fail(f"create_registry() failed: {e}")

    def test_all_imported_guards_exist(self):
        """Test that all guards imported in main.py actually exist."""
        # Get the main module source to analyze imports
        main_source = inspect.getsource(main)

        # Find all guard imports (looking for 'from guards import (' pattern)
        import re

        # Extract the multi-line import from guards
        import_pattern = r'from guards import \(([^)]+)\)'
        match = re.search(import_pattern, main_source, re.DOTALL)

        if not match:
            self.fail("Could not find 'from guards import (...)' pattern in main.py")

        # Parse the imported guard names
        imported_guards = []
        for line in match.group(1).split('\n'):
            line = line.strip().rstrip(',')
            if line and not line.startswith('#'):
                imported_guards.append(line)

        # Test that each imported guard can be instantiated
        for guard_name in imported_guards:
            with self.subTest(guard=guard_name):
                try:
                    # Import the guard class from the guards module
                    import guards
                    guard_class = getattr(guards, guard_name, None)

                    if guard_class is None:
                        self.fail(f"Guard '{guard_name}' imported in main.py but not found in guards module")

                    # Try to instantiate the guard
                    guard_instance = guard_class()
                    self.assertIsNotNone(guard_instance)

                except Exception as e:
                    self.fail(f"Failed to instantiate guard '{guard_name}': {e}")

    def test_all_registered_guards_are_imported(self):
        """Test that all guards used in create_registry() are properly imported."""
        # Get the create_registry function source
        create_registry_source = inspect.getsource(main.create_registry)

        # Find all .register() calls
        import re
        register_pattern = r'registry\.register\((\w+)\(\)'
        registered_guards = re.findall(register_pattern, create_registry_source)

        # Remove duplicates
        registered_guards = list(set(registered_guards))

        # Test that each registered guard is properly imported in main.py
        main_source = inspect.getsource(main)

        for guard_name in registered_guards:
            with self.subTest(guard=guard_name):
                # Check if the guard is imported
                if guard_name not in main_source:
                    self.fail(f"Guard '{guard_name}' is registered but not imported in main.py")

                # Try to access the guard class from main module
                try:
                    guard_class = getattr(main, guard_name, None)
                    if guard_class is None:
                        self.fail(f"Guard '{guard_name}' is registered but not accessible in main.py")

                    # Try to instantiate
                    guard_instance = guard_class()
                    self.assertIsNotNone(guard_instance)

                except Exception as e:
                    self.fail(f"Failed to instantiate registered guard '{guard_name}': {e}")

    def test_guards_module_exports_match_imports(self):
        """Test that guards/__init__.py exports all guards used in main.py."""
        # Import guards module
        import guards

        # Get list of exported guards from __all__
        exported_guards = guards.__all__

        # Get list of imported guards from main.py
        main_source = inspect.getsource(main)
        import re
        import_pattern = r'from guards import \(([^)]+)\)'
        match = re.search(import_pattern, main_source, re.DOTALL)

        if not match:
            self.fail("Could not find 'from guards import (...)' pattern in main.py")

        imported_guards = []
        for line in match.group(1).split('\n'):
            line = line.strip().rstrip(',')
            if line and not line.startswith('#'):
                imported_guards.append(line)

        # Check that all imported guards are exported
        for guard_name in imported_guards:
            with self.subTest(guard=guard_name):
                if guard_name not in exported_guards:
                    self.fail(f"Guard '{guard_name}' imported in main.py but not exported in guards/__init__.py")

    def test_registry_creation_with_all_guards(self):
        """Test that registry creation works with all guards instantiated."""
        try:
            registry = main.create_registry()

            # Verify registry has guards registered
            self.assertGreater(len(registry._guards), 0, "Registry has no guards registered")

            # Try to access all registered guards to ensure they're properly instantiated
            for tool_name, guard_list in registry._guards.items():
                for guard in guard_list:
                    # Verify guard has required attributes
                    self.assertTrue(hasattr(guard, 'name'), f"Guard missing 'name' attribute: {guard}")
                    self.assertTrue(hasattr(guard, 'description'), f"Guard missing 'description' attribute: {guard}")
                    self.assertTrue(hasattr(guard, 'should_trigger'), f"Guard missing 'should_trigger' method: {guard}")
                    self.assertTrue(hasattr(guard, 'get_message'), f"Guard missing 'get_message' method: {guard}")
                    self.assertTrue(hasattr(guard, 'get_default_action'), f"Guard missing 'get_default_action' method: {guard}")

        except Exception as e:
            self.fail(f"Registry creation with all guards failed: {e}")

    def test_no_circular_imports(self):
        """Test that there are no circular import issues."""
        try:
            # Force reimport of main module to catch circular imports
            if 'main' in sys.modules:
                del sys.modules['main']

            # Import with fresh module cache
            import main as fresh_main

            # Try to create registry
            registry = fresh_main.create_registry()
            self.assertIsInstance(registry, GuardRegistry)

        except Exception as e:
            self.fail(f"Circular import or fresh import failed: {e}")

    def test_all_guard_files_importable(self):
        """Test that all guard files in guards/ directory are importable."""
        guards_dir = Path(__file__).parent.parent / "guards"

        for guard_file in guards_dir.glob("*.py"):
            if guard_file.name.startswith("__"):
                continue

            module_name = f"guards.{guard_file.stem}"

            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except Exception as e:
                    self.fail(f"Failed to import guard module '{module_name}': {e}")


if __name__ == "__main__":
    unittest.main()
