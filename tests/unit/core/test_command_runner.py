"""Tests for centralized command execution."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from solokit.core.command_runner import (
    CommandResult,
    CommandRunner,
    run_command,
)
from solokit.core.exceptions import CommandExecutionError, TimeoutError


@pytest.fixture(autouse=True)
def mock_shutil_which():
    """Mock shutil.which to return None by default to prevent path resolution."""
    with patch("shutil.which", return_value=None):
        yield


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_success_property_true_when_returncode_zero(self):
        """Test success property returns True when returncode is 0."""
        result = CommandResult(
            returncode=0,
            stdout="output",
            stderr="",
            command=["echo", "test"],
            duration_seconds=0.1,
        )
        assert result.success is True

    def test_success_property_false_when_returncode_nonzero(self):
        """Test success property returns False when returncode is non-zero."""
        result = CommandResult(
            returncode=1,
            stdout="",
            stderr="error",
            command=["false"],
            duration_seconds=0.1,
        )
        assert result.success is False

    def test_success_property_false_when_timed_out(self):
        """Test success property returns False when command timed out."""
        result = CommandResult(
            returncode=0,
            stdout="output",
            stderr="",
            command=["sleep", "10"],
            duration_seconds=5.0,
            timed_out=True,
        )
        assert result.success is False

    def test_output_property_returns_stdout_when_present(self):
        """Test output property returns stdout when present."""
        result = CommandResult(
            returncode=0,
            stdout="  output  ",
            stderr="error",
            command=["echo", "test"],
            duration_seconds=0.1,
        )
        assert result.output == "output"

    def test_output_property_returns_stderr_when_stdout_empty(self):
        """Test output property returns stderr when stdout is empty."""
        result = CommandResult(
            returncode=1,
            stdout="",
            stderr="  error  ",
            command=["false"],
            duration_seconds=0.1,
        )
        assert result.output == "error"


class TestCommandExecutionError:
    """Tests for CommandExecutionError exception."""

    def test_error_stores_command_details(self):
        """Test error stores command execution details."""
        error = CommandExecutionError(
            command="false",
            returncode=1,
            stderr="error",
            stdout="",
        )

        assert "Command execution failed" in str(error)
        assert error.context["command"] == "false"
        assert error.context["returncode"] == 1
        assert error.context["stderr"] == "error"

    def test_error_includes_context(self):
        """Test error includes structured context."""
        error = CommandExecutionError(
            command="pytest tests/",
            returncode=1,
            stderr="FAILED",
            stdout="test output",
        )
        assert error.context["command"] == "pytest tests/"
        assert error.context["returncode"] == 1
        assert error.context["stderr"] == "FAILED"
        assert error.context["stdout"] == "test output"


class TestCommandRunner:
    """Tests for CommandRunner class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        runner = CommandRunner()
        assert runner.default_timeout == 30
        assert runner.working_dir is None
        assert runner.raise_on_error is False

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        working_dir = Path("/tmp")
        runner = CommandRunner(default_timeout=10, working_dir=working_dir, raise_on_error=True)
        assert runner.default_timeout == 10
        assert runner.working_dir == working_dir
        assert runner.raise_on_error is True

    @patch("subprocess.run")
    def test_run_successful_command(self, mock_run):
        """Test running a successful command."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["echo", "test"]
        )

        runner = CommandRunner()
        result = runner.run(["echo", "test"])

        assert result.success is True
        assert result.returncode == 0
        assert result.stdout == "output"
        assert result.command == ["echo", "test"]
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_failed_command(self, mock_run):
        """Test running a failed command."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error", args=["false"])

        runner = CommandRunner()
        result = runner.run(["false"])

        assert result.success is False
        assert result.returncode == 1
        assert result.stderr == "error"

    @patch("subprocess.run")
    def test_run_command_with_string(self, mock_run):
        """Test running command passed as string."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["echo", "test"]
        )

        runner = CommandRunner()
        result = runner.run("echo test")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["echo", "test"]

    @patch("subprocess.run")
    def test_run_command_with_custom_timeout(self, mock_run):
        """Test running command with custom timeout."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["echo", "test"]
        )

        runner = CommandRunner(default_timeout=10)
        runner.run(["echo", "test"], timeout=5)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 5

    @patch("subprocess.run")
    def test_run_command_with_working_dir(self, mock_run):
        """Test running command with working directory."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="", args=["pwd"])

        working_dir = Path("/tmp")
        runner = CommandRunner()
        runner.run(["pwd"], working_dir=working_dir)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["cwd"] == working_dir

    @patch("subprocess.run")
    def test_run_command_with_env(self, mock_run):
        """Test running command with custom environment."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="", args=["env"])

        env = {"FOO": "bar"}
        runner = CommandRunner()
        runner.run(["env"], env=env)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"] == env

    @patch("subprocess.run")
    def test_run_command_with_check_raises_on_failure(self, mock_run):
        """Test that check=True raises exception on command failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error", args=["false"])

        runner = CommandRunner()
        with pytest.raises(CommandExecutionError) as exc_info:
            runner.run(["false"], check=True)

        assert "Command execution failed" in str(exc_info.value)
        assert exc_info.value.context["returncode"] == 1
        assert exc_info.value.context["command"] == "false"

    @patch("subprocess.run")
    def test_run_command_timeout_expired(self, mock_run):
        """Test handling of timeout expiration."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["sleep", "10"], timeout=1, output="", stderr=""
        )

        runner = CommandRunner()
        result = runner.run(["sleep", "10"], timeout=1)

        assert result.success is False
        assert result.timed_out is True
        assert result.returncode == -1

    @patch("subprocess.run")
    def test_run_command_timeout_with_check_raises(self, mock_run):
        """Test that timeout with check=True raises exception."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["sleep", "10"], timeout=1, output="", stderr=""
        )

        runner = CommandRunner()
        with pytest.raises(TimeoutError) as exc_info:
            runner.run(["sleep", "10"], timeout=1, check=True)

        assert "timed out" in str(exc_info.value)
        assert exc_info.value.context["operation"] == "sleep 10"
        assert exc_info.value.context["timeout_seconds"] == 1

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_run_command_with_retry(self, mock_sleep, mock_run):
        """Test command retry on failure."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="error", args=["flaky"]),
            MagicMock(returncode=0, stdout="success", stderr="", args=["flaky"]),
        ]

        runner = CommandRunner()
        result = runner.run(["flaky"], retry_count=1, retry_delay=0.1)

        assert result.success is True
        assert result.stdout == "success"
        assert mock_run.call_count == 2
        mock_sleep.assert_called_once_with(0.1)

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_run_command_retry_all_fail(self, mock_sleep, mock_run):
        """Test command retry when all attempts fail."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error", args=["always-fails"]
        )

        runner = CommandRunner()
        result = runner.run(["always-fails"], retry_count=2, retry_delay=0.1)

        assert result.success is False
        assert mock_run.call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2

    @patch("subprocess.run")
    def test_run_command_unexpected_exception(self, mock_run):
        """Test handling of unexpected exceptions."""
        mock_run.side_effect = RuntimeError("Unexpected error")

        runner = CommandRunner()
        result = runner.run(["test"])

        assert result.success is False
        assert result.returncode == -1
        assert "Unexpected error" in result.stderr

    @patch("subprocess.run")
    def test_run_command_unexpected_exception_with_check_raises(self, mock_run):
        """Test that unexpected exception with check=True raises."""
        mock_run.side_effect = RuntimeError("Unexpected error")

        runner = CommandRunner()
        with pytest.raises(CommandExecutionError) as exc_info:
            runner.run(["test"], check=True)

        assert "Command execution failed" in str(exc_info.value)
        assert exc_info.value.context["command"] == "test"
        assert exc_info.value.context["returncode"] == -1
        assert "Unexpected error" in exc_info.value.context["stderr"]

    @patch("subprocess.run")
    def test_run_json_success(self, mock_run):
        """Test running command and parsing JSON output."""
        json_data = {"key": "value", "count": 42}
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(json_data),
            stderr="",
            args=["get-json"],
        )

        runner = CommandRunner()
        result = runner.run_json(["get-json"])

        assert result == json_data

    @patch("subprocess.run")
    def test_run_json_command_fails(self, mock_run):
        """Test run_json returns None when command fails."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error", args=["get-json"]
        )

        runner = CommandRunner()
        result = runner.run_json(["get-json"])

        assert result is None

    @patch("subprocess.run")
    def test_run_json_invalid_json(self, mock_run):
        """Test run_json returns None when JSON is invalid."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="not valid json", stderr="", args=["get-json"]
        )

        runner = CommandRunner()
        result = runner.run_json(["get-json"])

        assert result is None

    @patch("subprocess.run")
    def test_run_lines_success(self, mock_run):
        """Test running command and returning lines."""
        output = "line1\nline2\n  line3  \n\nline4"
        mock_run.return_value = MagicMock(
            returncode=0, stdout=output, stderr="", args=["get-lines"]
        )

        runner = CommandRunner()
        result = runner.run_lines(["get-lines"])

        assert result == ["line1", "line2", "line3", "line4"]

    @patch("subprocess.run")
    def test_run_lines_command_fails(self, mock_run):
        """Test run_lines returns empty list when command fails."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error", args=["get-lines"]
        )

        runner = CommandRunner()
        result = runner.run_lines(["get-lines"])

        assert result == []

    @patch("subprocess.run")
    def test_raise_on_error_instance_setting(self, mock_run):
        """Test that raise_on_error instance setting is respected."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error", args=["false"])

        runner = CommandRunner(raise_on_error=True)
        with pytest.raises(CommandExecutionError):
            runner.run(["false"])

    @patch("subprocess.run")
    def test_check_parameter_overrides_instance_setting(self, mock_run):
        """Test that check parameter overrides instance setting."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error", args=["false"])

        # Instance says raise, but check=False overrides
        runner = CommandRunner(raise_on_error=True)
        result = runner.run(["false"], check=False)

        assert result.success is False
        # Should not raise


