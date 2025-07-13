#!/bin/bash

# ---------------------------------------------------------------------
# ADAPTIVE CLAUDE CODE SAFETY GUARD
# ---------------------------------------------------------------------
#
# This script implements comprehensive safety protections for Claude Code by
# enforcing critical rules from CLAUDE.md to prevent costly mistakes that
# have caused real harm in documented incidents.
#
# KEY FEATURES:
# - Adaptive behavior: Works both interactively and non-interactively
# - Safety-first policy: Blocks dangerous operations by default
# - Comprehensive coverage: Protects against multiple types of mistakes
# - Clear guidance: Provides helpful alternatives for blocked actions
# - Battle-tested patterns: Based on documented real-world incidents
#
# GUARDS IMPLEMENTED:
# 1. Git No-Verify Prevention - Stops bypassing pre-commit hooks with --no-verify
# 2. Docker Restart Prevention - Prevents catastrophic restart after code changes
# 3. Pre-Commit Skip Prevention - Stops bypassing hooks with SKIP= environment variables
# 4. Hook Installation Protection - Blocks direct edits/copies, enforces install script usage
# 5. Docker Without Compose Prevention - Enforces docker-compose usage for container management
# 6. Git Force Push Prevention - Blocks dangerous force pushes that rewrite history
# 7. Mock Code Prevention - Blocks creation of mock/simulation code without permission
# 8. Container Rebuild Reminder - Reminds to rebuild after Docker file changes
# 9. Database Schema Verification - Reminds to check schema before writing queries
# 10. Temporary File Management - Suggests proper location for temporary scripts
# 11. [Extensible] - Easy to add new guards following established patterns
#
# DOCUMENTED INCIDENTS PREVENTED:
# - June 23, 2025: Audio incident from not checking volume
# - June 30, 2025: SMAPI service breakage from docker restart
# - Multiple incidents: Bypassed pre-commit hooks, incomplete testing
#
# USAGE:
#   Called automatically by Claude Code hooks system
#   Receives JSON input via stdin with tool execution details
#   Returns exit code 0 (allow) or 1 (block) to control tool execution
#
# CONFIGURATION:
#   Interactive mode: Prompts user for dangerous operations
#   Non-interactive mode: Uses safety-first blocking policy
#   Detection: Automatic based on TTY availability
#
# ADDING NEW GUARDS:
# 1. Add new section with clear header comments
# 2. Follow pattern: detect -> message -> get_user_permission -> exit
# 3. Use descriptive variable names and comprehensive error messages
# 4. Test both interactive and non-interactive modes
# 5. Update this header documentation
#
# OUTPUT CONSIDERATIONS FOR CLAUDE CODE:
# - Messages go to stdout and appear in Claude Code interface
# - stderr can be used for debug info (visible with Ctrl-R)
# - Clear, formatted output helps users understand blocking decisions
# - Provide actionable alternatives for blocked operations
#
# MAINTENANCE:
#   This script should be kept in sync with CLAUDE.md rules
#   Test after any changes to ensure all modes work correctly
#   Update documentation when adding new guards
#
# ---------------------------------------------------------------------

set -euo pipefail

# Parse the hook input JSON from Claude Code
INPUT_JSON=$(cat)

# Extract parameters from Claude Code hook format
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command // empty')

# ---------------------------------------------------------------------
# INTERACTIVE DETECTION & USER PERMISSION SYSTEM
# ---------------------------------------------------------------------

# Detect if we're running in an interactive terminal environment
# This determines whether we can prompt the user or must use default policies
IS_INTERACTIVE=false
if [[ -t 0 ]] && [[ -t 1 ]] && [[ -t 2 ]]; then
    IS_INTERACTIVE=true
fi

