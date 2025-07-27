# Bug Finding Tool Implementation Plan

**Project**: Add `find_bugs` tool to code-review MCP server
**Approach**: TDD with comprehensive refactoring for shared components
**Timeline**: 5 phases with full testing at each stage

## 🎯 Project Goals

### Primary Objectives
- Add `find_bugs` tool to existing code-review MCP server
- Refactor codebase to share 70%+ of functionality between `review_code` and `find_bugs`
- Maintain 100% backward compatibility with existing `review_code` tool
- Achieve comprehensive test coverage (>90%) for all components

### Success Criteria
- ✅ Both tools work independently and concurrently
- ✅ Shared components reduce code duplication significantly
- ✅ All existing functionality preserved exactly
- ✅ New bug finding functionality thoroughly tested
- ✅ Performance maintained or improved

## 📋 Multi-Phase Development Plan

### Phase 1: Baseline Testing & Analysis 🧪
**Duration**: 1-2 days
**Goal**: Establish comprehensive test coverage before any changes

#### 1.1 Create Comprehensive Tests for Existing `review_code` Tool
**Requirements**:
- Unit tests for all parameters (`directory`, `focus_areas`, `model`, `max_file_size`)
- Integration tests with actual Gemini API calls (mocked and real)
- Error handling tests (missing API key, invalid directory, permission errors)
- Usage tracking and cost estimation validation
- Performance tests with large codebases

**Test Categories**:
```python
# Unit Tests
test_review_code_parameter_validation()
test_review_code_directory_validation()
test_review_code_file_filtering()
test_review_code_focus_areas()
test_review_code_model_selection()

# Integration Tests
test_review_code_full_workflow()
test_review_code_with_real_gemini_api()
test_review_code_concurrent_usage()

# Error Handling Tests
test_review_code_missing_api_key()
test_review_code_invalid_directory()
test_review_code_permission_denied()
test_review_code_api_rate_limits()

# Performance Tests
test_review_code_large_codebase()
test_review_code_memory_usage()
```

#### 1.2 Analyze Current MCP Server Structure
**Documentation Required**:
- Map file collection and filtering logic
- Document AI communication patterns and prompt engineering
- Identify logging, usage tracking, and error handling components
- Document configuration and parameter handling
- Create component dependency diagram

**Deliverables**:
- `CURRENT_ARCHITECTURE.md` - Complete documentation of existing structure
- Test suite with 100% coverage of existing functionality
- Performance baseline measurements

### Phase 2: Refactoring for Shared Components 🔧
**Duration**: 2-3 days
**Goal**: Extract reusable components without breaking existing functionality

#### 2.1 Design Shared Component Architecture
**Shared Components to Extract**:

```python
# Base analyzer with common functionality
class BaseCodeAnalyzer:
    def __init__(self, gemini_client: GeminiClient, usage_tracker: UsageTracker)
    def collect_files(self, directory: str, max_file_size: int) -> List[CodeFile]
    def filter_by_language(self, files: List[CodeFile]) -> List[CodeFile]
    def prepare_context(self, files: List[CodeFile]) -> str
    def validate_parameters(self, **kwargs) -> ValidationResult

# AI communication wrapper
class GeminiClient:
    def __init__(self, api_key: str, model: str)
    def analyze_code(self, prompt: str, context: str) -> AnalysisResult
    def count_tokens(self, text: str) -> int
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float

# Usage tracking and logging
class UsageTracker:
    def track_analysis(self, tool_name: str, tokens_used: int, cost: float)
    def get_usage_summary(self) -> UsageSummary
    def log_analysis_request(self, tool_name: str, parameters: dict)

# MCP tool interface
class MCPTool:
    def __init__(self, name: str, description: str, analyzer: BaseCodeAnalyzer)
    def get_tool_definition(self) -> ToolDefinition
    async def execute(self, **kwargs) -> ToolResult
```

#### 2.2 Extract Shared Components
**TDD Process**:
1. **Write tests first** for each shared component
2. **Extract component** while keeping existing code working
3. **Verify all tests pass** before moving to next component
4. **Refactor incrementally** - one component at a time

**Testing Strategy**:
- Each shared component has comprehensive unit tests
- Integration tests verify components work together
- Regression tests ensure existing functionality unchanged

#### 2.3 Refactor Existing `review_code` Tool
**Requirements**:
- Migrate to use shared components
- Maintain exact same external interface
- Preserve all existing functionality and behavior
- No performance regression

**Verification**:
- All Phase 1 tests must pass unchanged
- Performance benchmarks must meet or exceed baseline
- API compatibility verified with existing MCP clients

