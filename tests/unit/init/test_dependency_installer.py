"""
Tests for dependency_installer module.

Validates dependency installation for npm and pip packages.

Run tests:
    pytest tests/unit/init/test_dependency_installer.py -v

Run with coverage:
    pytest tests/unit/init/test_dependency_installer.py --cov=solokit.init.dependency_installer --cov-report=term-missing

Target: 90%+ coverage
"""

from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from solokit.core.exceptions import CommandExecutionError, FileOperationError
from solokit.init.dependency_installer import (
    get_installation_commands,
    install_dependencies,
    install_npm_dependencies,
    install_python_dependencies,
    load_stack_versions,
)


class TestLoadStackVersions:
    """Tests for load_stack_versions()."""

    def test_load_versions_success(self, mock_stack_versions):
        """Test successful loading of stack versions."""
        versions_yaml = yaml.dump(mock_stack_versions)

        with patch("solokit.init.dependency_installer.Path") as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_file

            with patch("builtins.open", mock_open(read_data=versions_yaml)):
                result = load_stack_versions()

                assert "stacks" in result
                assert "saas_t3" in result["stacks"]

    def test_file_not_found(self):
        """Test error when stack-versions.yaml doesn't exist."""
        import solokit.init.dependency_installer as dep_module

        # Mock __file__ to point to a location where stack-versions.yaml doesn't exist
        fake_file = "/fake/path/dependency_installer.py"

        with patch.object(dep_module, "__file__", fake_file):
            with pytest.raises(FileOperationError) as exc:
                load_stack_versions()

            assert exc.value.operation == "load"
            assert "stack-versions.yaml not found" in exc.value.details

    def test_invalid_yaml(self):
        """Test error when YAML is invalid."""
        with patch("solokit.init.dependency_installer.Path") as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_file

            with patch("builtins.open", mock_open(read_data="invalid: yaml: {")):
                with pytest.raises(FileOperationError) as exc:
                    load_stack_versions()

                assert exc.value.operation == "parse"
                assert "Invalid YAML" in exc.value.details


class TestGetInstallationCommands:
    """Tests for get_installation_commands()."""

    def test_get_commands_for_valid_stack(self, mock_stack_versions):
        """Test getting installation commands for valid stack."""
        with patch(
            "solokit.init.dependency_installer.load_stack_versions",
            return_value=mock_stack_versions,
        ):
            commands = get_installation_commands("saas_t3", "tier-1")

            assert "commands" in commands
            assert "base" in commands["commands"]

    def test_stack_not_found(self, mock_stack_versions):
        """Test error when stack not found."""
        with patch(
            "solokit.init.dependency_installer.load_stack_versions",
            return_value=mock_stack_versions,
        ):
            with pytest.raises(FileOperationError) as exc:
                get_installation_commands("invalid_stack", "tier-1")

            assert "Stack 'invalid_stack' not found" in exc.value.details

    def test_no_installation_commands(self, mock_stack_versions):
        """Test error when stack has no installation section."""
        mock_stack_versions["stacks"]["saas_t3"].pop("installation")

        with patch(
            "solokit.init.dependency_installer.load_stack_versions",
            return_value=mock_stack_versions,
        ):
            with pytest.raises(FileOperationError) as exc:
                get_installation_commands("saas_t3", "tier-1")

            assert "No installation commands found" in exc.value.details


