# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Unit tests for find_bugs bug detection with known vulnerability samples.

This test suite focuses on testing the bug detection capabilities using
realistic code samples with known vulnerabilities across different categories.
Tests the complete workflow without requiring actual API calls.

Testing approach:
- Real integration tests with actual files and data
- External service boundaries handled appropriately
- See TESTING_STRATEGY.md for detailed guidelines
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Import the components to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bug_finding_analyzer import BugFindingAnalyzer
from usage_tracker import UsageTracker


class TestFindBugsBugDetectionSamples(unittest.TestCase):
    """Test find_bugs detection capabilities with known vulnerability samples."""

    def setUp(self):
        """Set up test fixtures."""
        self.usage_tracker = UsageTracker()
        self.analyzer = BugFindingAnalyzer(usage_tracker=self.usage_tracker)

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sql_injection_vulnerability_detection(self):
        """Test detection of SQL injection vulnerabilities."""
        # Create vulnerable Python code with SQL injection
        vulnerable_code = '''
import sqlite3

def get_user_by_id(user_id):
    """Vulnerable function with SQL injection."""
    conn = sqlite3.connect('users.db')
    # VULNERABILITY: Direct string interpolation allows SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.execute(query)
    return cursor.fetchone()

def search_users(search_term):
    """Another vulnerable function."""
    conn = sqlite3.connect('users.db')
    # VULNERABILITY: String concatenation in SQL
    query = "SELECT * FROM users WHERE name LIKE '%" + search_term + "%'"
    return conn.execute(query).fetchall()

def login_user(username, password):
    """Direct SQL injection in login."""
    conn = sqlite3.connect('users.db')
    # VULNERABILITY: No parameterization
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = conn.execute(query).fetchone()
    return result is not None
'''

        test_file = Path(self.temp_dir) / "vulnerable.py"
        test_file.write_text(vulnerable_code)

        # Test that prompt contains SQL injection detection instructions
        files = {"vulnerable.py": vulnerable_code}
        file_tree = "vulnerable.py"

        # Test that prompt contains SQL injection detection instructions
        prompt = self.analyzer.format_analysis_prompt(
            files,
            file_tree,
            ["security"],
            None,
            bug_categories=["security"],
            severity_filter=["critical", "high"],
            include_suggestions=True,
        )

        # Verify security-specific prompts are included
        self.assertIn("SQL injection", prompt)
        self.assertIn("Direct string interpolation", prompt)
        self.assertIn("security engineer", prompt)
        self.assertIn("parameterized queries", prompt)

        # Verify the vulnerable code is included for analysis
        self.assertIn('f"SELECT * FROM users WHERE id = {user_id}"', prompt)
        self.assertIn("'%\" + search_term + \"%'", prompt)

    def test_xss_vulnerability_detection(self):
        """Test detection of XSS vulnerabilities in JavaScript."""
        # Create vulnerable JavaScript code
        vulnerable_js = """
function displayUserMessage(userInput) {
    // VULNERABILITY: Direct DOM manipulation with user input
    document.getElementById('message').innerHTML = userInput;
}

function showAlert(message) {
    // VULNERABILITY: Using eval with user input
    eval("alert('" + message + "')");
}

function updateUrl(userPath) {
    // VULNERABILITY: Unsafe URL construction
    window.location.href = "https://example.com/" + userPath;
}

function renderTemplate(data) {
    // VULNERABILITY: Unsafe template rendering
    return "<div>" + data.content + "</div>";
}
"""

        test_file = Path(self.temp_dir) / "vulnerable.js"
        test_file.write_text(vulnerable_js)

        files = {"vulnerable.js": vulnerable_js}
        file_tree = "vulnerable.js"

        # Test with security analysis parameters
        prompt = self.analyzer.format_analysis_prompt(
            files,
            file_tree,
            ["security"],
            None,
            bug_categories=["security"],
            severity_filter=None,
            include_suggestions=True,
        )

        # Verify XSS detection instructions
        self.assertIn("XSS vulnerabilities", prompt)
        self.assertIn("eval()", prompt)
        self.assertIn("innerHTML", prompt)
        self.assertIn("Unsanitized user input", prompt)

        # Verify vulnerable patterns are included
        self.assertIn("document.getElementById('message').innerHTML", prompt)
        self.assertIn('eval("alert(\'"', prompt)

    def test_memory_leak_detection(self):
        """Test detection of memory leak patterns."""
        # Create code with memory leak issues
        memory_leak_code = '''
import threading
import time

class DataProcessor:
    def __init__(self):
        self.data_cache = {}
        self.active_connections = []
        self.background_threads = []

    def process_data(self, data_id, data):
        """VULNERABILITY: Unbounded cache growth."""
        # Cache grows indefinitely - no cleanup
        self.data_cache[data_id] = data

        # VULNERABILITY: Connection not properly closed
        connection = self.create_connection()
        self.active_connections.append(connection)
        # Missing: connection.close()

        return self.analyze_data(data)

    def start_background_task(self):
        """VULNERABILITY: Thread not properly managed."""
        def worker():
            while True:  # Infinite loop
                time.sleep(1)
                # No way to stop this thread

        thread = threading.Thread(target=worker)
        self.background_threads.append(thread)
        thread.start()
        # Thread never joins or stops

    def create_connection(self):
        """Simulate connection creation."""
        return {"handle": "connection_123"}

class FileProcessor:
    def process_files(self, file_paths):
        """VULNERABILITY: Files not closed in exception path."""
        files = []
        try:
            for path in file_paths:
                f = open(path, 'r')
                files.append(f)
                data = f.read()
                # Process data...
        except Exception as e:
            # VULNERABILITY: Files remain open if exception occurs
            print(f"Error: {e}")
            return None
        finally:
            # Should close files here but doesn't
            pass

        # Files closed only in success path
        for f in files:
            f.close()
'''

        test_file = Path(self.temp_dir) / "memory_issues.py"
        test_file.write_text(memory_leak_code)

        files = {"memory_issues.py": memory_leak_code}
        file_tree = "memory_issues.py"

        # Test with memory analysis parameters
        prompt = self.analyzer.format_analysis_prompt(
            files,
            file_tree,
            ["memory"],
            None,
            bug_categories=["memory"],
            severity_filter=["high", "medium"],
            include_suggestions=True,
        )

        # Verify memory issue detection instructions
        self.assertIn("Memory Issues", prompt)
        self.assertIn("**Memory Leaks:**", prompt)
        self.assertIn("Objects not properly released", prompt)
        self.assertIn("Resources not properly closed", prompt)
        self.assertIn("Unbounded", prompt)

        # Verify vulnerable patterns are identified
        self.assertIn("self.data_cache[data_id] = data", prompt)
        self.assertIn("while True:", prompt)
        self.assertIn("open(path, 'r')", prompt)

    def test_logic_error_detection(self):
        """Test detection of logic errors and off-by-one issues."""
        logic_error_code = '''
def find_maximum(numbers):
    """VULNERABILITY: Off-by-one error in loop."""
    if not numbers:
        return None

    max_val = numbers[0]
    # BUG: Should be range(1, len(numbers)), starts at 0 again
    for i in range(0, len(numbers) - 1):  # Missing last element
        if numbers[i] > max_val:
            max_val = numbers[i]
    return max_val

def binary_search(arr, target):
    """VULNERABILITY: Infinite loop potential."""
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid  # BUG: Should be mid + 1, can cause infinite loop
        else:
            right = mid - 1
    return -1

def process_array(data):
    """VULNERABILITY: Division by zero and null pointer."""
    result = []
    total = 0

    for item in data:
        if item:  # BUG: Should check if item is not None AND not 0
            # VULNERABILITY: Division by zero if item is 0
            normalized = 100 / item
            result.append(normalized)
            total += item

    # VULNERABILITY: Division by zero if total is 0
    average = sum(data) / total
    return result, average

def validate_input(user_input):
    """VULNERABILITY: Boolean logic error."""
    # BUG: Should be AND, not OR - allows invalid input through
    if len(user_input) > 0 or user_input.isalnum():
        return True
    return False
'''

        test_file = Path(self.temp_dir) / "logic_errors.py"
        test_file.write_text(logic_error_code)

        files = {"logic_errors.py": logic_error_code}
        file_tree = "logic_errors.py"

        # Test with logic analysis parameters
        prompt = self.analyzer.format_analysis_prompt(
            files, file_tree, ["logic"], None, bug_categories=["logic"], severity_filter=None, include_suggestions=True
        )

        # Verify logic error detection instructions
        self.assertIn("Logic Issues", prompt)
        self.assertIn("Off-by-one errors", prompt)
        self.assertIn("Infinite loops", prompt)
        self.assertIn("Division by zero", prompt)
        self.assertIn("boolean logic", prompt)

        # Verify problematic patterns are included
        self.assertIn("range(0, len(numbers) - 1)", prompt)
        self.assertIn("left = mid", prompt)
        self.assertIn("100 / item", prompt)
        self.assertIn("len(user_input) > 0 or", prompt)

    def test_bug_parsing_edge_cases(self):
        """Test bug parsing with various edge cases and malformed responses."""
        # Test case 1: Valid bug with all fields
        valid_response = """
**BUG-001**
- **Category**: security
- **Severity**: critical
- **Title**: SQL Injection in Login Function
- **Location**: auth.py:25
- **Confidence**: 95%

**BUG-002**
- **Category**: logic
- **Severity**: high
- **Title**: Off-by-one Error in Array Processing
- **Location**: utils.py:142
- **Confidence**: 85%
"""

        bugs, stats = self.analyzer._parse_bug_findings(valid_response)

        self.assertEqual(len(bugs), 2)
        self.assertEqual(stats["total_bugs"], 2)
        self.assertEqual(stats["critical"], 1)
        self.assertEqual(stats["high"], 1)

        # Verify first bug details
        bug1 = bugs[0]
        self.assertEqual(bug1["bug_id"], "BUG-001")
        self.assertEqual(bug1["category"], "security")
        self.assertEqual(bug1["severity"], "critical")
        self.assertEqual(bug1["confidence"], 95)

        # Test case 2: Malformed response with missing fields
        malformed_response = """
**BUG-003**
- **Category**: memory
- **Title**: Memory Leak Issue
- **Location**: processor.py:78
# Missing severity and confidence

**BUG-004**
- **Severity**: medium
- **Confidence**: 70%
# Missing category, title, location
"""

        bugs, stats = self.analyzer._parse_bug_findings(malformed_response)

        self.assertEqual(len(bugs), 2)

        # Verify bug with missing fields has defaults
        bug3 = bugs[0]
        self.assertEqual(bug3["bug_id"], "BUG-003")
        self.assertEqual(bug3["category"], "memory")
        self.assertEqual(bug3["severity"], "unknown")  # Default value
        self.assertEqual(bug3["confidence"], 0)  # Default value

        bug4 = bugs[1]
        self.assertEqual(bug4["bug_id"], "BUG-004")
        self.assertEqual(bug4["category"], "unknown")  # Default value
        self.assertEqual(bug4["severity"], "medium")
        self.assertEqual(bug4["confidence"], 70)

        # Test case 3: No bugs found
        no_bugs_response = "No security issues detected.\nNo memory issues detected."
        bugs, stats = self.analyzer._parse_bug_findings(no_bugs_response)

        self.assertEqual(len(bugs), 0)
        self.assertEqual(stats["total_bugs"], 0)

        # Test case 4: Invalid confidence values
        invalid_confidence_response = """
**BUG-005**
- **Category**: performance
- **Severity**: low
- **Title**: Inefficient Algorithm
- **Location**: compute.py:15
- **Confidence**: not_a_number%

**BUG-006**
- **Category**: api_usage
- **Severity**: medium
- **Title**: Missing Error Handling
- **Location**: api.py:55
- **Confidence**: 150%
"""

        bugs, stats = self.analyzer._parse_bug_findings(invalid_confidence_response)

        self.assertEqual(len(bugs), 2)

        # Invalid confidence should default to 0
        self.assertEqual(bugs[0]["confidence"], 0)  # 'not_a_number' -> 0
        self.assertEqual(bugs[1]["confidence"], 150)  # '150%' -> 150 (parsed as int)

    def test_comprehensive_bug_categories_workflow(self):
        """Test complete workflow with multiple bug categories."""
        # Create comprehensive test code with multiple vulnerability types
        comprehensive_code = '''
# Security vulnerabilities
import subprocess
import sqlite3

def execute_command(user_input):
    """SQL injection and command injection."""
    # Security issue: Command injection
    result = subprocess.run(f"ls {user_input}", shell=True)

    # Security issue: SQL injection
    conn = sqlite3.connect('db.sqlite')
    query = f"SELECT * FROM files WHERE name = '{user_input}'"
    return conn.execute(query).fetchall()

# Memory issues
class ResourceManager:
    def __init__(self):
        self.connections = []

    def add_connection(self, conn):
        # Memory issue: Unbounded growth
        self.connections.append(conn)
        # Missing cleanup logic

# Logic errors
def calculate_average(numbers):
    if len(numbers) == 0:
        return 0
    # Logic error: Division by zero possible
    return sum(numbers) / len(numbers) if numbers else 1/0

# Performance issues
def find_duplicates(items):
    duplicates = []
    # Performance issue: O(n²) algorithm
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

# Concurrency issues
import threading
shared_counter = 0

def increment_counter():
    global shared_counter
    # Concurrency issue: Race condition
    temp = shared_counter
    shared_counter = temp + 1

# API usage issues
def process_file(filename):
    # API usage issue: File not closed
    file = open(filename, 'r')
    content = file.read()
    # Missing file.close()
    return content
'''

        test_file = Path(self.temp_dir) / "comprehensive.py"
        test_file.write_text(comprehensive_code)

        files = {"comprehensive.py": comprehensive_code}
        file_tree = "comprehensive.py"

        # Test with all bug categories
        all_categories = ["security", "memory", "logic", "performance", "concurrency", "api_usage"]
        prompt = self.analyzer.format_analysis_prompt(
            files, file_tree, [], None, bug_categories=all_categories, severity_filter=None, include_suggestions=True
        )

        # Verify all categories are covered in prompt
        self.assertIn("Security Issues", prompt)
        self.assertIn("Memory Issues", prompt)
        self.assertIn("Logic Issues", prompt)
        self.assertIn("Performance Issues", prompt)
        self.assertIn("Concurrency Issues", prompt)
        self.assertIn("Api_Usage Issues", prompt)

        # Verify specific vulnerability patterns are mentioned
        self.assertIn("SQL injection", prompt)
        self.assertIn("Command injection", prompt)
        self.assertIn("Memory Leaks", prompt)
        self.assertIn("Off-by-one", prompt)
        self.assertIn("O(n²)", prompt)
        self.assertIn("Race conditions", prompt)
        self.assertIn("not properly closed", prompt)

        # Verify the actual vulnerable code is included
        self.assertIn('subprocess.run(f"ls {user_input}"', prompt)
        self.assertIn("self.connections.append(conn)", prompt)
        self.assertIn("for i in range(len(items)):", prompt)
        self.assertIn("shared_counter = temp + 1", prompt)
        self.assertIn("file = open(filename, 'r')", prompt)

    def test_severity_classification_workflow(self):
        """Test severity classification and filtering workflow."""
        # Test severity filter with different levels
        sample_code = '''
def critical_vulnerability():
    """This should be critical severity."""
    password = "hardcoded_admin_password"  # Critical: hardcoded credentials

def high_severity_issue():
    """This should be high severity."""
    user_input = input("Enter SQL: ")
    query = f"SELECT * FROM users WHERE id = {user_input}"  # High: SQL injection

def medium_severity_issue():
    """This should be medium severity."""
    data = []
    for i in range(1000000):  # Medium: Performance issue
        data.append(i * 2)

def low_severity_issue():
    """This should be low severity."""
    # Low: Minor style/optimization issue
    x = 1
    y = 2
    result = x + y
'''

        files = {"severity_test.py": sample_code}
        file_tree = "severity_test.py"

        # Test critical and high only
        prompt = self.analyzer.format_analysis_prompt(
            files,
            file_tree,
            [],
            None,
            bug_categories=["security", "performance"],
            severity_filter=["critical", "high"],
            include_suggestions=True,
        )

        # Verify severity filtering instructions
        self.assertIn("ONLY report bugs with these severity levels: critical, high", prompt)
        self.assertIn("Critical**: Security vulnerabilities", prompt)
        self.assertIn("High**: Correctness issues", prompt)

        # Should not mention medium/low in filtering
        self.assertNotIn("medium, low", prompt)

        # Test with no severity filter (should include all)
        prompt = self.analyzer.format_analysis_prompt(
            files, file_tree, [], None, bug_categories=["security"], severity_filter=None, include_suggestions=False
        )

        # Should include all severity levels
        self.assertIn("Critical**: Security vulnerabilities", prompt)
        self.assertIn("High**: Correctness issues", prompt)
        self.assertIn("Medium**: Code quality issues", prompt)
        self.assertIn("Low**: Minor optimizations", prompt)

        # Should not include fix suggestions
        self.assertNotIn("Fix Suggestion", prompt)
        self.assertNotIn("Recommended fix", prompt)


if __name__ == "__main__":
    unittest.main()
