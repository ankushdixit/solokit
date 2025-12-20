"""Centralized command execution with consistent error handling.

This module provides a unified interface for running subprocess commands
with standardized timeout handling, error handling, logging, and retry logic.
"""

import json
import logging
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    CommandExecutionError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of a command execution."""

    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    duration_seconds: float
    timed_out: bool = False

    @property
    def success(self) -> bool:
        """Whether command succeeded."""
        return self.returncode == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """Get stdout or stderr if stdout empty."""
        return self.stdout.strip() if self.stdout else self.stderr.strip()


class CommandRunner:
    """Centralized command execution with consistent error handling."""

    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(
        self,
        default_timeout: float = DEFAULT_TIMEOUT,
        working_dir: Path | None = None,
        raise_on_error: bool = False,
    ):
        """Initialize command runner.

        Args:
            default_timeout: Default timeout in seconds
            working_dir: Working directory for commands (None = current)
            raise_on_error: Whether to raise exception on non-zero exit
        """
        self.default_timeout = default_timeout
        self.working_dir = working_dir
        self.raise_on_error = raise_on_error

    @log_errors()
    def run(
        self,
        command: str | list[str],
        timeout: float | None = None,
        check: bool | None = None,
        working_dir: Path | None = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
        env: dict | None = None,
    ) -> CommandResult:
        """Run a command with consistent error handling.

        Args:
            command: Command to run (string or list)
            timeout: Timeout in seconds (None = use default)
            check: Raise exception on non-zero exit (None = use instance setting)
            working_dir: Working directory (None = use instance setting)
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds
            env: Environment variables

        Returns:
            CommandResult with output and status

        Raises:
            ValueError: If command is empty or contains non-string elements, or if
                       parameters have invalid types or values
            CommandExecutionError: If check=True and command fails
            TimeoutError: If command exceeds timeout
        """
        # Validate timeout parameter
        if timeout is not None:
            if not isinstance(timeout, (int, float)):
                raise ValueError(
                    f"timeout must be a number, got {type(timeout).__name__}: {timeout!r}"
                )
            if timeout <= 0:
                raise ValueError(f"timeout must be positive, got {timeout}")

        # Validate check parameter
        if check is not None and not isinstance(check, bool):
            raise ValueError(f"check must be a boolean, got {type(check).__name__}: {check!r}")

        # Validate working_dir parameter
        if working_dir is not None and not isinstance(working_dir, (str, Path)):
            raise ValueError(
                f"working_dir must be a string or Path, got {type(working_dir).__name__}: {working_dir!r}"
            )

        # Validate retry_count parameter
        if not isinstance(retry_count, int):
            raise ValueError(
                f"retry_count must be an integer, got {type(retry_count).__name__}: {retry_count!r}"
            )
        if retry_count < 0:
            raise ValueError(f"retry_count must be non-negative, got {retry_count}")

        # Validate retry_delay parameter
        if not isinstance(retry_delay, (int, float)):
            raise ValueError(
                f"retry_delay must be a number, got {type(retry_delay).__name__}: {retry_delay!r}"
            )
        if retry_delay < 0:
            raise ValueError(f"retry_delay must be non-negative, got {retry_delay}")

        # Validate env parameter
        if env is not None and not isinstance(env, dict):
            raise ValueError(f"env must be a dictionary, got {type(env).__name__}: {env!r}")

        if isinstance(command, str):
            command = command.split()

        # Validate command is not empty
        if not command:
            raise ValueError("Command cannot be empty")

        # Create a copy to avoid mutating the caller's list
        command = command.copy()

        # Validate all command elements are strings
        for i, elem in enumerate(command):
            if not isinstance(elem, str):
                raise ValueError(
                    f"Command element at index {i} must be a string, got {type(elem).__name__}: {elem!r}"
                )

        timeout = timeout if timeout is not None else self.default_timeout
        check = check if check is not None else self.raise_on_error
        cwd = working_dir or self.working_dir

        # Resolve executable path once (fixes Windows .cmd/.bat issue).
        # We must respect the PATH in the provided 'env' if present, otherwise
        # shutil.which uses the system PATH by default.
        path = None
        if env:
            # Case-insensitive PATH lookup on Windows
            if sys.platform == "win32":
                # Windows env vars are case-insensitive
                for key in env:
                    if key.upper() == "PATH":
                        path = env[key]
                        break
            else:
                # Unix-like systems: case-sensitive, check both variants
                path = env.get("PATH", env.get("Path", None))

            # Validate PATH is a string if present
            if path is not None and not isinstance(path, str):
                raise ValueError(
                    f"PATH environment variable must be a string, got {type(path).__name__}: {path!r}"
                )

        executable = command[0]
        # shutil.which will use os.environ['PATH'] if path is None
        resolved_path = shutil.which(executable, path=path)
        if resolved_path:
            command[0] = resolved_path
            logger.debug(f"Resolved '{executable}' to '{resolved_path}'")
        else:
            logger.debug(f"Could not resolve path for '{executable}', using as-is")

        attempt = 0
        max_attempts = retry_count + 1

        while attempt < max_attempts:
            start_time = time.time()
            try:
                logger.debug(
                    f"Running command: {' '.join(command)} "
                    f"(timeout={timeout}s, cwd={cwd}, attempt={attempt + 1}/{max_attempts})"
                )

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,  # We handle errors ourselves
                    cwd=cwd,
                    env=env,
                )

                duration = time.time() - start_time

                cmd_result = CommandResult(
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    command=command,
                    duration_seconds=duration,
                )

                if cmd_result.success:
                    logger.debug(f"Command succeeded in {duration:.2f}s")
                    return cmd_result

                # Command failed
                logger.warning(
                    f"Command failed with exit code {result.returncode}: "
                    f"{' '.join(command)}\nstderr: {result.stderr[:200]}"
                )

                if check:
                    raise CommandExecutionError(
                        command=" ".join(command),
                        returncode=result.returncode,
                        stderr=result.stderr,
                        stdout=result.stdout,
                    )

                # Retry if configured
                if attempt < max_attempts - 1:
                    logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    attempt += 1
                    continue

                return cmd_result

            except subprocess.TimeoutExpired as e:
                duration = time.time() - start_time

                logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")

                stdout_str = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
                stderr_str = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")

                cmd_result = CommandResult(
                    returncode=-1,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    command=command,
                    duration_seconds=duration,
                    timed_out=True,
                )

                if check:
                    raise TimeoutError(
                        operation=" ".join(command),
                        timeout_seconds=int(timeout),
                        context={
                            "stdout": e.stdout or "",
                            "stderr": e.stderr or "",
                        },
                    ) from e

                # Retry if configured
                if attempt < max_attempts - 1:
                    logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    attempt += 1
                    continue

                return cmd_result

            except (CommandExecutionError, TimeoutError):
                # Re-raise our standardized errors as-is (don't catch and re-wrap)
                raise
            except FileNotFoundError as e:
                # Handle case where executable is not found (e.g. solokit not installed)
                # This can happen if shutil.which returned None and we proceeded anyway.
                duration = time.time() - start_time
                error_msg = f"Command not found: {command[0]}"
                logger.error(error_msg)

                if check:
                    raise CommandExecutionError(
                        command=" ".join(command),
                        returncode=127,  # Standard "command not found" exit code
                        stderr=error_msg,
                        stdout="",
                    ) from e

                return CommandResult(
                    returncode=127,
                    stdout="",
                    stderr=error_msg,
                    command=command,
                    duration_seconds=duration,
                )
            except Exception as e:
                logger.error(f"Unexpected error running command: {e}")

                if check:
                    raise CommandExecutionError(
                        command=" ".join(command),
                        returncode=-1,
                        stderr=str(e),
                        stdout="",
                    ) from e

                # Don't retry on unexpected errors
                return CommandResult(
                    returncode=-1,
                    stdout="",
                    stderr=str(e),
                    command=command,
                    duration_seconds=time.time() - start_time,
                )

        # Should never reach here
        raise RuntimeError("Retry logic error")

    @log_errors()
    def run_json(self, command: str | list[str], **kwargs: Any) -> dict[str, Any] | None:
        """Run command and parse JSON output.

        Args:
            command: Command to run
            **kwargs: Additional arguments passed to run()

        Returns:
            Parsed JSON dict or None if parse fails
        """
        result = self.run(command, **kwargs)
        if not result.success:
            return None

        try:
            parsed: dict[str, Any] = json.loads(result.stdout)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output: {e}")
            return None

    @log_errors()
    def run_lines(self, command: str | list[str], **kwargs: Any) -> list[str]:
        """Run command and return output as lines.

        Args:
            command: Command to run
            **kwargs: Additional arguments passed to run()

        Returns:
            List of non-empty lines
        """
        result = self.run(command, **kwargs)
        if not result.success:
            return []

        return [line.strip() for line in result.stdout.split("\n") if line.strip()]


# Global instance for convenience
_default_runner = CommandRunner()


def run_command(command: str | list[str], **kwargs: Any) -> CommandResult:
    """Convenience function to run command with default runner.

    Args:
        command: Command to run
        **kwargs: Additional arguments passed to run()

    Returns:
        Command result
    """
    return _default_runner.run(command, **kwargs)
