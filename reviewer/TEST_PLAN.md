# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Code Review MCP Server Test Plan

## Overview

Comprehensive test plan for the Code Review MCP Server, covering unit tests, integration tests, and end-to-end scenarios.

## Test Structure

```
reviewer/
├── tests/
│   ├── __init__.py
│   ├── test_file_collector.py
│   ├── test_review_formatter.py
│   ├── test_mcp_server.py
│   ├── test_integration.py
│   └── fixtures/
│       ├── sample_project/
│       │   ├── src/
│       │   │   ├── main.py
│       │   │   └── utils.py
│       │   ├── tests/
│       │   │   └── test_main.py
│       │   ├── README.md
│       │   └── CLAUDE.md
│       └── mock_responses/
│           └── gemini_review.json
```

## Unit Tests

### 1. File Collector Tests (`test_file_collector.py`)

```python
class TestFileCollector:
    def test_collect_python_files():
        """Test collection of Python files"""

    def test_collect_javascript_files():
        """Test collection of JS/TS files"""

    def test_respect_gitignore():
        """Ensure .gitignore patterns are respected"""

    def test_exclude_binary_files():
        """Verify binary files are skipped"""

    def test_handle_encoding_errors():
        """Test graceful handling of encoding issues"""

    def test_file_size_limits():
        """Test enforcement of file size limits"""

    def test_directory_traversal_safety():
        """Ensure no directory traversal exploits"""

    def test_symlink_handling():
        """Test behavior with symbolic links"""

    def test_empty_directory():
        """Handle empty directories gracefully"""

    def test_nested_directories():
        """Test deep directory structures"""
```

### 2. Review Formatter Tests (`test_review_formatter.py`)

```python
class TestReviewFormatter:
    def test_format_single_file():
        """Test formatting a single file for review"""

    def test_format_multiple_files():
        """Test formatting multiple files"""

    def test_include_claude_md():
        """Verify CLAUDE.md is properly included"""

    def test_file_tree_generation():
        """Test file tree structure output"""

    def test_prompt_template_substitution():
        """Test template variable substitution"""

    def test_focus_areas_formatting():
        """Test custom focus areas in prompt"""

    def test_large_codebase_handling():
        """Test handling of size limits"""

    def test_special_characters_escaping():
        """Test handling of special characters"""
```

### 3. MCP Server Tests (`test_mcp_server.py`)

```python
class TestMCPServer:
    def test_tool_registration():
        """Test tool is properly registered"""

    def test_input_validation():
        """Test parameter validation"""

    def test_absolute_path_requirement():
        """Ensure only absolute paths accepted"""

    def test_directory_exists_validation():
        """Test directory existence check"""

    def test_response_formatting():
        """Test MCP response format"""

    def test_error_response_format():
        """Test error response formatting"""

    def test_async_operation():
        """Test async handling"""
```

## Integration Tests

### 1. Gemini Integration (`test_integration.py`)

```python
class TestGeminiIntegration:
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No API key")
    def test_gemini_api_call():
        """Test actual API call with real Gemini"""
        # Use a small test file to minimize API costs

    def test_rate_limiting_handling():
        """Test rate limit retry logic with real API"""

    def test_api_error_handling():
        """Test error scenarios with invalid inputs to real API"""

    def test_response_parsing():
        """Test parsing real Gemini responses"""

    def test_timeout_handling():
        """Test request timeout with real network"""
```

### 2. End-to-End Tests

```python
class TestEndToEnd:
    @pytest.mark.e2e
    def test_review_sample_project():
        """Review the test fixture project"""

    def test_review_empty_project():
        """Handle empty directory review"""

    def test_review_large_project():
        """Test with size limit edge cases"""

    def test_review_with_focus_areas():
        """Test with specific focus areas"""

    def test_review_mixed_languages():
        """Test project with multiple languages"""
```

## Test Scenarios

### 1. Happy Path
- Review a small Python project
- Review a mixed JS/Python project
- Review with specific focus on security
- Review documentation-heavy project

