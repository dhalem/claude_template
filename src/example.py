"""Example module demonstrating best practices."""


def greet(name: str) -> str:
    """
    Generate a greeting message.

    Args:
        name: The name to greet

    Returns:
        A greeting message
    """
    return f"Hello, {name}!"


class Example:
    """Example class demonstrating documentation standards."""

    def __init__(self, value: str) -> None:
        """Initialize the Example."""
        self.value = value

    def process(self) -> str:
        """Process the value."""
        return self.value.upper()
