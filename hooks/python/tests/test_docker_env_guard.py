"""Tests for DockerEnvGuard.

REMINDER: Update HOOKS.md when adding new tests!
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardContext  # noqa: E402
from guards.docker_env_guard import DockerEnvGuard  # noqa: E402


class TestDockerEnvGuard(unittest.TestCase):
    """Test cases for DockerEnvGuard."""

    def setUp(self):
        """Set up test fixtures."""
        self.guard = DockerEnvGuard()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_context(self, command, tool_name="Bash"):
        """Helper to create GuardContext."""
        return GuardContext(tool_name=tool_name, tool_input={"command": command}, command=command)

    def test_non_bash_tool_not_triggered(self):
        """Should not trigger for non-Bash tools."""
        context = self.create_context("docker compose up", tool_name="Task")
        self.assertFalse(self.guard.should_trigger(context))

    def test_empty_command_not_triggered(self):
        """Should not trigger for empty commands."""
        context = self.create_context("")
        self.assertFalse(self.guard.should_trigger(context))

    def test_non_docker_commands_not_triggered(self):
        """Should not trigger for non-Docker commands."""
        non_docker_commands = [
            "ls -la",
            "git status",
            "python test.py",
            "make build",
            "npm install",
            "docker ps",  # Not compose up/run
            "docker images",
            "docker compose ps",  # Not up/run
            "docker compose logs",
        ]

        for cmd in non_docker_commands:
            with self.subTest(cmd=cmd):
                context = self.create_context(cmd)
                self.assertFalse(self.guard.should_trigger(context))

    def test_docker_compose_up_triggers(self):
        """Should trigger for docker compose up commands."""
        docker_up_commands = [
            "docker compose up",
            "docker-compose up",
            "docker compose up -d",
            "docker compose up service_name",
            "docker -c musicbot compose up",
            "docker -c musicbot compose up -d service",
            "docker -c musicbot compose -f docker-compose.yml up",
        ]

        with patch.object(self.guard, "_check_env_files", return_value=True):
            for cmd in docker_up_commands:
                with self.subTest(cmd=cmd):
                    context = self.create_context(cmd)
                    self.assertTrue(self.guard.should_trigger(context))

    def test_docker_compose_run_triggers(self):
        """Should trigger for docker compose run commands."""
        docker_run_commands = [
            "docker compose run service",
            "docker-compose run service",
            "docker compose run --rm service",
            "docker -c musicbot compose run service",
            "docker -c musicbot compose run --rm service command",
        ]

        with patch.object(self.guard, "_check_env_files", return_value=True):
            for cmd in docker_run_commands:
                with self.subTest(cmd=cmd):
                    context = self.create_context(cmd)
                    self.assertTrue(self.guard.should_trigger(context))

    def test_case_insensitive_matching(self):
        """Should match commands case-insensitively."""
        commands = [
            "DOCKER COMPOSE UP",
            "Docker Compose Up",
            "docker COMPOSE up",
        ]

        with patch.object(self.guard, "_check_env_files", return_value=True):
            for cmd in commands:
                with self.subTest(cmd=cmd):
                    context = self.create_context(cmd)
                    self.assertTrue(self.guard.should_trigger(context))

    @patch("os.path.exists")
    @patch("os.getcwd")
    def test_check_env_files_missing(self, mock_getcwd, mock_exists):
        """Should trigger when required .env files are missing."""
        # Simulate being in gemini_playlist_suggester directory
        mock_getcwd.return_value = "/home/user/spotidal/gemini_playlist_suggester"
        mock_exists.return_value = False  # .env doesn't exist

        result = self.guard._check_env_files("docker compose up")
        self.assertTrue(result)

    @patch("os.path.exists")
    @patch("os.getcwd")
    def test_check_env_files_present(self, mock_getcwd, mock_exists):
        """Should not trigger when required .env files exist."""
        # Simulate being in gemini_playlist_suggester directory
        mock_getcwd.return_value = "/home/user/spotidal/gemini_playlist_suggester"
        mock_exists.return_value = True  # .env exists

        result = self.guard._check_env_files("docker compose up")
        self.assertFalse(result)

    @patch("os.path.exists")
    @patch("os.getcwd")
    def test_service_without_env_requirement(self, mock_getcwd, mock_exists):
        """Should not trigger for services that don't need .env files."""
        # Simulate being in monitoring directory (no .env required)
        mock_getcwd.return_value = "/home/user/spotidal/monitoring"
        mock_exists.return_value = False  # Doesn't matter

        result = self.guard._check_env_files("docker compose up")
        self.assertFalse(result)

    def test_detect_service_directory_from_compose_file(self):
        """Should detect service directory from -f flag."""
        command = "docker compose -f /home/user/spotidal/syncer/docker-compose.yml up"
        result = self.guard._detect_service_directory(command)
        self.assertEqual(result, "/home/user/spotidal/syncer")

    @patch("os.getcwd")
    def test_detect_service_directory_from_cwd(self, mock_getcwd):
        """Should detect service directory from current working directory."""
        mock_getcwd.return_value = "/home/user/spotidal/syncer_v2"

        result = self.guard._detect_service_directory("docker compose up")
        self.assertEqual(result, "/home/user/spotidal/syncer_v2")

    @patch("os.getcwd")
    def test_detect_service_directory_nested(self, mock_getcwd):
        """Should detect service directory even when in subdirectory."""
        mock_getcwd.return_value = "/home/user/spotidal/gemini_playlist_suggester/src/utils"

        result = self.guard._detect_service_directory("docker compose up")
        self.assertEqual(result, "/home/user/spotidal/gemini_playlist_suggester")

    @patch("os.getcwd")
    def test_detect_service_directory_unknown(self, mock_getcwd):
        """Should return current directory if service can't be determined."""
        mock_getcwd.return_value = "/home/user/random/path"

        result = self.guard._detect_service_directory("docker compose up")
        self.assertEqual(result, "/home/user/random/path")

    def test_get_message_includes_service_info(self):
        """Should include service and missing file info in message."""
        context = self.create_context("docker compose up")

        with patch.object(
            self.guard, "_detect_service_directory", return_value="/path/gemini_playlist_suggester"
        ), patch("os.path.exists", return_value=False):
            message = self.guard.get_message(context)

            self.assertIn("gemini_playlist_suggester", message)
            self.assertIn(".env", message)
            self.assertIn("Missing API keys", message)
            self.assertIn("cp sample.env .env", message)

    def test_get_message_service_specific_info(self):
        """Should include service-specific requirements in message."""
        context = self.create_context("docker compose up")

        message = self.guard.get_message(context)

        # Check for service-specific sections
        self.assertIn("gemini_playlist_suggester", message)
        self.assertIn("syncer", message)
        self.assertIn("syncer_v2", message)
        self.assertIn("Google, OpenAI, Anthropic", message)
        self.assertIn("Spotify/Tidal credentials", message)

    def test_get_default_action_is_block(self):
        """Should have BLOCK as default action."""
        self.assertEqual(self.guard.get_default_action().value, "block")

    def test_guard_metadata(self):
        """Should have correct metadata."""
        self.assertEqual(self.guard.name, "Docker Environment File Guard")
        self.assertIn("required .env files", self.guard.description)

    def test_env_requirements_configuration(self):
        """Should have correct env requirements configuration."""
        # Check known services
        self.assertIn("gemini_playlist_suggester", self.guard.env_requirements)
        self.assertIn("syncer", self.guard.env_requirements)
        self.assertIn("syncer_v2", self.guard.env_requirements)
        self.assertIn("monitoring", self.guard.env_requirements)
        self.assertIn("sonos_server", self.guard.env_requirements)

        # Check requirements
        self.assertEqual(self.guard.env_requirements["gemini_playlist_suggester"], [".env"])
        self.assertEqual(self.guard.env_requirements["monitoring"], [])  # No .env needed
        self.assertEqual(self.guard.env_requirements["sonos_server"], [])  # Uses config.py

    @patch("os.path.exists")
    @patch("os.getcwd")
    def test_multiple_env_files(self, mock_getcwd, mock_exists):
        """Should check multiple .env files if configured."""
        # Modify guard to require multiple files for testing
        self.guard.env_requirements["test_service"] = [".env", ".env.local"]

        mock_getcwd.return_value = "/home/user/spotidal/test_service"

        # First file exists, second doesn't
        def exists_side_effect(path):
            return ".env.local" not in path

        mock_exists.side_effect = exists_side_effect

        result = self.guard._check_env_files("docker compose up")
        self.assertTrue(result)  # Should trigger because .env.local is missing

    @patch("os.path.exists")
    @patch("os.getcwd")
    def test_all_env_files_present(self, mock_getcwd, mock_exists):
        """Should not trigger when all required files exist."""
        self.guard.env_requirements["test_service"] = [".env", ".env.local"]

        mock_getcwd.return_value = "/home/user/spotidal/test_service"
        mock_exists.return_value = True  # All files exist

        result = self.guard._check_env_files("docker compose up")
        self.assertFalse(result)

    def test_unknown_service_triggers(self):
        """Should trigger for unknown services to be safe."""
        with patch.object(self.guard, "_detect_service_directory", return_value=None):
            result = self.guard._check_env_files("docker compose up")
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