### 2. Edge Cases
- Empty directory
- Directory with only binary files
- Directory with files exceeding size limits
- Deeply nested directory structure (>10 levels)
- Directory with circular symlinks
- Non-UTF8 encoded files
- Files with no read permissions

### 3. Error Scenarios
- Invalid directory path
- Relative path provided
- Directory doesn't exist
- No GEMINI_API_KEY set
- Network timeout during API call
- Gemini API returns error
- Malformed response from Gemini

### 4. Security Tests
- Path traversal attempts (`../../../etc/passwd`)
- Symlink to sensitive files
- Very large file DoS attempt
- Unicode normalization attacks

## Test Strategies (No Mocks)

### 1. Real File System Testing
```python
# Use actual test directories with real files
@pytest.fixture
def sample_project(tmp_path):
    """Create a real sample project structure"""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass")
    (tmp_path / "CLAUDE.md").write_text("# Test project rules")
    return tmp_path

@pytest.fixture
def real_project_path():
    """Use the reviewer directory itself for testing"""
    return Path(__file__).parent.parent.absolute()
```

### 2. Gemini Test Fixture (Flash Model)
```python
@pytest.fixture
def gemini_test_client():
    """Test fixture using Gemini 1.5 Flash for testing"""
    class GeminiTestClient:
        def __init__(self):
            # Use cheaper Gemini 1.5 Flash for testing
            self.client = GeminiClient(model="gemini-1.5-flash")
            self.total_tokens = 0
            self.call_count = 0

        def review_code(self, content):
            # Make real API call with Flash model
            response = self.client.generate_content(content)
            self.total_tokens += response.usage_metadata.total_tokens
            self.call_count += 1
            return response

        def get_usage_report(self):
            return {
                "tokens": self.total_tokens,
                "calls": self.call_count,
                "estimated_cost": self.total_tokens * 0.00000001,  # Flash pricing
                "model": "gemini-1.5-flash"
            }

    client = GeminiTestClient()
    yield client

    # Report usage after test
    usage = client.get_usage_report()
    print(f"\nTest API Usage ({usage['model']}): {usage['calls']} calls, "
          f"{usage['tokens']} tokens, ~${usage['estimated_cost']:.6f}")
```

### 3. Production Model Fixture
```python
@pytest.fixture
def gemini_production_client():
    """Test fixture for production model tests"""
    class GeminiProductionClient:
        def __init__(self):
            # Use production Gemini 2.5 Pro model
            self.client = GeminiClient(model="gemini-2.0-pro-exp")
            self.total_tokens = 0
            self.call_count = 0

        def review_code(self, content):
            response = self.client.generate_content(content)
            self.total_tokens += response.usage_metadata.total_tokens
            self.call_count += 1
            return response

        def get_usage_report(self):
            return {
                "tokens": self.total_tokens,
                "calls": self.call_count,
                "estimated_cost": self.total_tokens * 0.000002,  # Pro pricing
                "model": "gemini-2.0-pro-exp"
            }

    client = GeminiProductionClient()
    yield client

    usage = client.get_usage_report()
    print(f"\nProduction API Usage ({usage['model']}): {usage['calls']} calls, "
          f"{usage['tokens']} tokens, ~${usage['estimated_cost']:.4f}")
```

### 4. Smart Test Data Fixture
```python
@pytest.fixture
def minimal_test_project():
    """Creates minimal test data to reduce API costs"""
    return {
        "tiny": "def add(a, b): return a + b",  # ~10 tokens
        "small": "# Small module\n" + "def hello():\n    return 'world'\n" * 5,  # ~50 tokens
        "medium": open("reviewer/test_fixtures/medium_sample.py").read(),  # ~500 tokens
    }

def test_review_with_flash_model(gemini_test_client, minimal_test_project):
    """Example test using cheap Flash model fixture"""
    # Start with tiny code - very cheap with Flash
    response = gemini_test_client.review_code(
        f"Review this code:\n{minimal_test_project['tiny']}"
    )
    assert "function" in response.text.lower()

    # Can test more extensively with Flash due to lower cost
    response = gemini_test_client.review_code(
        f"Review this code:\n{minimal_test_project['small']}"
    )
    assert response is not None

@pytest.mark.expensive
def test_review_with_production_model(gemini_production_client, minimal_test_project):
    """Example test using expensive production model - run sparingly"""
    # Only test one small sample with production model
    response = gemini_production_client.review_code(
        f"Review this code:\n{minimal_test_project['tiny']}"
    )
    # Production model should give higher quality responses
    assert len(response.text) > 50  # Expect more detailed response
```

