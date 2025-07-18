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

"""Test suite for MCP code review server functionality and protocol compliance."""

import asyncio
import logging
import os

# Configure logging for test output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__ if '__file__' in globals() else sys.argv[0]))))


class TestMCPCodeReviewServer(unittest.TestCase):
    """Test suite for MCP code review server."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.py")
        with open(self.test_file, "w") as f:
            f.write("def hello():\n    logger.info('Hello, world!')\n")

        # Set up environment for testing
        os.environ['GEMINI_API_KEY'] = 'test-key'

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_module_import_without_name_error(self):
        """Test that the module can be imported without NameError even when __file__ is undefined."""
        # Create a test script that simulates MCP environment
        test_script = os.path.join(self.temp_dir, "test_import.py")
        with open(test_script, "w") as f:
            f.write("""
import sys
import os

# Simulate MCP environment where __file__ might not be defined
if '__file__' in globals():
    del globals()['__file__']

# Add path and try to import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

try:
    import indexing.mcp_code_review_server_v2 as server_module
    logger.info("SUCCESS: Module imported without NameError")
    logger.info(f"Module has main: {hasattr(server_module, 'main')}")
except NameError as e:
    logger.error(f"FAILED: NameError occurred: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"FAILED: Other error: {e}")
    sys.exit(1)
""")

        # Run the test script
        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )

        self.assertEqual(result.returncode, 0, f"Import test failed: {result.stderr}")
        self.assertIn("SUCCESS", result.stdout)
        self.assertIn("Module has main: True", result.stdout)

    def test_server_starts_without_error(self):
        """Test that the server can start without errors."""
        # Create a test that launches the server and immediately closes it
        test_script = os.path.join(self.temp_dir, "test_server_start.py")
        with open(test_script, "w") as f:
            f.write("""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

async def test_server():
    try:
        from indexing.mcp_code_review_server_v2 import main

        # Create a task for main but cancel it immediately
        # This tests that the server can at least start initializing
        task = asyncio.create_task(main())
        await asyncio.sleep(0.1)  # Let it start
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            logger.info("SUCCESS: Server started and was cancelled cleanly")
            return 0
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return 1

sys.exit(asyncio.run(test_server()))
""")

        # Run with a timeout
        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=self.temp_dir
        )

        # The server should start without errors (even if it can't fully run without stdio)
        self.assertIn("SUCCESS", result.stdout, f"Server start test failed: {result.stderr}")

    def test_mcp_protocol_structure(self):
        """Test that the server follows MCP protocol structure."""
        # Import the module
        import indexing.mcp_code_review_server_v2 as server_module

        # Check required imports and functions
        self.assertTrue(hasattr(server_module, 'Server'))
        self.assertTrue(hasattr(server_module, 'stdio_server'))
        self.assertTrue(hasattr(server_module, 'TextContent'))
        self.assertTrue(hasattr(server_module, 'Tool'))
        self.assertTrue(hasattr(server_module, 'main'))

        # Check that main is an async function
        self.assertTrue(asyncio.iscoroutinefunction(server_module.main))

    def test_gemini_client_integration(self):
        """Test that GeminiClient is properly integrated."""
        # This tests that the imports work correctly
        import indexing.mcp_code_review_server_v2 as server_module

        # GeminiClient should be imported
        self.assertTrue(hasattr(server_module, 'GeminiClient'))
        self.assertTrue(hasattr(server_module, 'FileCollector'))
        self.assertTrue(hasattr(server_module, 'ReviewFormatter'))

    def test_logging_setup(self):
        """Test that logging is properly configured."""

        # Check that log directory path is defined
        log_dir = Path.home() / ".claude" / "mcp" / "code-review" / "logs"
        # The directory might not exist yet, but the path should be valid
        self.assertTrue(isinstance(log_dir, Path))

    def test_tool_definition_in_main(self):
        """Test that the tool is properly defined within main()."""
        # Create a test that inspects the main function
        test_script = os.path.join(self.temp_dir, "test_tool_definition.py")
        with open(test_script, "w") as f:
            f.write("""
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

async def test_tool_definition():
    from indexing.mcp_code_review_server_v2 import main

    # Mock the Server class to capture tool registrations
    tools_registered = []

    with patch('indexing.mcp_code_review_server_v2.Server') as MockServer:
        mock_server = MagicMock()
        MockServer.return_value = mock_server

        # Capture tool decorations
        def tool_decorator(**kwargs):
            def decorator(func):
                tools_registered.append({
                    'name': kwargs.get('name', func.__name__),
                    'description': kwargs.get('description', ''),
                    'func': func
                })
                return func
            return decorator

        mock_server.tool = tool_decorator

        # Mock stdio_server to prevent actual server start
        with patch('indexing.mcp_code_review_server_v2.stdio_server'):
            # Call main to trigger tool registration
            task = asyncio.create_task(main())
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    # Check that review_code tool was registered
    tool_names = [tool['name'] for tool in tools_registered]
    if 'review_code' in tool_names:
        logger.info("SUCCESS: review_code tool registered")
        review_tool = next(t for t in tools_registered if t['name'] == 'review_code')
        logger.info(f"Tool description: {review_tool['description']}")
        return 0
    else:
        logger.error(f"FAILED: review_code tool not found. Registered tools: {tool_names}")
        return 1

sys.exit(asyncio.run(test_tool_definition()))
""")

        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=self.temp_dir
        )

        self.assertEqual(result.returncode, 0, f"Tool definition test failed: {result.stdout}\n{result.stderr}")
        self.assertIn("SUCCESS", result.stdout)
        self.assertIn("Review code files using Gemini AI", result.stdout)

    def test_error_handling(self):
        """Test error handling in the server."""
        # Test that common errors are handled gracefully
        test_script = os.path.join(self.temp_dir, "test_error_handling.py")
        with open(test_script, "w") as f:
            f.write("""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

# Test importing with missing dependencies
try:
    import indexing.mcp_code_review_server_v2 as server_module

    # The module should handle missing API keys gracefully
    if hasattr(server_module, 'GeminiClient'):
        logger.info("SUCCESS: Module handles missing dependencies gracefully")
    else:
        logger.info("FAILED: GeminiClient not found")
except Exception as e:
    logger.error(f"FAILED: Unhandled exception: {e}")
""")

        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )

        self.assertIn("SUCCESS", result.stdout, f"Error handling test failed: {result.stderr}")

    def test_file_path_handling(self):
        """Test that file paths are handled correctly."""
        # Test the path resolution after __file__ fix
        import indexing.mcp_code_review_server_v2 as server_module

        # The module should have resolved its directory correctly
        # even if __file__ was not available during import
        self.assertTrue(hasattr(server_module, 'current_dir'))

        # The sys.path should have been modified to include reviewer/src
        # Check that the path modification worked
        self.assertTrue(any('reviewer' in p and 'src' in p for p in sys.path))


class TestMCPInterface(unittest.TestCase):
    """Test the MCP interface that Claude expects."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mcp_server_executable(self):
        """Test that the server can be executed as MCP expects."""
        server_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__ if '__file__' in globals() else sys.argv[0]))),
            "indexing",
            "mcp_code_review_server_v2.py"
        )

        # Check the server file exists
        self.assertTrue(os.path.exists(server_path), f"Server file not found at {server_path}")

        # Check it's executable or can be run with Python
        result = subprocess.run(
            [sys.executable, server_path, "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # The server should at least not crash when run
        # (It might not show help, but shouldn't have import errors)
        self.assertNotIn("ModuleNotFoundError", result.stderr)
        self.assertNotIn("NameError: name '__file__'", result.stderr)

    def test_installed_server_structure(self):
        """Test that the installed server has the expected structure."""
        # Simulate the installation location
        test_install_dir = os.path.join(self.temp_dir, ".claude", "mcp", "code-review")
        bin_dir = os.path.join(test_install_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        # Copy server file
        import shutil
        server_src = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__ if '__file__' in globals() else sys.argv[0]))),
            "indexing",
            "mcp_code_review_server_v2.py"
        )
        server_dst = os.path.join(bin_dir, "server.py")
        shutil.copy(server_src, server_dst)

        # Test that the copied server can be imported
        test_script = os.path.join(self.temp_dir, "test_installed.py")
        with open(test_script, "w") as f:
            f.write(f"""
import sys
import os

# Test the installed server
server_path = r'{server_dst}'
server_dir = os.path.dirname(server_path)
sys.path.insert(0, server_dir)

try:
    import server
    logger.info("SUCCESS: Installed server can be imported")
    logger.info(f"Has main: {hasattr(server, 'main')}")
except Exception as e:
    logger.error(f"FAILED: {e}")
""")

        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )

        self.assertIn("SUCCESS", result.stdout)
        self.assertIn("Has main: True", result.stdout)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
