# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Test Validation MCP Server

This directory contains the Test Validation MCP (Model Context Protocol) server that enforces a rigorous 4-stage validation pipeline for all test files, preventing the creation of fake or useless tests.

## Directory Structure

```
test-validation/
├── server/         # MCP server implementation and tools
├── database/       # Database management and schema
├── utils/          # Utilities (fingerprinting, tokens, config)
├── tests/          # Unit tests for test-validation components
├── logs/           # Server logs (never stdout during operation)
└── docs/           # Additional documentation
```

## Core Components

### 1. Database (`database/`)
- **manager.py**: Database connection and table management
- **schema.py**: SQL schema definitions for all tables
- **migrations/**: Database migration scripts

### 2. Server (`server/`)
- **server.py**: Main MCP server entry point
- **tools/**: Individual tool implementations
  - **design_test.py**: Stage 1 - Test design validation
  - **validate_implementation.py**: Stage 2 - Implementation analysis
  - **verify_breaking_behavior.py**: Stage 3 - Breaking verification
  - **approve_test.py**: Stage 4 - Final approval
- **gemini_client.py**: Gemini API integration with cost tracking

### 3. Utilities (`utils/`)
- **fingerprint.py**: Content fingerprinting for test files
- **tokens.py**: Token generation and validation
- **config.py**: Configuration loading and management
- **patterns.py**: Test file and fake test pattern definitions

## 4-Stage Validation Pipeline

1. **Design Stage** (`design_test`)
   - Validates test purpose and user value
   - Ensures specificity and feasibility
   - Generates `design_token`

2. **Implementation Stage** (`validate_implementation`)
   - Analyzes code for real vs fake patterns
   - Detects actual system interactions
   - Requires `design_token`, generates `implementation_token`

3. **Breaking Verification** (`verify_breaking_behavior`)
   - Proves test catches real bugs
   - Generates breaking scenarios
   - Requires `implementation_token`, generates `breaking_token`

4. **Final Approval** (`approve_test`)
   - Comprehensive quality assessment
   - Production readiness check
   - Requires all tokens, generates `final_token`

## Development Setup

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/unit/test_validation_mcp -v

# Start server (for testing)
python indexing/test-validation/server/server.py
```

## Configuration

Server configuration is managed through:
- Environment variables (API keys, etc.)
- `~/.claude/test-validation-config.json` (optional overrides)
- Default values in code

## Testing

Following strict TDD methodology:
1. RED - Write failing tests first
2. GREEN - Implement minimal code to pass
3. REVIEW - Code review MCP analysis
4. REFACTOR - Address all feedback
5. COMMIT - Save validated work

## Integration

This MCP server integrates with:
- **TestValidationGuard**: Blocks test file operations
- **TodoWrite**: Enforces workflow progression
- **Pre-commit hooks**: Final validation before commits
- **Database**: Persistent validation state

## Cost Management

- Daily budget limit: $10 (configurable)
- Uses Gemini 2.5 Flash for fast, cost-effective reviews
- Aggressive caching to reduce API calls
- Usage tracking and reporting

## Logging

All logs are written to `logs/` directory with daily rotation:
- `server_YYYYMMDD.log`: Server operations
- Never write to stdout/stderr during operation (breaks MCP protocol)
