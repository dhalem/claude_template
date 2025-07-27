# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Tests for BugFindingAnalyzer functionality.

Validates the bug finding analyzer implementation to ensure proper integration
with shared components and correct bug analysis workflow.

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


class TestBugFindingAnalyzer(unittest.TestCase):
    """Test BugFindingAnalyzer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.usage_tracker = UsageTracker()
        self.analyzer = BugFindingAnalyzer(usage_tracker=self.usage_tracker)

        # Create temporary directory with sample files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = self._create_test_files()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_files(self):
        """Create test files with known security issues."""
        # Create sample Python file with SQL injection vulnerability
        vulnerable_py = Path(self.temp_dir) / "vulnerable.py"
        vulnerable_py.write_text(
            """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    # SQL injection vulnerability - direct string interpolation
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()

def authenticate(username, password):
    # Hardcoded password - security issue
    if username == "admin" and password == "admin123":
        return True
    return False
"""
        )

        # Create sample JavaScript file with XSS vulnerability
        vulnerable_js = Path(self.temp_dir) / "vulnerable.js"
        vulnerable_js.write_text(
            """
function displayMessage(userInput) {
    // XSS vulnerability - unsanitized user input
    document.getElementById('message').innerHTML = userInput;
}

function insecureEval(userCode) {
    // Command injection vulnerability
    eval(userCode);
}
"""
        )

        # Create sample config file
        config_file = Path(self.temp_dir) / "config.json"
        config_file.write_text('{"database": "users.db", "debug": true}')

        return {
            str(vulnerable_py): vulnerable_py.read_text(),
            str(vulnerable_js): vulnerable_js.read_text(),
            str(config_file): config_file.read_text(),
        }

    def test_tool_info_structure(self):
        """Test that tool info is correctly structured."""
        tool_name, description, additional_schema = self.analyzer.get_tool_info()

        self.assertEqual(tool_name, "find_bugs")
        self.assertIn("Find potential bugs", description)
        self.assertIn("security vulnerabilities", description)

        # Verify additional schema includes bug-specific parameters
        properties = additional_schema.get("properties", {})
        self.assertIn("severity_filter", properties)
        self.assertIn("bug_categories", properties)
        self.assertIn("include_suggestions", properties)

        # Verify enum values are correct
        severity_enum = properties["severity_filter"]["items"]["enum"]
        self.assertEqual(set(severity_enum), {"critical", "high", "medium", "low"})

        category_enum = properties["bug_categories"]["items"]["enum"]
        expected_categories = {"security", "memory", "logic", "performance", "concurrency", "api_usage"}
        self.assertEqual(set(category_enum), expected_categories)

    def test_complete_tool_schema(self):
        """Test that complete tool schema merges base and bug-specific parameters."""
        schema = self.analyzer.get_complete_tool_schema()

        properties = schema.get("properties", {})

        # Verify base parameters are present
        self.assertIn("directory", properties)
        self.assertIn("focus_areas", properties)
        self.assertIn("model", properties)
        self.assertIn("max_file_size", properties)

        # Verify bug-specific parameters are present
        self.assertIn("severity_filter", properties)
        self.assertIn("bug_categories", properties)
        self.assertIn("include_suggestions", properties)

        # Verify required fields
        self.assertIn("directory", schema.get("required", []))

    def test_parameter_validation_basic(self):
        """Test basic parameter validation works correctly."""
        # Test with valid directory
        is_valid, error = self.analyzer.validate_parameters({"directory": self.temp_dir})
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Test with invalid directory
        is_valid, error = self.analyzer.validate_parameters({"directory": "/nonexistent/path"})
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)

        # Test missing directory parameter
        is_valid, error = self.analyzer.validate_parameters({})
        self.assertFalse(is_valid)
        self.assertIn("required", error)

    def test_parameter_validation_bug_specific(self):
        """Test bug-specific parameter validation."""
        base_args = {"directory": self.temp_dir}

        # Test with valid bug-specific parameters
        valid_args = {
            **base_args,
            "severity_filter": ["critical", "high"],
            "bug_categories": ["security", "memory"],
            "include_suggestions": True,
        }
        is_valid, error = self.analyzer.validate_parameters(valid_args)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_prompt_formatting_integration(self):
        """Test integration with BugFormatter for prompt generation."""
        files = {"test.py": "def vulnerable(): pass"}
        file_tree = "test.py"
        focus_areas = ["security"]
        claude_md_path = None

        # Pass bug-specific parameters via kwargs
        prompt = self.analyzer.format_analysis_prompt(
            files,
            file_tree,
            focus_areas,
            claude_md_path,
            bug_categories=["security"],
            severity_filter=["critical", "high"],
            include_suggestions=True,
        )

        # Verify prompt contains expected elements
        self.assertIn("Bug Finding Analysis Request", prompt)
        self.assertIn("security engineer and code auditor", prompt)
        self.assertIn("security", prompt.lower())
        self.assertIn("critical, high", prompt)
        self.assertIn("Fix Suggestion", prompt)

    def test_bug_parsing_functionality(self):
        """Test bug finding parsing from AI response."""
        # Sample AI response with bug findings
        sample_response = """
