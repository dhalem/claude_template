"""Non-blocking reminder guards that provide helpful information.

REMINDER: Update HOOKS.md when modifying guards!
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext  # noqa: E402
from utils.patterns import (  # noqa: E402
    DOCKER_FILE_PATTERNS,
    SQL_QUERY_PATTERN,
    TEMP_FILE_PATTERNS,
    matches_any_pattern,
)


class ContainerRebuildReminder(BaseGuard):
    """Reminds to rebuild containers after Docker file changes."""

    def __init__(self):
        super().__init__(name="Container Rebuild Reminder", description="Reminds to rebuild after Docker file changes")

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name not in ["Edit", "Write", "MultiEdit"]:
            return False

        if not context.file_path:
            return False

        return matches_any_pattern(context.file_path, DOCKER_FILE_PATTERNS)

    def get_message(self, context: GuardContext) -> str:
        return """📦 CONTAINER REBUILD REMINDER

You've modified Docker configuration files.
Remember to rebuild containers for changes to take effect:

  docker -c musicbot compose build <service>
  docker -c musicbot compose up -d <service>

❌ NEVER use 'docker restart' - it uses OLD images!
✅ ALWAYS rebuild after Docker file changes

This reminder exists because using restart instead of
rebuild has wasted hours of debugging time."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.ALLOW  # Non-blocking reminder


class DatabaseSchemaReminder(BaseGuard):
    """Reminds to verify database schema before writing queries."""

    def __init__(self):
        super().__init__(name="Database Schema Reminder", description="Reminds to check schema before writing queries")

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name not in ["Write", "Edit", "MultiEdit"]:
            return False

        # Check content being written
        content_to_check = ""
        if context.content:
            content_to_check += context.content
        if context.new_string:
            content_to_check += "\n" + context.new_string

        if not content_to_check:
            return False

        return bool(SQL_QUERY_PATTERN.search(content_to_check))

    def get_message(self, context: GuardContext) -> str:
        return """🗄️  DATABASE SCHEMA REMINDER

You're writing SQL queries. Remember to verify schema first:

  DESCRIBE <table_name>;
  SHOW TABLES;
  SHOW CREATE TABLE <table_name>;

Common schema mistakes:
  ❌ Using 'track_number' instead of 'track_position'
  ❌ Using 'disc_number' instead of 'disc_no'
  ❌ Assuming standard column names exist

This reminder exists because schema assumptions have
caused query failures and wasted debugging time."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.ALLOW  # Non-blocking reminder


class TempFileLocationGuard(BaseGuard):
    """Suggests proper location for temporary scripts."""

    def __init__(self):
        super().__init__(name="Temporary File Management", description="Suggests proper location for temporary scripts")

    def should_trigger(self, context: GuardContext) -> bool:
        if context.tool_name != "Write":
            return False

        if not context.file_path:
            return False

        # Check if creating test/debug scripts in root directory
        file_name = context.file_path.split("/")[-1]

        # Must be a script file
        if not (file_name.endswith((".py", ".js", ".sh"))):
            return False

        # Must match temporary patterns
        if not matches_any_pattern(file_name, TEMP_FILE_PATTERNS):
            return False

        # Must be in root directory (no path separators before filename)
        # Check if path has directory components (not just the filename)
        return "/" not in context.file_path

    def get_message(self, context: GuardContext) -> str:
        file_name = context.file_path.split("/")[-1]

        return f"""📁 TEMPORARY FILE LOCATION WARNING

You're creating a temporary script in the repository root.

✅ BETTER: Use the temp/ directory (gitignored):
  mkdir -p temp/
  vim temp/{file_name}

Or use system temp for truly temporary files:
  vim /tmp/{file_name}

Why this matters:
  - Prevents repository clutter (60+ files accumulated!)
  - Avoids accidental commits of test code
  - Keeps git status clean

The temp/ directory is gitignored for this purpose."""

    def get_default_action(self) -> GuardAction:
        return GuardAction.ALLOW  # Non-blocking warning
