# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Test suite for pre-commit duplicate prevention integration - RED phase.

These tests verify that duplicate prevention works in pre-commit hooks.
Uses REAL integration testing with actual git operations and file system.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest


@pytest.mark.skip(reason="Skip during development - pre-commit integration being reworked")
class TestPreCommitDuplicatePrevention(unittest.TestCase):
    """Test suite for pre-commit duplicate prevention integration.

    RED PHASE: These tests should FAIL until pre-commit integration is implemented.
    Uses REAL git operations and file system - no mocks.
    """

    def setUp(self):
        """Set up test git repository with duplicate prevention system."""
        # Create temporary directory for test repository
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Initialize git repository
        os.chdir(self.test_dir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

        # Copy necessary files for duplicate prevention
        project_root = Path(__file__).parent.parent.parent.parent

        # Copy duplicate prevention system
        shutil.copytree(project_root / "duplicate_prevention", Path(self.test_dir) / "duplicate_prevention")

        # Copy hooks system
        shutil.copytree(project_root / "hooks", Path(self.test_dir) / "hooks")

        # Copy scripts directory for pre-commit script
        if (project_root / "scripts").exists():
            shutil.copytree(project_root / "scripts", Path(self.test_dir) / "scripts")

        # Create basic pre-commit config with duplicate prevention hook
        precommit_config = r"""
repos:
  - repo: local
    hooks:
      - id: duplicate-prevention-check
        name: "🔍 Duplicate Code Prevention Check"
        entry: bash -c './hooks/scripts/pre-commit-duplicate-check.sh'
        language: system
        types: [text]
        files: \.(py|js|jsx|ts|tsx|java|cpp|c|go|rs)$
        verbose: true
"""

        with open(".pre-commit-config.yaml", "w") as f:
            f.write(precommit_config)

        # Install pre-commit hooks
        try:
            subprocess.run(["pre-commit", "install"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # pre-commit might not be installed, skip hook installation
            pass

    def tearDown(self):
        """Clean up test repository."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_precommit_hook_exists_and_configured(self):
        """Test that pre-commit hook is properly configured."""
        # Check that pre-commit config exists
        self.assertTrue(os.path.exists(".pre-commit-config.yaml"))

        # Check that duplicate prevention is configured
        with open(".pre-commit-config.yaml", "r") as f:
            config_content = f.read()

        self.assertIn("duplicate-prevention-check", config_content)
        self.assertIn("hooks/python/main.py", config_content)

    def test_precommit_hook_blocks_similar_files(self):
        """Test that pre-commit hook blocks commits with similar files."""
        # Create initial file with a unique function that won't match indexed code
        initial_file = '''
def unique_test_function_xyz123(param_a, param_b):
    """Unique test function for duplicate prevention testing."""
    result = param_a * 42 + param_b * 137
    return f"Test result: {result}"
'''

        # Write and commit initial file
        with open("test_unique_utils.py", "w") as f:
            f.write(initial_file)

        subprocess.run(["git", "add", "test_unique_utils.py"], check=True)
        subprocess.run(["git", "commit", "-m", "Add initial utility function"], check=True)

        # Create very similar file (should be blocked by pre-commit hook)
        similar_file = '''
def another_unique_test_xyz123(a_param, b_param):
    """Another unique test function for testing."""
    calculated_result = a_param * 42 + b_param * 137
    return f"Test result: {calculated_result}"
'''

        with open("test_similar_utils.py", "w") as f:
            f.write(similar_file)

        subprocess.run(["git", "add", "test_similar_utils.py"], check=True)

        # Attempt to commit - should fail due to duplicate prevention
        result = subprocess.run(["git", "commit", "-m", "Add similar function"], capture_output=True, text=True)

        # Commit should fail
        self.assertNotEqual(result.returncode, 0)

        # Output should mention duplicate prevention
        output = result.stdout + result.stderr
        self.assertIn("duplicate", output.lower())
        self.assertIn("similar", output.lower())

    def test_precommit_hook_allows_different_files(self):
        """Test that pre-commit hook allows commits with different files."""
        # Create initial file
        initial_file = '''
def send_email(to_address, subject, body):
    """Send an email message."""
    import smtplib
    # Email sending logic here
    return True
'''

        # Write and commit initial file
        with open("email_utils.py", "w") as f:
            f.write(initial_file)

        subprocess.run(["git", "add", "email_utils.py"], check=True)
        subprocess.run(["git", "commit", "-m", "Add email utility"], check=True)

        # Create completely different file (should be allowed)
        different_file = '''
def calculate_fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
'''

        with open("math_utils.py", "w") as f:
            f.write(different_file)

        subprocess.run(["git", "add", "math_utils.py"], check=True)

        # Commit should succeed
        result = subprocess.run(["git", "commit", "-m", "Add different function"], capture_output=True, text=True)

        # Commit should succeed
        self.assertEqual(result.returncode, 0)

    def test_precommit_hook_handles_javascript_files(self):
        """Test that pre-commit hook works with JavaScript files."""
        # Create initial JavaScript file
        initial_js = r"""
class UserValidator {
    constructor() {
        this.emailPattern = /^[^@]+@[^@]+\.[^@]+$/;
    }

    validateEmail(email) {
        return this.emailPattern.test(email);
    }
}
"""

        with open("UserValidator.js", "w") as f:
            f.write(initial_js)

        subprocess.run(["git", "add", "UserValidator.js"], check=True)
        subprocess.run(["git", "commit", "-m", "Add user validator"], check=True)

        # Create similar JavaScript file
        similar_js = r"""
class EmailValidator {
    constructor() {
        this.pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    }

    validate(email) {
        return this.pattern.test(email);
    }
}
"""

        with open("EmailValidator.js", "w") as f:
            f.write(similar_js)

        subprocess.run(["git", "add", "EmailValidator.js"], check=True)

        # Should detect similarity in JavaScript files
        result = subprocess.run(["git", "commit", "-m", "Add similar email validator"], capture_output=True, text=True)

        # Should fail due to similarity
        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn("similar", output.lower())

    def test_precommit_hook_ignores_small_files(self):
        """Test that pre-commit hook ignores very small files."""
        # Create initial small file
        small_file1 = 'print("hello")\n'

        with open("small1.py", "w") as f:
            f.write(small_file1)

        subprocess.run(["git", "add", "small1.py"], check=True)
        subprocess.run(["git", "commit", "-m", "Add small file 1"], check=True)

        # Create another small file (should be allowed even if similar)
        small_file2 = 'print("hello world")\n'

        with open("small2.py", "w") as f:
            f.write(small_file2)

        subprocess.run(["git", "add", "small2.py"], check=True)

        # Should succeed because files are too small to check
        result = subprocess.run(["git", "commit", "-m", "Add small file 2"], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)

    def test_precommit_hook_ignores_non_code_files(self):
        """Test that pre-commit hook ignores non-code files."""
        # Create documentation file
        readme_content = """
# Project Documentation

This is a readme file with documentation.
It should not trigger duplicate prevention.
"""

        with open("README.md", "w") as f:
            f.write(readme_content)

        subprocess.run(["git", "add", "README.md"], check=True)

        # Should succeed because it's not a code file
        result = subprocess.run(["git", "commit", "-m", "Add README"], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)

    def test_precommit_hook_provides_helpful_message(self):
        """Test that pre-commit hook provides helpful guidance when blocking."""
        # Create initial file
        initial_file = '''
def hash_password(password):
    """Hash a password using SHA-256."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
'''

        with open("auth.py", "w") as f:
            f.write(initial_file)

        subprocess.run(["git", "add", "auth.py"], check=True)
        subprocess.run(["git", "commit", "-m", "Add auth utility"], check=True)

        # Create similar file
        similar_file = '''
def create_password_hash(pwd):
    """Create SHA-256 hash of password."""
    import hashlib
    return hashlib.sha256(pwd.encode()).hexdigest()
'''

        with open("security.py", "w") as f:
            f.write(similar_file)

        subprocess.run(["git", "add", "security.py"], check=True)

        result = subprocess.run(
            ["git", "commit", "-m", "Add similar security function"], capture_output=True, text=True
        )

        # Should provide helpful message
        output = result.stdout + result.stderr
        self.assertIn("similar", output.lower())
        self.assertIn("existing", output.lower())
        # Should suggest editing existing file instead
        self.assertIn("edit", output.lower())

    def test_precommit_hook_handles_multiple_files_in_commit(self):
        """Test that pre-commit hook handles commits with multiple files."""
        # Create initial file
        initial_file = '''
def validate_input(data):
    """Validate input data."""
    return data is not None and len(str(data)) > 0
'''

        with open("validation.py", "w") as f:
            f.write(initial_file)

        subprocess.run(["git", "add", "validation.py"], check=True)
        subprocess.run(["git", "commit", "-m", "Add validation"], check=True)

        # Create multiple new files, one similar and one different
        similar_file = '''
def check_input_validity(input_data):
    """Check if input data is valid."""
    return input_data is not None and len(str(input_data)) > 0
'''

        different_file = '''
def format_json(data):
    """Format data as JSON string."""
    import json
    return json.dumps(data, indent=2)
'''

        with open("input_checker.py", "w") as f:
            f.write(similar_file)

        with open("json_utils.py", "w") as f:
            f.write(different_file)

        subprocess.run(["git", "add", "input_checker.py", "json_utils.py"], check=True)

        # Should fail because one file is similar
        result = subprocess.run(["git", "commit", "-m", "Add multiple utilities"], capture_output=True, text=True)

        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn("similar", output.lower())

    def test_precommit_hook_performance_with_large_repository(self):
        """Test that pre-commit hook performs reasonably with larger repositories."""
        # Create multiple existing files to build up repository
        for i in range(10):
            file_content = f'''
def function_{i}(param):
    """Function number {i}."""
    return param * {i} + {i}
'''
            with open(f"module_{i}.py", "w") as f:
                f.write(file_content)

            subprocess.run(["git", "add", f"module_{i}.py"], check=True)
            subprocess.run(["git", "commit", "-m", f"Add module {i}"], check=True)

        # Now add a new different file
        new_file = '''
def unique_function():
    """A completely unique function."""
    return "unique result that should not match anything"
'''

        with open("unique_module.py", "w") as f:
            f.write(new_file)

        subprocess.run(["git", "add", "unique_module.py"], check=True)

        # Should complete in reasonable time (< 30 seconds)
        import time

        start_time = time.time()

        result = subprocess.run(
            ["git", "commit", "-m", "Add unique module"],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        duration = time.time() - start_time

        # Should succeed and complete quickly
        self.assertEqual(result.returncode, 0)
        self.assertLess(duration, 30)  # Should complete within 30 seconds


if __name__ == "__main__":
    unittest.main()