# Function: get_user_permission
# Purpose: Safely get user permission for dangerous operations
# Parameters:
#   $1 - message: Detailed explanation of the dangerous operation
#   $2 - default_action: "allow" or "block" - what to do in non-interactive mode
# Returns:
#   0 - User approved or default policy allows
#   1 - User denied or default policy blocks
# Notes:
#   - In interactive mode: Prompts user with clear explanation
#   - In non-interactive mode: Uses safety-first default policy
#   - Always provides clear feedback about the decision made
get_user_permission() {
    local message="$1"
    local default_action="$2"  # "allow" or "block"

    if [[ "$IS_INTERACTIVE" == "true" ]]; then
        # Interactive mode - ask user
        echo "$message"
        read -p "Do you want to allow this action? (y/N): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            return 0  # Allow
        else
            return 2  # Block
        fi
    else
        # Non-interactive mode - use default policy
        echo "$message"
        if [[ "$default_action" == "allow" ]]; then
            echo "⚠️  Non-interactive mode: Allowing by default (configure policy if needed)"
            return 0
        else
            echo "🚨 Non-interactive mode: Blocking by default (safety-first policy)"
            echo "🚨 RULE FAILURE: This operation violates established safety policies"
            return 2
        fi
    fi
}

# ---------------------------------------------------------------------
# GIT NO-VERIFY PREVENTION GUARD
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ git[[:space:]]+.*commit.*--no-verify ]]; then
    MESSAGE="🚨 SECURITY ALERT: Git --no-verify detected!

Command: $COMMAND

Pre-commit hooks exist to:
  - Prevent production issues
  - Maintain code quality
  - Enforce documentation standards
  - Run critical tests

Your project rules explicitly forbid bypassing hooks without permission."

    if ! get_user_permission "$MESSAGE" "block"; then
        {
            echo "🚨 RULE FAILURE: Git --no-verify blocked by safety policy"
            echo ""
            echo "❌ This command bypasses pre-commit hooks which protect code quality"
            echo ""
            echo "✅ Suggested alternatives:"
            echo "  1. Fix the underlying issue causing hook failures"
            echo "  2. Temporarily disable specific hooks in .pre-commit-config.yaml"
            echo "  3. Use 'git commit' without --no-verify and address failures"
            echo ""
            echo "💡 Why this rule exists:"
            echo "  Pre-commit hooks prevent production issues and maintain code quality."
            echo "  Bypassing them has caused real incidents in this project."
        } >&2
        exit 2
    else
        echo ""
        echo "⚠️  User authorized --no-verify bypass"
        echo "⚠️  Remember to fix underlying issues that required this bypass"
        echo ""
    fi
fi

# ---------------------------------------------------------------------
# DOCKER RESTART PREVENTION GUARD
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Bash" ]] && ([[ "$COMMAND" =~ docker.*restart ]] || [[ "$COMMAND" =~ docker.*compose.*restart ]]); then
    MESSAGE="🚨 CRITICAL ERROR: Docker restart detected after code changes!

Command: $COMMAND

WHY THIS IS CATASTROPHIC:
  - 'docker restart' only stops/starts containers with EXISTING images
  - Your code changes are NOT loaded into the running container
  - This previously broke entire SMAPI service (June 30, 2025)
  - Hours of debugging required to recover from this mistake

CORRECT PROCEDURE AFTER CODE CHANGES:
  1. docker -c musicbot compose build service-name
  2. docker -c musicbot compose up -d service-name
  3. Test that your changes actually work"

    if ! get_user_permission "$MESSAGE" "block"; then
        {
            echo "🚨 RULE FAILURE: Docker restart blocked for your protection"
            echo ""
            echo "❌ Docker restart after code changes ignores new code!"
            echo ""
            echo "✅ Correct procedure after code changes:"
            echo "  1. docker -c musicbot compose build service-name"
            echo "  2. docker -c musicbot compose up -d service-name"
            echo "  3. Test that your changes actually work"
            echo ""
            echo "💡 Quick status check:"
            echo "  docker -c musicbot compose ps"
            echo ""
            echo "⚠️  Why this rule exists:"
            echo "  Docker restart has broken entire services in this project."
            echo "  It only stops/starts containers with EXISTING images."
        } >&2
        exit 2
    else
        echo ""
        echo "⚠️  User authorized dangerous docker restart"
        echo "⚠️  WARNING: This may load old code and break functionality"
        echo "⚠️  Remember: Restart ≠ Rebuild. Code changes require rebuild!"
        echo ""
    fi