### Phase 3: Bug Finding Implementation 🐛
**Duration**: 3-4 days
**Goal**: Implement new `find_bugs` tool using shared infrastructure

#### 3.1 Implement `find_bugs` Tool Interface
**Tool Signature**:
```python
async def find_bugs(
    directory: str,
    focus_areas: Optional[List[str]] = None,  # ["security", "memory_leaks", "null_pointers", "logic_errors"]
    model: str = "gemini-1.5-flash",
    max_file_size: int = 1048576,
    severity_filter: Optional[str] = None,  # "critical", "high", "medium", "low"
    include_fixes: bool = True  # Whether to suggest fixes
) -> BugFindingResult
```

**Result Structure**:
```python
@dataclass
class BugFindingResult:
    bugs_found: List[Bug]
    summary: BugSummary
    usage_info: UsageInfo
    analysis_metadata: AnalysisMetadata

@dataclass
class Bug:
    file_path: str
    line_number: int
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "security", "memory", "logic", "performance"
    description: str
    potential_impact: str
    suggested_fix: Optional[str]
    confidence_score: float
```

#### 3.2 Create Bug-Specific Analysis Prompts
**Bug Categories and Focus Areas**:

1. **Security Vulnerabilities**:
   - SQL injection, XSS, CSRF
   - Authentication and authorization flaws
   - Cryptographic issues
   - Input validation problems

2. **Memory Issues**:
   - Memory leaks
   - Buffer overflows/underflows
   - Use-after-free
   - Double-free errors

3. **Logic Errors**:
   - Null pointer dereferences
   - Race conditions
   - Deadlocks
   - Off-by-one errors

4. **Performance Issues**:
   - Inefficient algorithms (O(n²) where O(n) possible)
   - Resource leaks
   - Excessive memory usage
   - Blocking operations

**Prompt Engineering**:
```python
def create_bug_finding_prompt(focus_areas: List[str], include_fixes: bool) -> str:
    """Create specialized prompts for different bug categories."""
    base_prompt = """
    Analyze this code for bugs and potential issues. Focus on:
    {focus_areas_description}

    For each bug found, provide:
    1. Exact file and line location
    2. Severity level (critical/high/medium/low)
    3. Bug category and description
    4. Potential impact
    {fix_instruction}

    Be specific and actionable. Flag only real issues, not style preferences.
    """
```

#### 3.3 Implement Bug Analysis Logic
**Core Implementation**:
```python
class BugFinder(BaseCodeAnalyzer):
    def __init__(self, gemini_client: GeminiClient, usage_tracker: UsageTracker):
        super().__init__(gemini_client, usage_tracker)
        self.bug_patterns = self._load_bug_patterns()

    async def find_bugs(self, directory: str, **kwargs) -> BugFindingResult:
        # Use shared base functionality
        files = self.collect_files(directory, kwargs.get('max_file_size', 1048576))
        context = self.prepare_context(files)

        # Bug-specific analysis
        prompt = self._create_bug_prompt(kwargs.get('focus_areas', []))
        analysis = await self.gemini_client.analyze_code(prompt, context)

        # Parse and structure results
        bugs = self._parse_bug_results(analysis)
        summary = self._create_bug_summary(bugs)

        return BugFindingResult(bugs, summary, analysis.usage_info, analysis.metadata)
```

### Phase 4: Comprehensive Testing 🧪
**Duration**: 2-3 days
**Goal**: Ensure new functionality is thoroughly tested

#### 4.1 Unit Tests for `find_bugs` Tool
**Test Coverage Requirements**:
```python
# Parameter Validation Tests
test_find_bugs_parameter_validation()
test_find_bugs_directory_validation()
test_find_bugs_focus_areas_validation()
test_find_bugs_severity_filter_validation()

# Bug Detection Tests (with known buggy code samples)
test_find_bugs_detects_sql_injection()
test_find_bugs_detects_memory_leaks()
test_find_bugs_detects_null_pointers()
test_find_bugs_detects_race_conditions()

# Filtering and Categorization Tests
test_find_bugs_severity_filtering()
test_find_bugs_focus_area_filtering()
test_find_bugs_confidence_scoring()

# Integration with Shared Components
test_find_bugs_uses_base_analyzer()
test_find_bugs_uses_gemini_client()
test_find_bugs_tracks_usage()
```

#### 4.2 Test Code Repositories
**Create Test Datasets**:
1. **Vulnerable Code Samples** - Known security issues
2. **Memory Bug Examples** - Leaks, overflows, use-after-free
3. **Logic Error Cases** - Race conditions, null pointers
4. **Performance Issues** - Inefficient algorithms, resource leaks

