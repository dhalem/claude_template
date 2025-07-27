# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Current Architecture Analysis - Phase 1.6
## MCP Code Review Server - Pre-Refactoring Analysis

### Overview
This document analyzes the current architecture of the MCP code review server to identify shared components that can be extracted for the upcoming bug finding tool implementation.

### Current Component Structure

#### 1. MCP Server Core (`mcp_review_server.py`)
**Purpose**: Main MCP server implementation using official MCP library
**Key Responsibilities**:
- MCP protocol handling and tool registration
- Request routing and parameter validation
- Response formatting and error handling
- Integration of all components

**Current Implementation**:
```python
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    # Returns single tool: review_code

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Handles review_code tool calls
```

**Shared Potential**:
- Parameter validation logic
- MCP protocol handling patterns
- Error response formatting
- Component orchestration patterns

#### 2. File Collection (`src/file_collector.py`)
**Purpose**: Recursively scans directories for source files
**Key Responsibilities**:
- Directory traversal with gitignore support
- File filtering by extension and size
- Binary content detection
- File tree generation
- Collection summary reporting

**Key Methods**:
- `collect_files(directory: str) -> Dict[str, str]`
- `get_file_tree() -> str`
- `get_collection_summary() -> Dict`

**Shared Potential**: **HIGH**
- Both review_code and find_bugs need identical file collection
- All filtering logic is reusable
- Summary reporting useful for both tools

#### 3. Gemini AI Client (`src/gemini_client.py`)
**Purpose**: Google Gemini API integration with usage tracking
**Key Responsibilities**:
- Gemini API communication using official SDK
- Token usage tracking and cost estimation
- Response parsing and error handling
- Configurable pricing models

**Key Methods**:
- `review_code(content: str) -> str`
- `get_usage_report() -> Dict`
- `_update_usage(response) -> None`

**Shared Potential**: **HIGH**
- Core API communication logic identical for both tools
- Usage tracking essential for both tools
- Only difference will be prompt content
- Error handling patterns reusable

#### 4. Review Formatting (`src/review_formatter.py`)
**Purpose**: Formats collected files into review prompts
**Key Responsibilities**:
- File content formatting with syntax highlighting
- CLAUDE.md integration for project context
- Focus areas handling
- Prompt template construction

**Key Methods**:
- `format_review_request(files, file_tree, focus_areas, claude_md_path) -> str`
- `_build_review_prompt(focus_areas_prompt) -> str`

**Shared Potential**: **MEDIUM**
- File formatting logic reusable
- CLAUDE.md integration needed for both
- Template structure can be abstracted
- Bug-specific prompts will need different templates

### Dependency Analysis

```
mcp_review_server.py
├── file_collector.py (creates FileCollector)
├── gemini_client.py (creates GeminiClient)
├── review_formatter.py (creates ReviewFormatter)
└── Standard MCP library

Current Flow:
1. Server receives review_code request
2. FileCollector.collect_files() -> Dict[str, str]
3. ReviewFormatter.format_review_request() -> str (prompt)
4. GeminiClient.review_code() -> str (AI response)
5. Server returns formatted response
```

### Identified Shared Components for Extraction

#### 1. BaseCodeAnalyzer (New Abstract Base)
**Purpose**: Common interface for all code analysis tools
**Shared Functionality**:
- File collection orchestration
- Parameter validation
- Result formatting
- Error handling patterns

**Interface**:
```python
class BaseCodeAnalyzer:
    def __init__(self, file_collector, ai_client, formatter)
    def analyze(self, directory, **kwargs) -> AnalysisResult
    def validate_parameters(self, **kwargs) -> None
    def get_usage_report() -> Dict
```

#### 2. Enhanced GeminiClient (Refactored)
**Purpose**: Generalized AI client for any prompt type
**Enhancements**:
- Generic `analyze_content()` method replacing `review_code()`
- Pluggable prompt formatters
- Enhanced error handling
- Better usage tracking granularity

**Interface**:
```python
class GeminiClient:
    def analyze_content(self, content: str, task_type: str) -> str
    def get_usage_report(self, task_type: Optional[str]) -> Dict
    def reset_usage_tracking() -> None
```

