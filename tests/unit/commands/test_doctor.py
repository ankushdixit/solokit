"""Unit tests for doctor command."""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from solokit.commands.doctor import (
    DiagnosticCheck,
    check_config_valid,
    check_git_installed,
    check_python_version,
    check_quality_tools,
    check_session_directory,
    check_work_items_valid,
    main,
    parse_version,
    print_diagnostic_results,
    run_diagnostics,
)


def test_parse_version_standard():
    """Test parsing standard version string."""
    assert parse_version("3.11.7") == (3, 11, 7)
    assert parse_version("2.45.0") == (2, 45, 0)


def test_parse_version_with_v_prefix():
    """Test parsing version string with 'v' prefix."""
    assert parse_version("v3.11.7") == (3, 11, 7)
    assert parse_version("v2.45.0") == (2, 45, 0)


def test_parse_version_without_patch():
    """Test parsing version string without patch version."""
    assert parse_version("3.11") == (3, 11, 0)


def test_parse_version_invalid():
    """Test parsing invalid version string."""
    with pytest.raises(ValueError):
        parse_version("invalid")


def test_parse_version_single_number():
    """Test parsing version string with only one number."""
    with pytest.raises(ValueError):
        parse_version("3")


def test_parse_version_non_numeric():
    """Test parsing version string with non-numeric parts."""
    with pytest.raises(ValueError):
        parse_version("3.abc.7")


def test_check_python_version_passes():
    """Test that Python version check passes for current Python."""
    result = check_python_version()
    # Current Python should meet minimum requirements (3.11+)
    assert result.passed is True
    assert "Python" in result.message
    assert result.name == "Python Version"


def test_check_python_version_fails():
    """Test Python version check with old Python version."""
    # Mock sys.version_info to simulate old Python
    with patch("sys.version_info", (3, 8, 0)):
        result = check_python_version()
        assert result.passed is False
        assert "Python 3.8.0" in result.message
        assert result.suggestion is not None


def test_check_git_installed_success():
    """Test git installed check when git is available."""
    with patch("shutil.which", return_value="/usr/bin/git"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="git version 2.39.0\n")
            result = check_git_installed()
            assert result.passed is True
            assert "git version" in result.message


def test_check_git_installed_not_found():
    """Test git installed check when git is not in PATH."""
    with patch("shutil.which", return_value=None):
        result = check_git_installed()
        assert result.passed is False
        assert "not found in PATH" in result.message
        assert result.suggestion is not None


def test_check_git_installed_error():
    """Test git installed check when git command fails."""
    with patch("shutil.which", return_value="/usr/bin/git"):
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            result = check_git_installed()
            assert result.passed is False
            assert "not working correctly" in result.message


def test_check_git_installed_timeout():
    """Test git installed check when git command times out."""
    with patch("shutil.which", return_value="/usr/bin/git"):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5)):
            result = check_git_installed()
            assert result.passed is False
            assert "not working correctly" in result.message


def test_check_session_directory_missing(tmp_path, monkeypatch):
    """Test session directory check when .session doesn't exist."""
    monkeypatch.chdir(tmp_path)
    result = check_session_directory()
    assert result.passed is False
    assert "directory not found" in result.message
    assert result.suggestion is not None


def test_check_session_directory_missing_config(tmp_path, monkeypatch):
    """Test session directory check when config.json is missing."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    monkeypatch.chdir(tmp_path)

    result = check_session_directory()
    assert result.passed is False
    assert "missing config.json" in result.message


def test_check_session_directory_success(tmp_path, monkeypatch):
    """Test session directory check when everything exists."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    (session_dir / "config.json").write_text("{}")
    monkeypatch.chdir(tmp_path)

    result = check_session_directory()
    assert result.passed is True
    assert "exists with config.json" in result.message


def test_check_config_valid_missing(tmp_path, monkeypatch):
    """Test config validation when config.json doesn't exist."""
    monkeypatch.chdir(tmp_path)
    result = check_config_valid()
    assert result.passed is False
    assert "not found" in result.message


def test_check_config_valid_invalid_json(tmp_path, monkeypatch):
    """Test config validation with invalid JSON."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_file.write_text("{invalid json")
    monkeypatch.chdir(tmp_path)

    result = check_config_valid()
    assert result.passed is False
    assert "invalid JSON" in result.message


def test_check_config_valid_not_dict(tmp_path, monkeypatch):
    """Test config validation when config is not a dictionary."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_file.write_text("[]")
    monkeypatch.chdir(tmp_path)

    result = check_config_valid()
    assert result.passed is False
    assert "not a valid object" in result.message


def test_check_config_valid_empty(tmp_path, monkeypatch):
    """Test config validation when config is empty."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_file.write_text("{}")
    monkeypatch.chdir(tmp_path)

    result = check_config_valid()
    assert result.passed is False
    assert "empty" in result.message


def test_check_config_valid_success(tmp_path, monkeypatch):
    """Test config validation with valid config."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_file.write_text('{"test": "data"}')
    monkeypatch.chdir(tmp_path)

    result = check_config_valid()
    assert result.passed is True
    assert "valid" in result.message


def test_check_config_valid_read_error(tmp_path, monkeypatch):
    """Test config validation when file read error occurs."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_file.write_text('{"test": "data"}')
    monkeypatch.chdir(tmp_path)

    # Mock open to raise an exception
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        result = check_config_valid()
        assert result.passed is False
        assert "Error reading" in result.message


def test_check_work_items_valid_missing(tmp_path, monkeypatch):
    """Test work items validation when file doesn't exist."""
    monkeypatch.chdir(tmp_path)
    result = check_work_items_valid()
    assert result.passed is True
    assert "will be created when needed" in result.message


