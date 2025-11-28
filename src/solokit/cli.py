#!/usr/bin/env python3
"""
Solokit CLI Entry Point

Universal interface for all Session-Driven Development commands.

Usage:
    solokit <command> [args...]

Examples:
    sk work-list
    sk work-list --status not_started
    sk work-show feature_user_auth
    sk start
    sk learn-search "authentication"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from solokit.core.argparse_helpers import HelpfulArgumentParser
from solokit.core.error_formatter import ErrorFormatter

# Import error handling infrastructure
from solokit.core.exceptions import (
    ErrorCode,
    SolokitError,
    SystemError,
)

# Import logging configuration
from solokit.core.logging_config import get_logger, setup_logging
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()

# Command routing table
# Format: 'command-name': (module_path, class_name, function_name, needs_argparse)
# - module_path: Python import path
# - class_name: Class to instantiate (None for standalone functions)
# - function_name: Method or function to call
# - needs_argparse: True if script has its own argparse handling
COMMANDS = {
    # Work Item Management (WorkItemManager class)
    "work-list": (
        "solokit.work_items.manager",
        "WorkItemManager",
        "list_work_items",
        False,
    ),
    "work-next": (
        "solokit.work_items.manager",
        "WorkItemManager",
        "get_next_work_item",
        False,
    ),
    "work-show": (
        "solokit.work_items.manager",
        "WorkItemManager",
        "show_work_item",
        False,
    ),
    "work-update": (
        "solokit.work_items.manager",
        "WorkItemManager",
        "update_work_item",
        False,
    ),
    "work-new": (
        "solokit.work_items.manager",
        "WorkItemManager",
        "create_work_item_from_args",
        False,
    ),
    "work-delete": ("solokit.work_items.delete", None, "main", True),
    # Dependency Graph (uses argparse in main)
    "work-graph": ("solokit.visualization.dependency_graph", None, "main", True),
    # Session Management (standalone main functions)
    "start": ("solokit.session.briefing", None, "main", True),
    "end": ("solokit.session.complete", None, "main", True),
    "status": ("solokit.session.status", None, "get_session_status", False),
    "validate": ("solokit.session.validate", None, "main", True),
    # Learning System (uses argparse in main)
    "learn": ("solokit.learning.curator", None, "main", True),
    "learn-show": ("solokit.learning.curator", None, "main", True),
    "learn-search": ("solokit.learning.curator", None, "main", True),
    "learn-curate": ("solokit.learning.curator", None, "main", True),
    # Project Initialization
    "init": ("solokit.project.init", None, "main", True),
    "adopt": ("solokit.project.adopt", None, "main", True),
    # Utility Commands
    "help": ("solokit.commands.help", None, "main", True),
    "version": ("solokit.commands.version", None, "main", False),
    "doctor": ("solokit.commands.doctor", None, "main", True),
    "config": ("solokit.commands.config", None, "main", True),
}


def parse_work_list_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-list command."""
    parser = argparse.ArgumentParser(description="List work items")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--type", help="Filter by type")
    parser.add_argument("--milestone", help="Filter by milestone")
    return parser.parse_args(args)


def parse_work_show_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-show command."""
    parser = HelpfulArgumentParser(
        description="Show work item details",
        epilog="""
Examples:
  sk work-show feat_001
  sk work-show bug_fix_phase_1_error_messaging_an

💡 List all work items: /work-list
💡 View work item dependencies: /work-graph --focus <work_id>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("work_id", help="Work item ID")
    return parser.parse_args(args)


def parse_work_new_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-new command."""
    parser = HelpfulArgumentParser(
        description="Create a new work item",
        epilog="""
Examples:
  sk work-new --type feature --title "Add user authentication" --priority high
  sk work-new -t bug -T "Fix login error" -p critical
  sk work-new -t refactor -T "Improve database queries" -p medium --dependencies feat_001
  sk work-new -t bug -T "Critical hotfix" -p high --urgent

Valid types: feature, bug, refactor, security, integration_test, deployment
Valid priorities: critical, high, medium, low

The --urgent flag marks an item for immediate attention. Only ONE item can be urgent at a time.
When you mark a new item as urgent, you'll be prompted to clear the existing urgent flag.

💡 View existing work items: /work-list
💡 For interactive creation, use /work-new
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--type",
        "-t",
        required=True,
        help="Work item type",
    )
    parser.add_argument("--title", "-T", required=True, help="Work item title")
    parser.add_argument(
        "--priority",
        "-p",
        required=True,
        help="Priority level",
    )
    parser.add_argument("--dependencies", "-d", default="", help="Comma-separated dependency IDs")
    parser.add_argument(
        "--urgent",
        action="store_true",
        help="Mark this item as urgent (requires immediate attention, only one can be urgent at a time)",
    )
    return parser.parse_args(args)