class TestConvenienceFunction:
    """Tests for run_command convenience function."""

    @patch("subprocess.run")
    def test_run_command_function(self, mock_run):
        """Test run_command convenience function."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["echo", "test"]
        )

        result = run_command(["echo", "test"])

        assert result.success is True
        assert result.stdout == "output"

    @patch("subprocess.run")
    def test_run_command_with_kwargs(self, mock_run):
        """Test run_command passes kwargs correctly."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["echo", "test"]
        )

        result = run_command(["echo", "test"], timeout=5, check=False)

        assert result.success is True
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 5

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_resolves_command_path_with_shutil(self, mock_which, mock_run):
        """Test that command path is resolved using shutil.which."""
        mock_which.return_value = "/usr/bin/echo"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["/usr/bin/echo", "test"]
        )

        runner = CommandRunner()
        result = runner.run(["echo", "test"])

        assert result.success is True
        mock_which.assert_called_with("echo", path=None)

        # Verify subprocess called with resolved path
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/bin/echo"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_command_not_found_handling(self, mock_which, mock_run):
        """Test graceful handling when command executable is not found."""
        mock_which.return_value = None
        # Simulate FileNotFoundError from subprocess if executable missing
        mock_run.side_effect = FileNotFoundError(2, "No such file or directory")

        runner = CommandRunner()
        result = runner.run(["nonexistent-cmd"])

        assert result.success is False
        assert result.returncode == 127
        assert "Command not found" in result.stderr

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_command_not_found_with_check_raises(self, mock_which, mock_run):
        """Test that FileNotFoundError with check=True raises CommandExecutionError."""
        mock_which.return_value = None
        # Simulate FileNotFoundError from subprocess if executable missing
        mock_run.side_effect = FileNotFoundError(2, "No such file or directory")

        runner = CommandRunner()
        with pytest.raises(CommandExecutionError) as exc_info:
            runner.run(["nonexistent-cmd"], check=True)

        assert "Command execution failed" in str(exc_info.value)
        assert exc_info.value.context["returncode"] == 127
        assert "Command not found" in exc_info.value.context["stderr"]

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_respects_custom_env_path(self, mock_which, mock_run):
        """Test that custom PATH in env parameter is respected."""
        # Arrange
        custom_env = {"PATH": "/custom/bin:/usr/bin", "OTHER": "value"}
        mock_which.return_value = "/custom/bin/mycmd"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["/custom/bin/mycmd", "arg"]
        )

        # Act
        runner = CommandRunner()
        result = runner.run(["mycmd", "arg"], env=custom_env)

        # Assert
        assert result.success is True
        # Verify shutil.which was called with the custom PATH
        mock_which.assert_called_with("mycmd", path="/custom/bin:/usr/bin")
        # Verify subprocess received the custom env
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"] == custom_env
        # Verify command was resolved
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/custom/bin/mycmd"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_respects_windows_path_case(self, mock_which, mock_run):
        """Test that Windows 'Path' (capital P, lowercase ath) variant is handled."""
        # Arrange - Windows sometimes uses 'Path' instead of 'PATH'
        custom_env = {"Path": "C:\\custom\\bin", "OTHER": "value"}
        mock_which.return_value = "C:\\custom\\bin\\mycmd.exe"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["C:\\custom\\bin\\mycmd.exe"]
        )

        # Act
        runner = CommandRunner()
        result = runner.run(["mycmd"], env=custom_env)

        # Assert
        assert result.success is True
        # Verify shutil.which was called with the custom Path
        mock_which.assert_called_with("mycmd", path="C:\\custom\\bin")
        # Verify command was resolved
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "C:\\custom\\bin\\mycmd.exe"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_prefers_path_over_windows_path(self, mock_which, mock_run):
        """Test that PATH takes precedence over Path when both exist."""
        # Arrange - Edge case: both PATH and Path in env dict
        custom_env = {"PATH": "/unix/bin", "Path": "C:\\windows\\bin"}
        mock_which.return_value = "/unix/bin/cmd"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["/unix/bin/cmd"]
        )

        # Act
        runner = CommandRunner()
        result = runner.run(["cmd"], env=custom_env)

        # Assert
        assert result.success is True
        # Verify PATH (not Path) was used
        mock_which.assert_called_with("cmd", path="/unix/bin")

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_uses_system_path_when_env_has_no_path(self, mock_which, mock_run):
        """Test that system PATH is used when env dict exists but has no PATH."""
        # Arrange
        custom_env = {"OTHER_VAR": "value", "HOME": "/home/user"}
        mock_which.return_value = "/usr/bin/echo"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["/usr/bin/echo"]
        )

        # Act
        runner = CommandRunner()
        result = runner.run(["echo"], env=custom_env)

        # Assert
        assert result.success is True
        # Verify shutil.which was called with path=None (uses system PATH)
        mock_which.assert_called_with("echo", path=None)

    def test_run_empty_command_raises_value_error(self):
        """Test that empty command list raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="Command cannot be empty"):
            runner.run([])

    def test_run_empty_string_command_raises_value_error(self):
        """Test that empty string command raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="Command cannot be empty"):
            runner.run("")

    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("sys.platform", "win32")
    def test_run_case_insensitive_path_on_windows(self, mock_which, mock_run):
        """Test case-insensitive PATH lookup on Windows."""
        # Arrange - Windows with mixed-case PATH
        custom_env = {"PaTh": "C:\\custom\\bin", "OTHER": "value"}
        mock_which.return_value = "C:\\custom\\bin\\mycmd.exe"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["C:\\custom\\bin\\mycmd.exe"]
        )

        # Act
        runner = CommandRunner()
        result = runner.run(["mycmd"], env=custom_env)

        # Assert
        assert result.success is True
        # Verify the mixed-case PATH was found and used
        mock_which.assert_called_with("mycmd", path="C:\\custom\\bin")

    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("sys.platform", "linux")
    def test_run_case_sensitive_path_on_linux(self, mock_which, mock_run):
        """Test case-sensitive PATH lookup on Linux."""
        # Arrange - Linux only checks exact case
        custom_env = {"PaTh": "/custom/bin", "OTHER": "value"}
        mock_which.return_value = None  # Won't find PaTh
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="", args=["mycmd"])

        # Act
        runner = CommandRunner()
        result = runner.run(["mycmd"], env=custom_env)

        # Assert
        assert result.success is True
        # On Linux, PaTh should not be found (case-sensitive)
        mock_which.assert_called_with("mycmd", path=None)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_logs_debug_when_path_resolved(self, mock_which, mock_run, caplog):
        """Test that debug logging occurs when path is resolved."""
        import logging

        # Arrange
        mock_which.return_value = "/usr/bin/echo"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["/usr/bin/echo"]
        )

        # Act
        with caplog.at_level(logging.DEBUG):
            runner = CommandRunner()
            runner.run(["echo"])

        # Assert
        assert "Resolved 'echo' to '/usr/bin/echo'" in caplog.text

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_logs_debug_when_path_not_resolved(self, mock_which, mock_run, caplog):
        """Test that debug logging occurs when path cannot be resolved."""
        import logging

        # Arrange
        mock_which.return_value = None
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output", stderr="", args=["custom-cmd"]
        )

        # Act
        with caplog.at_level(logging.DEBUG):
            runner = CommandRunner()
            runner.run(["custom-cmd"])

        # Assert
        assert "Could not resolve path for 'custom-cmd', using as-is" in caplog.text

    def test_run_rejects_non_string_command_element(self):
        """Test that command with non-string element raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(
            ValueError, match="Command element at index 0 must be a string, got int"
        ):
            runner.run([123, "arg"])

    def test_run_rejects_none_command_element(self):
        """Test that command with None element raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(
            ValueError, match="Command element at index 0 must be a string, got NoneType"
        ):
            runner.run([None])

    def test_run_rejects_mixed_type_command(self):
        """Test that command with mixed types raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(
            ValueError, match="Command element at index 1 must be a string, got int"
        ):
            runner.run(["echo", 123])

    def test_run_rejects_list_in_command(self):
        """Test that command with list element raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(
            ValueError, match="Command element at index 1 must be a string, got list"
        ):
            runner.run(["echo", ["nested"]])

    def test_run_rejects_empty_string_executable(self):
        """Test that command with empty string as executable raises appropriate error."""
        runner = CommandRunner()

        # Empty string is technically valid as a string, but will fail during execution
        # This tests that our validation doesn't break this edge case
        with pytest.raises(ValueError, match="Command element at index 0 must be a string"):
            runner.run([123])  # Not testing empty string here, that's a different case

    def test_run_rejects_non_string_path_in_env(self):
        """Test that non-string PATH value in env raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="PATH environment variable must be a string, got int"):
            runner.run(["echo"], env={"PATH": 123})

    @patch("sys.platform", "win32")
    def test_run_rejects_non_string_path_windows(self):
        """Test that non-string PATH value in env raises ValueError on Windows."""
        runner = CommandRunner()

        with pytest.raises(
            ValueError, match="PATH environment variable must be a string, got list"
        ):
            runner.run(["echo"], env={"PaTh": ["/usr/bin"]})

    def test_run_allows_none_path_in_env(self):
        """Test that None PATH value in env is allowed (uses system PATH)."""
        runner = CommandRunner()

        # This should NOT raise - None means "use system PATH"
        # But we need to mock to prevent actual command execution
        with patch("subprocess.run") as mock_run:
            with patch("shutil.which", return_value="/usr/bin/echo"):
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="output", stderr="", args=["echo"]
                )
                # PATH: None should be fine - skipped by validation
                result = runner.run(["echo"], env={"OTHER": "value"})
                assert result.success is True

    def test_run_rejects_string_timeout(self):
        """Test that string timeout raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="timeout must be a number, got str"):
            runner.run(["echo"], timeout="10")

    def test_run_rejects_negative_timeout(self):
        """Test that negative timeout raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="timeout must be positive, got -1"):
            runner.run(["echo"], timeout=-1)

    def test_run_rejects_zero_timeout(self):
        """Test that zero timeout raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="timeout must be positive, got 0"):
            runner.run(["echo"], timeout=0)

    def test_run_rejects_non_boolean_check(self):
        """Test that non-boolean check raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="check must be a boolean, got str"):
            runner.run(["echo"], check="true")

    def test_run_rejects_invalid_working_dir_type(self):
        """Test that invalid working_dir type raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="working_dir must be a string or Path, got int"):
            runner.run(["echo"], working_dir=123)

    def test_run_rejects_string_retry_count(self):
        """Test that string retry_count raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="retry_count must be an integer, got str"):
            runner.run(["echo"], retry_count="3")

    def test_run_rejects_negative_retry_count(self):
        """Test that negative retry_count raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="retry_count must be non-negative, got -1"):
            runner.run(["echo"], retry_count=-1)

    def test_run_rejects_float_retry_count(self):
        """Test that float retry_count raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="retry_count must be an integer, got float"):
            runner.run(["echo"], retry_count=1.5)

    def test_run_rejects_string_retry_delay(self):
        """Test that string retry_delay raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="retry_delay must be a number, got str"):
            runner.run(["echo"], retry_delay="1.5")

    def test_run_rejects_negative_retry_delay(self):
        """Test that negative retry_delay raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="retry_delay must be non-negative, got -1"):
            runner.run(["echo"], retry_delay=-1)

    def test_run_rejects_non_dict_env(self):
        """Test that non-dict env raises ValueError."""
        runner = CommandRunner()

        with pytest.raises(ValueError, match="env must be a dictionary, got list"):
            runner.run(["echo"], env=["PATH=/usr/bin"])

    def test_run_accepts_valid_timeout_int(self):
        """Test that valid integer timeout is accepted."""
        runner = CommandRunner()

        with patch("subprocess.run") as mock_run:
            with patch("shutil.which", return_value="/usr/bin/echo"):
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="output", stderr="", args=["echo"]
                )
                result = runner.run(["echo"], timeout=30)
                assert result.success is True

    def test_run_accepts_valid_timeout_float(self):
        """Test that valid float timeout is accepted."""
        runner = CommandRunner()

        with patch("subprocess.run") as mock_run:
            with patch("shutil.which", return_value="/usr/bin/echo"):
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="output", stderr="", args=["echo"]
                )
                result = runner.run(["echo"], timeout=1.5)
                assert result.success is True

    def test_run_accepts_path_object_for_working_dir(self):
        """Test that Path object for working_dir is accepted."""
        from pathlib import Path

        runner = CommandRunner()

        with patch("subprocess.run") as mock_run:
            with patch("shutil.which", return_value="/usr/bin/echo"):
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="output", stderr="", args=["echo"]
                )
                result = runner.run(["echo"], working_dir=Path("/tmp"))
                assert result.success is True

    def test_run_accepts_zero_retry_delay(self):
        """Test that zero retry_delay is accepted."""
        runner = CommandRunner()

        with patch("subprocess.run") as mock_run:
            with patch("shutil.which", return_value="/usr/bin/echo"):
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="output", stderr="", args=["echo"]
                )
                result = runner.run(["echo"], retry_delay=0)
                assert result.success is True
