# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Bug-specific prompt formatter for code analysis.

This module provides specialized prompts for different categories of bug detection,
focusing on security vulnerabilities, memory issues, logic errors, and other
bug types that AI can effectively identify in code.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BugFormatter:
    """Formatter for bug-specific analysis prompts."""

    def __init__(self):
        """Initialize the bug formatter."""
        pass

    def format_bug_finding_request(
        self,
        files: Dict[str, str],
        file_tree: str,
        bug_categories: List[str],
        focus_areas: List[str],
        claude_md_path: Optional[str],
        include_suggestions: bool = True,
        severity_filter: Optional[List[str]] = None,
    ) -> str:
        """Format a comprehensive bug finding request for AI analysis.

        Args:
            files: Dictionary mapping file paths to contents
            file_tree: String representation of the file structure
            bug_categories: Specific categories of bugs to look for
            focus_areas: Additional focus areas for analysis
            claude_md_path: Optional path to CLAUDE.md file
            include_suggestions: Whether to include fix suggestions
            severity_filter: Optional severity levels to focus on

        Returns:
            Formatted prompt string for bug finding analysis
        """
        # Build category-specific instructions
        category_instructions = self._build_category_instructions(bug_categories)

        # Build severity filter instructions
        severity_instructions = self._build_severity_instructions(severity_filter)

        # Build focus area instructions
        focus_instructions = self._build_focus_instructions(focus_areas)

        # Read CLAUDE.md if available
        project_context = ""
        if claude_md_path and claude_md_path in files:
            project_context = f"""
## Project Context (from CLAUDE.md)
{files[claude_md_path]}
"""

        # Build the comprehensive prompt
        prompt = f"""# Bug Finding Analysis Request

You are a senior security engineer and code auditor tasked with finding potential bugs, security vulnerabilities, and correctness issues in the provided codebase. Your analysis should be thorough, systematic, and focused on real, actionable issues.

## Analysis Objectives

**Primary Goal**: Identify potential bugs, security vulnerabilities, and correctness issues that could lead to:
- Security breaches or data exposure
- System crashes or instability
- Incorrect behavior or logic errors
- Performance problems or resource leaks
- Concurrency issues or race conditions

**Focus Areas**: {', '.join(focus_areas) if focus_areas else 'General bug detection across all categories'}

{category_instructions}

{severity_instructions}

{project_context}

## Codebase Structure
```
{file_tree}
```

## Code to Analyze

"""

        # Add each file's content
        for file_path, content in files.items():
            if file_path != claude_md_path:  # Skip CLAUDE.md as it's already included above
                prompt += f"""
### File: {file_path}
```{self._get_file_language(file_path)}
{content}
```
"""

        # Analysis instructions
        analysis_instructions = self._build_analysis_instructions(include_suggestions)

        # Build the fix suggestion field for JSON
        fix_suggestion_json = '"fix_suggestion": "Recommended fix or mitigation",' if include_suggestions else ""

        # Build the numbered list item for fix suggestion
        fix_suggestion_item = "9. **Fix Suggestion**: Recommended fix or mitigation" if include_suggestions else ""

        # Build the example fix line
        fix_example = (
            "- **Fix**: Use parameterized queries: `cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))`"
            if include_suggestions
            else ""
        )

        # Categories list
        categories = ", ".join(["security", "memory", "logic", "performance", "concurrency", "api_usage"])

        prompt += f"""

{analysis_instructions}

## Output Format

**IMPORTANT**: Provide your findings in both structured JSON and human-readable markdown formats.

First, provide a JSON summary of all bugs found within a markdown code block:

```json
{{
  "bugs": [
    {{
      "bug_id": "BUG-001",
      "category": "security|memory|logic|performance|concurrency|api_usage",
      "severity": "critical|high|medium|low",
      "title": "Brief descriptive title",
      "location": {{
        "file": "path/to/file.py",
        "line": 45,
        "function": "function_name"
      }},
      "description": "Clear explanation of the issue and potential impact",
      "code_snippet": "relevant code showing the problem",
      "confidence": 95,
      {fix_suggestion_json}
      "additional_context": {{}}
    }}
  ],
  "summary": {{
    "total_bugs": 0,
    "by_severity": {{"critical": 0, "high": 0, "medium": 0, "low": 0}},
    "by_category": {{"security": 0, "memory": 0, "logic": 0, "performance": 0, "concurrency": 0, "api_usage": 0}},
    "files_analyzed": 0
  }}
}}
```

Then, provide a detailed markdown report for each bug:

## Bug Details

For each bug found, provide:

1. **Bug ID**: Unique identifier (e.g., BUG-001)
2. **Category**: {categories}
3. **Severity**: critical, high, medium, or low
4. **Title**: Brief descriptive title
5. **File & Location**: File path and line number (if identifiable)
6. **Description**: Clear explanation of the issue and potential impact
7. **Code Snippet**: Relevant code showing the problem
8. **Confidence**: Your confidence level (0-100%)
{fix_suggestion_item}

### Example Markdown Format

**BUG-001**
- **Category**: security
- **Severity**: critical
- **Title**: SQL Injection Vulnerability
- **Location**: api/users.py:45
- **Description**: Direct string interpolation in SQL query allows SQL injection attacks
- **Code**: `query = f"SELECT * FROM users WHERE id = {{user_id}}"`
- **Confidence**: 95%
{fix_example}

If no bugs are found in a category, include that in the JSON summary and state "No [category] issues detected" in the markdown.

Begin your analysis now:"""

        return prompt

    def _build_category_instructions(self, bug_categories: List[str]) -> str:
        """Build category-specific analysis instructions."""
        if not bug_categories:
            bug_categories = ["security", "memory", "logic", "performance", "concurrency", "api_usage"]

        instructions = "## Bug Categories to Analyze\n\n"

        category_details = {
            "security": self._get_security_instructions(),
            "memory": self._get_memory_instructions(),
            "logic": self._get_logic_instructions(),
            "performance": self._get_performance_instructions(),
            "concurrency": self._get_concurrency_instructions(),
            "api_usage": self._get_api_usage_instructions(),
        }

        for category in bug_categories:
            if category in category_details:
                instructions += f"### {category.title()} Issues\n{category_details[category]}\n\n"

        return instructions

    def _get_security_instructions(self) -> str:
        """Get detailed security vulnerability detection instructions."""
        return """**Look for these security vulnerabilities:**

**Input Validation & Injection Attacks:**
- SQL injection: Direct string interpolation in SQL queries
- NoSQL injection: Unsafe query construction
- Command injection: Unsanitized input to system commands
- Path traversal: User input in file paths without validation
- XSS vulnerabilities: Unsanitized user input in HTML output
- LDAP injection: Unsafe LDAP query construction

**Authentication & Authorization:**
- Missing authentication checks on sensitive endpoints
- Weak password policies or storage
- Session management flaws
- Authorization bypass opportunities
- Privilege escalation vulnerabilities
- JWT token vulnerabilities (weak secrets, no expiration)

**Cryptographic Issues:**
- Weak or deprecated encryption algorithms
- Hardcoded encryption keys or secrets
- Improper random number generation
- Insecure hash functions (MD5, SHA1 for passwords)
- Missing certificate validation
- Improper key management

**Data Exposure:**
- Sensitive data in logs
- Information disclosure in error messages
- Unencrypted sensitive data storage/transmission
- Missing access controls on sensitive data
- Debug information exposure in production

**Configuration & Deployment:**
- Default credentials still in use
- Overly permissive CORS policies
- Missing security headers
- Insecure default configurations
- Exposed administrative interfaces
- Missing input sanitization

**Specific Patterns to Flag:**
- `eval()`, `exec()` with user input
- `os.system()`, `subprocess.call()` with unsanitized input
- Database queries with string concatenation
- File operations using user-provided paths
- Deserialization of untrusted data
- Missing CSRF protection
- Improper certificate/TLS validation"""

    def _get_memory_instructions(self) -> str:
        """Get memory-related bug detection instructions."""
        return """**Look for these memory issues:**

**Memory Leaks:**
- Objects not properly released
- Event listeners not removed
- File handles/connections not closed
- Large data structures growing unbounded
- Circular references preventing garbage collection

**Buffer Issues:**
- Buffer overflows/underflows
- Array bounds violations
- String buffer overruns
- Unsafe memory operations

**Pointer/Reference Issues:**
- Null pointer dereferences
- Use-after-free
- Double-free errors
- Dangling pointers
- Uninitialized variables/pointers

**Resource Management:**
- Resources not properly closed (files, connections, streams)
- Missing try-finally or with statements
- Resource leaks in exception paths
- Improper cleanup in destructors/finalizers"""

    def _get_logic_instructions(self) -> str:
        """Get logic error detection instructions."""
        return """**Look for these logic errors:**

**Conditional Logic:**
- Off-by-one errors in loops and array access
- Incorrect boolean logic (AND/OR confusion)
- Missing or incorrect null/empty checks
- Improper error condition handling
- Edge case handling failures

**Control Flow:**
- Unreachable code
- Infinite loops or recursion
- Missing break statements in switch/case
- Incorrect exception handling
- Return value not checked

**Data Handling:**
- Race conditions in data access
- Incorrect data type assumptions
- Missing input validation
- Incorrect algorithm implementation
- State management errors

**Mathematical/Calculation:**
- Division by zero possibilities
- Integer overflow/underflow
- Floating point precision issues
- Incorrect mathematical operations
- Wrong assumptions about number ranges"""

    def _get_performance_instructions(self) -> str:
        """Get performance issue detection instructions."""
        return """**Look for these performance issues:**

**Algorithmic Inefficiency:**
- Inefficient algorithms (O(n²) where O(n log n) possible)
- Nested loops that could be optimized
- Repeated expensive operations
- Unnecessary sorting or searching

**Resource Usage:**
- Memory waste (large unused allocations)
- CPU-intensive operations in UI threads
- Blocking operations without timeouts
- Inefficient data structures for use case

**I/O Performance:**
- Synchronous I/O in performance-critical paths
- Missing connection pooling
- Inefficient database queries (N+1 problems)
- Large file loading without streaming
- Missing caching for expensive operations

**Concurrency Issues:**
- Excessive thread creation
- Lock contention
- Missing async/await opportunities
- Inefficient synchronization"""

    def _get_concurrency_instructions(self) -> str:
        """Get concurrency issue detection instructions."""
        return """**Look for these concurrency issues:**

**Race Conditions:**
- Shared data access without synchronization
- Check-then-act race conditions
- Non-atomic operations on shared state
- Missing volatile/atomic declarations

**Deadlocks:**
- Multiple locks acquired in different orders
- Nested locking without timeout
- Lock not released in all code paths
- Circular dependencies in locking

**Thread Safety:**
- Non-thread-safe operations in multi-threaded context
- Shared mutable state without protection
- Improper use of thread-local storage
- Missing synchronization primitives

**Async/Await Issues:**
- Blocking calls in async methods
- Missing await keywords
- Improper exception handling in async code
- Resource contention in concurrent operations"""

    def _get_api_usage_instructions(self) -> str:
        """Get API usage issue detection instructions."""
        return """**Look for these API usage issues:**

**Incorrect API Usage:**
- Deprecated function/method usage
- Wrong parameter types or orders
- Missing required parameters
- Improper error handling for API calls

**Resource Management:**
- Resources not properly closed (connections, files, streams)
- Missing cleanup in finally blocks
- Improper disposal of IDisposable objects
- Connection leaks

**Error Handling:**
- Catching and ignoring exceptions
- Not handling API-specific exceptions
- Missing timeout handling
- Improper retry logic

**Protocol Violations:**
- Not following API contracts
- Improper state management with stateful APIs
- Missing required headers or authentication
- Incorrect HTTP method usage"""

    def _build_severity_instructions(self, severity_filter: Optional[List[str]]) -> str:
        """Build severity filtering instructions."""
        if not severity_filter:
            return """## Severity Assessment

Classify each bug using these severity levels:
- **Critical**: Security vulnerabilities, data loss, system crashes
- **High**: Correctness issues, significant performance problems
- **Medium**: Code quality issues, potential future problems
- **Low**: Minor optimizations, style improvements

Focus on **critical** and **high** severity issues first."""

        severity_list = ", ".join(severity_filter)
        return f"""## Severity Focus

**ONLY report bugs with these severity levels: {severity_list}**

Severity definitions:
- **Critical**: Security vulnerabilities, data loss, system crashes
- **High**: Correctness issues, significant performance problems
- **Medium**: Code quality issues, potential future problems
- **Low**: Minor optimizations, style improvements"""

    def _build_focus_instructions(self, focus_areas: List[str]) -> str:
        """Build focus area specific instructions."""
        if not focus_areas:
            return ""

        return f"""## Additional Focus Areas

Pay special attention to: {', '.join(focus_areas)}

Look for issues specifically related to these areas throughout your analysis."""

    def _build_analysis_instructions(self, include_suggestions: bool) -> str:
        """Build analysis methodology instructions."""
        suggestion_text = (
            """
- **Fix Suggestions**: For each bug, provide specific, actionable fix recommendations
- **Prevention**: Suggest how to prevent similar issues in the future"""
            if include_suggestions
            else ""
        )

        return f"""## Analysis Methodology

**Be Systematic:**
- Examine each file for potential issues
- Consider interactions between components
- Look for common vulnerability patterns
- Check error handling and edge cases

**Be Practical:**
- Focus on real, exploitable issues (not theoretical)
- Consider the actual risk and impact
- Prioritize based on severity and exploitability
- Provide confidence levels for each finding{suggestion_text}

**Be Thorough:**
- Check all user input handling
- Examine data flow and transformations
- Review error handling and logging
- Consider concurrent execution scenarios"""

    def _get_file_language(self, file_path: str) -> str:
        """Determine the programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".cs": "csharp",
            ".sql": "sql",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
        }

        for ext, lang in extension_map.items():
            if file_path.lower().endswith(ext):
                return lang

        return "text"
