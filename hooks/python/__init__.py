"""Claude Code Hook System - Python Implementation.

This package provides a comprehensive safety hook system for Claude Code
that enforces critical rules from CLAUDE.md and prevents costly mistakes.
"""

__version__ = "2.0.0"
__author__ = "Claude Code Safety Team"

from .base_guard import BaseGuard, GuardContext, GuardResult
from .registry import GuardRegistry

__all__ = ["BaseGuard", "GuardContext", "GuardResult", "GuardRegistry"]