#### 3. PromptFormatter (Abstract Base)
**Purpose**: Base class for all prompt formatting
**Shared Functionality**:
- File content formatting
- CLAUDE.md integration
- Basic template structure

**Subclasses**:
- `ReviewPromptFormatter` (existing logic)
- `BugFindingPromptFormatter` (new for bugs)

#### 4. UsageTracker (Extracted)
**Purpose**: Centralized usage and cost tracking
**Responsibilities**:
- Token counting across all tools
- Cost estimation with configurable pricing
- Usage reporting and analytics
- Session management

### Component Relationships After Refactoring

```
BaseCodeAnalyzer (Abstract)
├── ReviewAnalyzer (extends BaseCodeAnalyzer)
└── BugFinder (extends BaseCodeAnalyzer)

Shared Components:
├── FileCollector (unchanged, already well-designed)
├── GeminiClient (enhanced for multiple task types)
├── UsageTracker (extracted from GeminiClient)
└── PromptFormatter (abstract base)
    ├── ReviewPromptFormatter
    └── BugFindingPromptFormatter

MCP Server:
├── Registers both tools: review_code, find_bugs
├── Routes to appropriate analyzer
└── Uses shared error handling
```

### Code Reuse Analysis

#### High Reuse Potential (70-80% shared):
1. **File Collection**: 100% reusable
   - Directory traversal logic
   - Gitignore processing
   - File filtering and validation
   - Collection summaries

2. **AI Client Core**: 90% reusable
   - API communication
   - Authentication handling
   - Response parsing
   - Error handling
   - Usage tracking foundation

3. **Base Infrastructure**: 85% reusable
   - Parameter validation patterns
   - Error response formatting
   - MCP protocol handling
   - Logging infrastructure

#### Medium Reuse Potential (40-60% shared):
1. **Prompt Formatting**: 50% reusable
   - File content formatting
   - CLAUDE.md integration
   - Basic template structure
   - Bug prompts need different templates

2. **Result Processing**: 40% reusable
   - Basic response handling
   - Error extraction
   - Bug results need structured parsing

### Testing Strategy for Refactoring

#### Baseline Tests (✅ Already Complete - 36 tests)
- Parameter validation: 10 tests
- File collection: 9 tests
- Gemini integration: 5 tests
- Error handling: 6 tests
- Review formatting: 6 tests

#### Refactoring Validation Tests (Phase 2.6)
- All 36 baseline tests must pass after refactoring
- Performance regression tests
- Component isolation tests

### Implementation Recommendations

#### Phase 2 Priorities:
1. **Extract BaseCodeAnalyzer** - provides common interface
2. **Enhance GeminiClient** - make it task-agnostic
3. **Extract UsageTracker** - centralize cost/usage logic
4. **Create PromptFormatter hierarchy** - enable multiple prompt types
5. **Refactor existing review_code** - use new shared components
6. **Validate with baseline tests** - ensure no regression

#### Design Principles:
- **Single Responsibility**: Each component has one clear purpose
- **Open/Closed**: Easy to add new analysis types without changing existing code
- **Dependency Injection**: Components are loosely coupled
- **Test Coverage**: All shared components must have >90% test coverage

### Risk Analysis

#### Low Risk (Well-Established Patterns):
- FileCollector is already well-designed
- GeminiClient API integration is stable
- Baseline test coverage is comprehensive

#### Medium Risk (Refactoring Required):
- Prompt formatting abstraction
- Usage tracking extraction
- Parameter validation generalization

#### High Risk (New Functionality):
- Bug result parsing and classification
- Bug-specific prompt engineering
- Severity assessment logic

### Success Metrics

#### Code Reuse Target: 70%+ shared functionality
- FileCollector: 100% reused
- GeminiClient core: 90% reused
- Infrastructure: 85% reused
- Overall target: 70%+ achieved

#### Quality Targets:
- All 36 baseline tests pass after refactoring
- No performance regression (same response times)
- Test coverage >90% for all shared components
- Memory usage unchanged or improved

---

**Phase 1.6 Complete**: Architecture analysis identifies clear shared components with high reuse potential. Ready for Phase 2 refactoring implementation.
