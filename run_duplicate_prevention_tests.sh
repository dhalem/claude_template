#!/bin/bash
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Test runner for duplicate prevention system
# Runs comprehensive test suite including unit, integration, and performance tests

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
TEST_DIR="$SCRIPT_DIR/duplicate_prevention/tests"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if virtual environment is available
check_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        log_error "Virtual environment not found at $VENV_DIR"
        log_info "Please run: ./setup-venv.sh"
        exit 1
    fi

    if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
        log_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Function to activate virtual environment
activate_venv() {
    log_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Verify activation
    if [[ "$(which python3)" != "$VENV_DIR/bin/python3" ]]; then
        log_error "Failed to activate virtual environment"
        log_error "Expected: $VENV_DIR/bin/python3"
        log_error "Got: $(which python3)"
        exit 1
    fi

    log_success "Virtual environment activated"
}

# Function to check if Qdrant is running
check_qdrant() {
    log_info "Checking Qdrant database connection..."

    if ! python3 -c "
from duplicate_prevention.database import get_health_status
status = get_health_status()
if not status['status'] == 'healthy':
    exit(1)
print('Qdrant connection verified')
" 2>/dev/null; then
        log_warning "Qdrant database not running or not accessible"
        log_info "Starting Qdrant with Docker..."

        if command -v docker >/dev/null 2>&1; then
            cd "$SCRIPT_DIR/duplicate_prevention"
            if [[ -f "docker-compose.yml" ]]; then
                docker-compose up -d qdrant
                sleep 5
                log_info "Waiting for Qdrant to be ready..."

                # Wait up to 30 seconds for Qdrant to be ready
                for i in {1..30}; do
                    if python3 -c "
from duplicate_prevention.database import get_health_status
status = get_health_status()
if status['status'] == 'healthy':
    exit(0)
exit(1)
" 2>/dev/null; then
                        log_success "Qdrant is ready"
                        break
                    fi

                    if [[ $i -eq 30 ]]; then
                        log_error "Qdrant failed to start within 30 seconds"
                        exit 1
                    fi

                    sleep 1
                done
            else
                log_error "docker-compose.yml not found"
                exit 1
            fi
        else
            log_error "Docker not available to start Qdrant"
            log_info "Please start Qdrant manually or install Docker"
            exit 1
        fi
    else
        log_success "Qdrant database is running"
    fi
}

# Function to run unit tests
run_unit_tests() {
    log_info "Running unit tests..."

    if python3 -m pytest "$TEST_DIR/unit/" -v --tb=short; then
        log_success "All unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    log_info "Running integration tests..."

    if [[ -d "$TEST_DIR/integration" ]] && [[ -n "$(ls -A "$TEST_DIR/integration")" ]]; then
        if python3 -m pytest "$TEST_DIR/integration/" -v --tb=short; then
            log_success "All integration tests passed"
            return 0
        else
            log_error "Integration tests failed"
            return 1
        fi
    else
        log_warning "No integration tests found"
        return 0
    fi
}

# Function to run performance tests
run_performance_tests() {
    log_info "Running performance tests..."

    if [[ -d "$TEST_DIR/performance" ]] && [[ -n "$(ls -A "$TEST_DIR/performance")" ]]; then
        if python3 -m pytest "$TEST_DIR/performance/" -v --tb=short; then
            log_success "All performance tests passed"
            return 0
        else
            log_error "Performance tests failed"
            return 1
        fi
    else
        log_warning "No performance tests found"
        return 0
    fi
}

# Function to run specific test file or directory
run_specific_tests() {
    local test_path="$1"
    log_info "Running tests from: $test_path"

    if python3 -m pytest "$test_path" -v --tb=short; then
        log_success "Tests passed: $test_path"
        return 0
    else
        log_error "Tests failed: $test_path"
        return 1
    fi
}

