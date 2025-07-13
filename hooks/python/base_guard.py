"""Base classes for the Claude Code hook guard system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class GuardAction(Enum):
    """Possible actions a guard can take."""

    ALLOW = "allow"
    BLOCK = "block"


@dataclass
class GuardContext:
    """Context information passed to guards for decision making."""

    tool_name: str
    tool_input: Dict[str, Any]
    command: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    new_string: Optional[str] = None
    raw_input: Dict[str, Any] = None

    @classmethod
    def from_claude_input(cls, input_json: Dict[str, Any]) -> "GuardContext":
        """Create a GuardContext from Claude Code hook input."""
        tool_name = input_json.get("tool_name", "")
        tool_input = input_json.get("tool_input", {})

        # Extract common fields
        command = tool_input.get("command")
        file_path = tool_input.get("file_path")
        content = tool_input.get("content")
        new_string = tool_input.get("new_string")

        # Handle MultiEdit edits array
        if tool_name == "MultiEdit" and "edits" in tool_input:
            # Combine all new_strings for pattern matching
            new_strings = []
            for edit in tool_input.get("edits", []):
                if "new_string" in edit:
                    new_strings.append(edit["new_string"])
            if new_strings:
                new_string = "\n".join(new_strings)
            else:
                # Empty edits array should have empty string, not None
                new_string = ""

        return cls(
            tool_name=tool_name,
            tool_input=tool_input,
            command=command,
            file_path=file_path,
            content=content,
            new_string=new_string,
            raw_input=input_json,
        )


@dataclass
class GuardResult:
    """Result of a guard check."""

    should_block: bool
    message: Optional[str] = None
    exit_code: int = 0

    def __post_init__(self):
        """Set exit code based on should_block."""
        if self.should_block:
            self.exit_code = 2  # Critical: exit 2 blocks, exit 1 doesn't!


class BaseGuard(ABC):
    """Abstract base class for all guards."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def should_trigger(self, context: GuardContext) -> bool:
        """Determine if this guard should activate for the given context."""
        pass

    @abstractmethod
    def get_message(self, context: GuardContext) -> str:
        """Get the warning message to display to the user."""
        pass

    @abstractmethod
    def get_default_action(self) -> GuardAction:
        """Return the default action for non-interactive mode."""
        pass

    def check(self, context: GuardContext, is_interactive: bool = False) -> GuardResult:
        """Main entry point for guard checking."""
        if not self.should_trigger(context):
            return GuardResult(should_block=False)

        message = self.get_message(context)

        if is_interactive:
            # In interactive mode, prompt user
            user_choice = self._prompt_user(message)
            should_block = not user_choice
        else:
            # In non-interactive mode, use default action
            default_action = self.get_default_action()
            should_block = default_action == GuardAction.BLOCK

            # Handle None message case
            if message is not None:
                if should_block:
                    message += "\n\n🚨 Non-interactive mode: Blocking by default (safety-first policy)"
                    message += "\n🚨 RULE FAILURE: This operation violates established safety policies"
                else:
                    message += "\n\n⚠️  Non-interactive mode: Allowing by default (configure policy if needed)"

        return GuardResult(should_block=should_block, message=message)

    def _prompt_user(self, message: str) -> bool:
        """Prompt user for permission in interactive mode."""
        if message is not None:
            print(message)
            print()

        response = input("Do you want to allow this action? (y/N): ").strip().lower()
        print()

        if response in ["y", "yes"]:
            print("⚠️  User authorized potentially dangerous action")
            return True
        else:
            print("❌ Action blocked by user")
            return False