**BUG-001**
- **Category**: security
- **Severity**: critical
- **Title**: SQL Injection Vulnerability
- **Location**: vulnerable.py:5
- **Confidence**: 95%

**BUG-002**
- **Category**: security
- **Severity**: high
- **Title**: Hardcoded Credentials
- **Location**: vulnerable.py:10
- **Confidence**: 90%

**BUG-003**
- **Category**: security
- **Severity**: medium
- **Title**: XSS Vulnerability
- **Location**: vulnerable.js:3
- **Confidence**: 85%
"""

        bug_findings, summary_stats = self.analyzer._parse_bug_findings(sample_response)

        # Verify bug findings
        self.assertEqual(len(bug_findings), 3)

        # Check first bug
        bug1 = bug_findings[0]
        self.assertEqual(bug1["bug_id"], "BUG-001")
        self.assertEqual(bug1["category"], "security")
        self.assertEqual(bug1["severity"], "critical")
        self.assertEqual(bug1["title"], "SQL Injection Vulnerability")
        self.assertEqual(bug1["location"], "vulnerable.py:5")
        self.assertEqual(bug1["confidence"], 95)

        # Verify summary statistics
        self.assertEqual(summary_stats["total_bugs"], 3)
        self.assertEqual(summary_stats["critical"], 1)
        self.assertEqual(summary_stats["high"], 1)
        self.assertEqual(summary_stats["medium"], 1)
        self.assertEqual(summary_stats["low"], 0)
        self.assertIn("security", summary_stats["categories"])
        self.assertEqual(summary_stats["files_with_bugs"], 2)  # vulnerable.py and vulnerable.js

    def test_bug_parsing_json_format(self):
        """Test bug finding parsing from JSON-formatted AI response."""
        # Sample AI response with JSON format
        sample_response = """
Here are the bugs I found:

```json
{
  "bugs": [
    {
      "bug_id": "BUG-001",
      "category": "security",
      "severity": "critical",
      "title": "SQL Injection Vulnerability",
      "location": {
        "file": "vulnerable.py",
        "line": 5,
        "function": "get_user"
      },
      "description": "Direct string interpolation in SQL query allows SQL injection attacks",
      "code_snippet": "query = f\\"SELECT * FROM users WHERE id = {user_id}\\"",
      "confidence": 95,
      "fix_suggestion": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
    },
    {
      "bug_id": "BUG-002",
      "category": "security",
      "severity": "high",
      "title": "Hardcoded Credentials",
      "location": "vulnerable.py:10",
      "description": "Hardcoded admin credentials in source code",
      "code_snippet": "if username == \\"admin\\" and password == \\"admin123\\":",
      "confidence": 90,
      "fix_suggestion": "Store credentials securely using environment variables or a secure key management system"
    },
    {
      "bug_id": "BUG-003",
      "category": "security",
      "severity": "medium",
      "title": "XSS Vulnerability",
      "location": {
        "file": "vulnerable.js",
        "line": 3,
        "function": "displayMessage"
      },
      "description": "Unsanitized user input rendered as HTML",
      "code_snippet": "document.getElementById('message').innerHTML = userInput;",
      "confidence": 85,
      "fix_suggestion": "Use textContent instead of innerHTML or sanitize user input"
    }
  ],
  "summary": {
    "total_bugs": 3,
    "by_severity": {"critical": 1, "high": 1, "medium": 1, "low": 0},
    "by_category": {"security": 3, "memory": 0, "logic": 0, "performance": 0, "concurrency": 0, "api_usage": 0},
    "files_analyzed": 3
  }
}
```

And here's the detailed markdown report for each bug...
"""

        bug_findings, summary_stats = self.analyzer._parse_bug_findings(sample_response)

        # Verify bug findings
        self.assertEqual(len(bug_findings), 3)

        # Check first bug with dict location
        bug1 = bug_findings[0]
        self.assertEqual(bug1["bug_id"], "BUG-001")
        self.assertEqual(bug1["category"], "security")
        self.assertEqual(bug1["severity"], "critical")
        self.assertEqual(bug1["title"], "SQL Injection Vulnerability")
        self.assertEqual(bug1["location"], "vulnerable.py:5")  # Normalized from dict
        self.assertEqual(bug1["confidence"], 95)
        self.assertEqual(bug1["description"], "Direct string interpolation in SQL query allows SQL injection attacks")
        self.assertIn("SELECT * FROM users", bug1["code_snippet"])
        self.assertIn("parameterized queries", bug1["fix_suggestion"])

        # Check second bug with string location
        bug2 = bug_findings[1]
        self.assertEqual(bug2["location"], "vulnerable.py:10")  # Already a string

        # Verify summary statistics from JSON
        self.assertEqual(summary_stats["total_bugs"], 3)
        self.assertEqual(summary_stats["critical"], 1)
        self.assertEqual(summary_stats["high"], 1)
        self.assertEqual(summary_stats["medium"], 1)
        self.assertEqual(summary_stats["low"], 0)
        self.assertIn("security", summary_stats["categories"])
        self.assertEqual(summary_stats["files_with_bugs"], 2)  # vulnerable.py and vulnerable.js

    def test_bug_parsing_json_fallback(self):
        """Test fallback to text parsing when JSON parsing fails."""
        # Sample response with malformed JSON
        sample_response = """
