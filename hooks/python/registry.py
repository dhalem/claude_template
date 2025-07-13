"""Guard registry for managing and executing guards."""

import os
import sys
from typing import Dict, List, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base_guard import BaseGuard, GuardContext, GuardResult


class GuardRegistry:
    """Registry for managing guards by tool type."""

    def __init__(self):
        self._guards: Dict[str, List[BaseGuard]] = {
            "Bash": [],
            "Edit": [],
            "Write": [],
            "MultiEdit": [],
            "*": [],  # Guards that apply to all tools
        }

    def register(self, guard: BaseGuard, tool_names: List[str] = None):
        """Register a guard for specific tool types."""
        if tool_names is None:
            tool_names = ["*"]

        for tool_name in tool_names:
            if tool_name not in self._guards:
                self._guards[tool_name] = []
            self._guards[tool_name].append(guard)

    def check_all(self, context: GuardContext, is_interactive: bool = False) -> GuardResult:
        """Check all applicable guards for the given context."""
        # Get guards for specific tool and universal guards
        applicable_guards = []
        if context.tool_name in self._guards:
            applicable_guards.extend(self._guards[context.tool_name])
        applicable_guards.extend(self._guards.get("*", []))

        # Check each guard
        for guard in applicable_guards:
            result = guard.check(context, is_interactive)

            # If any guard blocks, return immediately
            if result.should_block:
                if result.message:
                    print(result.message, file=sys.stderr)
                return result

            # Print non-blocking messages
            if result.message:
                print(result.message)

        # All guards passed
        return GuardResult(should_block=False)

    def get_guards_for_tool(self, tool_name: str) -> List[BaseGuard]:
        """Get all guards registered for a specific tool."""
        guards = []
        if tool_name in self._guards:
            guards.extend(self._guards[tool_name])
        guards.extend(self._guards.get("*", []))
        return guards

    def get_all_tools(self) -> Set[str]:
        """Get all tool names that have registered guards."""
        return set(self._guards.keys()) - {"*"}
