"""Unit tests for reminder guards."""

import os
import sys
import unittest
import unittest.mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.reminder_guards import ContainerRebuildReminder, DatabaseSchemaReminder, TempFileLocationGuard  # noqa: E402


class TestContainerRebuildReminder(unittest.TestCase):
    """Test cases for ContainerRebuildReminder."""

    def setUp(self):
        self.guard = ContainerRebuildReminder()

    def test_should_trigger_on_dockerfile_edit(self):
        """Test that reminder triggers on Dockerfile edits."""
        test_files = [
            "Dockerfile",
            "Dockerfile.prod",
            "Dockerfile.dev",
            "path/to/Dockerfile",
            "service/Dockerfile.test",
        ]

        for file_path in test_files:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Edit", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_docker_compose_edit(self):
        """Test that reminder triggers on docker-compose file edits."""
        test_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "docker-compose.override.yml",
            "docker-compose.prod.yaml",
            "compose.yml",
            "compose.yaml",
        ]

        for file_path in test_files:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Write", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_other_files(self):
        """Test that reminder doesn't trigger on non-Docker files."""
        test_files = ["README.md", "package.json", "config.yml", "requirements.txt", "setup.py"]

        for file_path in test_files:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Edit", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_file_operations(self):
        """Test that reminder doesn't trigger on non-file operations."""
        context = GuardContext(tool_name="Bash", tool_input={"command": "docker build ."}, command="docker build .")

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_without_file_path(self):
        """Test that reminder doesn't trigger without file path."""
        context = GuardContext(tool_name="Edit", tool_input={}, file_path=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_instructions(self):
        """Test that reminder message contains rebuild instructions."""
        context = GuardContext(tool_name="Edit", tool_input={"file_path": "Dockerfile"}, file_path="Dockerfile")

        message = self.guard.get_message(context)

        self.assertIn("CONTAINER REBUILD REMINDER", message)
        self.assertIn("Docker configuration files", message)
        self.assertIn("docker -c musicbot compose build", message)
        self.assertIn("docker -c musicbot compose up -d", message)
        self.assertIn("NEVER use 'docker restart'", message)

    def test_default_action_is_allow(self):
        """Test that default action is to allow (non-blocking)."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.ALLOW)


class TestDatabaseSchemaReminder(unittest.TestCase):
    """Test cases for DatabaseSchemaReminder."""

    def setUp(self):
        self.guard = DatabaseSchemaReminder()

    def test_should_trigger_on_sql_queries(self):
        """Test that reminder triggers on SQL queries."""
        sql_content_cases = [
            "SELECT * FROM users WHERE id = 1",
            "INSERT INTO tracks (name, artist) VALUES ('Song', 'Artist')",
            "UPDATE albums SET year = 2023 WHERE id = 5",
            "DELETE FROM playlists WHERE user_id = 10",
            "CREATE TABLE new_table (id INT PRIMARY KEY)",
            "ALTER TABLE tracks ADD COLUMN duration INT",
            "DROP TABLE old_table",
        ]

        for content in sql_content_cases:
            with self.subTest(content=content):
                context = GuardContext(
                    tool_name="Write", tool_input={"file_path": "query.sql", "content": content}, content=content
                )

                self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_edit_with_sql(self):
        """Test that reminder triggers on edits containing SQL."""
        context = GuardContext(
            tool_name="Edit",
            tool_input={"file_path": "test.py", "new_string": "cursor.execute('SELECT track_number FROM tracks')"},
            new_string="cursor.execute('SELECT track_number FROM tracks')",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_trigger_on_multiedit_with_sql(self):
        """Test that reminder triggers on MultiEdit containing SQL."""
        context = GuardContext(
            tool_name="MultiEdit",
            tool_input={
                "file_path": "script.py",
                "edits": [
                    {"old_string": "old", "new_string": "SELECT * FROM albums"},
                    {"old_string": "old2", "new_string": "new2"},
                ],
            },
            new_string="SELECT * FROM albums\nnew2",
        )

        self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_sql_content(self):
        """Test that reminder doesn't trigger on non-SQL content."""
        non_sql_cases = [
            "def function():\n    return True",
            "console.log('Hello World')",
            "import mysql.connector",
            "# This is a comment about SQL",
            "const variable = 'SELECT like string but not SQL'",
        ]

        for content in non_sql_cases:
            with self.subTest(content=content):
                context = GuardContext(
                    tool_name="Write", tool_input={"file_path": "test.py", "content": content}, content=content
                )

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_file_operations(self):
        """Test that reminder doesn't trigger on non-file operations."""
        context = GuardContext(tool_name="Bash", tool_input={"command": "mysql -u user -p"}, command="mysql -u user -p")

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_empty_content(self):
        """Test that reminder doesn't trigger on empty content."""
        context = GuardContext(tool_name="Write", tool_input={"file_path": "test.py"}, content=None, new_string=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_schema_advice(self):
        """Test that reminder message contains schema checking advice."""
        context = GuardContext(
            tool_name="Write",
            tool_input={"file_path": "query.py", "content": "SELECT track_number FROM tracks"},
            content="SELECT track_number FROM tracks",
        )

        message = self.guard.get_message(context)

        self.assertIn("DATABASE SCHEMA REMINDER", message)
        self.assertIn("SQL queries", message)
        self.assertIn("DESCRIBE <table_name>", message)
        self.assertIn("SHOW TABLES", message)
        self.assertIn("schema mistakes", message)
        self.assertIn("track_number", message)
        self.assertIn("disc_number", message)

    def test_default_action_is_allow(self):
        """Test that default action is to allow (non-blocking)."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.ALLOW)


class TestTempFileLocationGuard(unittest.TestCase):
    """Test cases for TempFileLocationGuard."""

    def setUp(self):
        self.guard = TempFileLocationGuard()

    def test_should_trigger_on_temp_scripts_in_root(self):
        """Test that guard triggers on temporary scripts in root directory."""
        temp_file_cases = [
            "test_feature.py",
            "check_status.js",
            "debug_issue.sh",
            "temp_script.py",
            "quick_fix.js",
            "investigate_bug.py",
        ]

        for file_path in temp_file_cases:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Write", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertTrue(self.guard.should_trigger(context))

    def test_should_not_trigger_on_scripts_in_subdirs(self):
        """Test that guard doesn't trigger on scripts in subdirectories."""
        subdir_cases = [
            "src/test_feature.py",
            "scripts/debug_issue.sh",
            "temp/quick_fix.js",
            "tests/test_module.py",
            "/full/path/to/test_script.py",
        ]

        for file_path in subdir_cases:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Write", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_permanent_files(self):
        """Test that guard doesn't trigger on permanent/production files."""
        permanent_cases = ["main.py", "config.js", "utils.sh", "service.py", "component.ts", "module.py"]

        for file_path in permanent_cases:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Write", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_script_files(self):
        """Test that guard doesn't trigger on non-script file extensions."""
        non_script_cases = [
            "test_data.txt",
            "debug_info.json",
            "temp_config.yml",
            "check_results.md",
            "quick_notes.doc",
        ]

        for file_path in non_script_cases:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Write", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_non_write_operations(self):
        """Test that guard doesn't trigger on non-Write operations."""
        non_write_cases = ["Edit", "MultiEdit", "Read", "Bash"]

        for tool_name in non_write_cases:
            with self.subTest(tool_name=tool_name):
                context = GuardContext(
                    tool_name=tool_name, tool_input={"some_param": "test_script.py"}, file_path="test_script.py"
                )

                self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_without_file_path(self):
        """Test that guard doesn't trigger without file path."""
        context = GuardContext(tool_name="Write", tool_input={"content": "test content"}, file_path=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_suggests_temp_directory(self):
        """Test that message suggests using temp directory."""
        context = GuardContext(
            tool_name="Write", tool_input={"file_path": "test_feature.py"}, file_path="test_feature.py"
        )

        message = self.guard.get_message(context)

        self.assertIn("TEMPORARY FILE LOCATION WARNING", message)
        self.assertIn("temporary script in the repository root", message)
        self.assertIn("temp/", message)
        self.assertIn("temp/test_feature.py", message)
        self.assertIn("/tmp/test_feature.py", message)
        self.assertIn("gitignored", message)
        self.assertIn("repository clutter", message)

    def test_default_action_is_allow(self):
        """Test that default action is to allow (non-blocking)."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.ALLOW)


class TestReminderGuardEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for reminder guards."""

    def test_container_rebuild_reminder_with_complex_paths(self):
        """Test container rebuild reminder with complex file paths."""
        guard = ContainerRebuildReminder()

        complex_paths = [
            "./Dockerfile",
            "../service/Dockerfile",
            "/full/path/to/docker-compose.yml",
            "services/web/Dockerfile.prod",
            "docker/compose/docker-compose.override.yaml",
        ]

        for file_path in complex_paths:
            with self.subTest(file_path=file_path):
                context = GuardContext(tool_name="Edit", tool_input={"file_path": file_path}, file_path=file_path)

                # Check if path matches the actual patterns used by the guard
                should_trigger = "Dockerfile" in file_path or (
                    ("docker-compose" in file_path or file_path.endswith(("compose.yml", "compose.yaml")))
                    and file_path.endswith((".yml", ".yaml"))
                )

                self.assertEqual(guard.should_trigger(context), should_trigger)

    def test_database_schema_reminder_with_complex_sql(self):
        """Test database schema reminder with complex SQL patterns."""
        guard = DatabaseSchemaReminder()

        complex_sql_cases = [
            "SELECT a.name, b.title FROM artists a JOIN albums b ON a.id = b.artist_id",
            "WITH RECURSIVE category_tree AS (SELECT * FROM categories) SELECT * FROM category_tree",
            "INSERT INTO tracks (name, album_id) SELECT name, album_id FROM temp_tracks",
            "UPDATE tracks SET duration = CASE WHEN duration < 60 THEN 60 ELSE duration END",
            "SELECT COUNT(*) as total, AVG(rating) as avg_rating FROM reviews WHERE created_at > '2023-01-01'",
        ]

        for sql_content in complex_sql_cases:
            with self.subTest(sql_content=sql_content):
                context = GuardContext(
                    tool_name="Write",
                    tool_input={"file_path": "complex_query.py", "content": sql_content},
                    content=sql_content,
                )

                self.assertTrue(guard.should_trigger(context))

    def test_temp_file_guard_edge_cases(self):
        """Test temp file guard with edge cases."""
        guard = TempFileLocationGuard()

        edge_cases = [
            ("test_something.py", True),  # With underscore should trigger
            ("testfile.py", False),  # No underscore, not temp pattern
            ("my_test_file.py", False),  # Doesn't start with temp pattern
            ("test", False),  # No extension
            ("test.txt", False),  # Wrong extension
            ("investigate_bug.py", True),  # Should match investigate_ pattern
        ]

        for file_path, should_trigger in edge_cases:
            with self.subTest(file_path=file_path, should_trigger=should_trigger):
                context = GuardContext(tool_name="Write", tool_input={"file_path": file_path}, file_path=file_path)

                self.assertEqual(guard.should_trigger(context), should_trigger)

    @unittest.mock.patch("builtins.input", return_value="y")
    def test_reminder_guards_non_interactive_behavior(self, mock_input):
        """Test that reminder guards allow in both interactive modes."""
        guards = [ContainerRebuildReminder(), DatabaseSchemaReminder(), TempFileLocationGuard()]

        contexts = [
            GuardContext(tool_name="Edit", tool_input={"file_path": "Dockerfile"}, file_path="Dockerfile"),
            GuardContext(
                tool_name="Write", tool_input={"content": "SELECT * FROM users"}, content="SELECT * FROM users"
            ),
            GuardContext(tool_name="Write", tool_input={"file_path": "test_script.py"}, file_path="test_script.py"),
        ]

        for guard, context in zip(guards, contexts):
            with self.subTest(guard=guard.__class__.__name__):
                # All reminder guards should allow (non-blocking)
                interactive_result = guard.check(context, is_interactive=True)
                non_interactive_result = guard.check(context, is_interactive=False)

                # Both should allow since these are reminders, not blocks
                self.assertFalse(interactive_result.should_block)
                self.assertFalse(non_interactive_result.should_block)
                self.assertEqual(interactive_result.exit_code, 0)
                self.assertEqual(non_interactive_result.exit_code, 0)

    def test_reminder_guards_message_formatting(self):
        """Test that reminder guard messages are properly formatted."""
        container_guard = ContainerRebuildReminder()
        db_guard = DatabaseSchemaReminder()
        temp_guard = TempFileLocationGuard()

        container_context = GuardContext(
            tool_name="Edit", tool_input={"file_path": "Dockerfile"}, file_path="Dockerfile"
        )

        db_context = GuardContext(
            tool_name="Write", tool_input={"content": "SELECT * FROM tracks"}, content="SELECT * FROM tracks"
        )

        temp_context = GuardContext(
            tool_name="Write", tool_input={"file_path": "debug_script.py"}, file_path="debug_script.py"
        )

        # Test that all messages have proper structure
        container_message = container_guard.get_message(container_context)
        db_message = db_guard.get_message(db_context)
        temp_message = temp_guard.get_message(temp_context)

        # All should have emoji headers and clear structure
        self.assertTrue(container_message.startswith("📦"))
        self.assertTrue(db_message.startswith("🗄️"))
        self.assertTrue(temp_message.startswith("📁"))

        # All should have multiple lines with clear sections
        self.assertGreater(len(container_message.split("\n")), 5)
        self.assertGreater(len(db_message.split("\n")), 5)
        self.assertGreater(len(temp_message.split("\n")), 5)


if __name__ == "__main__":
    unittest.main()