### 4. MCP Protocol Testing
```python
# Test with real MCP server running
@pytest.fixture
async def running_mcp_server():
    """Start actual MCP server for testing"""
    server = await start_server()
    yield server
    await server.shutdown()
```

## Performance Tests

```python
class TestPerformance:
    def test_large_file_collection_speed():
        """Ensure file collection is fast"""
        # Should collect 1000 files in < 5 seconds

    def test_memory_usage():
        """Test memory usage with large codebases"""
        # Should not exceed 500MB for 10MB codebase
```

## Test Execution

```bash
# Run all tests except expensive ones (uses Flash model - cheap)
GEMINI_API_KEY=your-key pytest reviewer/tests/ -m "not expensive"

# Run only local tests (no API calls)
pytest reviewer/tests/ -m "not integration and not e2e"

# Run integration tests with Flash model (cheap)
pytest reviewer/tests/ -m "integration and not expensive"

# Run expensive tests with production model (costly - run sparingly)
pytest reviewer/tests/ -m "expensive" --maxfail=1

# Full test suite (Flash + Production models)
pytest reviewer/tests/ --maxfail=1

# Run with coverage
pytest reviewer/tests/ --cov=reviewer --cov-report=html

# Run specific test file
pytest reviewer/tests/test_file_collector.py -v
```

## Continuous Testing

### Pre-commit Hooks
```yaml
- repo: local
  hooks:
  - id: reviewer-tests
    name: Code Reviewer Tests
    entry: pytest reviewer/tests/ -m "not integration"
    language: system
    files: ^reviewer/.*\.py$
    pass_filenames: false
```

### GitHub Actions
```yaml
name: Test Code Reviewer
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: |
        pip install -r reviewer/requirements-test.txt
        pytest reviewer/tests/
```

## Test Data

### Sample Files for Testing

1. **Valid Python File**
```python
# test_fixtures/valid.py
def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b
```

2. **File with Issues**
```python
# test_fixtures/problematic.py
def risky_function(user_input):
    eval(user_input)  # Security issue
    print(password)   # Undefined variable
```

3. **Large File** (generated)
```python
# Generate 2MB Python file for size testing
content = "# Large file\n" + "x = 1\n" * 100000
```

## Test Cost Management

Since we're using real API calls:

1. **Minimize API Usage**:
   - Use smallest possible test inputs
   - Cache responses for repeated test runs (in test mode only)
   - Mark expensive tests with `@pytest.mark.expensive`
   - Use `--maxfail=1` to stop on first failure

2. **Test Data Strategy**:
   - Tiny test files (<100 lines) for most tests
   - One comprehensive test with real codebase
   - Reuse test outputs for verification

3. **CI/CD Considerations**:
   - Run full integration tests only on main branch
   - Use API key from secrets
   - Daily/weekly schedule for expensive tests

## Success Criteria

1. **Unit Test Coverage**: >90% code coverage
2. **Integration Tests**: All pass with real Gemini API
3. **E2E Tests**: At least one successful review of real code
4. **Performance**: <5s for 1000 file collection
5. **Security**: No path traversal vulnerabilities
6. **Error Handling**: All errors return proper MCP format
7. **API Cost**:
   - Flash model tests: <$0.05 per run
   - Production model tests: <$0.20 per run (marked as expensive)
   - Full test suite: <$0.25 per run
