"""
Tests for format_lint_fixer module.

Validates format and lint auto-fix functionality for Node.js and Python projects.

Run tests:
    pytest tests/unit/init/test_format_lint_fixer.py -v

Run with coverage:
    pytest tests/unit/init/test_format_lint_fixer.py --cov=solokit.init.format_lint_fixer --cov-report=term-missing

Target: 90%+ coverage
"""

from unittest.mock import Mock, patch

from solokit.init.format_lint_fixer import (
    _run_nodejs_fixes,
    _run_python_fixes,
    run_format_lint_fix,
)


class TestRunFormatLintFix:
    """Tests for run_format_lint_fix() main function."""

    def test_routes_to_python_for_ml_ai_fastapi(self, temp_project):
        """Test that ml_ai_fastapi template uses Python fixes."""
        with patch("solokit.init.format_lint_fixer._run_python_fixes") as mock_python_fixes:
            mock_python_fixes.return_value = {
                "format_success": True,
                "lint_success": True,
            }

            result = run_format_lint_fix("ml_ai_fastapi", temp_project)

            mock_python_fixes.assert_called_once_with(temp_project)
            assert result["format_success"] is True
            assert result["lint_success"] is True

    def test_routes_to_nodejs_for_saas_t3(self, temp_project):
        """Test that saas_t3 template uses Node.js fixes."""
        with patch("solokit.init.format_lint_fixer._run_nodejs_fixes") as mock_nodejs_fixes:
            mock_nodejs_fixes.return_value = {
                "format_success": True,
                "lint_success": True,
            }

            result = run_format_lint_fix("saas_t3", temp_project)

            mock_nodejs_fixes.assert_called_once_with(temp_project)
            assert result["format_success"] is True

    def test_routes_to_nodejs_for_fullstack_nextjs(self, temp_project):
        """Test that fullstack_nextjs template uses Node.js fixes."""
        with patch("solokit.init.format_lint_fixer._run_nodejs_fixes") as mock_nodejs_fixes:
            mock_nodejs_fixes.return_value = {
                "format_success": True,
                "lint_success": True,
            }

            result = run_format_lint_fix("fullstack_nextjs", temp_project)

            mock_nodejs_fixes.assert_called_once_with(temp_project)
            assert result["format_success"] is True

    def test_routes_to_nodejs_for_dashboard_refine(self, temp_project):
        """Test that dashboard_refine template uses Node.js fixes."""
        with patch("solokit.init.format_lint_fixer._run_nodejs_fixes") as mock_nodejs_fixes:
            mock_nodejs_fixes.return_value = {
                "format_success": True,
                "lint_success": True,
            }

            result = run_format_lint_fix("dashboard_refine", temp_project)

            mock_nodejs_fixes.assert_called_once_with(temp_project)
            assert result["format_success"] is True

    def test_uses_current_directory_when_no_project_root(self):
        """Test that function uses current directory when project_root is None."""
        with patch("solokit.init.format_lint_fixer._run_nodejs_fixes") as mock_nodejs_fixes:
            mock_nodejs_fixes.return_value = {
                "format_success": True,
                "lint_success": True,
            }
            with patch("solokit.init.format_lint_fixer.Path") as mock_path:
                mock_cwd = Mock()
                mock_path.cwd.return_value = mock_cwd

                run_format_lint_fix("saas_t3", None)

                mock_nodejs_fixes.assert_called_once_with(mock_cwd)


class TestRunNodejsFixes:
    """Tests for _run_nodejs_fixes() function."""

    def test_skips_when_no_package_json(self, temp_project):
        """Test that function skips when package.json doesn't exist."""
        result = _run_nodejs_fixes(temp_project)

        assert result["format_success"] is True
        assert result["lint_success"] is True

    def test_runs_format_and_lint_successfully(self, temp_project):
        """Test successful format and lint execution."""
        # Create package.json
        (temp_project / "package.json").write_text('{"name": "test"}')

        mock_success_result = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = mock_success_result
            mock_runner_cls.return_value = mock_runner

            result = _run_nodejs_fixes(temp_project)

            assert result["format_success"] is True
            assert result["lint_success"] is True
            assert mock_runner.run.call_count == 2

            # Verify correct commands were called
            calls = mock_runner.run.call_args_list
            assert calls[0][0][0] == ["npm", "run", "format"]
            assert calls[1][0][0] == ["npm", "run", "lint:fix"]

    def test_format_failure_is_non_blocking(self, temp_project):
        """Test that format failure doesn't block lint."""
        (temp_project / "package.json").write_text('{"name": "test"}')

        format_fail = Mock(success=False, stdout="", stderr="format error", returncode=1)
        lint_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.side_effect = [format_fail, lint_success]
            mock_runner_cls.return_value = mock_runner

            result = _run_nodejs_fixes(temp_project)

            assert result["format_success"] is False
            assert result["lint_success"] is True

    def test_lint_failure_is_recorded(self, temp_project):
        """Test that lint failure is properly recorded."""
        (temp_project / "package.json").write_text('{"name": "test"}')

        format_success = Mock(success=True, stdout="", stderr="", returncode=0)
        lint_fail = Mock(success=False, stdout="", stderr="lint error", returncode=1)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.side_effect = [format_success, lint_fail]
            mock_runner_cls.return_value = mock_runner

            result = _run_nodejs_fixes(temp_project)

            assert result["format_success"] is True
            assert result["lint_success"] is False

    def test_both_failures_are_recorded(self, temp_project):
        """Test that both format and lint failures are recorded."""
        (temp_project / "package.json").write_text('{"name": "test"}')

        fail_result = Mock(success=False, stdout="", stderr="error", returncode=1)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = fail_result
            mock_runner_cls.return_value = mock_runner

            result = _run_nodejs_fixes(temp_project)

            assert result["format_success"] is False
            assert result["lint_success"] is False


