# Testing Strategy for Code Analysis Tools

## Overview

This document clarifies the testing philosophy and strategy for the code analysis tools project. It emphasizes our commitment to real integration testing while providing practical guidelines for different testing scenarios.

## Core Testing Philosophy: Real Integration First

Our testing approach prioritizes **real, working tests** that validate actual functionality:

### 1. Real Integration Tests (Primary Focus)
- **Always test with real files**: Create actual test directories and files
- **Use real parsers**: Test parsing logic with actual code samples
- **Validate real workflows**: Exercise complete tool pipelines
- **Test real error conditions**: Verify handling of actual edge cases

### 2. External Service Boundaries
For external services that require API keys, network access, or incur costs:
- **Use test fixtures**: Pre-recorded responses from real API calls
- **Create test servers**: Local implementations that simulate service behavior
- **Environment isolation**: Separate test environments from production
- **Cost management**: Avoid expensive API calls in routine test runs

### 3. Component Testing
- **Test real implementations**: Never bypass core business logic
- **Use actual data**: Create realistic test data sets
- **Verify real behavior**: Ensure tests catch actual bugs

## Testing Categories

### Integration Tests (80% of test suite)
Tests that verify complete workflows with real components:
```python
def test_real_file_collection(self):
    # Create actual test files
    test_dir = self.create_test_directory()

    # Use real file collector
    collector = FileCollector()
    files = collector.collect_files(test_dir)

    # Verify actual results
    assert len(files) > 0
```

### Component Tests (15% of test suite)
Tests that verify individual components with real data:
```python
def test_bug_parsing_real_response(self):
    # Use actual AI response format
    real_response = load_fixture('real_ai_bug_response.txt')

    # Test real parser
    bugs, stats = analyzer._parse_bug_findings(real_response)

    # Verify parsing worked correctly
    assert bugs[0]['severity'] == 'critical'
```

### Performance Tests (5% of test suite)
Tests that ensure acceptable performance with real data:
```python
def test_large_codebase_performance(self):
    # Use real large codebase sample
    large_dir = 'test_data/large_project'

    # Time actual collection
    start = time.time()
    files = collector.collect_files(large_dir)
    duration = time.time() - start

    # Verify performance
    assert duration < 5.0  # Should complete in 5 seconds
```

## External Service Testing Guidelines

### For AI/LLM Services (Gemini API)
1. **Development**: Use fixture-based responses from real API calls
2. **CI/CD**: Skip expensive API tests or use minimal test quotas
3. **Integration**: Run full API tests weekly with monitoring
4. **Fixtures**: Update fixtures quarterly with fresh API responses

### For Network Services
1. **Local testing**: Run services in containers
2. **Network isolation**: Test in controlled environments
3. **Timeout handling**: Verify real timeout scenarios
4. **Error simulation**: Test real network failures

## Test Data Management

### Creating Test Fixtures
```bash
# Capture real API responses for test fixtures
python capture_api_responses.py --output test_fixtures/

# Create realistic test codebases
python generate_test_projects.py --complexity medium
```

### Test Data Categories
- **Small projects**: 5-10 files for quick tests
- **Medium projects**: 50-100 files for integration tests
- **Large projects**: 500+ files for performance tests
- **Edge cases**: Empty files, binary files, special characters

## Updated File Headers

Replace any contradictory statements with:

```python
"""Tests for [Component Name].

Testing approach:
- Real integration tests with actual files and data
- External service boundaries handled appropriately
- See TESTING_STRATEGY.md for detailed guidelines
"""
```

## Running Tests

### Full Test Suite (MANDATORY for commits)
```bash
./run_tests.sh  # Runs ALL tests, no shortcuts
```

### Test Categories
```bash
# Integration tests
pytest indexing/tests/ -k "integration" -v

# Component tests
pytest indexing/tests/ -k "component" -v

# Performance tests
pytest indexing/tests/test_performance_baseline.py -v
```

### With External Services
```bash
# With real API calls (requires API key)
ENABLE_EXTERNAL_APIS=true pytest indexing/tests/ -v

# With fixtures only (default)
pytest indexing/tests/ -v
```

## Best Practices

1. **Test real scenarios**: Use actual code samples from real projects
2. **Create comprehensive fixtures**: Cover success and failure cases
3. **Isolate external dependencies**: But test the real integration points
4. **Maintain test data quality**: Regular updates to match production
5. **Document test purposes**: Clear docstrings explaining what's tested
6. **Monitor test reliability**: Track and fix flaky tests
7. **Validate against production**: Ensure tests match real-world usage

## Anti-Patterns to Avoid

❌ **Bypassing core logic**: Never skip the actual functionality being tested
❌ **Unrealistic test data**: Always use data that resembles production
❌ **Ignoring external failures**: Test how the system handles service outages
❌ **Testing implementation details**: Focus on behavior, not internals

## Continuous Improvement

- **Quarterly review**: Update fixtures and test data
- **Performance tracking**: Monitor test suite execution time
- **Coverage analysis**: Identify and fill testing gaps
- **Production feedback**: Add tests for any production issues
- **Tool updates**: Keep testing tools and practices current

---

*This strategy ensures we ship working software, not just passing tests.*