class TestInstallNpmDependencies:
    """Tests for install_npm_dependencies()."""

    def test_install_tier1_dependencies(self, tmp_path, mock_stack_versions):
        """Test installing tier-1 dependencies."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                result = install_npm_dependencies("saas_t3", "tier-1-essential", tmp_path)

                assert result is True
                # Should install base and tier1
                assert mock_runner.run.call_count >= 2

    def test_install_tier4_dependencies(self, tmp_path, mock_stack_versions):
        """Test installing tier-4 dependencies (includes all tiers)."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                result = install_npm_dependencies("saas_t3", "tier-4-production", tmp_path)

                assert result is True
                # Should install base, tier1, tier2, tier3, tier4_dev, tier4_prod
                assert mock_runner.run.call_count >= 6

    def test_install_fails(self, tmp_path, mock_stack_versions):
        """Test error when npm install fails."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=False, stdout="", stderr="Install failed", returncode=1
                )

                with pytest.raises(CommandExecutionError) as exc:
                    install_npm_dependencies("saas_t3", "tier-1-essential", tmp_path)

                assert exc.value.returncode == 1
                assert "Install failed" in exc.value.stderr

    def test_unknown_template_id(self, tmp_path):
        """Test handling of unknown template ID."""
        result = install_npm_dependencies("unknown_template", "tier-1-essential", tmp_path)

        assert result is False

    def test_install_uses_cwd_when_project_root_none(self, mock_stack_versions):
        """Test that install uses cwd when project_root is None."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                with patch("solokit.init.dependency_installer.Path.cwd") as mock_cwd:
                    from pathlib import Path

                    mock_cwd.return_value = Path("/test/path")
                    result = install_npm_dependencies("saas_t3", "tier-1-essential", None)

                    assert result is True
                    mock_cwd.assert_called_once()

    def test_missing_command_key_warning(self, tmp_path, mock_stack_versions):
        """Test warning when command key is missing."""
        # Remove tier1 from commands
        mock_stack_versions["stacks"]["saas_t3"]["installation"]["commands"].pop("tier1")

        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                # Should still succeed, just skip missing command
                result = install_npm_dependencies("saas_t3", "tier-1-essential", tmp_path)
                assert result is True

    def test_tier3_with_preinstalled_playwright_browsers(self, tmp_path, mock_stack_versions):
        """Test tier-3 installation with pre-installed Playwright browsers."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                with patch.dict("os.environ", {"PLAYWRIGHT_BROWSERS_PATH": "/pre/installed"}):
                    result = install_npm_dependencies("saas_t3", "tier-3-comprehensive", tmp_path)

                    assert result is True
                    # Should not try to install browsers

    def test_tier3_linux_playwright_installation(self, tmp_path, mock_stack_versions):
        """Test tier-3 installation on Linux with Playwright."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                with patch("platform.system", return_value="Linux"):
                    with patch.dict("os.environ", {}, clear=True):
                        result = install_npm_dependencies(
                            "saas_t3", "tier-3-comprehensive", tmp_path
                        )

                        assert result is True
                        # Should have called playwright install commands

    def test_tier3_playwright_browser_install_failure(self, tmp_path, mock_stack_versions):
        """Test tier-3 with Playwright browser install failure (non-critical)."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner

                # Success for main installs, failure for playwright browsers
                def run_side_effect(cmd, check=True, timeout=None):
                    if "playwright install" in " ".join(str(c) for c in cmd):
                        return Mock(success=False, stderr="Browser install failed", returncode=1)
                    return Mock(success=True, stdout="", stderr="", returncode=0)

                mock_runner.run.side_effect = run_side_effect

                with patch("platform.system", return_value="Darwin"):
                    with patch.dict("os.environ", {}, clear=True):
                        result = install_npm_dependencies(
                            "saas_t3", "tier-3-comprehensive", tmp_path
                        )

                        # Should still succeed (playwright is non-critical)
                        assert result is True

    def test_tier3_linux_playwright_deps_failure(self, tmp_path, mock_stack_versions):
        """Test tier-3 on Linux with Playwright system deps failure."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["saas_t3"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner

                # Success for main installs, failure for playwright install-deps
                def run_side_effect(cmd, check=True, timeout=None):
                    if "install-deps" in " ".join(str(c) for c in cmd):
                        return Mock(success=False, stderr="install-deps failed", returncode=1)
                    return Mock(success=True, stdout="", stderr="", returncode=0)

                mock_runner.run.side_effect = run_side_effect

                with patch("platform.system", return_value="Linux"):
                    with patch.dict("os.environ", {}, clear=True):
                        result = install_npm_dependencies(
                            "saas_t3", "tier-3-comprehensive", tmp_path
                        )

                        # Should still succeed (deps install is non-critical)
                        assert result is True


