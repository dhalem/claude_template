#!/usr/bin/env python3
"""Discord webhook notification for Claude Code Stop hook.

RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
1. Read CLAUDE.md COMPLETELY before responding
2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
3. Search for rules related to the request
4. Only proceed after confirming no violations
Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.

GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
NEVER weaken, disable, or bypass guards - they prevent real harm

This hook sends Discord notifications when Claude Code finishes work.
It extracts workspace name and final message, sending a rich embed to Discord.
"""

import json
import os
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class DiscordStopHook:
    """Handles Discord webhook notifications for Stop events."""

    def __init__(self):
        """Initialize the Discord Stop hook."""
        # Get webhook URL from environment or config
        self.webhook_url = self._get_webhook_url()
        self.timeout = 5  # 5 second timeout for webhook calls

    def _get_webhook_url(self) -> Optional[str]:
        """Get webhook URL from environment or config file.

        Priority:
        1. DISCORD_WEBHOOK_URL environment variable
        2. ~/.claude/discord_webhook_config.json
        3. Hardcoded URL (for initial testing)
        """
        # Check environment variable
        url = os.environ.get("DISCORD_WEBHOOK_URL")
        if url:
            return url

        # Check config file
        config_path = Path.home() / ".claude" / "discord_webhook_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    url = config.get("webhook_url")
                    if url:
                        return url
            except Exception:
                pass  # Fail silently, use fallback

        # Hardcoded URL for initial setup (you provided this)
        return "https://discord.com/api/webhooks/1404272102944538634/Iwmwb5gU9ZJjQKELjyK8_fwEK5HYfACcw6GgSOWLOq9n8Hgt_zsTinBwyiXUxVhPizMR"

    def _extract_workspace_name(self, cwd: str) -> str:
        """Extract workspace/project name from current working directory.

        Args:
            cwd: Current working directory path

        Returns:
            Workspace name (project root, not subdirectory)
        """
        try:
            path = Path(cwd)
            print(f"DEBUG: CWD is: {cwd}", file=sys.stderr)

            # Special case: for /home/dhalem/github/*/... paths
            parts = path.parts
            try:
                if len(parts) >= 4 and parts[1] == "home" and parts[3] == "github":
                    # Return the directory directly under github
                    workspace = parts[4]
                    print(f"DEBUG: Using github workspace: {workspace}", file=sys.stderr)
                    return workspace
            except IndexError:
                pass

            # Look for common project indicators going up the tree
            current = path
            while current != current.parent:
                # Check for git repository
                if (current / ".git").exists():
                    print(f"DEBUG: Found git root at: {current}", file=sys.stderr)
                    return current.name
                # Check for common project files
                if any(
                    (current / f).exists()
                    for f in [".mcp.json", "package.json", "pyproject.toml", "setup.py", "Cargo.toml"]
                ):
                    return current.name
                current = current.parent

            # Fallback: if path contains common project patterns
            parts = path.parts
            for i, part in enumerate(parts):
                if part in ["github", "projects", "repos", "workspace"]:
                    # Return the next part if it exists
                    if i + 1 < len(parts):
                        return parts[i + 1]

            # Last resort: return the directory name
            return path.name or "Unknown Workspace"
        except Exception:
            return "Unknown Workspace"

    def _extract_final_message(self, transcript_path: Optional[str]) -> str:
        """Extract the final message from conversation transcript.

        Args:
            transcript_path: Path to conversation transcript file

        Returns:
            Final message summary (truncated to 1024 chars for Discord)
        """
        if not transcript_path:
            print("DEBUG: No transcript path provided", file=sys.stderr)
            return "No transcript available"

        try:
            path = Path(transcript_path)
            print(f"DEBUG: Transcript path: {transcript_path}", file=sys.stderr)

            if not path.exists():
                print(f"DEBUG: Transcript file does not exist: {path}", file=sys.stderr)
                return "Transcript file not found"

            print(f"DEBUG: Transcript file size: {path.stat().st_size} bytes", file=sys.stderr)

            # Read the transcript (JSONL format)
            messages = []
            line_count = 0
            with open(path, "r") as f:
                for line in f:
                    line_count += 1
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            messages.append(msg)
                            # Debug: print structure of first message
                            if line_count == 1:
                                print(f"DEBUG: First message keys: {list(msg.keys())}", file=sys.stderr)
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: JSON decode error on line {line_count}: {e}", file=sys.stderr)
                            continue

            print(f"DEBUG: Total messages parsed: {len(messages)}", file=sys.stderr)

            # Find the last assistant message - try multiple formats
            last_message = "No message found"

            for i, msg in enumerate(reversed(messages)):
                # Debug last few messages
                if i < 3:
                    print(f"DEBUG: Message {i} keys: {list(msg.keys())}", file=sys.stderr)
                    if "role" in msg:
                        print(f"DEBUG: Message {i} role: {msg['role']}", file=sys.stderr)

                # Try different message formats
                content = None

                # Format 1: Standard {role: "assistant", content: "..."}
                if msg.get("role") == "assistant" and "content" in msg:
                    content = msg["content"]
                    print("DEBUG: Found assistant via role/content", file=sys.stderr)

                # Format 2: Check for any field that looks like message content
                elif not content:
                    for key in ["content", "message", "text", "body"]:
                        if key in msg and msg[key]:
                            # Simple heuristic: if it's a reasonably long string, it might be content
                            candidate = msg[key]
                            if isinstance(candidate, str) and len(candidate) > 20:
                                content = candidate
                                print(f"DEBUG: Found content via key '{key}'", file=sys.stderr)
                                break
                            elif isinstance(candidate, list) and len(candidate) > 0:
                                # Handle content as list of parts
                                text_parts = []
                                for part in candidate:
                                    if isinstance(part, dict) and "text" in part:
                                        text_parts.append(part["text"])
                                    elif isinstance(part, str):
                                        text_parts.append(part)
                                if text_parts:
                                    content = " ".join(text_parts)
                                    print(f"DEBUG: Found content via list in key '{key}'", file=sys.stderr)
                                    break

                if content and isinstance(content, str) and len(content.strip()) > 0:
                    # Get first 1000 chars (leave room for ellipsis)
                    content = content.strip()
                    if len(content) > 1000:
                        last_message = content[:1000] + "..."
                    else:
                        last_message = content
                    print(f"DEBUG: Extracted message length: {len(last_message)}", file=sys.stderr)
                    break

            return last_message

        except Exception as e:
            return f"Error reading transcript: {str(e)}"

    def _create_discord_embed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Discord embed from hook data.

        Args:
            data: Hook input data

        Returns:
            Discord webhook payload with embed
        """
        # Extract relevant information
        cwd = data.get("cwd", "")
        workspace = self._extract_workspace_name(cwd)
        transcript_path = data.get("transcript_path")
        session_id = data.get("session_id", "unknown")
        final_message = self._extract_final_message(transcript_path)

        # Create timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Create embed
        embed = {
            "title": "🤖 Claude Code Session Complete",
            "description": f"**Workspace:** `{workspace}` (from `{cwd}`)",
            "color": 5814783,  # Blue color
            "fields": [
                {"name": "📝 Final Message", "value": final_message[:1024], "inline": False},  # Discord field limit
                {
                    "name": "🔍 Session ID",
                    "value": f"`{session_id[:16]}...`" if len(session_id) > 16 else f"`{session_id}`",
                    "inline": True,
                },
                {"name": "📂 Working Directory", "value": f"`{cwd}`"[:1024], "inline": False},
                {
                    "name": "🐛 Debug",
                    "value": f"Transcript exists: {Path(transcript_path).exists() if transcript_path else 'No path'}",
                    "inline": True,
                },
            ],
            "timestamp": timestamp,
            "footer": {"text": "Claude Code Stop Hook", "icon_url": "https://www.anthropic.com/favicon.ico"},
        }

        # Create webhook payload
        payload = {"username": "Claude Code", "avatar_url": "https://www.anthropic.com/favicon.ico", "embeds": [embed]}

        return payload

    def send_webhook(self, data: Dict[str, Any]) -> bool:
        """Send Discord webhook notification.

        Args:
            data: Hook input data

        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            print("Warning: No Discord webhook URL configured", file=sys.stderr)
            return False

        try:
            # Create payload
            payload = self._create_discord_embed(data)

            # Convert to JSON
            json_data = json.dumps(payload).encode("utf-8")

            # Create request with User-Agent to avoid 403
            req = urllib.request.Request(
                self.webhook_url,
                data=json_data,
                headers={"Content-Type": "application/json", "User-Agent": "Claude-Code-Stop-Hook/1.0"},
            )

            # Send with timeout
            with urllib.request.urlopen(req, timeout=self.timeout) as response:  # nosec B310
                if response.getcode() == 204:  # Discord returns 204 on success
                    return True

        except urllib.error.URLError as e:
            print(f"Discord webhook error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Unexpected error sending webhook: {e}", file=sys.stderr)

        return False

    def run(self) -> int:
        """Main entry point for the hook.

        Returns:
            Exit code (always 0 to not block Claude)
        """
        try:
            # Read input from stdin
            input_data = sys.stdin.read()
            if not input_data:
                print("No input data received", file=sys.stderr)
                return 0

            # Parse JSON input
            try:
                data = json.loads(input_data)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON input: {e}", file=sys.stderr)
                return 0

            # Check if this is a Stop event
            event_name = data.get("hook_event_name")
            if event_name != "Stop":
                # Not a Stop event, ignore
                return 0

            # Send Discord notification
            success = self.send_webhook(data)
            if success:
                print("Discord notification sent successfully", file=sys.stderr)
            else:
                print("Failed to send Discord notification", file=sys.stderr)

        except Exception as e:
            # Log error but don't block Claude
            print(f"Discord Stop hook error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

        # Always return 0 to not block Claude
        return 0


def main():
    """Main entry point."""
    hook = DiscordStopHook()
    sys.exit(hook.run())


if __name__ == "__main__":
    main()
