"""Common regex patterns used by guards."""

import re
from typing import List, Pattern

# Git patterns
# Updated to catch --no-verify in git commit commands, including multiline HEREDOC
# The DOTALL flag makes . match newlines, so this catches multiline commands
GIT_NO_VERIFY_PATTERN = re.compile(r"git\s+commit.*--no-verify", re.IGNORECASE | re.DOTALL)
GIT_FORCE_PUSH_PATTERNS = [
    re.compile(r"git\s+push\s+.*--force(?!\-with\-lease)", re.IGNORECASE),  # --force but not --force-with-lease
    re.compile(r"git\s+push\s+.*-f\s", re.IGNORECASE),
    re.compile(r"git\s+push\s+.*-f$", re.IGNORECASE),
]

# Git checkout patterns that could lose work
GIT_CHECKOUT_PATTERNS = [
    re.compile(r"git\s+checkout\s+.*", re.IGNORECASE),
    re.compile(r"git\s+switch\s+.*", re.IGNORECASE),
    re.compile(r"git\s+restore\s+.*", re.IGNORECASE),
    re.compile(r"git\s+reset\s+.*", re.IGNORECASE),
]

# Docker patterns
DOCKER_RESTART_PATTERNS = [
    # Match docker restart but not in comments or strings
    re.compile(r"^(?!#).*\bdocker\s+.*\brestart\b", re.IGNORECASE),
    re.compile(r"^(?!#).*\bdocker-compose\s+.*\brestart\b", re.IGNORECASE),
    re.compile(r"^(?!#).*\bdocker\s+.*compose\s+.*\brestart\b", re.IGNORECASE),
]

DOCKER_WITHOUT_COMPOSE_PATTERN = re.compile(r"^(?!#).*\bdocker\s+(?!.*compose)", re.IGNORECASE)
DOCKER_SAFE_COMMANDS = re.compile(
    r"\bdocker\s+(?:ps|logs|exec|images|system|info|version|help|--help)\b", re.IGNORECASE
)

# File path patterns
CLAUDE_DIR_PATTERN = re.compile(r"\.claude/", re.IGNORECASE)
PRECOMMIT_CONFIG_PATTERN = re.compile(r"\.pre-commit-config\.yaml$", re.IGNORECASE)

# Mock code patterns
MOCK_CODE_PATTERNS = [
    re.compile(r"@mock\.patch", re.IGNORECASE),
    re.compile(r"unittest\.mock", re.IGNORECASE),
    re.compile(r"MagicMock", re.IGNORECASE),
    re.compile(r"Mock\(\)", re.IGNORECASE),
    re.compile(r"SIMULATION:", re.IGNORECASE),
    re.compile(r"if.*test_mode.*return.*fake", re.IGNORECASE),
    re.compile(r"mock_.*=", re.IGNORECASE),
    re.compile(r"\.patch\(", re.IGNORECASE),
]

# Location-dependent command patterns
LOCATION_DEPENDENT_PATTERNS = [
    re.compile(r"cd\s+[^/]"),  # cd to relative path
    re.compile(r"\./.*"),  # execute local script
    re.compile(r"\.\.\/.*"),  # any relative path with ../
    re.compile(r"^[^/]*\.sh"),  # script execution without full path
    re.compile(r"docker.*compose.*-f [^/]"),  # docker compose with relative file
    re.compile(r"^make"),  # make commands are directory-dependent
    re.compile(r"^npm"),  # npm commands are directory-dependent
    re.compile(r"^yarn"),  # yarn commands are directory-dependent
    re.compile(r"python\s+[^/]*\.py"),  # python script without full path (no / in filename)
    re.compile(r"python\s+-m\s+.*\s+[^/]"),  # python -m with relative path argument
    re.compile(r"docker.*-v\s+\./"),  # docker with relative volume mount
]

# Completion claim patterns
COMPLETION_PATTERNS = [
    re.compile(r"echo.*complete", re.IGNORECASE),
    re.compile(r"echo.*done", re.IGNORECASE),
    re.compile(r"echo.*finished", re.IGNORECASE),
    re.compile(r"echo.*working", re.IGNORECASE),
    re.compile(r"echo.*ready", re.IGNORECASE),
    re.compile(r"echo.*implemented", re.IGNORECASE),
    re.compile(r"echo.*fixed", re.IGNORECASE),
    re.compile(r"echo.*success", re.IGNORECASE),
    re.compile(r"echo.*passing", re.IGNORECASE),
    re.compile(r"All.*tests.*passed", re.IGNORECASE),
    re.compile(r"Feature.*complete", re.IGNORECASE),
    re.compile(r"Implementation.*complete", re.IGNORECASE),
]

# Temporary file patterns
TEMP_FILE_PATTERNS = [
    re.compile(r"^test_"),
    re.compile(r"^check_"),
    re.compile(r"^debug_"),
    re.compile(r"^temp_"),
    re.compile(r"^quick_"),
    re.compile(r"^investigate_"),
]

# SQL patterns
# Match SQL keywords when they appear to be actual SQL queries
# Covers: SELECT ... FROM, INSERT INTO, UPDATE ... SET, DELETE FROM, CREATE TABLE, etc.
# Also matches SHOW TABLES/DATABASES and DESCRIBE table
SQL_QUERY_PATTERN = re.compile(
    r"""
    \b(?:
        SELECT\s+.+?\s+FROM |           # SELECT ... FROM
        INSERT\s+INTO |                 # INSERT INTO
        UPDATE\s+.+?\s+SET |           # UPDATE ... SET
        DELETE\s+FROM |                # DELETE FROM
        CREATE\s+(?:TABLE|DATABASE|INDEX|VIEW) |  # CREATE TABLE/DATABASE/etc
        ALTER\s+TABLE |                # ALTER TABLE
        DROP\s+(?:TABLE|DATABASE|INDEX|VIEW) |    # DROP TABLE/DATABASE/etc
        DESCRIBE\s+\w+ |               # DESCRIBE tablename
        SHOW\s+(?:TABLES|DATABASES|CREATE)   # SHOW TABLES/DATABASES/CREATE
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Docker file patterns
DOCKER_FILE_PATTERNS = [
    re.compile(r"Dockerfile"),
    re.compile(r"docker-compose.*\.(yml|yaml)$"),
    re.compile(r"compose\.(yml|yaml)$"),
]


def matches_any_pattern(text: str, patterns: List[Pattern]) -> bool:
    """Check if text matches any of the given patterns."""
    return any(pattern.search(text) for pattern in patterns)


def find_matching_patterns(text: str, patterns: List[Pattern]) -> List[str]:
    """Find all patterns that match the given text."""
    return [pattern.pattern for pattern in patterns if pattern.search(text)]