**Test Validation**:
- Bug detection accuracy (precision/recall metrics)
- False positive rate analysis
- Performance benchmarks
- Consistency across different code languages

#### 4.3 Integration Tests
**Dual Tool Operation**:
```python
test_both_tools_work_concurrently()
test_both_tools_share_components_correctly()
test_both_tools_independent_usage_tracking()
test_both_tools_handle_same_codebase()
```

**MCP Server Integration**:
```python
test_mcp_server_registers_both_tools()
test_mcp_server_handles_concurrent_requests()
test_mcp_server_error_handling_both_tools()
```

### Phase 5: Documentation & Integration 📚
**Duration**: 1-2 days
**Goal**: Complete the feature with proper documentation

#### 5.1 Update MCP Server Registration
**Code Changes Required**:
```python
# In server.py
async def get_available_tools() -> list[Tool]:
    return [
        Tool(
            name="review_code",
            description="Perform comprehensive code review using AI",
            inputSchema=review_code_schema
        ),
        Tool(
            name="find_bugs",
            description="Find bugs and potential issues in code using AI",
            inputSchema=find_bugs_schema
        )
    ]
```

#### 5.2 Documentation Updates
**Required Documentation**:
1. **Update `indexing/MCP_SERVER_USAGE.md`**:
   - Add `find_bugs` tool documentation
   - Include usage examples and parameters
   - Document focus areas and severity levels

2. **Create `BUG_FINDING_GUIDE.md`**:
   - Comprehensive guide to using the bug finding tool
   - Best practices for different bug categories
   - Interpreting results and severity levels

3. **Update README.md**:
   - Add bug finding tool to feature list
   - Update MCP server capabilities section

## 🧪 Testing Standards and Requirements

### Test-Driven Development (TDD) Process
1. **Red**: Write failing test first
2. **Green**: Write minimal code to pass test
3. **Refactor**: Improve code while keeping tests green
4. **Repeat**: For each new feature or component

### Testing Requirements
- **Unit Test Coverage**: >90% for all new code
- **Integration Test Coverage**: All major workflows tested
- **Regression Tests**: All existing functionality verified
- **Performance Tests**: No degradation from baseline

### Test Categories
1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: Component interactions
3. **System Tests**: Full tool workflows
4. **Performance Tests**: Speed and memory usage
5. **Security Tests**: Vulnerability scanning
6. **Compatibility Tests**: MCP protocol compliance

### Commit Standards
- **Atomic Commits**: Each commit represents one logical change
- **Test-Passing Commits**: All tests pass before commit
- **Descriptive Messages**: Clear description of changes
- **Pre-commit Hooks**: Run full test suite before commit

## 🔧 Implementation Guidelines

### Code Quality Standards
- Follow existing codebase patterns and conventions
- Comprehensive docstrings for all public methods
- Type hints for all function signatures
- Error handling for all external dependencies

### Shared Component Design Principles
- **Single Responsibility**: Each component has one clear purpose
- **Dependency Injection**: Components are easily testable
- **Interface Segregation**: Clean, minimal interfaces
- **Open/Closed**: Open for extension, closed for modification

### Performance Requirements
- **No Regression**: Performance must match or exceed current `review_code` tool
- **Concurrent Safety**: Both tools must work simultaneously
- **Memory Efficiency**: Shared components reduce memory usage
- **API Rate Limits**: Respect Gemini API limits and implement backoff

## 📊 Success Metrics

### Quantitative Metrics
- **Test Coverage**: >90% for all new code
- **Performance**: No degradation from baseline
- **Code Reuse**: >70% of functionality shared between tools
- **Bug Detection Accuracy**: >80% precision on test datasets

### Qualitative Metrics
- **Code Maintainability**: Easier to add new analysis tools
- **Developer Experience**: Clear, intuitive API
- **Documentation Quality**: Comprehensive, accurate documentation
- **Backward Compatibility**: 100% compatibility with existing usage

## 🚀 Deployment and Rollout

### Testing Phases
1. **Local Development**: Full test suite passes
2. **Integration Testing**: MCP server integration verified
3. **User Acceptance Testing**: Manual testing with real codebases
4. **Production Deployment**: Gradual rollout with monitoring

### Rollback Plan
- Maintain ability to disable new `find_bugs` tool
- Preserve original code as backup
- Monitor usage and performance metrics
- Quick rollback procedure documented

---

**Created**: Following claude_template TDD and testing standards
**Status**: Implementation Plan - Ready for Phase 1 execution
**Next Steps**: Begin Phase 1 - Baseline Testing & Analysis
