# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Find Bugs Tool Design Specification

## Overview

The `find_bugs` tool is a specialized code analysis tool that extends the shared component architecture to identify potential bugs, security vulnerabilities, and correctness issues in codebases. It reuses 70%+ of the existing infrastructure while providing bug-specific analysis capabilities.

## Tool Interface

### Tool Name and Description
- **Tool Name**: `find_bugs`
- **Description**: "Find potential bugs, security vulnerabilities, and correctness issues in code using AI analysis"
- **Task Type**: `bug_finding` (for usage tracking)

### Parameters Schema

The tool extends the base schema from BaseCodeAnalyzer with bug-specific parameters:

```json
{
  "type": "object",
  "properties": {
    // Base parameters from BaseCodeAnalyzer
    "directory": {
      "type": "string",
      "description": "Absolute path to the directory to analyze for bugs"
    },
    "focus_areas": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Optional: Specific bug categories to focus on"
    },
    "model": {
      "type": "string",
      "description": "Optional: Gemini model to use (default: gemini-2.5-pro)",
      "enum": ["gemini-1.5-flash", "gemini-2.5-pro"]
    },
    "max_file_size": {
      "type": "number",
      "description": "Optional: Maximum file size in bytes (default: 1048576)"
    },

    // Bug-specific parameters
    "severity_filter": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["critical", "high", "medium", "low"]
      },
      "description": "Optional: Only report bugs of specified severity levels"
    },
    "bug_categories": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["security", "memory", "logic", "performance", "concurrency", "api_usage"]
      },
      "description": "Optional: Specific categories of bugs to look for"
    },
    "include_suggestions": {
      "type": "boolean",
      "description": "Optional: Include fix suggestions for found bugs (default: true)"
    }
  },
  "required": ["directory"]
}
```

## Bug Categories and Detection Focus

### 1. Security Vulnerabilities
- SQL injection possibilities
- XSS vulnerabilities
- Authentication/authorization flaws
- Insecure data handling
- Cryptographic issues
- Input validation failures

### 2. Memory Issues
- Memory leaks
- Buffer overflows/underflows
- Use-after-free
- Double-free
- Null pointer dereferences
- Uninitialized variables

### 3. Logic Errors
- Off-by-one errors
- Incorrect conditional logic
- Race conditions
- Infinite loops
- Dead code
- Unreachable code

### 4. Performance Issues
- Inefficient algorithms
- Resource leaks
- Unnecessary computations
- Poor data structure choices
- I/O bottlenecks

### 5. Concurrency Issues
- Race conditions
- Deadlocks
- Thread safety violations
- Incorrect synchronization
- Atomic operation misuse

### 6. API Usage Issues
- Incorrect API usage
- Missing error handling
- Resource not properly closed
- Deprecated function usage
- Protocol violations

## Bug Result Structure

### Bug Finding Data Model

```python
class BugFinding:
    def __init__(self, bug_id: str, category: str, severity: str,
                 title: str, description: str, file_path: str,
                 line_number: Optional[int], code_snippet: str,
                 suggestion: Optional[str], confidence: float):
        self.bug_id = bug_id
        self.category = category  # security, memory, logic, etc.
        self.severity = severity  # critical, high, medium, low
        self.title = title
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.suggestion = suggestion
        self.confidence = confidence  # 0.0-1.0

class BugAnalysisResult:
    def __init__(self, findings: List[BugFinding], summary: Dict,
                 analysis_metadata: AnalysisResult):
        self.findings = findings
        self.summary = summary
        self.analysis_metadata = analysis_metadata
```

### Severity Classification

- **Critical**: Security vulnerabilities, memory corruption, data loss
- **High**: Logic errors affecting correctness, performance bottlenecks
- **Medium**: Code quality issues, potential future problems
- **Low**: Style issues, minor optimizations

### Confidence Levels

- **High (0.8-1.0)**: Clear, definitive bugs
- **Medium (0.5-0.8)**: Likely bugs requiring review
- **Low (0.2-0.5)**: Potential issues, code smells

## Response Format

### Summary Section
```json
{
  "total_bugs_found": 15,
  "critical_count": 2,
  "high_count": 5,
  "medium_count": 6,
  "low_count": 2,
  "categories_found": ["security", "logic", "performance"],
  "files_with_bugs": 8,
  "overall_risk_level": "high"
}
```

