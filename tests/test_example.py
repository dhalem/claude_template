"""Tests for example module."""
import pytest
from src.example import greet, Example


def test_greet():
    """Test the greet function."""
    assert greet("World") == "Hello, World!"
    assert greet("Python") == "Hello, Python!"


class TestExample:
    """Test the Example class."""

    def test_initialization(self):
        """Test Example initialization."""
        example = Example("test")
        assert example.value == "test"

    def test_process(self):
        """Test the process method."""
        example = Example("hello")
        assert example.process() == "HELLO"
