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
        mock_which.assert_called_with("echo")
        
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

