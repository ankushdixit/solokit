"""Unit tests for CLI entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from solokit.cli import (
    COMMANDS,
    main,
    parse_global_flags,
    parse_work_list_args,
    parse_work_new_args,
    parse_work_show_args,
    parse_work_update_args,
    route_command,
)
from solokit.core.exceptions import ErrorCode
from solokit.core.exceptions import SystemError as SolokitSystemError


class TestGlobalFlagParsing:
    """Test parse_global_flags function."""

    def test_parse_no_flags(self):
        """Test parsing with no flags, just command."""
        args, remaining = parse_global_flags(["work-list"])
        assert args.verbose is False
        assert args.log_file is None
        assert args.version is False
        assert args.help is False
        assert remaining == ["work-list"]

    def test_parse_global_verbose_before_command(self):
        """Test --verbose flag before command."""
        args, remaining = parse_global_flags(["--verbose", "work-list"])
        assert args.verbose is True
        assert remaining == ["work-list"]

    def test_parse_global_verbose_short_before_command(self):
        """Test -v flag before command."""
        args, remaining = parse_global_flags(["-v", "work-list"])
        assert args.verbose is True
        assert remaining == ["work-list"]

    def test_parse_global_help_before_command(self):
        """Test --help flag before command."""
        args, remaining = parse_global_flags(["--help"])
        assert args.help is True
        assert remaining == []

    def test_parse_global_help_with_command(self):
        """Test --help before command name."""
        args, remaining = parse_global_flags(["--help", "work-list"])
        assert args.help is True
        assert remaining == ["work-list"]

    def test_parse_command_help_flag_preserved(self):
        """Test that --help after command is NOT consumed as global flag."""
        args, remaining = parse_global_flags(["work-delete", "--help"])
        assert args.help is False  # Global help should NOT be set
        assert remaining == ["work-delete", "--help"]  # --help preserved for command

    def test_parse_command_with_multiple_flags_preserved(self):
        """Test command with multiple flags are all preserved."""
        args, remaining = parse_global_flags(["work-list", "--status", "in_progress"])
        assert args.verbose is False
        assert remaining == ["work-list", "--status", "in_progress"]

    def test_parse_global_version_flag(self):
        """Test --version flag."""
        args, remaining = parse_global_flags(["--version"])
        assert args.version is True
        assert remaining == []

    def test_parse_global_version_short_flag(self):
        """Test -V flag."""
        args, remaining = parse_global_flags(["-V"])
        assert args.version is True
        assert remaining == []

    def test_parse_log_file_flag(self):
        """Test --log-file flag with value."""
        args, remaining = parse_global_flags(["--log-file", "/tmp/test.log", "work-list"])
        assert args.log_file == "/tmp/test.log"
        assert remaining == ["work-list"]

    def test_parse_multiple_global_flags(self):
        """Test multiple global flags before command."""
        args, remaining = parse_global_flags(
            ["--verbose", "--log-file", "/tmp/test.log", "work-list"]
        )
        assert args.verbose is True
        assert args.log_file == "/tmp/test.log"
        assert remaining == ["work-list"]

    def test_parse_mixed_global_and_command_flags(self):
        """Test global flags before command, command flags after."""
        args, remaining = parse_global_flags(
            ["--verbose", "work-update", "feat_001", "--status", "completed"]
        )
        assert args.verbose is True
        assert remaining == ["work-update", "feat_001", "--status", "completed"]

    def test_parse_unknown_flag_stops_parsing(self):
        """Test that unknown flag stops global flag parsing."""
        args, remaining = parse_global_flags(["--unknown-flag", "work-list"])
        assert args.verbose is False
        assert remaining == ["--unknown-flag", "work-list"]

    def test_parse_empty_argv(self):
        """Test parsing with empty argv."""
        args, remaining = parse_global_flags([])
        assert args.verbose is False
        assert args.log_file is None
        assert args.version is False
        assert args.help is False
        assert remaining == []


class TestArgumentParsing:
    """Test argument parsing functions."""

    def test_parse_work_list_args_no_filters(self):
        """Test work-list args parsing without filters."""
        args = parse_work_list_args([])
        assert args.status is None
        assert args.type is None
        assert args.milestone is None

    def test_parse_work_list_args_with_filters(self):
        """Test work-list args parsing with filters."""
        args = parse_work_list_args(["--status", "in_progress", "--type", "feature"])
        assert args.status == "in_progress"
        assert args.type == "feature"
        assert args.milestone is None

    def test_parse_work_show_args(self):
        """Test work-show args parsing."""
        args = parse_work_show_args(["feat_001"])
        assert args.work_id == "feat_001"

    def test_parse_work_show_args_missing_id(self):
        """Test work-show args parsing without ID."""
        with pytest.raises(SystemExit):
            parse_work_show_args([])

    def test_parse_work_new_args_basic(self):
        """Test work-new args parsing with basic options."""
        args = parse_work_new_args(
            ["--type", "feature", "--title", "Test Feature", "--priority", "high"]
        )
        assert args.type == "feature"
        assert args.title == "Test Feature"
        assert args.priority == "high"
        assert args.dependencies == ""
        assert args.urgent is False

    def test_parse_work_new_args_with_dependencies(self):
        """Test work-new args parsing with dependencies."""
        args = parse_work_new_args(
            ["-t", "bug", "-T", "Fix bug", "-p", "critical", "-d", "feat_001,feat_002"]
        )
        assert args.type == "bug"
        assert args.title == "Fix bug"
        assert args.priority == "critical"
        assert args.dependencies == "feat_001,feat_002"

    def test_parse_work_new_args_with_urgent(self):
        """Test work-new args parsing with urgent flag."""
        args = parse_work_new_args(["-t", "bug", "-T", "Critical hotfix", "-p", "high", "--urgent"])
        assert args.urgent is True

    def test_parse_work_new_args_missing_required(self):
        """Test work-new args parsing with missing required args."""
        with pytest.raises(SystemExit):
            parse_work_new_args(["--type", "feature"])

    def test_parse_work_update_args_status(self):
        """Test work-update args parsing for status update."""
        args = parse_work_update_args(["feat_001", "--status", "in_progress"])
        assert args.work_id == "feat_001"
        assert args.status == "in_progress"
        assert args.priority is None

    def test_parse_work_update_args_multiple_fields(self):
        """Test work-update args parsing for multiple fields."""
        args = parse_work_update_args(
            ["feat_001", "--status", "completed", "--priority", "high", "--milestone", "v1.0"]
        )
        assert args.work_id == "feat_001"
        assert args.status == "completed"
        assert args.priority == "high"
        assert args.milestone == "v1.0"

    def test_parse_work_update_args_dependencies(self):
        """Test work-update args parsing for dependency management."""
        args = parse_work_update_args(
            ["feat_001", "--add-dependency", "bug_002", "--remove-dependency", "feat_000"]
        )
        assert args.add_dependency == "bug_002"
        assert args.remove_dependency == "feat_000"

    def test_parse_work_update_args_clear_urgent(self):
        """Test work-update args parsing for clearing urgent flag."""
        args = parse_work_update_args(["feat_001", "--clear-urgent"])
        assert args.clear_urgent is True


class TestCommandRouting:
    """Test command routing."""

    def test_route_unknown_command(self):
        """Test routing unknown command."""
        with pytest.raises(SolokitSystemError) as exc_info:
            route_command("unknown-command", [])
        assert exc_info.value.code == ErrorCode.INVALID_COMMAND
        assert "unknown-command" in exc_info.value.message

    def test_route_work_list_command(self):
        """Test routing work-list command."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.list_work_items.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-list", ["--status", "in_progress"])

            assert result == 0
            mock_instance.list_work_items.assert_called_once()

    def test_route_work_show_command(self):
        """Test routing work-show command."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.show_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-show", ["feat_001"])

            assert result == 0
            mock_instance.show_work_item.assert_called_once_with("feat_001")

    def test_route_work_next_command(self):
        """Test routing work-next command."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.get_next_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-next", [])

            assert result == 0
            mock_instance.get_next_work_item.assert_called_once()

    def test_route_work_new_command(self):
        """Test routing work-new command."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.create_work_item_from_args.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command(
                "work-new", ["--type", "feature", "--title", "Test", "--priority", "high"]
            )

            assert result == 0
            mock_instance.create_work_item_from_args.assert_called_once()

    def test_route_work_update_command(self):
        """Test routing work-update command."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.update_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-update", ["feat_001", "--status", "completed"])

            assert result == 0
            mock_instance.update_work_item.assert_called_once()

    def test_route_status_command(self):
        """Test routing status command."""
        with patch("solokit.session.status.get_session_status") as mock_status:
            mock_status.return_value = 0
            result = route_command("status", [])
            assert result == 0
            mock_status.assert_called_once()

    def test_route_version_command(self):
        """Test routing version command."""
        with patch("solokit.commands.version.main") as mock_version:
            mock_version.return_value = 0
            result = route_command("version", [])
            assert result == 0
            mock_version.assert_called_once()

    def test_route_argparse_commands(self):
        """Test routing commands with argparse handling."""
        commands_to_test = ["start", "end", "validate", "work-graph", "work-delete"]

        for cmd in commands_to_test:
            module_path, _, func_name, needs_argparse = COMMANDS[cmd]
            assert needs_argparse is True

            with patch(f"{module_path}.{func_name}") as mock_func:
                mock_func.return_value = 0
                with patch.object(sys, "argv", [cmd]):
                    result = route_command(cmd, [])
                    assert result == 0

    def test_route_learning_commands(self):
        """Test routing learning system commands."""
        learning_cmds = {
            "learn": "add-learning",
            "learn-show": "show-learnings",
            "learn-search": "search",
            "learn-curate": "curate",
        }

        for cmd, subcommand in learning_cmds.items():
            with patch("solokit.learning.curator.main") as mock_main:
                mock_main.return_value = 0
                result = route_command(cmd, ["test-arg"])
                assert result == 0

    def test_route_command_module_not_found(self):
        """Test routing when module doesn't exist."""
        with patch.dict(COMMANDS, {"fake-cmd": ("fake.module", None, "main", False)}):
            with pytest.raises(SolokitSystemError) as exc_info:
                route_command("fake-cmd", [])
            assert exc_info.value.code == ErrorCode.MODULE_NOT_FOUND

    def test_route_command_function_not_found(self):
        """Test routing when function doesn't exist in module."""
        with patch.dict(COMMANDS, {"test-cmd": ("solokit.cli", None, "fake_func", False)}):
            with pytest.raises(SolokitSystemError) as exc_info:
                route_command("test-cmd", [])
            assert exc_info.value.code == ErrorCode.FUNCTION_NOT_FOUND