# Function to show test statistics
show_test_stats() {
    log_info "Generating test coverage and statistics..."

    # Count test files and test functions
    local unit_tests
    local integration_tests
    local performance_tests
    local total_test_functions

    unit_tests=$(find "$TEST_DIR/unit" -name "test_*.py" 2>/dev/null | wc -l)
    integration_tests=$(find "$TEST_DIR/integration" -name "test_*.py" 2>/dev/null | wc -l)
    performance_tests=$(find "$TEST_DIR/performance" -name "test_*.py" 2>/dev/null | wc -l)

    # Count test functions
    total_test_functions=$(python3 -c "
import os
import ast
import sys

def count_test_functions(directory):
    count = 0
    if not os.path.exists(directory):
        return 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        tree = ast.parse(f.read())

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                            count += 1
                except Exception:
                    continue
    return count

unit_count = count_test_functions('$TEST_DIR/unit')
integration_count = count_test_functions('$TEST_DIR/integration')
performance_count = count_test_functions('$TEST_DIR/performance')

print(f'Unit test functions: {unit_count}')
print(f'Integration test functions: {integration_count}')
print(f'Performance test functions: {performance_count}')
print(f'Total test functions: {unit_count + integration_count + performance_count}')
")

    echo
    log_info "Test Suite Statistics:"
    echo "  Unit test files: $unit_tests"
    echo "  Integration test files: $integration_tests"
    echo "  Performance test files: $performance_tests"
    echo "  $total_test_functions"
    echo
}

# Function to cleanup test artifacts
cleanup_tests() {
    log_info "Cleaning up test artifacts..."

    # Remove temporary test collections from Qdrant
    python3 -c "
from duplicate_prevention.database import DatabaseConnector
import re

try:
    db = DatabaseConnector()
    collections = db.list_collections()

    # Delete collections that match test pattern
    test_patterns = [
        r'test_.*',
        r'.*_test$',
        r'.*_test_\d+$'
    ]

    deleted_count = 0
    for collection in collections:
        collection_name = collection.get('name', '')
        for pattern in test_patterns:
            if re.match(pattern, collection_name):
                if db.delete_collection(collection_name):
                    deleted_count += 1
                    print(f'Deleted test collection: {collection_name}')
                break

    if deleted_count > 0:
        print(f'Cleaned up {deleted_count} test collections')
    else:
        print('No test collections to clean up')

except Exception as e:
    print(f'Warning: Failed to cleanup test collections: {e}')
"

    # Remove pytest cache
    if [[ -d "$SCRIPT_DIR/.pytest_cache" ]]; then
        rm -rf "$SCRIPT_DIR/.pytest_cache"
        log_info "Removed pytest cache"
    fi

    log_success "Cleanup completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [TEST_PATH]"
    echo
    echo "OPTIONS:"
    echo "  -h, --help          Show this help message"
    echo "  -u, --unit-only     Run only unit tests"
    echo "  -i, --integration   Run only integration tests"
    echo "  -p, --performance   Run only performance tests"
    echo "  -s, --stats         Show test statistics"
    echo "  -c, --cleanup       Cleanup test artifacts and exit"
    echo "  --skip-qdrant       Skip Qdrant connection check"
    echo
    echo "EXAMPLES:"
    echo "  $0                                           # Run all tests"
    echo "  $0 -u                                        # Run only unit tests"
    echo "  $0 duplicate_prevention/tests/unit/test_self_similarity.py  # Run specific test file"
    echo "  $0 -s                                        # Show test statistics"
    echo "  $0 -c                                        # Cleanup test artifacts"
}

# Main execution
main() {
    local unit_only=false
    local integration_only=false
    local performance_only=false
    local show_stats=false
    local cleanup_only=false
    local skip_qdrant=false
    local specific_test=""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -u|--unit-only)
                unit_only=true
                shift
                ;;
            -i|--integration)
                integration_only=true
                shift
                ;;
            -p|--performance)
                performance_only=true
                shift
                ;;
            -s|--stats)
                show_stats=true
                shift
                ;;
            -c|--cleanup)
                cleanup_only=true
                shift
                ;;
            --skip-qdrant)
                skip_qdrant=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                specific_test="$1"
                shift
                ;;
        esac
    done

    # Change to script directory
    cd "$SCRIPT_DIR"

    log_info "Duplicate Prevention Test Runner"
    log_info "==============================="

    # Check and activate virtual environment
    check_venv
    activate_venv

    # Handle cleanup only
    if [[ "$cleanup_only" == true ]]; then
        cleanup_tests
        exit 0
    fi

    # Handle stats only
    if [[ "$show_stats" == true ]]; then
        show_test_stats
        exit 0
    fi

    # Check Qdrant connection unless skipped
    if [[ "$skip_qdrant" != true ]]; then
        check_qdrant
    fi

    # Run specific test if provided
    if [[ -n "$specific_test" ]]; then
        if [[ ! -e "$specific_test" ]]; then
            log_error "Test path not found: $specific_test"
            exit 1
        fi
        run_specific_tests "$specific_test"
        exit $?
    fi

    # Run tests based on options
    local failed_tests=()

    if [[ "$unit_only" == true ]]; then
        if ! run_unit_tests; then
            failed_tests+=("unit")
        fi
    elif [[ "$integration_only" == true ]]; then
        if ! run_integration_tests; then
            failed_tests+=("integration")
        fi
    elif [[ "$performance_only" == true ]]; then
        if ! run_performance_tests; then
            failed_tests+=("performance")
        fi
    else
        # Run all tests
        if ! run_unit_tests; then
            failed_tests+=("unit")
        fi

        if ! run_integration_tests; then
            failed_tests+=("integration")
        fi

        if ! run_performance_tests; then
            failed_tests+=("performance")
        fi
    fi

    # Show results
    echo
    if [[ ${#failed_tests[@]} -eq 0 ]]; then
        log_success "All tests passed successfully!"
        show_test_stats
        exit 0
    else
        log_error "Some tests failed: ${failed_tests[*]}"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