class TestInstallPythonDependencies:
    """Tests for install_python_dependencies()."""

    def test_create_venv(self, tmp_path, mock_stack_versions):
        """Test creating virtual environment."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                result = install_python_dependencies("tier-1-essential", None, tmp_path)

                assert result is True
                # First call should be venv creation
                first_call = mock_runner.run.call_args_list[0][0][0]
                assert "venv" in first_call

    def test_existing_venv(self, tmp_path, mock_stack_versions):
        """Test when virtual environment already exists."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "pip").write_text("#!/usr/bin/env python")

        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                result = install_python_dependencies("tier-1-essential", None, tmp_path)

                assert result is True

    def test_tier4_additional_packages(self, tmp_path, mock_stack_versions):
        """Test installing tier-4 specific packages."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "pip").write_text("#!/usr/bin/env python")

        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                result = install_python_dependencies("tier-4-production", None, tmp_path)

                assert result is True
                # Should install all_tiers and tier4
                assert mock_runner.run.call_count >= 3  # upgrade pip + all_tiers + tier4

    def test_venv_creation_fails(self, tmp_path, mock_stack_versions):
        """Test error when venv creation fails."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=False, stdout="", stderr="Venv failed", returncode=1
                )

                with pytest.raises(CommandExecutionError):
                    install_python_dependencies("tier-1-essential", None, tmp_path)

    def test_python_install_uses_cwd_when_project_root_none(self, mock_stack_versions):
        """Test that Python install uses cwd when project_root is None."""
        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                with patch("solokit.init.dependency_installer.Path.cwd") as mock_cwd:
                    from pathlib import Path

                    mock_cwd.return_value = Path("/test/path")
                    # Need to create the venv path for the test
                    with patch.object(Path, "exists", return_value=True):
                        result = install_python_dependencies("tier-1-essential", None, None)
                        assert result is True
                        mock_cwd.assert_called()

    def test_python_missing_command_key_warning(self, tmp_path, mock_stack_versions):
        """Test warning when command key is missing in Python install."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "pip").write_text("#!/usr/bin/env python")

        # Remove tier1 from commands
        mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]["commands"].pop("tier1")

        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                # Should still succeed, just skip missing command
                result = install_python_dependencies("tier-1-essential", None, tmp_path)
                assert result is True

    def test_python_install_failure(self, tmp_path, mock_stack_versions):
        """Test error when Python package install fails."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "pip").write_text("#!/usr/bin/env python")

        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner

                # Success for pip upgrade, failure for package install
                def run_side_effect(cmd, check=True, timeout=None):
                    if "upgrade" in " ".join(str(c) for c in cmd):
                        return Mock(success=True, stdout="", stderr="", returncode=0)
                    return Mock(success=False, stderr="Install failed", returncode=1)

                mock_runner.run.side_effect = run_side_effect

                with pytest.raises(CommandExecutionError) as exc:
                    install_python_dependencies("tier-1-essential", None, tmp_path)

                assert "Install failed" in exc.value.stderr

    def test_python_security_fixes_success(self, tmp_path, mock_stack_versions):
        """Test successful security fixes application."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "pip").write_text("#!/usr/bin/env python")

        # Add security_fixes command
        mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]["commands"][
            "security_fixes"
        ] = "pip install --upgrade certifi"

        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(
                    success=True, stdout="", stderr="", returncode=0
                )

                result = install_python_dependencies("tier-1-essential", None, tmp_path)
                assert result is True

    def test_python_security_fixes_failure(self, tmp_path, mock_stack_versions):
        """Test non-critical failure of security fixes."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "pip").write_text("#!/usr/bin/env python")

        # Add security_fixes command
        mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]["commands"][
            "security_fixes"
        ] = "pip install --upgrade certifi"

        with patch("solokit.init.dependency_installer.get_installation_commands") as mock_get:
            mock_get.return_value = mock_stack_versions["stacks"]["ml_ai_fastapi"]["installation"]

            with patch("solokit.init.dependency_installer.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner

                # Success for main installs, failure for security fixes
                def run_side_effect(cmd, check=True, timeout=None):
                    if "certifi" in " ".join(str(c) for c in cmd):
                        return Mock(success=False, stderr="Security fix failed", returncode=1)
                    return Mock(success=True, stdout="", stderr="", returncode=0)

                mock_runner.run.side_effect = run_side_effect

                # Should still succeed (security fixes are non-critical)
                result = install_python_dependencies("tier-1-essential", None, tmp_path)
                assert result is True


class TestInstallDependencies:
    """Tests for install_dependencies()."""

    def test_install_for_nodejs_template(self, tmp_path):
        """Test routing to npm installer for Node.js templates."""
        with patch("solokit.init.dependency_installer.install_npm_dependencies") as mock_npm:
            mock_npm.return_value = True

            result = install_dependencies("saas_t3", "tier-1-essential", None, tmp_path)

            assert result is True
            mock_npm.assert_called_once()

    def test_install_for_python_template(self, tmp_path):
        """Test routing to pip installer for Python templates."""
        with patch("solokit.init.dependency_installer.install_python_dependencies") as mock_pip:
            mock_pip.return_value = True

            result = install_dependencies("ml_ai_fastapi", "tier-1-essential", None, tmp_path)

            assert result is True
            mock_pip.assert_called_once()

    def test_passes_python_binary(self, tmp_path):
        """Test that python_binary is passed through."""
        with patch("solokit.init.dependency_installer.install_python_dependencies") as mock_pip:
            mock_pip.return_value = True

            install_dependencies(
                "ml_ai_fastapi", "tier-1-essential", "/usr/bin/python3.11", tmp_path
            )

            mock_pip.assert_called_once_with("tier-1-essential", "/usr/bin/python3.11", tmp_path)