fi

# ---------------------------------------------------------------------
# PRE-COMMIT SKIP PREVENTION GUARD
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ SKIP= ]]; then
    MESSAGE="🚨 PRE-COMMIT BYPASS ALERT: SKIP= environment variable detected!

Command: $COMMAND

WHY THIS IS DANGEROUS:
  - SKIP= bypasses pre-commit hooks that protect code quality
  - This is a form of --no-verify bypass using environment variables
  - Leads to the same production issues as --no-verify
  - Previously caused repository degradation and production failures

PRE-COMMIT HOOKS EXIST TO:
  - Prevent syntax errors in production
  - Maintain consistent code formatting
  - Enforce security policies
  - Run critical validation tests
  - Keep documentation synchronized

Your project rules explicitly forbid bypassing hooks without permission."

    if ! get_user_permission "$MESSAGE" "block"; then
        {
            echo "🚨 RULE FAILURE: SKIP= pre-commit bypass blocked by safety policy"
            echo ""
            echo "❌ This command bypasses pre-commit hooks using environment variables"
            echo ""
            echo "✅ Suggested alternatives:"
            echo "  1. Fix the underlying issue causing hook failures"
            echo "  2. Use specific hook exclusions in .pre-commit-config.yaml if needed"
            echo "  3. Run 'git commit' normally and address hook failures properly"
            echo "  4. Debug hooks with: pre-commit run --all-files"
            echo ""
            echo "💡 Why this rule exists:"
            echo "  SKIP= bypasses are equivalent to --no-verify and cause production issues."
            echo "  Pre-commit hooks are your first line of defense against bugs."
        } >&2
        exit 2
    else
        echo ""
        echo "⚠️  User authorized SKIP= bypass"
        echo "⚠️  Remember to fix underlying issues that required this bypass"
        echo "⚠️  Consider if specific .pre-commit-config.yaml exclusions are better"
        echo ""
    fi
fi

# ---------------------------------------------------------------------
# HOOK FILE DIRECT MODIFICATION PREVENTION GUARD
# ---------------------------------------------------------------------

# Check for Edit/Write/MultiEdit operations on .claude directory
if [[ "$TOOL_NAME" =~ ^(Edit|Write|MultiEdit)$ ]]; then
    # Try multiple methods to get the file path
    FILE_PATH=""

    # Method 1: Try parsing INPUT_JSON with jq
    if command -v jq >/dev/null 2>&1 && [[ -n "$INPUT_JSON" ]]; then
        FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
    fi

    # Method 2: Check tool-specific environment variables
    if [[ -z "$FILE_PATH" ]]; then
        case "$TOOL_NAME" in
            Edit|MultiEdit)
                FILE_PATH="${EDIT_PATH:-${FILE_PATH:-}}"
                ;;
            Write)
                # For Write tool, file path is typically first argument
                FILE_PATH="${1:-${FILE_PATH:-}}"
                ;;
        esac
    fi

    # Method 3: Final fallback to first argument
    if [[ -z "$FILE_PATH" ]] && [[ -n "${1:-}" ]]; then
        FILE_PATH="$1"
    fi

    # Debug logging
    {
        echo "Hook Protection Debug:"
        echo "  Tool: $TOOL_NAME"
        echo "  Detected path: $FILE_PATH"
        echo "  First arg: ${1:-none}"
        echo "  EDIT_PATH: ${EDIT_PATH:-none}"
        echo "  INPUT_JSON exists: $([ -n "$INPUT_JSON" ] && echo "yes" || echo "no")"
    } >&2

    if [[ "$FILE_PATH" =~ \.claude/ ]]; then
        MESSAGE="🚨 DIRECT HOOK MODIFICATION BLOCKED: Use install script instead!

Attempted operation: $TOOL_NAME on $FILE_PATH

