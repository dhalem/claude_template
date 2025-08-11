#!/usr/bin/env python3
"""Test script for Discord webhook functionality.

RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
1. Read CLAUDE.md COMPLETELY before responding
2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
3. Search for rules related to the request
4. Only proceed after confirming no violations
Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.

GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
NEVER weaken, disable, or bypass guards - they prevent real harm
"""

import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def create_test_transcript():
    """Create a test transcript file with sample messages."""
    transcript = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)

    # Write sample messages
    messages = [
        {"role": "user", "content": "Hello, can you help me with a Python script?"},
        {
            "role": "assistant",
            "content": "I'd be happy to help you with a Python script! What would you like to create?",
        },
        {"role": "user", "content": "I need to parse JSON files"},
        {
            "role": "assistant",
            "content": "I've created a JSON parser script that handles reading, parsing, and processing JSON files with proper error handling. The script includes functions for loading JSON from files, validating structure, and extracting specific fields. It also handles both single JSON objects and JSON arrays efficiently.",
        },
    ]

    for msg in messages:
        transcript.write(json.dumps(msg) + "\n")

    transcript.close()
    return transcript.name


def test_discord_hook():
    """Test the Discord Stop hook with sample data."""
    print("🧪 Testing Discord Stop Hook")
    print("-" * 50)

    # Create test transcript
    transcript_path = create_test_transcript()
    print(f"✅ Created test transcript: {transcript_path}")

    # Prepare test data that simulates a Stop event
    test_data = {
        "session_id": "test-session-123456",
        "transcript_path": transcript_path,
        "cwd": "/home/dhalem/github/claude_template",
        "hook_event_name": "Stop",
        "tool_name": None,
        "tool_input": None,
    }

    # Convert to JSON
    json_input = json.dumps(test_data, indent=2)
    print("📝 Test input data:")
    print(json_input)
    print("-" * 50)

    # Run the hook script
    script_path = Path(__file__).parent / "discord-stop-hook.py"

    try:
        print(f"🚀 Running Discord hook: {script_path}")
        result = subprocess.run(
            [sys.executable, str(script_path)], input=json_input, capture_output=True, text=True, timeout=10
        )

        print(f"✅ Exit code: {result.returncode}")

        if result.stdout:
            print("📤 STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("📤 STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("\n✅ SUCCESS: Hook executed successfully!")
            print("Check your Discord channel for the notification.")
        else:
            print(f"\n❌ ERROR: Hook returned non-zero exit code: {result.returncode}")

    except subprocess.TimeoutExpired:
        print("❌ ERROR: Hook script timed out after 10 seconds")
    except Exception as e:
        print(f"❌ ERROR: Failed to run hook script: {e}")
    finally:
        # Clean up test transcript
        try:
            Path(transcript_path).unlink()
            print("🧹 Cleaned up test transcript")
        except:
            pass


def test_webhook_directly():
    """Test sending a webhook directly without the hook script."""
    print("\n" + "=" * 50)
    print("🔧 Testing Discord Webhook Directly")
    print("-" * 50)

    import urllib.error
    import urllib.request

    webhook_url = "https://discord.com/api/webhooks/1404272102944538634/Iwmwb5gU9ZJjQKELjyK8_fwEK5HYfACcw6GgSOWLOq9n8Hgt_zsTinBwyiXUxVhPizMR"

    # Create a simple test message
    payload = {
        "username": "Claude Code Test",
        "content": "🧪 Test webhook connection successful!",
        "embeds": [
            {
                "title": "Webhook Test",
                "description": "This is a test message from the Discord Stop hook test script.",
                "color": 65280,  # Green
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "fields": [
                    {"name": "Test Status", "value": "✅ Connection successful", "inline": True},
                    {"name": "Timestamp", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                ],
            }
        ],
    }

    try:
        # Send webhook
        json_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=json_data,
            headers={"Content-Type": "application/json", "User-Agent": "Claude-Code-Test/1.0"},
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 204:
                print("✅ Direct webhook test successful!")
                print("Check your Discord channel for the test message.")
            else:
                print(f"⚠️ Unexpected response code: {response.getcode()}")

    except urllib.error.URLError as e:
        print(f"❌ Webhook error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("Discord Stop Hook Test Suite")
    print("=" * 50)

    # Test the hook script
    test_discord_hook()

    # Test webhook directly
    test_webhook_directly()

    print("\n" + "=" * 50)
    print("Test suite complete!")
    print("=" * 50)
