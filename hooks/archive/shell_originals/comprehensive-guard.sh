#!/bin/bash

# Section separator
# CLAUDE CODE COMPREHENSIVE SAFETY GUARD
# Section separator
#
# This script consolidates all safety hooks for Claude Code to enforce
# critical rules from CLAUDE.md and prevent costly mistakes.
#
# ADDING NEW GUARDS:
# 1. Add a new section below with clear header comments
# 2. Follow the same pattern: detect -> warn -> require permission
# 3. Use descriptive variable names and add comments
# 4. Test the new guard thoroughly before deployment
# 5. Update this header documentation
#
# CURRENT GUARDS:
# - Git No-Verify Prevention (PreventS bypassing pre-commit hooks)
# - Docker Restart Prevention (Prevents using old images after code changes)
# - Directory Awareness (Enforces pwd verification for location-dependent commands)
# - Test Suite Enforcement (Prevents completion claims without proper testing)
# - Mock Code Prevention (Blocks forbidden mock/simulation code - file operations only)
# - Pre-Commit Config Protection (Guards .pre-commit-config.yaml modifications)
#
# Section separator

set -euo pipefail

# Parse the hook input JSON
# Claude Code passes JSON as first argument, but allow stdin for testing
if [[ $# -eq 0 ]]; then
    # Read from stdin for testing
    INPUT_JSON=$(cat)
else
    # Read from argument for actual Claude Code usage
    INPUT_JSON="$1"
fi

# Validate we have JSON input
if [[ -z "$INPUT_JSON" ]]; then
    echo "ERROR: No JSON input provided"
    echo "Usage: echo '{\"tool\":\"Bash\",\"parameters\":{\"command\":\"ls\"}}' | $0"
    echo "   or: $0 '{\"tool\":\"Bash\",\"parameters\":{\"command\":\"ls\"}}'"
    exit 1
fi

# Extract common parameters
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool // empty')
COMMAND=$(echo "$INPUT_JSON" | jq -r '.parameters.command // empty')

# Section separator
# BASH TOOL GUARDS (for command execution)
# Section separator

if [[ "$TOOL_NAME" == "Bash" ]]; then

    # -------------------------------------------------------------------------
    # GIT NO-VERIFY PREVENTION GUARD
    # -------------------------------------------------------------------------
    # Prevents bypassing pre-commit hooks with --no-verify flag
    # Critical because hooks protect code quality and prevent production issues

    if [[ "$COMMAND" =~ git[[:space:]]+.*commit.*--no-verify ]]; then
        echo "🚨 SECURITY ALERT: Claude is attempting to bypass pre-commit hooks!"
        echo ""
        echo "Command: $COMMAND"
        echo ""
        echo "Pre-commit hooks exist to:"
        echo "  - Prevent production issues"
        echo "  - Maintain code quality"
        echo "  - Enforce documentation standards"
        echo "  - Run critical tests"
        echo ""
        echo "Your project rules explicitly forbid bypassing hooks without permission."
        echo ""
        read -p "Do you want to allow this --no-verify command? (y/N): " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Hook execution blocked by user"
            echo ""
            echo "Suggested alternatives:"
            echo "  1. Fix the underlying issue that's causing hook failures"
            echo "  2. Temporarily disable specific hooks in .pre-commit-config.yaml"
            echo "  3. Use 'git commit' without --no-verify and address the failures"
            echo ""
            exit 1
        else
            echo "⚠️  User authorized --no-verify bypass"
            echo "⚠️  Remember to fix the underlying issues that required this bypass"
            echo ""
        fi
    fi

    # -------------------------------------------------------------------------
    # DOCKER RESTART PREVENTION GUARD
    # -------------------------------------------------------------------------
    # Prevents catastrophic use of docker restart after code changes
    # Critical because restart uses old images, not new code

    if [[ "$COMMAND" =~ docker.*restart ]] || [[ "$COMMAND" =~ docker.*compose.*restart ]]; then
        echo "🚨 CRITICAL ERROR: Docker restart detected after code changes!"
        echo ""
        echo "Command blocked: $COMMAND"
        echo ""
        echo "❌ WHY THIS IS CATASTROPHIC:"
        echo "  - 'docker restart' only stops/starts containers with EXISTING images"
        echo "  - Your code changes are NOT loaded into the running container"
        echo "  - This has previously broken entire SMAPI service (June 30, 2025)"
        echo "  - Hours of debugging required to recover from this mistake"
        echo ""
        echo "✅ CORRECT PROCEDURE AFTER CODE CHANGES:"
        echo "  1. docker -c musicbot compose build service-name"
        echo "  2. docker -c musicbot compose up -d service-name"
        echo "  3. Test that your changes actually work"
        echo ""
        echo "🔍 VERIFICATION REQUIRED:"
        echo "  - Check logs: docker -c musicbot compose logs service-name"
        echo "  - Test API: ./curl_wrapper.sh -s http://musicbot:PORT/endpoint"
        echo ""

        read -p "Do you want to proceed with restart anyway? (y/N): " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Docker restart blocked for your protection"
            echo ""
            echo "💡 TIP: If you just want to check container status:"
            echo "  docker -c musicbot compose ps"
            echo ""
            exit 1
        else
            echo "⚠️  User authorized dangerous docker restart"
            echo "⚠️  WARNING: This may load old code and break functionality"
            echo "⚠️  Remember: Restart ≠ Rebuild. Code changes require rebuild!"
            echo ""
        fi
    fi

    # -------------------------------------------------------------------------
    # DIRECTORY AWARENESS GUARD
    # -------------------------------------------------------------------------
    # Enforces directory verification before location-dependent commands
    # Prevents mistakes from running commands in wrong directory

    # Define location-dependent command patterns
    LOCATION_DEPENDENT_PATTERNS=(
        "^cd [^/]"           # cd to relative path
        "^\./[^/]"           # execute local script
        "\.\./.*"            # any relative path with ../
        "^[^/]*\.sh"         # script execution without full path
        "docker.*compose.*-f [^/]"  # docker compose with relative file
        "^make"              # make commands are directory-dependent
        "^npm"               # npm commands are directory-dependent
        "^yarn"              # yarn commands are directory-dependent
        "^python.*[^/]\.py"  # python script without full path
    )

    # Skip if command already starts with pwd (user is being safe)
    if [[ ! "$COMMAND" =~ ^pwd ]]; then
        # Check for location-dependent patterns
        DETECTED_PATTERNS=()
        for pattern in "${LOCATION_DEPENDENT_PATTERNS[@]}"; do
            if echo "$COMMAND" | grep -qE "$pattern"; then
                DETECTED_PATTERNS+=("$pattern")
            fi
        done

        # If location-dependent commands detected, warn and suggest pwd
        if [ ${#DETECTED_PATTERNS[@]} -gt 0 ]; then
            echo "📍 DIRECTORY AWARENESS: Location-dependent command detected!"
            echo ""
            echo "Command: $COMMAND"
            echo ""
            echo "⚠️  RULE FROM CLAUDE.md:"
            echo "  'ALWAYS run pwd before ANY command that could be location-dependent'"
            echo ""
            echo "🗂️  PROJECT STRUCTURE REFERENCE:"
            echo "  Root: spotidal/ (for ./run_tests.sh, ./curl_wrapper.sh, docker commands)"
            echo "  Sonos: cd sonos_server"
            echo "  AI Backend: cd gemini_playlist_suggester"
            echo "  React App: cd gemini_playlist_suggester/react-app"
            echo "  Workers: cd syncer"
            echo "  Syncer v2: cd syncer_v2"
            echo "  Monitoring: cd monitoring"
            echo ""
            echo "💡 RECOMMENDED APPROACH:"
            echo "  1. Run 'pwd' first to verify current directory"
            echo "  2. Then run your location-dependent command"
            echo "  3. Or use absolute paths to avoid ambiguity"
            echo ""

            read -p "Do you want to run 'pwd' first to verify directory? (Y/n): " -n 1 -r
            echo ""

            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                echo "📍 Running pwd to verify current directory first..."
                echo ""
                pwd
                echo ""
                echo "✅ Current directory verified. Proceeding with original command..."
                echo ""
            else
                echo "⚠️  User chose to skip directory verification"
                echo "⚠️  WARNING: Ensure you're in the correct directory for this command"
                echo ""
            fi
        fi
    fi

    # -------------------------------------------------------------------------
    # TEST SUITE ENFORCEMENT GUARD
    # -------------------------------------------------------------------------
    # Prevents completion claims without proper test execution
    # Critical for maintaining quality and preventing "it should work" syndrome

    # Define completion claim patterns
    COMPLETION_PATTERNS=(
        "echo.*complete"
        "echo.*done"
        "echo.*finished"
        "echo.*working"
        "echo.*ready"
        "echo.*implemented"
        "echo.*fixed"
        "echo.*success"
        "All.*tests.*passed"
        "Feature.*complete"
        "Implementation.*complete"
    )

    # Check if command contains completion claims
    DETECTED_COMPLETION=false
    for pattern in "${COMPLETION_PATTERNS[@]}"; do
        if echo "$COMMAND" | grep -qiE "$pattern"; then
            DETECTED_COMPLETION=true
            break
        fi
    done

    # If completion claim detected, check for proper test execution
    if [ "$DETECTED_COMPLETION" = true ]; then
        echo "🧪 TEST ENFORCEMENT: Completion claim detected!"
        echo ""
        echo "Command: $COMMAND"
        echo ""
        echo "❌ RULE FROM CLAUDE.md:"
        echo "  'NEVER claim work is complete without running the FULL containerized test suite'"
        echo ""
        echo "🚫 FORBIDDEN PRACTICES:"
        echo "  - Creating one-off test files (test_something.py)"
        echo "  - Running individual tests and claiming success"
        echo "  - Skipping test suite 'because it worked manually'"
        echo "  - Saying 'tests should pass' without running them"
        echo ""
        echo "📋 MANDATORY TEST COMMANDS BY SERVICE:"
        echo ""
        echo "  SONOS SMAPI SERVER:"
        echo "    cd sonos_server && ./run_full_test_suite.sh"
        echo ""
        echo "  AI PLAYLIST SUGGESTER:"
        echo "    cd gemini_playlist_suggester && ./run_all_real_integration_tests.sh"
        echo ""
        echo "  REACT WEB APP:"
        echo "    cd gemini_playlist_suggester/react-app && ./run-react-tests.sh all"
        echo ""
        echo "  SYNCER V2 (Dagster):"
        echo "    cd syncer_v2/integration_tests && ./run_integration_tests.sh --playlists 25"
        echo ""
        echo "  WORKER SERVICES:"
        echo "    cd syncer && ./run_worker_tests.sh"
        echo ""
        echo "🏆 GOLDEN TESTING RULE - NO FEATURE IS COMPLETE UNTIL:"
        echo "  ✅ API endpoints verified with ./curl_wrapper.sh"
        echo "  ✅ Real service integration tested (not mocks)"
        echo "  ✅ End-to-end user workflow validated"
        echo "  ✅ Error scenarios tested and handled"
        echo "  ✅ ACTUALLY RUNS - docker compose up must work"
        echo "  ✅ NO LYING - Never claim work done without verifying execution"
        echo "  ✅ COMMITTED TO GIT - Work isn't safe until committed"
        echo "  ✅ FULL CONTAINERIZED TEST SUITE PASSES - ALL tests must pass"
        echo ""

        read -p "Have you run the proper test suite for this completion claim? (y/N): " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Completion claim blocked - test suite execution required"
            echo ""
            echo "💡 MANDATORY PROTOCOL:"
            echo "  1. Run the appropriate test suite command above"
            echo "  2. Wait for 'ALL TESTS PASSED' or equivalent success message"
            echo "  3. Only THEN claim work is complete"
            echo ""
            echo "⚠️  WHY THIS MATTERS:"
            echo "  Individual manual tests miss integration issues, race conditions,"
            echo "  and edge cases. The containerized test suite catches problems"
            echo "  that destroy production systems."
            echo ""
            exit 1
        else
            echo "✅ User confirms proper test suite execution"
            echo "✅ Completion claim authorized"
            echo ""
        fi
    fi

fi

# Section separator
# FILE OPERATION GUARDS (for Edit, MultiEdit, Write tools)
# Section separator

if [[ "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "MultiEdit" || "$TOOL_NAME" == "Write" ]]; then

    # -------------------------------------------------------------------------
    # MOCK CODE PREVENTION GUARD
    # -------------------------------------------------------------------------
    # Prevents creation of forbidden mock/simulation code
    # Critical because mocks provide false confidence and hide integration issues

    # Extract content being written/edited
    NEW_STRING=""
    CONTENT=""

    if [[ "$TOOL_NAME" == "Edit" ]]; then
        NEW_STRING=$(echo "$INPUT_JSON" | jq -r '.parameters.new_string // empty')
    elif [[ "$TOOL_NAME" == "MultiEdit" ]]; then
        # Check all edits in the array
        NEW_STRING=$(echo "$INPUT_JSON" | jq -r '.parameters.edits[]?.new_string // empty' | tr '\n' ' ')
    elif [[ "$TOOL_NAME" == "Write" ]]; then
        CONTENT=$(echo "$INPUT_JSON" | jq -r '.parameters.content // empty')
        NEW_STRING="$CONTENT"
    fi

    # Check for forbidden mock patterns
    MOCK_PATTERNS=(
        "@mock\.patch"
        "unittest\.mock"
        "SIMULATION:"
        "if.*test_mode.*return.*fake"
        "mock_.*="
        "\.patch\("
        "MagicMock"
        "Mock\(\)"
    )

    DETECTED_PATTERNS=()

    for pattern in "${MOCK_PATTERNS[@]}"; do
        if echo "$NEW_STRING" | grep -qE "$pattern"; then
            DETECTED_PATTERNS+=("$pattern")
        fi
    done

    # If mock patterns detected, block and require permission
    if [ ${#DETECTED_PATTERNS[@]} -gt 0 ]; then
        echo "🚨 MOCK CODE DETECTION: Forbidden patterns found!"
        echo ""
        echo "Detected patterns:"
        for pattern in "${DETECTED_PATTERNS[@]}"; do
            echo "  - $pattern"
        done
        echo ""
        echo "❌ RULE VIOLATION: MOCKS AND SIMULATIONS ARE STRICTLY FORBIDDEN"
        echo ""
        echo "📜 FROM CLAUDE.md RULES:"
        echo "  - Mocks prove code compiles, not that features work"
        echo "  - Real integration testing is mandatory"
        echo "  - Mock-only testing causes features that pass tests but fail in production"
        echo ""
        echo "🔒 MANDATORY PERMISSION PROTOCOL:"
        echo "  1. STOP immediately - Do not write any mock code"
        echo "  2. Ask user permission with detailed justification"
        echo "  3. Get explicit written approval before proceeding"
        echo ""
        echo "✅ ALTERNATIVES:"
        echo "  - Use real integration tests with actual services"
        echo "  - Test against real databases/APIs"
        echo "  - Use containerized test environments"
        echo ""

        read -p "Do you have explicit user permission to write mock code? (y/N): " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Mock code creation blocked by safety protocol"
            echo ""
            echo "💡 RECOMMENDED APPROACH:"
            echo "  1. Ask user for permission with detailed justification"
            echo "  2. Explain why mocks are needed vs real integration tests"
            echo "  3. Get explicit written approval before proceeding"
            echo ""
            exit 1
        else
            echo "⚠️  User claims to have authorized mock code"
            echo "⚠️  WARNING: Ensure you have explicit written permission"
            echo "⚠️  Remember: Real integration tests are always preferred"
            echo ""
        fi
    fi

    # -------------------------------------------------------------------------
    # PRE-COMMIT CONFIG PROTECTION GUARD
    # -------------------------------------------------------------------------
    # Prevents unauthorized changes to .pre-commit-config.yaml
    # Critical because pre-commit hooks protect code quality and prevent issues

    # Extract file path being modified
    FILE_PATH=""

    if [[ "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Write" ]]; then
        FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.parameters.file_path // empty')
    elif [[ "$TOOL_NAME" == "MultiEdit" ]]; then
        FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.parameters.file_path // empty')
    fi

    # Check if modifying .pre-commit-config.yaml
    if [[ "$FILE_PATH" =~ \.pre-commit-config\.yaml$ ]]; then
        echo "🚨 PRE-COMMIT CONFIG PROTECTION: Unauthorized modification detected!"
        echo ""
        echo "File: $FILE_PATH"
        echo ""
        echo "❌ RULE VIOLATION FROM CLAUDE.md:"
        echo "  'PRE-COMMIT HOOKS MAY NEVER BE DISABLED WITHOUT EXPLICIT USER PERMISSION'"
        echo ""
        echo "🔒 FORBIDDEN PRACTICES:"
        echo "  - Commenting out hooks"
        echo "  - Adding --exit-zero or bypass flags to working hooks"
        echo "  - Using exclude patterns to skip validation"
        echo "  - Disabling hooks temporarily 'just for this commit'"
        echo ""
        echo "✅ MANDATORY PROTOCOL WHEN HOOKS FAIL:"
        echo "  1. READ the hook error message - it tells you exactly what to fix"
        echo "  2. FIX THE CODE - don't bypass the check"
        echo "  3. UPDATE DOCUMENTATION when required (INDEX.md, etc.)"
        echo "  4. NEVER disable the hook - that defeats the purpose"
        echo ""
        echo "🛡️  WHY THIS PROTECTION EXISTS:"
        echo "  - Pre-commit hooks prevent production issues"
        echo "  - Maintain code quality and enforce documentation standards"
        echo "  - Disabling them has caused real production failures"
        echo "  - Hours of debugging required when bypassed"
        echo ""

        read -p "Do you have explicit USER PERMISSION to modify pre-commit config? (y/N): " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Pre-commit config modification blocked by safety protocol"
            echo ""
            echo "💡 TO GET PERMISSION:"
            echo "  1. Ask user for explicit written permission"
            echo "  2. Provide detailed justification for the change"
            echo "  3. Explain why hook bypass is needed vs fixing the underlying issue"
            echo ""
            exit 1
        else
            echo "⚠️  User claims to have authorized pre-commit config changes"
            echo "⚠️  WARNING: Ensure you have explicit written permission"
            echo "⚠️  Remember: Fix underlying issues instead of bypassing checks"
            echo ""
        fi
    fi

fi

# Section separator
# GUARD SCRIPT COMPLETION
# Section separator
# All guards passed - allow the tool operation to proceed
exit 0