WHY THIS IS BLOCKED:
  - Direct modifications to ~/.claude/ bypass version control
  - Changes are lost when hooks are reinstalled
  - No automatic backups are created
  - Breaks the repository-first development workflow
  - Makes debugging and maintenance difficult
  - The install script handles proper backup and deployment

CORRECT WORKFLOW:
  1. Make changes in repository: /home/dhalem/github/sptodial_one/spotidal/hooks/
  2. Test your changes
  3. Run the install script: cd hooks && ./install-hooks.sh
  4. The script will:
     - Create timestamped backups of existing files
     - Install all hooks properly
     - Validate syntax
     - Show installation summary

This ensures proper versioning, backups, and deployment."

        if ! get_user_permission "$MESSAGE" "block"; then
            {
                echo "🚨 RULE FAILURE: Direct hook modification blocked"
                echo ""
                echo "❌ Direct operations on ~/.claude/ files are prohibited"
                echo ""
                echo "✅ Required workflow:"
                echo "  1. Edit in repository: /home/dhalem/github/sptodial_one/spotidal/hooks/"
                echo "  2. Run install script: cd hooks && ./install-hooks.sh"
                echo ""
                echo "📦 The install script provides:"
                echo "  - Automatic timestamped backups"
                echo "  - Syntax validation"
                echo "  - Proper permissions"
                echo "  - Installation verification"
                echo ""
                echo "💡 Why this rule exists:"
                echo "  Manual modifications bypass safety checks and backup procedures."
                echo "  The install script ensures consistent, safe deployment."
            } >&2
            exit 2
        else
            echo ""
            echo "⚠️  User authorized direct modification (NOT RECOMMENDED)"
            echo "⚠️  Consider using: cd hooks && ./install-hooks.sh"
            echo "⚠️  Changes may be lost without proper backup"
            echo ""
        fi
    fi
fi

# Check for Bash cp/copy operations targeting .claude directory
if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ (cp|copy)[[:space:]].*\.claude/ ]]; then
    MESSAGE="🚨 DIRECT COPY TO HOOKS BLOCKED: Use install script instead!

Command: $COMMAND

WHY THIS IS BLOCKED:
  - Manual copying doesn't create backups
  - No syntax validation before deployment
  - No verification of successful installation
  - Bypasses the proper deployment workflow
  - Risk of overwriting custom modifications

CORRECT PROCEDURE:
  1. Ensure changes are in repository: /home/dhalem/github/sptodial_one/spotidal/hooks/
  2. Run the installation script:
     cd /home/dhalem/github/sptodial_one/spotidal/hooks
     ./install-hooks.sh

  The install script will:
  - Back up existing files with timestamps
  - Validate all hook syntax
  - Set proper permissions
  - Show what was installed
  - Display backup management info

BENEFITS OF USING INSTALL SCRIPT:
  - Preserves existing customizations as backups
  - Ensures consistent deployment
  - Provides installation verification
  - Maintains audit trail of changes"

    if ! get_user_permission "$MESSAGE" "block"; then
        {
            echo "🚨 RULE FAILURE: Direct copy to ~/.claude/ blocked"
            echo ""
            echo "❌ Manual copying to hook directory is prohibited"
            echo ""
            echo "✅ Use the install script instead:"
            echo "  cd /home/dhalem/github/sptodial_one/spotidal/hooks"
            echo "  ./install-hooks.sh"
            echo ""
            echo "📦 Why use the install script:"
            echo "  - Creates timestamped backups automatically"
            echo "  - Validates syntax before deployment"
            echo "  - Handles all hooks consistently"
            echo "  - Shows installation summary"
            echo ""
            echo "💡 Quick tip:"
            echo "  The script backs up to: ~/.claude/*.backup.TIMESTAMP"
            echo "  You can always restore from backups if needed"
        } >&2
        exit 2
    else
        echo ""
        echo "⚠️  User authorized direct copy (BYPASSING SAFETY)"
        echo "⚠️  No backup will be created"
        echo "⚠️  Strongly recommend using install-hooks.sh instead"
        echo ""
    fi
fi