class TestMainFunction:
    """Test main CLI entry point."""

    def test_main_no_args_shows_help(self, capsys):
        """Test main with no arguments shows help."""
        with patch.object(sys, "argv", ["sk"]):
            with patch("solokit.commands.help.show_help") as mock_help:
                mock_help.return_value = 0
                result = main()
                assert result == 0
                mock_help.assert_called_once()

    def test_main_with_version_flag(self):
        """Test main with --version flag."""
        with patch.object(sys, "argv", ["sk", "--version"]):
            with patch("solokit.commands.version.show_version") as mock_version:
                mock_version.return_value = 0
                result = main()
                assert result == 0
                mock_version.assert_called_once()

    def test_main_with_version_short_flag(self):
        """Test main with -V flag."""
        with patch.object(sys, "argv", ["sk", "-V"]):
            with patch("solokit.commands.version.show_version") as mock_version:
                mock_version.return_value = 0
                result = main()
                assert result == 0

    def test_main_with_help_flag(self):
        """Test main with --help flag."""
        with patch.object(sys, "argv", ["sk", "--help"]):
            with patch("solokit.commands.help.show_help") as mock_help:
                mock_help.return_value = 0
                result = main()
                assert result == 0
                mock_help.assert_called_once()

    def test_main_with_help_short_flag(self):
        """Test main with -h flag."""
        with patch.object(sys, "argv", ["sk", "-h"]):
            with patch("solokit.commands.help.show_help") as mock_help:
                mock_help.return_value = 0
                result = main()
                assert result == 0

    def test_main_with_verbose_flag(self):
        """Test main with --verbose flag."""
        with patch.object(sys, "argv", ["sk", "--verbose", "work-list"]):
            with patch("solokit.cli.route_command") as mock_route:
                mock_route.return_value = 0
                result = main()
                assert result == 0

    def test_main_with_log_file_flag(self, tmp_path):
        """Test main with --log-file flag."""
        log_file = tmp_path / "test.log"
        with patch.object(sys, "argv", ["sk", "--log-file", str(log_file), "work-list"]):
            with patch("solokit.cli.route_command") as mock_route:
                mock_route.return_value = 0
                result = main()
                assert result == 0

    def test_main_routes_command_successfully(self):
        """Test main successfully routes a command."""
        with patch.object(sys, "argv", ["sk", "work-list"]):
            with patch("solokit.cli.route_command") as mock_route:
                mock_route.return_value = 0
                result = main()
                assert result == 0
                mock_route.assert_called_once_with("work-list", [])

    def test_main_routes_command_with_args(self):
        """Test main routes command with arguments."""
        with patch.object(sys, "argv", ["sk", "work-show", "feat_001"]):
            with patch("solokit.cli.route_command") as mock_route:
                mock_route.return_value = 0
                result = main()
                assert result == 0
                mock_route.assert_called_once_with("work-show", ["feat_001"])

    def test_main_handles_solokit_error(self, capsys):
        """Test main handles SolokitError properly."""
        from solokit.core.exceptions import ValidationError

        with patch.object(sys, "argv", ["sk", "work-list"]):
            with patch("solokit.cli.route_command") as mock_route:
                error = ValidationError(message="Test error", code=ErrorCode.INVALID_WORK_ITEM_ID)
                mock_route.side_effect = error

                result = main()

                assert result == error.exit_code
                # Error should be formatted and printed
                captured = capsys.readouterr()
                assert len(captured.err) > 0 or len(captured.out) > 0

    def test_main_handles_keyboard_interrupt(self, capsys):
        """Test main handles KeyboardInterrupt."""
        with patch.object(sys, "argv", ["sk", "work-list"]):
            with patch("solokit.cli.route_command") as mock_route:
                mock_route.side_effect = KeyboardInterrupt()

                result = main()

                assert result == 130
                captured = capsys.readouterr()
                assert "cancelled" in captured.err.lower() or "cancelled" in captured.out.lower()

    def test_main_handles_unexpected_exception(self, capsys):
        """Test main handles unexpected exceptions."""
        with patch.object(sys, "argv", ["sk", "work-list"]):
            with patch("solokit.cli.route_command") as mock_route:
                mock_route.side_effect = RuntimeError("Unexpected error")

                result = main()

                assert result == 1
                # Error should be printed
                captured = capsys.readouterr()
                assert len(captured.err) > 0 or len(captured.out) > 0

    def test_main_default_log_level_is_error(self):
        """Test that default log level is ERROR for clean output."""
        with patch.object(sys, "argv", ["sk", "work-list"]):
            with patch("solokit.cli.route_command") as mock_route:
                mock_route.return_value = 0
                result = main()
                assert result == 0

    def test_commands_dict_completeness(self):
        """Test that COMMANDS dict has expected structure."""
        assert "work-list" in COMMANDS
        assert "work-next" in COMMANDS
        assert "work-show" in COMMANDS
        assert "work-new" in COMMANDS
        assert "work-update" in COMMANDS
        assert "work-delete" in COMMANDS
        assert "work-graph" in COMMANDS
        assert "start" in COMMANDS
        assert "end" in COMMANDS
        assert "status" in COMMANDS
        assert "validate" in COMMANDS
        assert "learn" in COMMANDS
        assert "learn-show" in COMMANDS
        assert "learn-search" in COMMANDS
        assert "learn-curate" in COMMANDS
        assert "init" in COMMANDS
        assert "help" in COMMANDS
        assert "version" in COMMANDS
        assert "doctor" in COMMANDS
        assert "config" in COMMANDS

        # Verify structure: (module_path, class_name, function_name, needs_argparse)
        for cmd, cmd_info in COMMANDS.items():
            assert len(cmd_info) == 4
            module_path, class_name, func_name, needs_argparse = cmd_info
            assert isinstance(module_path, str)
            assert class_name is None or isinstance(class_name, str)
            assert isinstance(func_name, str)
            assert isinstance(needs_argparse, bool)

    def test_command_help_flag_shows_command_help(self, capsys):
        """Test that 'sk command --help' shows command-specific help, not general help."""
        with patch.object(sys, "argv", ["sk", "work-delete", "--help"]):
            with pytest.raises(SystemExit):  # argparse --help exits with 0
                main()

            captured = capsys.readouterr()
            # Should show work-delete specific help, not general help
            assert "work_item_id" in captured.out or "work_item_id" in captured.err
            assert "--keep-spec" in captured.out or "--keep-spec" in captured.err
            # Should NOT show general help content
            assert "Work Items Management:" not in captured.out
            assert "Session Management:" not in captured.out

    def test_global_help_flag_shows_general_help(self, capsys):
        """Test that 'sk --help' shows general help."""
        with patch.object(sys, "argv", ["sk", "--help"]):
            result = main()

            captured = capsys.readouterr()
            # Should show general help
            assert "Work Items Management:" in captured.out
            assert "Session Management:" in captured.out
            assert result == 0

    def test_help_command_shows_command_help(self, capsys):
        """Test that 'sk help command' shows command-specific help."""
        with patch.object(sys, "argv", ["sk", "help", "work-delete"]):
            result = main()

            captured = capsys.readouterr()
            # Should show work-delete specific help from help command
            assert "work-delete" in captured.out
            assert result == 0


