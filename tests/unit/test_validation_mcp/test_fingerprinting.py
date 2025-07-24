# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Unit tests for test fingerprinting utility following TDD RED phase.
These tests should FAIL initially as the implementation doesn't exist yet.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.utils.fingerprinting import TestFingerprinter


class TestTestFingerprinting:
    """Test test file fingerprinting for unique identification."""

    def test_fingerprinter_exists(self):
        """Test that TestFingerprinter class exists."""
        # This should fail - TestFingerprinter doesn't exist yet
        assert TestFingerprinter is not None, "TestFingerprinter class not implemented yet"

    def test_fingerprint_file_content(self):
        """Test fingerprinting based on file content."""
        # This should fail - generate_fingerprint method doesn't exist
        fingerprinter = TestFingerprinter()

        test_content = '''
def test_example():
    assert 1 + 1 == 2

def test_another():
    assert "hello" == "hello"
'''

        fingerprint = fingerprinter.generate_fingerprint(test_content, "test_file.py")

        # Should be a hex string
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in fingerprint)

    def test_fingerprint_consistency(self):
        """Test that same content produces same fingerprint."""
        # This should fail - generate_fingerprint method doesn't exist
        fingerprinter = TestFingerprinter()

        test_content = '''
def test_consistency():
    assert True
'''

        fp1 = fingerprinter.generate_fingerprint(test_content, "test1.py")
        fp2 = fingerprinter.generate_fingerprint(test_content, "test1.py")

        assert fp1 == fp2, "Same content should produce identical fingerprints"

    def test_fingerprint_different_content(self):
        """Test that different content produces different fingerprints."""
        # This should fail - generate_fingerprint method doesn't exist
        fingerprinter = TestFingerprinter()

        content1 = '''
def test_one():
    assert 1 == 1
'''

        content2 = '''
def test_two():
    assert 2 == 2
'''

        fp1 = fingerprinter.generate_fingerprint(content1, "test1.py")
        fp2 = fingerprinter.generate_fingerprint(content2, "test2.py")

        assert fp1 != fp2, "Different content should produce different fingerprints"

    def test_fingerprint_whitespace_normalization(self):
        """Test that fingerprinting normalizes whitespace differences."""
        # This should fail - normalization feature doesn't exist
        fingerprinter = TestFingerprinter()

        content1 = '''def test_function():
    assert True'''

        content2 = '''def test_function():
        assert True'''  # Different indentation

        content3 = '''def test_function():
    assert True
'''  # Extra newline

        fp1 = fingerprinter.generate_fingerprint(content1, "test.py")
        fp2 = fingerprinter.generate_fingerprint(content2, "test.py")
        fp3 = fingerprinter.generate_fingerprint(content3, "test.py")

        # With normalization, these should be the same
        assert fp1 == fp2 == fp3, "Whitespace differences should be normalized"

    def test_fingerprint_from_file_path(self):
        """Test generating fingerprint directly from file path."""
        # This should fail - generate_from_file method doesn't exist
        fingerprinter = TestFingerprinter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def test_from_file():
    assert "file" == "file"
''')
            temp_path = f.name

        try:
            fingerprint = fingerprinter.generate_from_file(temp_path)

            assert isinstance(fingerprint, str)
            assert len(fingerprint) == 64
        finally:
            os.unlink(temp_path)

    def test_fingerprint_includes_filename(self):
        """Test that filename affects fingerprint (prevents collisions)."""
        # This should fail - filename consideration doesn't exist
        fingerprinter = TestFingerprinter()

        content = '''
def test_same_content():
    assert True
'''

        fp1 = fingerprinter.generate_fingerprint(content, "test1.py")
        fp2 = fingerprinter.generate_fingerprint(content, "test2.py")

        assert fp1 != fp2, "Same content in different files should have different fingerprints"

    def test_fingerprint_ast_based(self):
        """Test that fingerprinting is based on AST, not just text."""
        # This should fail - AST-based fingerprinting doesn't exist
        fingerprinter = TestFingerprinter()

        # Semantically equivalent but textually different
        content1 = '''
def test_function():
    x = 1
    y = 2
    return x + y
'''

        content2 = '''
def test_function():
    # Different comment
    x = 1  # inline comment
    y = 2
    return x + y
'''

        fp1 = fingerprinter.generate_fingerprint(content1, "test.py", method="ast")
        fp2 = fingerprinter.generate_fingerprint(content2, "test.py", method="ast")

        assert fp1 == fp2, "AST-based fingerprinting should ignore comments"

    def test_fingerprint_specific_function(self):
        """Test fingerprinting specific functions within a file."""
        # This should fail - function-specific fingerprinting doesn't exist
        fingerprinter = TestFingerprinter()

        content = '''
def test_function_one():
    assert 1 == 1

def test_function_two():
    assert 2 == 2

def helper_function():
    return "helper"
'''

        fp1 = fingerprinter.generate_function_fingerprint(content, "test_function_one", "test.py")
        fp2 = fingerprinter.generate_function_fingerprint(content, "test_function_two", "test.py")

        assert fp1 != fp2, "Different functions should have different fingerprints"
        assert isinstance(fp1, str)
        assert len(fp1) == 64

    def test_fingerprint_change_detection(self):
        """Test detecting changes in test function implementations."""
        # This should fail - change detection doesn't exist
        fingerprinter = TestFingerprinter()

        original_content = '''
def test_original():
    assert 1 + 1 == 2
'''

        modified_content = '''
def test_original():
    assert 1 + 1 == 3  # Bug introduced
'''

        fp_original = fingerprinter.generate_fingerprint(original_content, "test.py")
        fp_modified = fingerprinter.generate_fingerprint(modified_content, "test.py")

        assert fp_original != fp_modified, "Modified test should have different fingerprint"

        # Test change detection
        is_changed = fingerprinter.has_changed(fp_original, fp_modified)
        assert is_changed is True, "Should detect that test has changed"

    def test_fingerprint_metadata_extraction(self):
        """Test extracting metadata from test files for fingerprinting."""
        # This should fail - metadata extraction doesn't exist
        fingerprinter = TestFingerprinter()

        content = '''
"""Test module docstring."""

import pytest


class TestClass:
    """Test class docstring."""

    def test_method(self):
        """Test method docstring."""
        assert True

    @pytest.mark.slow
    def test_marked_method(self):
        assert True


def test_function():
    """Function test docstring."""
    assert True
'''

        metadata = fingerprinter.extract_metadata(content, "test_module.py")

        assert isinstance(metadata, dict)
        assert "functions" in metadata
        assert "classes" in metadata
        assert "imports" in metadata
        assert "decorators" in metadata

        assert len(metadata["functions"]) == 1  # test_function
        assert len(metadata["classes"]) == 1   # TestClass
        assert "pytest" in metadata["imports"]
        assert "pytest.mark.slow" in metadata["decorators"]

    def test_fingerprint_caching(self):
        """Test that fingerprints can be cached for performance."""
        # This should fail - caching doesn't exist
        fingerprinter = TestFingerprinter(cache_enabled=True)

        content = '''
def test_cached():
    assert True
'''

        # First call - should compute
        fp1 = fingerprinter.generate_fingerprint(content, "test.py")

        # Second call - should use cache
        fp2 = fingerprinter.generate_fingerprint(content, "test.py")

        assert fp1 == fp2

        # Check cache statistics
        stats = fingerprinter.get_cache_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1


if __name__ == "__main__":
    # Run tests - these should all FAIL in RED phase
    pytest.main([__file__, "-v"])