def parse_work_update_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-update command."""
    parser = HelpfulArgumentParser(
        description="Update work item fields",
        epilog="""
Examples:
  sk work-update feat_001 --status in_progress
  sk work-update feat_001 --priority critical
  sk work-update feat_001 --add-dependency bug_002
  sk work-update feat_001 --milestone "v1.0"
  sk work-update feat_001 --status completed --priority high
  sk work-update feat_001 --set-urgent
  sk work-update feat_001 --clear-urgent

Valid statuses: not_started, in_progress, blocked, completed
Valid priorities: critical, high, medium, low

The --set-urgent flag marks an item as urgent (only one item can be urgent at a time).
The --clear-urgent flag removes the urgent status from a work item.

💡 View current work item status: /work-show <work_id>
💡 For interactive updates, use /work-update
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("work_id", help="Work item ID")
    parser.add_argument("--status", help="Update status")
    parser.add_argument("--priority", help="Update priority")
    parser.add_argument("--milestone", help="Update milestone")
    parser.add_argument("--add-dependency", help="Add dependency by ID")
    parser.add_argument("--remove-dependency", help="Remove dependency by ID")
    parser.add_argument(
        "--set-urgent",
        action="store_true",
        help="Mark this item as urgent (only one item can be urgent at a time)",
    )
    parser.add_argument(
        "--clear-urgent",
        action="store_true",
        help="Clear the urgent flag from this work item",
    )
    return parser.parse_args(args)


def route_command(command_name: str, args: list[str]) -> int:
    """
    Route command to appropriate script/function.

    Args:
        command_name: Name of the command (e.g., 'work-list')
        args: List of command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)

    Raises:
        SystemError: If command is unknown or execution fails
    """
    if command_name not in COMMANDS:
        available = ", ".join(sorted(COMMANDS.keys()))
        raise SystemError(
            message=f"Unknown command '{command_name}'",
            code=ErrorCode.INVALID_COMMAND,
            context={"command": command_name, "available_commands": list(COMMANDS.keys())},
            remediation=f"Available commands: {available}",
        )

    module_path, class_name, function_name, needs_argparse = COMMANDS[command_name]

    try:
        # Import the module
        module = __import__(module_path, fromlist=[class_name or function_name])

        # Handle different command types
        if needs_argparse:
            # Scripts with argparse: set sys.argv and call main()
            # The script's own argparse will handle arguments
            if command_name in ["learn", "learn-show", "learn-search", "learn-curate"]:
                # Learning commands need special handling for subcommands
                if command_name == "learn":
                    sys.argv = ["learning_curator.py", "add-learning"] + args
                elif command_name == "learn-show":
                    sys.argv = ["learning_curator.py", "show-learnings"] + args
                elif command_name == "learn-search":
                    sys.argv = ["learning_curator.py", "search"] + args
                elif command_name == "learn-curate":
                    sys.argv = ["learning_curator.py", "curate"] + args
            else:
                # Other argparse commands (work-graph, start, end, validate)
                sys.argv = [command_name] + args

            func = getattr(module, function_name)
            result = func()
            return int(result) if result is not None else 0

        elif class_name:
            # Class-based commands: instantiate class and call method
            cls = getattr(module, class_name)
            instance = cls()
            method = getattr(instance, function_name)

            # Special argument handling for specific commands
            if command_name == "work-list":
                parsed = parse_work_list_args(args)
                result = method(
                    status_filter=parsed.status,
                    type_filter=parsed.type,
                    milestone_filter=parsed.milestone,
                )
            elif command_name == "work-show":
                parsed = parse_work_show_args(args)
                result = method(parsed.work_id)
            elif command_name == "work-next":
                result = method()
            elif command_name == "work-new":
                # Parse arguments (all required)
                parsed = parse_work_new_args(args)
                result = method(
                    work_type=parsed.type,
                    title=parsed.title,
                    priority=parsed.priority,
                    dependencies=parsed.dependencies,
                    urgent=parsed.urgent,
                )
            elif command_name == "work-update":
                # Parse arguments
                parsed = parse_work_update_args(args)

                # Build kwargs from provided flags
                kwargs = {}
                if parsed.status:
                    kwargs["status"] = parsed.status
                if parsed.priority:
                    kwargs["priority"] = parsed.priority
                if parsed.milestone:
                    kwargs["milestone"] = parsed.milestone
                if parsed.add_dependency:
                    kwargs["add_dependency"] = parsed.add_dependency
                if parsed.remove_dependency:
                    kwargs["remove_dependency"] = parsed.remove_dependency
                if parsed.set_urgent:
                    kwargs["set_urgent"] = True
                if parsed.clear_urgent:
                    kwargs["clear_urgent"] = True

                result = method(parsed.work_id, **kwargs)
            else:
                result = method()

            # Handle different return types
            if result is None:
                return 0
            elif isinstance(result, bool):
                return 0 if result else 1
            elif isinstance(result, int):
                return result
            else:
                return 0

        else:
            # Standalone function commands
            func = getattr(module, function_name)
            result = func()
            return int(result) if result is not None else 0

    except ModuleNotFoundError as e:
        raise SystemError(
            message=f"Could not import module '{module_path}'",
            code=ErrorCode.MODULE_NOT_FOUND,
            context={"module_path": module_path, "command": command_name},
            remediation="Check that the command is properly installed",
            cause=e,
        ) from e
    except AttributeError as e:
        raise SystemError(
            message=f"Could not find function '{function_name}' in module '{module_path}'",
            code=ErrorCode.FUNCTION_NOT_FOUND,
            context={"function": function_name, "module": module_path, "command": command_name},
            remediation="This appears to be an internal error - please report it",
            cause=e,
        ) from e
    except SolokitError:
        # Re-raise SolokitError exceptions to be caught by main()
        raise
    except Exception as e:
        # Wrap unexpected exceptions
        raise SystemError(
            message=f"Unexpected error executing command '{command_name}'",
            code=ErrorCode.COMMAND_FAILED,
            context={"command": command_name},
            cause=e,
        ) from e