class TestRunPythonFixes:
    """Tests for _run_python_fixes() function."""

    def test_runs_ruff_commands_successfully(self, temp_project):
        """Test successful ruff format and check execution."""
        mock_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = mock_success
            mock_runner_cls.return_value = mock_runner

            result = _run_python_fixes(temp_project)

            assert result["format_success"] is True
            assert result["lint_success"] is True
            assert mock_runner.run.call_count == 2

            # Verify correct commands
            calls = mock_runner.run.call_args_list
            assert calls[0][0][0] == ["ruff", "format", "."]
            assert calls[1][0][0] == ["ruff", "check", "--fix", "."]

    def test_uses_venv_ruff_when_available(self, temp_project):
        """Test that venv ruff is preferred when available."""
        # Create venv with ruff
        venv_bin = temp_project / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        ruff_path = venv_bin / "ruff"
        ruff_path.write_text("#!/bin/bash")

        mock_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = mock_success
            mock_runner_cls.return_value = mock_runner

            _run_python_fixes(temp_project)

            # Verify venv ruff path was used
            calls = mock_runner.run.call_args_list
            assert str(ruff_path) in calls[0][0][0][0]

    def test_uses_windows_venv_path(self, temp_project):
        """Test that Windows venv path is used when Unix path doesn't exist."""
        # Create venv with Windows-style Scripts directory
        venv_scripts = temp_project / "venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        ruff_path = venv_scripts / "ruff"
        ruff_path.write_text("ruff.exe")

        mock_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = mock_success
            mock_runner_cls.return_value = mock_runner

            _run_python_fixes(temp_project)

            # Verify Windows ruff path was used
            calls = mock_runner.run.call_args_list
            assert str(ruff_path) in calls[0][0][0][0]

    def test_falls_back_to_system_ruff(self, temp_project):
        """Test fallback to system ruff when no venv exists."""
        # No venv directory
        mock_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = mock_success
            mock_runner_cls.return_value = mock_runner

            _run_python_fixes(temp_project)

            # Verify system ruff was used
            calls = mock_runner.run.call_args_list
            assert calls[0][0][0] == ["ruff", "format", "."]

    def test_format_failure_is_non_blocking(self, temp_project):
        """Test that format failure doesn't block lint check."""
        format_fail = Mock(success=False, stdout="", stderr="format error", returncode=1)
        lint_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.side_effect = [format_fail, lint_success]
            mock_runner_cls.return_value = mock_runner

            result = _run_python_fixes(temp_project)

            assert result["format_success"] is False
            assert result["lint_success"] is True

    def test_lint_failure_is_recorded(self, temp_project):
        """Test that lint failure is properly recorded."""
        format_success = Mock(success=True, stdout="", stderr="", returncode=0)
        lint_fail = Mock(success=False, stdout="", stderr="lint error", returncode=1)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.side_effect = [format_success, lint_fail]
            mock_runner_cls.return_value = mock_runner

            result = _run_python_fixes(temp_project)

            assert result["format_success"] is True
            assert result["lint_success"] is False


class TestIntegration:
    """Integration tests for format_lint_fixer module."""

    def test_full_nodejs_flow(self, temp_project):
        """Test complete Node.js format/lint flow."""
        # Setup Node.js project
        (temp_project / "package.json").write_text('{"name": "test-project"}')

        mock_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = mock_success
            mock_runner_cls.return_value = mock_runner

            result = run_format_lint_fix("fullstack_nextjs", temp_project)

            assert result["format_success"] is True
            assert result["lint_success"] is True

    def test_full_python_flow(self, temp_project):
        """Test complete Python format/lint flow."""
        mock_success = Mock(success=True, stdout="", stderr="", returncode=0)

        with patch("solokit.init.format_lint_fixer.CommandRunner") as mock_runner_cls:
            mock_runner = Mock()
            mock_runner.run.return_value = mock_success
            mock_runner_cls.return_value = mock_runner

            result = run_format_lint_fix("ml_ai_fastapi", temp_project)

            assert result["format_success"] is True
            assert result["lint_success"] is True