Here are the bugs I found:

```json
{
  "bugs": [
    {
      "bug_id": "BUG-001",
      "category": "security",
      INVALID JSON HERE
    }
  ]
}
```

Since the JSON is malformed, here's the text format:

**BUG-001**
- **Category**: security
- **Severity**: critical
- **Title**: SQL Injection
- **Location**: test.py:1
- **Confidence**: 95%
"""

        bug_findings, summary_stats = self.analyzer._parse_bug_findings(sample_response)

        # Should fall back to text parsing
        self.assertEqual(len(bug_findings), 1)
        bug1 = bug_findings[0]
        self.assertEqual(bug1["bug_id"], "BUG-001")
        self.assertEqual(bug1["category"], "security")
        self.assertEqual(bug1["severity"], "critical")

    def test_bug_parsing_empty_response(self):
        """Test parsing when no bugs are found."""
        # Test with JSON format
        json_response = """
No bugs found in the analysis.

```json
{
  "bugs": [],
  "summary": {
    "total_bugs": 0,
    "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "by_category": {"security": 0, "memory": 0, "logic": 0, "performance": 0, "concurrency": 0, "api_usage": 0},
    "files_analyzed": 3
  }
}
```
"""

        bug_findings, summary_stats = self.analyzer._parse_bug_findings(json_response)
        self.assertEqual(len(bug_findings), 0)
        self.assertEqual(summary_stats["total_bugs"], 0)

        # Test with text format
        text_response = "No security issues detected.\nNo memory issues detected.\nNo logic errors found."

        bug_findings, summary_stats = self.analyzer._parse_bug_findings(text_response)
        self.assertEqual(len(bug_findings), 0)
        self.assertEqual(summary_stats["total_bugs"], 0)

    def test_usage_tracker_integration(self):
        """Test integration with UsageTracker."""
        # Verify analyzer has usage tracker
        self.assertIs(self.analyzer.usage_tracker, self.usage_tracker)

        # Verify initial state
        total_usage = self.usage_tracker.get_total_usage()
        self.assertEqual(total_usage["total_tokens"], 0)
        self.assertEqual(total_usage["call_count"], 0)

        # Test that task type detection works
        tool_name, _, _ = self.analyzer.get_tool_info()
        self.assertEqual(tool_name, "find_bugs")

    def test_response_formatting(self):
        """Test comprehensive response formatting."""
        # Create test AnalysisResult
        from base_code_analyzer import AnalysisResult

        # Sample bug analysis content
        bug_content = """
**BUG-001**
- **Category**: security
- **Severity**: critical
- **Title**: SQL Injection
- **Location**: test.py:1
- **Confidence**: 95%

**BUG-002**
- **Category**: logic
- **Severity**: high
- **Title**: Off-by-one Error
- **Location**: test.py:5
- **Confidence**: 85%
"""

        test_result = AnalysisResult(
            content=bug_content,
            usage_stats={"total_tokens": 1500, "input_tokens": 1000, "output_tokens": 500, "estimated_cost": 0.003},
            collection_stats={"files_collected": 3, "total_size": 1024},
            directory="/test/dir",
            model="gemini-2.5-pro",
            focus_areas=["security", "logic"],
        )

        formatted_response = self.analyzer.format_analysis_response(test_result)

        # Verify response structure
        self.assertIn("# Bug Analysis Report", formatted_response)
        self.assertIn("## Summary", formatted_response)
        self.assertIn("## Bug Findings Summary", formatted_response)
        self.assertIn("## Usage Statistics", formatted_response)
        self.assertIn("## Detailed Bug Analysis", formatted_response)

        # Verify key information is included
        self.assertIn("Total Bugs Found**: 2", formatted_response)
        self.assertIn("Critical**: 1", formatted_response)
        self.assertIn("High**: 1", formatted_response)
        self.assertIn("Files Analyzed**: 3", formatted_response)
        self.assertIn("Total Tokens**: 1,500", formatted_response)
        self.assertIn("$0.003", formatted_response)

    def test_file_collection_integration(self):
        """Test integration with file collection from BaseCodeAnalyzer."""
        # Test that file collection works with the test directory
        files, file_tree = self.analyzer.collect_files(self.temp_dir, 1048576)

        # Should collect the test files we created
        self.assertGreater(len(files), 0)
        self.assertIn("vulnerable.py", file_tree or "")

        # Verify file contents are collected
        py_file_found = False
        for file_path, content in files.items():
            if file_path.endswith("vulnerable.py"):
                py_file_found = True
                self.assertIn("sqlite3", content)
                self.assertIn("SELECT * FROM users", content)

        self.assertTrue(py_file_found, "vulnerable.py should be found in collected files")


if __name__ == "__main__":
    unittest.main()