def parse_global_flags(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    """
    Parse only global flags that appear before the command name.

    This function manually parses global flags to ensure that flags appearing
    after the command name are passed to the command's own argument parser.
    This fixes the issue where `sk command --help` would show general help
    instead of command-specific help.

    Args:
        argv: Command-line arguments (typically sys.argv[1:])

    Returns:
        Tuple of (parsed_args, remaining_args) where:
        - parsed_args: Namespace with global flag values
        - remaining_args: Command name and its arguments (including flags)

    Examples:
        >>> parse_global_flags(['--verbose', 'work-list', '--status', 'done'])
        (Namespace(verbose=True, ...), ['work-list', '--status', 'done'])

        >>> parse_global_flags(['work-delete', '--help'])
        (Namespace(verbose=False, ...), ['work-delete', '--help'])
    """
    global_flags = argparse.Namespace(
        verbose=False,
        log_file=None,
        version=False,
        help=False,
    )
    remaining = []
    i = 0

    while i < len(argv):
        arg = argv[i]

        # Stop at first non-flag argument (the command)
        if not arg.startswith("-"):
            remaining = argv[i:]  # Everything from command onwards
            break

        # Parse global flags
        if arg in ("--verbose", "-v"):
            global_flags.verbose = True
        elif arg in ("--version", "-V"):
            global_flags.version = True
        elif arg in ("--help", "-h"):
            global_flags.help = True
        elif arg == "--log-file":
            i += 1
            if i < len(argv):
                global_flags.log_file = argv[i]
            else:
                # Missing value for --log-file, will be caught later
                remaining = argv[i - 1 :]
                break
        else:
            # Unknown flag - might be for subcommand, keep everything from here
            remaining = argv[i:]
            break
        i += 1

    return global_flags, remaining


def main() -> int:
    """
    Main entry point for CLI with centralized error handling.

    This function implements the standard error handling pattern:
    - Parse arguments
    - Route to command handlers
    - Catch all exceptions in centralized handler
    - Format errors using ErrorFormatter
    - Return appropriate exit codes

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Parse global flags that appear before the command
        # This ensures flags after the command (like --help) are passed to the command
        args, remaining = parse_global_flags(sys.argv[1:])

        # Handle global --version flag
        if args.version:
            from solokit.commands.version import show_version

            return show_version()

        # Handle global --help flag
        if args.help:
            from solokit.commands.help import show_help

            return show_help()

        # Setup logging based on global flags
        # Default to ERROR level for clean terminal output
        # Only show detailed logs with --verbose flag
        log_level = "DEBUG" if args.verbose else "ERROR"
        log_file = Path(args.log_file) if args.log_file else None
        setup_logging(level=log_level, log_file=log_file)

        # Check if command is provided
        if len(remaining) < 1:
            from solokit.commands.help import show_help

            return show_help()

        command = remaining[0]
        command_args = remaining[1:]

        # Route command - will raise exceptions on error
        exit_code = route_command(command, command_args)
        return exit_code

    except SolokitError as e:
        # Structured Solokit errors with proper formatting
        ErrorFormatter.print_error(e, verbose=args.verbose if "args" in locals() else False)
        return e.exit_code

    except KeyboardInterrupt:
        # User cancelled operation
        output.error("\n\nOperation cancelled by user")
        return 130

    except Exception as e:
        # Unexpected errors - show full details
        ErrorFormatter.print_error(e, verbose=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