# ---------------------------------------------------------------------
# DOCKER WITHOUT COMPOSE PREVENTION GUARD
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ docker[[:space:]] ]] && ! [[ "$COMMAND" =~ docker[[:space:]]+(-c[[:space:]]+[^[:space:]]+[[:space:]]+)?compose ]] && ! [[ "$COMMAND" =~ docker[[:space:]]+(--context[[:space:]]+[^[:space:]]+[[:space:]]+)?compose ]]; then
    # Allow certain safe docker commands that don't need compose
    if [[ "$COMMAND" =~ docker[[:space:]]+(ps|logs|exec|images|system|info|version|help|--help) ]]; then
        # These commands are safe to run without compose
        :
    else
        MESSAGE="🚨 DOCKER WITHOUT COMPOSE DETECTED: Use docker-compose instead!

Command: $COMMAND

WHY THIS IS BLOCKED:
  - Direct docker commands bypass docker-compose.yml configuration
  - Can create orphaned containers outside of compose management
  - Ignores network, volume, and dependency configurations
  - Makes debugging and maintenance extremely difficult
  - Previously caused SMAPI service breakage (June 30, 2025)

MANDATORY DOCKER PROTOCOL (from CLAUDE.md):
  - ALWAYS use docker-compose for container management
  - NEVER create ad-hoc containers with 'docker run'
  - NEVER bypass docker-compose for service operations

CORRECT COMMANDS:
  Instead of: docker run ...
  Use: docker -c musicbot compose run ...

  Instead of: docker start/stop container_name
  Use: docker -c musicbot compose start/stop service_name

  Instead of: docker create ...
  Use: Define service in docker-compose.yml

  Instead of: docker build ...
  Use: docker -c musicbot compose build service_name

ALLOWED EXCEPTIONS:
  - docker ps (viewing containers)
  - docker logs (checking logs)
  - docker exec (accessing containers)
  - docker images (listing images)
  - docker system prune (cleanup)

This rule prevents container management chaos and system breakage."

        if ! get_user_permission "$MESSAGE" "block"; then
            {
                echo "🚨 RULE FAILURE: Docker without compose blocked"
                echo ""
                echo "❌ Direct docker commands bypass compose orchestration"
                echo ""
                echo "✅ Use docker-compose instead:"
                echo "  docker -c musicbot compose [command] [service]"
                echo ""
                echo "📋 Examples:"
                echo "  docker -c musicbot compose ps"
                echo "  docker -c musicbot compose build sonos_server"
                echo "  docker -c musicbot compose up -d gemini_suggester"
                echo "  docker -c musicbot compose logs -f worker_name"
                echo ""
                echo "💡 Why this rule exists:"
                echo "  Ad-hoc docker commands have broken the entire system."
                echo "  Docker-compose ensures proper configuration and dependencies."
            } >&2
            exit 2
        else
            echo ""
            echo "⚠️  User authorized docker without compose"
            echo "⚠️  WARNING: This may create unmanaged containers"
            echo "⚠️  Consider using docker-compose for consistency"
            echo ""
        fi
    fi
fi

# ---------------------------------------------------------------------
# GIT FORCE PUSH PREVENTION GUARD
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Bash" ]] && ([[ "$COMMAND" =~ git[[:space:]]+push[[:space:]]+.*--force ]] || [[ "$COMMAND" =~ git[[:space:]]+push[[:space:]]+.*-f[[:space:]] ]] || [[ "$COMMAND" =~ git[[:space:]]+push[[:space:]]+.*-f$ ]]); then
    MESSAGE="🚨 DANGEROUS OPERATION: Git force push detected!

Command: $COMMAND

WHY FORCE PUSH IS DANGEROUS:
  - Rewrites remote repository history
  - Can permanently delete other people's commits
  - Breaks local repositories for all team members
  - Makes code review and debugging extremely difficult
  - Can cause permanent data loss if not careful

WHEN FORCE PUSH MIGHT BE NEEDED (RARE):
  - Removing sensitive data accidentally committed
  - Fixing a broken rebase on a personal feature branch
  - Cleaning up commits before merging (only on personal branches)

