#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Anti-Bypass Pattern Guard
Detects and blocks code patterns that attempt to bypass test enforcement
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Bypass patterns to detect
BYPASS_PATTERNS = [
    # Test skipping patterns
    (r'@pytest\.mark\.skip', 'Pytest skip marker'),
    (r'@pytest\.mark\.skipif', 'Pytest conditional skip'),
    (r'@unittest\.skip', 'Unittest skip decorator'),
    (r'pytest\.skip\(', 'Pytest skip function'),

    # Pre-commit stage bypass
    (r'stages:\s*\[\s*manual\s*\]', 'Manual stage in pre-commit config'),
    (r'stages:\s*\[\s*push\s*\]', 'Push-only stage in pre-commit config'),

    # Fast/quick mode patterns
    (r'--fast["\s]', 'Fast mode flag'),
    (r'--quick["\s]', 'Quick mode flag'),
    (r'-k\s*["\']not\s+slow', 'Excluding slow tests'),
    (r'if.*fast.*mode', 'Fast mode conditional', re.IGNORECASE),
    (r'FAST_MODE', 'Fast mode environment variable'),
    (r'FAST MODE', 'Fast mode pattern', re.IGNORECASE),

    # Comments suggesting bypass
    (r'#.*--no-verify', 'Comment suggesting --no-verify'),
    (r'#.*skip.*test', 'Comment about skipping tests', re.IGNORECASE),
    (r'#.*disable.*hook', 'Comment about disabling hooks', re.IGNORECASE),

    # Test selection bypass
    (r'pytest.*-k.*not\s+slow', 'Pytest test exclusion'),
    (r'-k.*["\']not\s+slow', 'Test exclusion pattern'),
    (r'SKIP_SLOW_TESTS', 'Skip slow tests variable'),
    (r'TEST_FAST_MODE', 'Test fast mode variable'),
]

# Log file path
LOG_PATH = Path.home() / ".claude/logs/bypass_patterns.log"


def log_bypass_attempt(file_path: str, patterns_found: List[Tuple[str, str]], matched_text: str = "") -> None:
    """Log bypass pattern detection"""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_PATH, 'a') as f:
        f.write(f"[{timestamp}] BYPASS PATTERN DETECTED in {file_path}\n")
        for pattern, description in patterns_found:
            f.write(f"  - {description}: {pattern}\n")
        if matched_text:
            # Extract relevant matched snippets
            for pattern_regex, description in patterns_found:
                match = re.search(pattern_regex, matched_text, re.IGNORECASE if 'case' in description.lower() else 0)
                if match:
                    f.write(f"    Matched: {match.group(0)}\n")
        f.write("\n")


def detect_bypass_patterns(content: str) -> List[Tuple[str, str]]:
    """Detect bypass patterns in content"""
    found_patterns = []

    for pattern_regex, description, *flags in BYPASS_PATTERNS:
        regex_flags = flags[0] if flags else 0
        if re.search(pattern_regex, content, regex_flags):
            found_patterns.append((pattern_regex, description))

    return found_patterns


def generate_override_code() -> str:
    """Generate override code for authorized bypasses"""
    import random
    timestamp = str(int(datetime.now().timestamp()))[-4:]
    random_num = random.randint(100, 999)
    return f"ABP{timestamp}{random_num}"


def show_bypass_warning(file_path: str, patterns_found: List[Tuple[str, str]],
                        override_code: str) -> None:
    """Show warning message about bypass patterns"""
    print(f"""
🚨 BYPASS PATTERN DETECTED 🚨

❌ OPERATION BLOCKED: Code contains patterns that bypass test enforcement

File: {file_path}

🔍 DETECTED PATTERNS:""", file=sys.stderr)

    for _, description in patterns_found:
        print(f"  • {description}", file=sys.stderr)

    if len(patterns_found) > 1:
        print(f"\n⚠️  CRITICAL: Found {len(patterns_found)} bypass patterns!", file=sys.stderr)

    print(f"""
📋 COMMON BYPASS PATTERNS:
• @pytest.mark.skip - Skips tests entirely
• stages: [manual] - Makes hooks optional
• --fast/--quick flags - Bypasses slow tests
• -k "not slow" - Excludes important tests

🔒 WHY THIS MATTERS:
- ALL tests must run EVERY time (mandatory policy)
- Skipping tests led to broken MCP functionality
- Fast modes hide critical failures
- Manual stages defeat automation

✅ CORRECT APPROACHES:
1. Fix slow tests instead of skipping them
2. Optimize test performance, don't bypass
3. All tests must pass before commit
4. If tests fail, fix the code or tests

🚨 REMEMBER THE MCP INCIDENT:
Tests were "temporarily" disabled and the feature broke.
This guard prevents that from happening again.

🔑 OVERRIDE (if authorized):
If this pattern is explicitly required:
  HOOK_OVERRIDE_CODE={override_code} <your command>

⚠️  Bypassing tests violates core engineering principles.
Fix the root cause, don't bypass the safety checks.
""", file=sys.stderr)


def main():
    """Main guard logic"""
    try:
        # Read JSON input from stdin
        input_data = sys.stdin.read()

        # Parse JSON
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            print("ERROR: Invalid JSON input", file=sys.stderr)
            sys.exit(1)

        # Extract tool information
        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})

        # Only check Edit and Write tools
        if tool_name not in ['Edit', 'Write', 'MultiEdit']:
            sys.exit(0)

        # Get content to check
        content = ''
        file_path = ''

        if tool_name == 'Write':
            content = tool_input.get('content', '')
            file_path = tool_input.get('file_path', '')
        elif tool_name == 'Edit':
            content = tool_input.get('new_string', '')
            file_path = tool_input.get('file_path', '')
        elif tool_name == 'MultiEdit':
            # Check all edits
            all_content = []
            file_path = tool_input.get('file_path', '')
            for edit in tool_input.get('edits', []):
                all_content.append(edit.get('new_string', ''))
            content = '\n'.join(all_content)

        # Skip if no content
        if not content:
            sys.exit(0)

        # Detect bypass patterns
        patterns_found = detect_bypass_patterns(content)

        if patterns_found:
            # Log the attempt
            log_bypass_attempt(file_path, patterns_found, content)

            # Check for override
            if os.environ.get('HOOK_OVERRIDE_CODE'):
                print("🔑 OVERRIDE APPLIED: Bypass pattern allowed with authorization",
                      file=sys.stderr)
                log_bypass_attempt(file_path,
                                   [(f"OVERRIDE: {os.environ['HOOK_OVERRIDE_CODE']}",
                                     "Authorized override")],
                                   content)
                sys.exit(0)

            # Generate override code and show warning
            override_code = generate_override_code()
            show_bypass_warning(file_path, patterns_found, override_code)

            # Block the operation
            sys.exit(2)

        # Allow operation if no patterns found
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: Guard failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