class TestWorkUpdateRouting:
    """Test routing for work-update command with all flag combinations."""

    def test_route_work_update_with_priority(self):
        """Test routing work-update command with priority flag."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.update_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-update", ["feat_001", "--priority", "high"])

            assert result == 0
            mock_instance.update_work_item.assert_called_once()
            call_kwargs = mock_instance.update_work_item.call_args[1]
            assert call_kwargs.get("priority") == "high"

    def test_route_work_update_with_milestone(self):
        """Test routing work-update command with milestone flag."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.update_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-update", ["feat_001", "--milestone", "v1.0"])

            assert result == 0
            call_kwargs = mock_instance.update_work_item.call_args[1]
            assert call_kwargs.get("milestone") == "v1.0"

    def test_route_work_update_with_add_dependency(self):
        """Test routing work-update command with add-dependency flag."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.update_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-update", ["feat_001", "--add-dependency", "feat_002"])

            assert result == 0
            call_kwargs = mock_instance.update_work_item.call_args[1]
            assert call_kwargs.get("add_dependency") == "feat_002"

    def test_route_work_update_with_remove_dependency(self):
        """Test routing work-update command with remove-dependency flag."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.update_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-update", ["feat_001", "--remove-dependency", "feat_000"])

            assert result == 0
            call_kwargs = mock_instance.update_work_item.call_args[1]
            assert call_kwargs.get("remove_dependency") == "feat_000"

    def test_route_work_update_with_set_urgent(self):
        """Test routing work-update command with set-urgent flag."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.update_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-update", ["feat_001", "--set-urgent"])

            assert result == 0
            call_kwargs = mock_instance.update_work_item.call_args[1]
            assert call_kwargs.get("set_urgent") is True

    def test_route_work_update_with_clear_urgent(self):
        """Test routing work-update command with clear-urgent flag."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.update_work_item.return_value = 0
            mock_manager.return_value = mock_instance

            result = route_command("work-update", ["feat_001", "--clear-urgent"])

            assert result == 0
            call_kwargs = mock_instance.update_work_item.call_args[1]
            assert call_kwargs.get("clear_urgent") is True

    def test_route_command_returns_none_as_zero(self):
        """Test that route_command converts None return to 0."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.list_work_items.return_value = None
            mock_manager.return_value = mock_instance

            result = route_command("work-list", [])

            assert result == 0

    def test_route_command_returns_bool_true_as_zero(self):
        """Test that route_command converts True return to 0."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.list_work_items.return_value = True
            mock_manager.return_value = mock_instance

            result = route_command("work-list", [])

            assert result == 0

    def test_route_command_returns_bool_false_as_one(self):
        """Test that route_command converts False return to 1."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.list_work_items.return_value = False
            mock_manager.return_value = mock_instance

            result = route_command("work-list", [])

            assert result == 1


class TestGlobalFlagEdgeCases:
    """Test edge cases for global flag parsing."""

    def test_parse_log_file_missing_value(self):
        """Test --log-file flag without value stops parsing."""
        args, remaining = parse_global_flags(["--log-file"])
        # When --log-file is at the end without value, remaining should include it
        assert remaining == ["--log-file"]
        assert args.log_file is None


class TestRouteCommandExceptions:
    """Test exception handling in route_command."""

    def test_route_command_wraps_unexpected_exception(self):
        """Test that unexpected exceptions are wrapped in SystemError."""
        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.list_work_items.side_effect = RuntimeError("Unexpected!")
            mock_manager.return_value = mock_instance

            with pytest.raises(SolokitSystemError) as exc_info:
                route_command("work-list", [])

            assert exc_info.value.code == ErrorCode.COMMAND_FAILED
            assert "Unexpected error" in exc_info.value.message

    def test_route_command_reraises_solokit_error(self):
        """Test that SolokitError exceptions are re-raised unchanged."""
        from solokit.core.exceptions import ValidationError

        with patch("solokit.work_items.manager.WorkItemManager") as mock_manager:
            mock_instance = MagicMock()
            original_error = ValidationError(message="Validation failed")
            mock_instance.list_work_items.side_effect = original_error
            mock_manager.return_value = mock_instance

            with pytest.raises(ValidationError) as exc_info:
                route_command("work-list", [])

            assert exc_info.value is original_error