SAFER ALTERNATIVES:
  1. Use 'git push --force-with-lease' (checks remote hasn't changed)
  2. Create a new branch instead of rewriting history
  3. Use 'git revert' to undo commits safely
  4. Communicate with team before any force push

This operation requires explicit permission due to high risk."

    if ! get_user_permission "$MESSAGE" "block"; then
        {
            echo "🚨 RULE FAILURE: Git force push blocked by safety policy"
            echo ""
            echo "❌ Force push can permanently damage repository history"
            echo ""
            echo "✅ Safer alternatives:"
            echo "  1. Use --force-with-lease instead of --force"
            echo "  2. Create a new branch: git checkout -b fixed-branch"
            echo "  3. Revert commits: git revert <commit-hash>"
            echo "  4. Regular push: git push (resolve conflicts properly)"
            echo ""
            echo "💡 Why this rule exists:"
            echo "  Force pushes have caused permanent data loss in many projects."
            echo "  They break every other developer's local repository."
            echo "  Recovery from bad force pushes is difficult and time-consuming."
        } >&2
        exit 2
    else
        echo ""
        echo "⚠️  User authorized DANGEROUS force push"
        echo "⚠️  WARNING: This will rewrite remote history!"
        echo "⚠️  Make sure you understand the consequences"
        echo "⚠️  Consider using --force-with-lease for safety"
        echo ""
    fi
fi

# ---------------------------------------------------------------------
# MOCK CODE PREVENTION HOOK
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "MultiEdit" ]]; then
    # Check if we're creating or editing Python files with mock patterns
    if [[ "$1" =~ \.py$ ]] || [[ "${EDIT_PATH}" =~ \.py$ ]] || [[ "${FILE_PATH}" =~ \.py$ ]]; then
        # Check for mock patterns in the content
        if [[ "${CONTENT}" =~ @mock\.patch ]] || [[ "${CONTENT}" =~ unittest\.mock ]] || [[ "${CONTENT}" =~ MagicMock ]] || [[ "${CONTENT}" =~ SIMULATION: ]] || [[ "${NEW_STRING}" =~ @mock\.patch ]] || [[ "${NEW_STRING}" =~ unittest\.mock ]] || [[ "${NEW_STRING}" =~ MagicMock ]] || [[ "${NEW_STRING}" =~ SIMULATION: ]]; then
            MESSAGE="🚨 MOCK CODE DETECTED: Real integration required!

WHY MOCKS ARE FORBIDDEN:
  - Mocks provide false confidence in broken code
  - Hide real integration issues until production
  - Waste hours debugging \"working\" tests that fail in reality
  - Violate CLAUDE.md rule: MOCKS AND SIMULATIONS ARE STRICTLY FORBIDDEN

REAL EXAMPLES OF MOCK FAILURES:
  - Mocked database tests passed, real queries failed
  - Mocked API tests passed, real endpoints broken
  - Mocked file operations passed, container paths wrong

CORRECT APPROACH:
  1. Use real test databases (containerized)
  2. Use real API endpoints (test environment)
  3. Use real file systems (temp directories)
  4. Use real service integrations (docker-compose)

MANDATORY PERMISSION PROTOCOL:
  1. STOP immediately - Do not write mock code
  2. Ask user permission with detailed justification
  3. Get explicit written approval before proceeding

This rule exists because mocks have caused real production failures."

            if ! get_user_permission "$MESSAGE" "block"; then
                {
                    echo "🚨 RULE FAILURE: Mock code creation blocked"
                    echo ""
                    echo "❌ Mocks hide real problems until production"
                    echo ""
                    echo "✅ Use real integration tests instead:"
                    echo "  - Containerized test databases"
                    echo "  - Real API endpoints"
                    echo "  - Actual file operations"
                    echo ""
                    echo "💡 Remember: Mocks lie. Real tests reveal truth."
                } >&2
                exit 2
            else
                echo ""
                echo "⚠️  User authorized mock code creation"
                echo "⚠️  WARNING: This may hide real integration issues"
                echo "⚠️  Consider real integration tests instead"
                echo ""
            fi
        fi
    fi
