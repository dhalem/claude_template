# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Duplicate Prevention System - Comprehensive Test Plan

## Executive Summary

This document outlines a comprehensive test plan for the duplicate prevention system based on gaps identified during implementation and code review. The plan addresses critical issues discovered during development, including path handling, self-similarity detection, configuration management, and Docker integration.

## Testing Gaps Identified

### 1. Path Translation and Handling
**Gap**: Docker paths (/app/) appearing in user-facing error messages
- No tests for relative-to-absolute path conversion
- No tests for path normalization across Docker/local boundaries
- No integration tests for path handling in error messages

### 2. Self-Similarity Detection
**Gap**: Guard blocking edits to the same file
- No tests for editing existing files
- No tests for path comparison logic
- No tests for different path representations of same file

### 3. Configuration and Environment
**Gap**: Workspace name mismatches and missing environment variables
- No validation tests for required environment variables
- No tests for configuration fallbacks
- No tests for Docker vs local environment detection

### 4. Database and Collection Management
**Gap**: Vector size mismatches and missing storage operations
- No tests for vector dimension validation
- No tests for empty collection behavior
- No tests for collection creation failures

### 5. Integration and End-to-End
**Gap**: Complex interactions between components
- No end-to-end tests for complete workflow
- No tests for Docker networking issues
- No tests for concurrent operations

## Test Implementation Plan

### Phase 1: Unit Tests for Core Components

#### 1.1 Path Translation Tests (`test_path_translation.py`)
```python
# Test cases:
- test_relative_to_absolute_conversion()
- test_absolute_path_unchanged()
- test_docker_to_local_path_mapping()
- test_path_normalization()
- test_workspace_root_detection()
- test_path_comparison_same_file_different_representations()
```

#### 1.2 Self-Similarity Detection Tests (`test_self_similarity.py`)
```python
# Test cases:
- test_same_file_not_blocked()
- test_same_filename_different_directory_blocked()
- test_edit_existing_file_allowed()
- test_relative_vs_absolute_path_comparison()
- test_symlink_handling()
```

#### 1.3 Configuration Validation Tests (`test_configuration.py`)
```python
# Test cases:
- test_required_environment_variables()
- test_workspace_name_override()
- test_qdrant_host_configuration()
- test_docker_detection()
- test_configuration_fallbacks()
```

### Phase 2: Integration Tests

#### 2.1 Docker Integration Tests (`test_docker_integration.py`)
```python
# Test cases:
- test_docker_container_networking()
- test_volume_mount_paths()
- test_indexer_workspace_detection()
- test_cross_container_communication()
- test_health_check_endpoints()
```

#### 2.2 Guard Integration Tests (`test_guard_integration.py`)
```python
# Test cases:
- test_guard_with_docker_indexed_files()
- test_guard_path_translation()
- test_guard_error_message_formatting()
- test_guard_override_mechanism()
- test_guard_default_action()
```

#### 2.3 End-to-End Workflow Tests (`test_e2e_workflow.py`)
```python
# Test cases:
- test_complete_indexing_and_detection_flow()
- test_multi_workspace_isolation()
- test_continuous_indexing_updates()
- test_database_wipe_and_rebuild()
- test_concurrent_operations()
```

### Phase 3: Performance and Edge Case Tests

#### 3.1 Performance Tests (`test_performance.py`)
```python
# Test cases:
- test_large_repository_indexing()
- test_high_frequency_updates()
- test_memory_usage_under_load()
- test_query_performance_with_large_dataset()
```

#### 3.2 Edge Case Tests (`test_edge_cases.py`)
```python
# Test cases:
- test_empty_files()
- test_binary_files()
- test_extremely_large_files()
- test_unicode_in_paths()
- test_special_characters_in_content()
- test_network_interruptions()
- test_database_unavailable()
```

### Phase 4: Operational Tests

#### 4.1 Installation and Setup Tests (`test_installation.py`)
```python
# Test cases:
- test_safe_install_backup_creation()
- test_safe_install_rollback()
- test_hook_installation_verification()
- test_mcp_server_registration()
```

#### 4.2 Debugging and Troubleshooting Tests (`test_debugging.py`)
```python
# Test cases:
- test_log_output_formatting()
- test_error_message_clarity()
- test_debug_mode_verbosity()
- test_health_check_diagnostics()
```

## Test Infrastructure Requirements

### 1. Test Fixtures (Using pytest)
```python
@pytest.fixture
def docker_environment():
    """Provides a Docker test environment"""

@pytest.fixture
def temp_workspace():
    """Creates temporary workspace with test files"""

@pytest.fixture
def mock_qdrant():
    """Provides a mock Qdrant instance for unit tests"""

@pytest.fixture
def indexed_repository():
    """Provides a pre-indexed test repository"""
```

### 2. Test Utilities
- Path comparison utilities
- Docker container management helpers
- Test data generators
- Performance measurement tools

### 3. CI/CD Integration
- Run all tests in Docker environment
- Separate unit and integration test stages
- Performance benchmarking
- Coverage reporting

## Implementation Priority

1. **Critical** (Week 1)
   - Path translation unit tests
   - Self-similarity detection tests
   - Basic integration tests

2. **High** (Week 2)
   - Docker integration tests
   - Configuration validation tests
   - End-to-end workflow tests

3. **Medium** (Week 3)
   - Performance tests
   - Edge case tests
   - Test infrastructure improvements

4. **Low** (Week 4)
   - Operational tests
   - Advanced debugging tests
   - Documentation tests

## Success Metrics

- **Code Coverage**: Achieve >90% coverage for core modules
- **Test Execution Time**: All unit tests complete in <5 seconds
- **Integration Test Reliability**: 100% pass rate over 100 runs
- **Bug Detection**: Catch 100% of identified historical issues

## Test Documentation Requirements

Each test file should include:
1. Clear docstrings explaining what is being tested
2. Setup/teardown requirements
3. Expected behaviors and edge cases
4. Links to related issues or bugs

## Continuous Improvement

- Weekly review of test failures
- Monthly analysis of coverage gaps
- Quarterly performance baseline updates
- Ongoing refinement based on production issues