def test_check_work_items_valid_success(tmp_path, monkeypatch):
    """Test work items validation with valid file."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    work_items_file = session_dir / "work_items.json"
    work_items_file.write_text('[{"id": "WI-001", "title": "Test"}]')
    monkeypatch.chdir(tmp_path)

    result = check_work_items_valid()
    assert result.passed is True
    assert "1 items" in result.message


def test_check_work_items_valid_not_list(tmp_path, monkeypatch):
    """Test work items validation when not a list."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    work_items_file = session_dir / "work_items.json"
    work_items_file.write_text("{}")
    monkeypatch.chdir(tmp_path)

    result = check_work_items_valid()
    assert result.passed is False
    assert "not a valid list" in result.message


def test_check_work_items_valid_invalid_json(tmp_path, monkeypatch):
    """Test work items validation with invalid JSON."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    work_items_file = session_dir / "work_items.json"
    work_items_file.write_text("[invalid json")
    monkeypatch.chdir(tmp_path)

    result = check_work_items_valid()
    assert result.passed is False
    assert "invalid JSON" in result.message


def test_check_work_items_valid_read_error(tmp_path, monkeypatch):
    """Test work items validation when file read error occurs."""
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    work_items_file = session_dir / "work_items.json"
    work_items_file.write_text("[]")
    monkeypatch.chdir(tmp_path)

    # Mock open to raise an exception
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        result = check_work_items_valid()
        assert result.passed is False
        assert "Error reading" in result.message


def test_check_quality_tools_all_available():
    """Test quality tools check when all tools are available."""
    with patch("shutil.which", return_value="/usr/bin/tool"):
        result = check_quality_tools()
        assert result.passed is True
        assert "All quality tools available" in result.message


def test_check_quality_tools_some_missing():
    """Test quality tools check when some tools are missing."""

    def mock_which(tool):
        return "/usr/bin/pytest" if tool == "pytest" else None

    with patch("shutil.which", side_effect=mock_which):
        result = check_quality_tools()
        assert result.passed is False
        assert "Some tools missing" in result.message
        assert "ruff" in result.message


def test_check_quality_tools_none_available():
    """Test quality tools check when no tools are available."""
    with patch("shutil.which", return_value=None):
        result = check_quality_tools()
        assert result.passed is False
        assert "No quality tools found" in result.message


def test_print_diagnostic_results_all_passed(capsys):
    """Test printing diagnostic results when all checks pass."""
    checks = [
        DiagnosticCheck(name="Test 1", passed=True, message="Test 1 passed"),
        DiagnosticCheck(name="Test 2", passed=True, message="Test 2 passed"),
    ]
    print_diagnostic_results(checks, verbose=False)

    captured = capsys.readouterr()
    assert "Running system diagnostics" in captured.out
    assert "Test 1 passed" in captured.out
    assert "Test 2 passed" in captured.out
    assert "All 2 checks passed" in captured.out


def test_print_diagnostic_results_some_failed(capsys):
    """Test printing diagnostic results when some checks fail."""
    checks = [
        DiagnosticCheck(name="Test 1", passed=True, message="Test 1 passed"),
        DiagnosticCheck(name="Test 2", passed=False, message="Test 2 failed", suggestion="Fix it"),
    ]
    print_diagnostic_results(checks, verbose=False)

    captured = capsys.readouterr()
    assert "Test 1 passed" in captured.out
    assert "Test 2 failed" in captured.out
    assert "Fix it" in captured.out
    assert "1/2 checks passed (1 failed)" in captured.out
    assert "Run with --verbose" in captured.out


def test_print_diagnostic_results_verbose(capsys):
    """Test printing diagnostic results in verbose mode."""
    checks = [
        DiagnosticCheck(name="Test", passed=False, message="Test failed", suggestion="Fix it"),
    ]
    print_diagnostic_results(checks, verbose=True)

    captured = capsys.readouterr()
    assert "Test failed" in captured.out
    assert "Fix it" in captured.out
    # Should not show verbose message when verbose=True
    assert "Run with --verbose" not in captured.out


def test_run_diagnostics_returns_exit_code(capsys):
    """Test that run_diagnostics returns appropriate exit code."""
    result = run_diagnostics(verbose=False)
    # Result should be 0 or 1
    assert result in [0, 1]

    captured = capsys.readouterr()
    assert "Running system diagnostics" in captured.out
    assert "checks passed" in captured.out


def test_run_diagnostics_verbose(capsys):
    """Test run_diagnostics with verbose flag."""
    result = run_diagnostics(verbose=True)
    assert result in [0, 1]

    captured = capsys.readouterr()
    assert "Running system diagnostics" in captured.out


def test_main_default(capsys):
    """Test main function with no arguments."""
    with patch.object(sys, "argv", ["doctor"]):
        result = main()
        assert result in [0, 1]


def test_main_verbose_flag(capsys):
    """Test main function with --verbose flag."""
    with patch.object(sys, "argv", ["doctor", "--verbose"]):
        result = main()
        assert result in [0, 1]


def test_main_v_flag(capsys):
    """Test main function with -v flag."""
    with patch.object(sys, "argv", ["doctor", "-v"]):
        result = main()
        assert result in [0, 1]