fi

# ---------------------------------------------------------------------
# CONTAINER REBUILD REMINDER HOOK
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "MultiEdit" ]]; then
    # Check if we're editing Docker-related files
    if [[ "$1" =~ Dockerfile ]] || [[ "$1" =~ docker-compose\.(yml|yaml)$ ]] || [[ "${EDIT_PATH}" =~ Dockerfile ]] || [[ "${EDIT_PATH}" =~ docker-compose\.(yml|yaml)$ ]] || [[ "${FILE_PATH}" =~ Dockerfile ]] || [[ "${FILE_PATH}" =~ docker-compose\.(yml|yaml)$ ]]; then
        echo ""
        echo "📦 CONTAINER REBUILD REMINDER"
        echo ""
        echo "You've modified Docker configuration files."
        echo "Remember to rebuild containers for changes to take effect:"
        echo ""
        echo "  docker -c musicbot compose build <service>"
        echo "  docker -c musicbot compose up -d <service>"
        echo ""
        echo "❌ NEVER use 'docker restart' - it uses OLD images!"
        echo "✅ ALWAYS rebuild after Docker file changes"
        echo ""
        echo "This reminder exists because using restart instead of"
        echo "rebuild has wasted hours of debugging time."
        echo ""
        # Non-blocking reminder - exit 0
    fi
fi

# ---------------------------------------------------------------------
# DATABASE SCHEMA VERIFICATION HOOK
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "MultiEdit" ]]; then
    # Check if we're writing SQL queries
    if [[ "${CONTENT}" =~ (SELECT|INSERT|UPDATE|DELETE)[[:space:]] ]] || [[ "${NEW_STRING}" =~ (SELECT|INSERT|UPDATE|DELETE)[[:space:]] ]]; then
        echo ""
        echo "🗄️  DATABASE SCHEMA REMINDER"
        echo ""
        echo "You're writing SQL queries. Remember to verify schema first:"
        echo ""
        echo "  DESCRIBE <table_name>;"
        echo "  SHOW TABLES;"
        echo "  SHOW CREATE TABLE <table_name>;"
        echo ""
        echo "Common schema mistakes:"
        echo "  ❌ Using 'track_number' instead of 'track_position'"
        echo "  ❌ Using 'disc_number' instead of 'disc_no'"
        echo "  ❌ Assuming standard column names exist"
        echo ""
        echo "This reminder exists because schema assumptions have"
        echo "caused query failures and wasted debugging time."
        echo ""
        # Non-blocking reminder - exit 0
    fi
fi

# ---------------------------------------------------------------------
# TEMPORARY FILE MANAGEMENT HOOK
# ---------------------------------------------------------------------

if [[ "$TOOL_NAME" == "Write" ]]; then
    # Check if creating test/debug scripts in root directory
    if [[ "$1" =~ ^[^/]*\.(py|js|sh)$ ]] && ([[ "$1" =~ ^test_ ]] || [[ "$1" =~ ^check_ ]] || [[ "$1" =~ ^debug_ ]] || [[ "$1" =~ ^temp_ ]] || [[ "$1" =~ ^quick_ ]]); then
        echo ""
        echo "📁 TEMPORARY FILE LOCATION WARNING"
        echo ""
        echo "You're creating a temporary script in the repository root."
        echo ""
        echo "✅ BETTER: Use the temp/ directory (gitignored):"
        echo "  mkdir -p temp/"
        echo "  vim temp/$1"
        echo ""
        echo "Or use system temp for truly temporary files:"
        echo "  vim /tmp/$1"
        echo ""
        echo "Why this matters:"
        echo "  - Prevents repository clutter (60+ files accumulated!)"
        echo "  - Avoids accidental commits of test code"
        echo "  - Keeps git status clean"
        echo ""
        echo "The temp/ directory is gitignored for this purpose."
        echo ""
        # Non-blocking warning - exit 0
    fi
fi

# Allow all other commands
exit 0
