"""Reusable CLI prompt utilities using questionary.

This module provides interactive CLI prompts with consistent styling and validation.
All prompts gracefully fall back to non-interactive defaults when stdin is not a TTY
(e.g., when running in CI/CD or with piped input).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import cast

import questionary


def confirm_action(message: str, default: bool = False) -> bool:
    """Display a confirmation prompt.

    Args:
        message: The question to ask the user
        default: Default value when non-interactive (default: False)

    Returns:
        True if user confirms, False otherwise

    Example:
        >>> if confirm_action("Delete all items?"):
        ...     delete_items()
    """
    if not sys.stdin.isatty():
        # Non-interactive mode: use default
        return default

    try:
        result = questionary.confirm(message, default=default).ask()
        return cast(bool, result if result is not None else default)
    except (EOFError, KeyboardInterrupt):
        # Handle EOF or interrupt gracefully
        return default


def select_from_list(message: str, choices: list[str], default: str | None = None) -> str:
    """Display a single-select list.

    Args:
        message: The question/prompt to show
        choices: List of options to choose from
        default: Default choice when non-interactive (uses first choice if None)

    Returns:
        Selected choice string

    Example:
        >>> tier = select_from_list("Select quality tier:", ["essential", "standard", "comprehensive"])
    """
    if not choices:
        return ""

    if not sys.stdin.isatty():
        # Non-interactive mode: return default or first choice
        return default if default is not None else choices[0]

    try:
        result = questionary.select(message, choices=choices).ask()
        return cast(
            str, result if result is not None else (default if default is not None else choices[0])
        )
    except (EOFError, KeyboardInterrupt):
        # Handle EOF or interrupt gracefully
        return default if default is not None else choices[0]


def multi_select_list(message: str, choices: list[str]) -> list[str]:
    """Display a multi-select checkbox list.

    Args:
        message: The question/prompt to show
        choices: List of options to choose from

    Returns:
        List of selected choice strings (empty list in non-interactive mode)

    Example:
        >>> features = multi_select_list("Select features:", ["docker", "ci-cd", "pre-commit"])
    """
    if not sys.stdin.isatty():
        # Non-interactive mode: return empty list
        return []

    try:
        result = questionary.checkbox(message, choices=choices).ask()
        return cast(list[str], result if result is not None else [])
    except (EOFError, KeyboardInterrupt):
        # Handle EOF or interrupt gracefully
        return []


def text_input(
    message: str, validate_fn: Callable[[str], bool] | None = None, default: str = ""
) -> str:
    """Display a text input prompt with optional validation.

    Args:
        message: The question/prompt to show
        validate_fn: Optional validation function that returns True if input is valid
        default: Default value when non-interactive

    Returns:
        User input string

    Example:
        >>> name = text_input("Enter project name:", validate_fn=lambda x: len(x) > 0)
    """
    if not sys.stdin.isatty():
        # Non-interactive mode: return default
        return default

    try:
        result = questionary.text(message, validate=validate_fn).ask()
        return cast(str, result if result is not None else default)
    except (EOFError, KeyboardInterrupt):
        # Handle EOF or interrupt gracefully
        return default
