"""Unit tests for pattern matching utilities."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.patterns import (  # noqa: E402
    COMPLETION_PATTERNS,
    DOCKER_RESTART_PATTERNS,
    DOCKER_SAFE_COMMANDS,
    DOCKER_WITHOUT_COMPOSE_PATTERN,
    GIT_FORCE_PUSH_PATTERNS,
    GIT_NO_VERIFY_PATTERN,
    LOCATION_DEPENDENT_PATTERNS,
    MOCK_CODE_PATTERNS,
    TEMP_FILE_PATTERNS,
    find_matching_patterns,
    matches_any_pattern,
)


class TestPatternMatching(unittest.TestCase):
    """Test cases for pattern matching functions."""

    def test_matches_any_pattern_true(self):
        """Test matches_any_pattern returns True when patterns match."""
        patterns = [GIT_NO_VERIFY_PATTERN]
        text = "git commit -m 'test' --no-verify"

        self.assertTrue(matches_any_pattern(text, patterns))

    def test_matches_any_pattern_false(self):
        """Test matches_any_pattern returns False when no patterns match."""
        patterns = [GIT_NO_VERIFY_PATTERN]
        text = "git commit -m 'test'"

        self.assertFalse(matches_any_pattern(text, patterns))

    def test_find_matching_patterns(self):
        """Test find_matching_patterns returns correct pattern strings."""
        patterns = GIT_FORCE_PUSH_PATTERNS
        text = "git push origin main --force"

        matching = find_matching_patterns(text, patterns)

        # Check that at least one pattern matches and contains the expected force pattern
        self.assertGreater(len(matching), 0)
        # The pattern should be the more specific one with negative lookahead
        force_pattern_found = any("--force" in pattern for pattern in matching)
        self.assertTrue(force_pattern_found)


class TestGitPatterns(unittest.TestCase):
    """Test cases for Git-related patterns."""

    def test_git_no_verify_pattern(self):
        """Test Git no-verify pattern matching."""
        positive_cases = [
            "git commit -m 'test' --no-verify",
            "git commit --no-verify -m 'message'",
            "git   commit   --no-verify",
            "sudo git commit --no-verify",
        ]

        negative_cases = [
            "git commit -m 'test'",
            "git commit --verify",
            "git push --no-verify",  # Different git command
            "echo '--no-verify'",  # Not a git command
        ]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertIsNotNone(GIT_NO_VERIFY_PATTERN.search(case))

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertIsNone(GIT_NO_VERIFY_PATTERN.search(case))

    def test_git_force_push_patterns(self):
        """Test Git force push pattern matching."""
        positive_cases = [
            "git push origin main --force",
            "git push --force",
            "git push origin main -f",
            "git push -f",
            "git push origin feature-branch --force",
        ]

        negative_cases = [
            "git push origin main",
            "git push --force-with-lease",
            "git commit --force",  # Not a push command
            "echo '--force'",
        ]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertTrue(matches_any_pattern(case, GIT_FORCE_PUSH_PATTERNS))

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertFalse(matches_any_pattern(case, GIT_FORCE_PUSH_PATTERNS))


class TestDockerPatterns(unittest.TestCase):
    """Test cases for Docker-related patterns."""

    def test_docker_restart_patterns(self):
        """Test Docker restart pattern matching."""
        positive_cases = [
            "docker restart container",
            "docker compose restart",
            "docker-compose restart service",
            "sudo docker restart my-app",
        ]

        negative_cases = ["docker start container", "docker stop container", "docker build .", "docker ps"]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertTrue(matches_any_pattern(case, DOCKER_RESTART_PATTERNS))

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertFalse(matches_any_pattern(case, DOCKER_RESTART_PATTERNS))

    def test_docker_without_compose_pattern(self):
        """Test Docker without compose pattern matching."""
        positive_cases = [
            "docker run -it ubuntu",
            "docker build .",
            "docker stop container",
            "docker create --name test ubuntu",
        ]

        negative_cases = [
            "docker compose up -d",
            "docker -c musicbot compose build",
            "docker --context musicbot compose ps",
            "docker-compose up",
        ]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertIsNotNone(DOCKER_WITHOUT_COMPOSE_PATTERN.search(case))

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertIsNone(DOCKER_WITHOUT_COMPOSE_PATTERN.search(case))

    def test_docker_safe_commands(self):
        """Test Docker safe commands pattern matching."""
        safe_cases = [
            "docker ps",
            "docker logs container",
            "docker exec -it container bash",
            "docker images",
            "docker system prune",
            "docker info",
            "docker version",
            "docker help",
        ]

        unsafe_cases = ["docker run ubuntu", "docker build .", "docker stop container", "docker create container"]

        for case in safe_cases:
            with self.subTest(case=case):
                self.assertIsNotNone(DOCKER_SAFE_COMMANDS.search(case))

        for case in unsafe_cases:
            with self.subTest(case=case):
                self.assertIsNone(DOCKER_SAFE_COMMANDS.search(case))


class TestMockPatterns(unittest.TestCase):
    """Test cases for mock code patterns."""

    def test_mock_code_patterns(self):
        """Test mock code pattern matching."""
        positive_cases = [
            "@mock.patch('service')",
            "import unittest.mock",
            "from unittest.mock import MagicMock",
            "mock_obj = MagicMock()",
            "Mock()",
            "SIMULATION: fake response",
            "if test_mode: return fake_result",
            "mock_database = Mock()",
            "service.patch('method')",
        ]

        negative_cases = [
            "import requests",
            "def get_data():",
            "return real_result",
            "# This is a comment",
            "class TestCase(unittest.TestCase):",
        ]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertTrue(matches_any_pattern(case, MOCK_CODE_PATTERNS), f"Should match: {case}")

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertFalse(matches_any_pattern(case, MOCK_CODE_PATTERNS), f"Should not match: {case}")


class TestLocationPatterns(unittest.TestCase):
    """Test cases for location-dependent patterns."""

    def test_location_dependent_patterns(self):
        """Test location-dependent command patterns."""
        positive_cases = [
            "cd relative/path",
            "./run_script.sh",
            "../config/setup.sh",
            "script.sh",
            "python local_script.py",
            "make build",
            "npm install",
            "yarn start",
        ]

        negative_cases = ["cd /absolute/path", "/usr/bin/script.sh", "python /full/path/script.py", "ls", "git status"]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertTrue(matches_any_pattern(case, LOCATION_DEPENDENT_PATTERNS), f"Should match: {case}")

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertFalse(matches_any_pattern(case, LOCATION_DEPENDENT_PATTERNS), f"Should not match: {case}")


class TestCompletionPatterns(unittest.TestCase):
    """Test cases for completion claim patterns."""

    def test_completion_patterns(self):
        """Test completion claim pattern matching."""
        positive_cases = [
            "echo 'Feature complete'",
            "echo 'Implementation done'",
            "echo 'Tests finished'",
            "echo 'System working'",
            "echo 'Ready for production'",
            "echo 'Bug fixed'",
            "All tests passed",
            "Feature complete",
            "Implementation complete",
        ]

        negative_cases = [
            "echo 'Starting work'",
            "echo 'In progress'",
            "echo 'Testing in progress'",
            "git commit -m 'Work in progress'",
            "ls files",
        ]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertTrue(matches_any_pattern(case, COMPLETION_PATTERNS), f"Should match: {case}")

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertFalse(matches_any_pattern(case, COMPLETION_PATTERNS), f"Should not match: {case}")


class TestTempFilePatterns(unittest.TestCase):
    """Test cases for temporary file patterns."""

    def test_temp_file_patterns(self):
        """Test temporary file pattern matching."""
        positive_cases = ["test_feature.py", "check_status.py", "debug_issue.js", "temp_script.sh", "quick_fix.py"]

        negative_cases = ["main.py", "config.js", "utils.sh", "service.py", "component.ts"]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertTrue(matches_any_pattern(case, TEMP_FILE_PATTERNS), f"Should match: {case}")

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertFalse(matches_any_pattern(case, TEMP_FILE_PATTERNS), f"Should not match: {case}")


if __name__ == "__main__":
    unittest.main()