### Detailed Findings
Each bug includes:
- Unique identifier
- Category and severity
- Location (file, line)
- Code snippet
- Description and impact
- Fix suggestion (if requested)
- Confidence level

### Formatted Output Example
```
# Bug Analysis Report

## Summary
- **Directory**: /path/to/project
- **Total Bugs Found**: 15 (2 critical, 5 high, 6 medium, 2 low)
- **Files Affected**: 8 out of 25 analyzed
- **Overall Risk Level**: HIGH

## Critical Issues

### 1. SQL Injection Vulnerability
- **File**: `api/user.py:45`
- **Category**: Security
- **Confidence**: 95%
- **Description**: Direct string interpolation in SQL query
- **Code**: `query = f"SELECT * FROM users WHERE id = {user_id}"`
- **Fix**: Use parameterized queries or ORM methods

## High Priority Issues
[... detailed listings ...]

## Usage Statistics
- **Total Tokens**: 12,450
- **Analysis Time**: 45 seconds
- **Cost**: $0.031
```

## Shared Component Integration

The find_bugs tool leverages the shared architecture:

1. **BaseCodeAnalyzer**: Core workflow orchestration
2. **FileCollector**: Same file collection and filtering
3. **GeminiClient**: Task-aware communication with "bug_finding" task type
4. **UsageTracker**: Centralized cost tracking across tools

### Code Reuse Metrics
- **File Collection**: 100% reuse (FileCollector)
- **Parameter Validation**: 80% reuse (base + bug-specific)
- **AI Communication**: 90% reuse (GeminiClient)
- **Usage Tracking**: 100% reuse (UsageTracker)
- **Result Formatting**: 30% reuse (custom bug formatting)

**Overall Code Reuse**: ~75% (exceeds target of 70%)

## Implementation Classes

### 1. BugFindingAnalyzer
Extends BaseCodeAnalyzer with bug-specific functionality:
- Bug-specific prompt generation
- Result parsing for bug findings
- Severity classification
- Bug deduplication

### 2. BugFormatter
Specialized formatter for bug-specific prompts:
- Security vulnerability detection prompts
- Memory issue detection prompts
- Logic error detection prompts
- Category-specific instructions

### 3. BugResultParser
Parses AI responses into structured bug findings:
- Extracts bug metadata
- Classifies severity levels
- Validates confidence scores
- Handles multiple bug formats

## Error Handling and Edge Cases

### Input Validation
- Validate severity_filter values
- Validate bug_categories values
- Handle empty or invalid directories
- Graceful handling of unsupported file types

### Analysis Edge Cases
- No bugs found (return empty findings)
- Low confidence results handling
- Duplicate bug detection
- Large codebase handling
- API rate limiting

### Output Edge Cases
- Malformed AI responses
- Missing required bug fields
- Invalid severity classifications
- Confidence score validation

## Testing Strategy

### Unit Tests Required
1. **Parameter Validation Tests**: Bug-specific parameters
2. **Bug Detection Tests**: Known bug samples
3. **Severity Classification Tests**: Proper categorization
4. **Result Parsing Tests**: AI response parsing
5. **Integration Tests**: End-to-end bug finding

### Test Bug Samples
Create sample files with known bugs:
- SQL injection vulnerabilities
- Memory leak examples
- Logic error samples
- Performance bottlenecks
- Concurrency issues

## Performance Considerations

### Optimization Strategies
- File filtering for relevant code types
- Incremental analysis for large codebases
- Parallel processing where possible
- Caching of analysis results
- Smart tokenization to stay within limits

### Expected Performance
- **Small Projects** (< 100 files): 30-60 seconds
- **Medium Projects** (100-500 files): 2-5 minutes
- **Large Projects** (500+ files): 5-15 minutes
- **Token Usage**: 50-200K tokens depending on size

## Future Extensions

### Potential Enhancements
1. **Custom Rule Support**: User-defined bug patterns
2. **Historical Analysis**: Track bug trends over time
3. **Integration Testing**: Find integration-specific bugs
4. **Fix Generation**: Automatic fix suggestions
5. **Continuous Monitoring**: Regular bug scanning

### Integration Opportunities
1. **CI/CD Integration**: Automated bug scanning
2. **IDE Plugins**: Real-time bug detection
3. **Code Review Integration**: Pre-commit bug checking
4. **Metrics Dashboard**: Bug tracking and trends

This design provides a comprehensive framework for implementing the find_bugs tool while maximizing code reuse and maintaining consistency with the existing review_code tool architecture.
