"""Unit tests for Docker-related guards."""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import GuardAction, GuardContext  # noqa: E402
from guards.docker_guards import DockerRestartGuard, DockerWithoutComposeGuard  # noqa: E402


class TestDockerRestartGuard(unittest.TestCase):
    """Test cases for DockerRestartGuard."""

    def setUp(self):
        self.guard = DockerRestartGuard()

    def test_should_trigger_on_docker_restart(self):
        """Test that guard triggers on docker restart commands."""
        test_cases = [
            "docker restart my-container",
            "docker   restart   container-name",
            "docker restart --time=30 container",
            "sudo docker restart container",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_trigger_on_compose_restart(self):
        """Test that guard triggers on docker compose restart commands."""
        test_cases = [
            "docker compose restart",
            "docker compose restart service-name",
            "docker-compose restart",
            "docker -c musicbot compose restart service",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_not_trigger_on_safe_commands(self):
        """Test that guard doesn't trigger on safe docker commands."""
        test_cases = [
            "docker ps",
            "docker logs container",
            "docker build .",
            "docker compose build",
            "docker compose up -d",
            "docker stop container",
            "docker start container",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context), f"Should not trigger on: {command}")

    def test_should_not_trigger_on_non_bash(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        context = GuardContext(tool_name="Edit", tool_input={"file_path": "test.py"}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_should_not_trigger_on_empty_command(self):
        """Test that guard doesn't trigger on empty commands."""
        context = GuardContext(tool_name="Bash", tool_input={}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_details(self):
        """Test that error message contains important details."""
        context = GuardContext(
            tool_name="Bash",
            tool_input={"command": "docker restart my-container"},
            command="docker restart my-container",
        )

        message = self.guard.get_message(context)

        # Check for key elements in the message
        self.assertIn("docker restart my-container", message)
        self.assertIn("EXISTING images", message)
        self.assertIn("June 30, 2025", message)  # Historical incident
        self.assertIn("docker -c musicbot compose build", message)
        self.assertIn("docker -c musicbot compose up -d", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)


class TestDockerWithoutComposeGuard(unittest.TestCase):
    """Test cases for DockerWithoutComposeGuard."""

    def setUp(self):
        self.guard = DockerWithoutComposeGuard()

    def test_should_trigger_on_docker_run(self):
        """Test that guard triggers on docker run commands."""
        test_cases = [
            "docker run -it ubuntu bash",
            "docker run -d --name test nginx",
            "docker create --name test ubuntu",
            "docker build -t myimage .",
            "docker stop container",
            "docker start container",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(self.guard.should_trigger(context), f"Should trigger on: {command}")

    def test_should_not_trigger_on_compose_commands(self):
        """Test that guard doesn't trigger on docker compose commands."""
        test_cases = [
            "docker compose up -d",
            "docker compose build",
            "docker -c musicbot compose ps",
            "docker --context musicbot compose logs",
            "docker-compose up",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context), f"Should not trigger on: {command}")

    def test_should_not_trigger_on_safe_commands(self):
        """Test that guard doesn't trigger on safe docker commands."""
        test_cases = [
            "docker ps",
            "docker ps -a",
            "docker logs container-name",
            "docker exec -it container bash",
            "docker images",
            "docker system prune",
            "docker info",
            "docker version",
            "docker help",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context), f"Should not trigger on: {command}")

    def test_should_not_trigger_on_non_docker_commands(self):
        """Test that guard doesn't trigger on non-docker commands."""
        test_cases = ["ls -la", "git status", "npm install", "python script.py"]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertFalse(self.guard.should_trigger(context), f"Should not trigger on: {command}")

    def test_should_not_trigger_on_non_bash(self):
        """Test that guard doesn't trigger on non-Bash tools."""
        context = GuardContext(tool_name="Write", tool_input={"file_path": "test.py"}, command=None)

        self.assertFalse(self.guard.should_trigger(context))

    def test_get_message_contains_alternatives(self):
        """Test that error message contains proper alternatives."""
        context = GuardContext(
            tool_name="Bash", tool_input={"command": "docker run -it ubuntu bash"}, command="docker run -it ubuntu bash"
        )

        message = self.guard.get_message(context)

        # Check for key elements in the message
        self.assertIn("docker run -it ubuntu bash", message)
        self.assertIn("docker-compose.yml", message)
        self.assertIn("docker -c musicbot compose", message)
        self.assertIn("June 30, 2025", message)  # Historical incident
        self.assertIn("ALLOWED EXCEPTIONS", message)

    def test_default_action_is_block(self):
        """Test that default action is to block."""
        self.assertEqual(self.guard.get_default_action(), GuardAction.BLOCK)


class TestDockerGuardEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for Docker guards."""

    def test_docker_restart_guard_with_options(self):
        """Test docker restart with various options and flags."""
        guard = DockerRestartGuard()

        test_cases = [
            "docker restart --time=10 container",
            "docker restart -t 30 container",
            "docker restart container1 container2",  # Multiple containers
            "docker restart --signal=SIGKILL container",
            "DOCKER_HOST=remote docker restart container",  # With env vars
            "docker --context remote restart container",  # With context
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_docker_restart_guard_case_insensitive(self):
        """Test that docker restart guard is case insensitive."""
        guard = DockerRestartGuard()

        test_cases = [
            "DOCKER RESTART container",
            "Docker Restart container",
            "docker RESTART container",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_docker_restart_with_shell_operators(self):
        """Test docker restart combined with shell operators."""
        guard = DockerRestartGuard()

        test_cases = [
            "docker ps && docker restart container",
            "docker restart container || echo 'failed'",
            "docker restart container; echo 'done'",
            "docker stop container && docker restart container",
        ]

        for command in test_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_docker_without_compose_edge_cases(self):
        """Test docker without compose guard with edge cases."""
        guard = DockerWithoutComposeGuard()

        edge_cases = [
            "docker run --rm -it ubuntu:latest bash",  # With registry
            "docker run -v /host:/container ubuntu",  # With volumes
            "docker run -p 8080:80 -e VAR=value nginx",  # With ports and env
            "docker create --name test --network host ubuntu",  # With network
            "docker build --no-cache -f Dockerfile.prod .",  # With build options
        ]

        for command in edge_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                self.assertTrue(guard.should_trigger(context))

    def test_docker_commands_with_complex_contexts(self):
        """Test docker commands with complex context specifications."""
        restart_guard = DockerRestartGuard()
        without_compose_guard = DockerWithoutComposeGuard()

        context_cases = [
            "docker --context musicbot restart service",
            "docker -c remote run ubuntu",
            "docker --host tcp://remote:2376 restart container",
            "docker -H unix:///var/run/docker.sock run ubuntu",
        ]

        for command in context_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                if "restart" in command:
                    self.assertTrue(restart_guard.should_trigger(context))
                if "run" in command and "compose" not in command:
                    self.assertTrue(without_compose_guard.should_trigger(context))

    def test_compose_variations_recognition(self):
        """Test recognition of different compose command variations."""
        guard = DockerWithoutComposeGuard()

        compose_variations = [
            "docker compose up -d",
            "docker-compose up",
            "docker compose -f custom.yml up",
            "docker --context musicbot compose build",
            "docker -c remote compose ps",
            "COMPOSE_FILE=override.yml docker compose up",
        ]

        for command in compose_variations:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                # These should NOT trigger (they use compose)
                self.assertFalse(guard.should_trigger(context))

    def test_docker_guards_with_quoted_arguments(self):
        """Test docker commands with quoted arguments."""
        restart_guard = DockerRestartGuard()
        without_compose_guard = DockerWithoutComposeGuard()

        quoted_cases = [
            "docker restart 'container-name'",
            'docker restart "container name"',
            "docker run -e 'VAR=value with spaces' ubuntu",
            'docker run --name "my container" ubuntu',
        ]

        for command in quoted_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                if "restart" in command:
                    self.assertTrue(restart_guard.should_trigger(context))
                if "run" in command and "compose" not in command:
                    self.assertTrue(without_compose_guard.should_trigger(context))

    def test_docker_guards_false_positives(self):
        """Test that guards don't trigger on false positives."""
        restart_guard = DockerRestartGuard()
        without_compose_guard = DockerWithoutComposeGuard()

        false_positive_cases = [
            "echo 'docker restart container'",  # Echo statement
            "grep 'docker run' file.txt",  # Grep for docker commands
            "# docker restart container",  # Comment
            "cat restart-script.sh",  # Reading file about restart
            "vim run-docker.sh",  # Editing script about docker run
        ]

        for command in false_positive_cases:
            with self.subTest(command=command):
                context = GuardContext(tool_name="Bash", tool_input={"command": command}, command=command)

                # Echo, grep, cat, vim etc. should not trigger Docker guards
                if command.startswith(("echo", "grep", "#", "cat", "vim")):
                    self.assertFalse(restart_guard.should_trigger(context))
                    self.assertFalse(without_compose_guard.should_trigger(context))

    def test_docker_guards_message_content_validation(self):
        """Test that guard messages contain all required information."""
        restart_guard = DockerRestartGuard()
        without_compose_guard = DockerWithoutComposeGuard()

        restart_context = GuardContext(
            tool_name="Bash", tool_input={"command": "docker restart my-service"}, command="docker restart my-service"
        )

        run_context = GuardContext(
            tool_name="Bash", tool_input={"command": "docker run ubuntu"}, command="docker run ubuntu"
        )

        restart_message = restart_guard.get_message(restart_context)
        run_message = without_compose_guard.get_message(run_context)

        # Check restart guard message content
        required_restart_content = [
            "docker restart my-service",  # The triggering command
            "EXISTING images",  # Key problem explanation
            "docker -c musicbot compose build",  # Correct alternative
            "docker -c musicbot compose up -d",  # Correct alternative
            "June 30, 2025",  # Historical context
        ]

        for content in required_restart_content:
            self.assertIn(content, restart_message, f"Missing required content: {content}")

        # Check without-compose guard message content
        required_run_content = [
            "docker run ubuntu",  # The triggering command
            "docker-compose.yml",  # Repository pattern
            "docker -c musicbot compose",  # Correct pattern
            "ALLOWED EXCEPTIONS",  # Exception policy
        ]

        for content in required_run_content:
            self.assertIn(content, run_message, f"Missing required content: {content}")

    def test_docker_guards_interactive_behavior(self):
        """Test docker guards behavior in interactive vs non-interactive modes."""
        restart_guard = DockerRestartGuard()

        context = GuardContext(
            tool_name="Bash", tool_input={"command": "docker restart container"}, command="docker restart container"
        )

        # Test non-interactive mode (should always block)
        non_interactive_result = restart_guard.check(context, is_interactive=False)
        self.assertTrue(non_interactive_result.should_block)
        self.assertEqual(non_interactive_result.exit_code, 2)
        self.assertIn("safety-first policy", non_interactive_result.message)

        # Test that default action is BLOCK
        self.assertEqual(restart_guard.get_default_action(), GuardAction.BLOCK)

    def test_docker_guards_performance_with_long_commands(self):
        """Test docker guards performance with very long command lines."""
        restart_guard = DockerRestartGuard()
        without_compose_guard = DockerWithoutComposeGuard()

        # Create a very long docker command
        long_options = " ".join([f"--env VAR{i}=value{i}" for i in range(50)])
        long_restart_command = f"docker restart {long_options} container"
        long_run_command = f"docker run {long_options} ubuntu"

        restart_context = GuardContext(
            tool_name="Bash", tool_input={"command": long_restart_command}, command=long_restart_command
        )

        run_context = GuardContext(tool_name="Bash", tool_input={"command": long_run_command}, command=long_run_command)

        # Should still trigger correctly despite long command
        self.assertTrue(restart_guard.should_trigger(restart_context))
        self.assertTrue(without_compose_guard.should_trigger(run_context))

        # Messages should handle long commands gracefully
        restart_message = restart_guard.get_message(restart_context)
        run_message = without_compose_guard.get_message(run_context)

        self.assertIn("docker restart", restart_message)
        self.assertIn("docker run", run_message)


if __name__ == "__main__":
    unittest.main()
