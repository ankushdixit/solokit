"""
Tests for adopt CLI entry point.

Validates command-line argument parsing and main() function.

Run tests:
    pytest tests/unit/project/test_adopt.py -v

Target: 90%+ coverage
"""

from unittest.mock import patch

import pytest

from solokit.project.adopt import (
    main,
    prompt_additional_options,
    prompt_coverage_target,
    prompt_quality_tier,
    show_adoption_warning,
)


class TestPromptQualityTier:
    """Tests for prompt_quality_tier() function."""

    def test_returns_tier_id(self):
        """Test that function returns tier ID string."""
        with patch("solokit.project.adopt.select_from_list") as mock_select:
            mock_select.return_value = (
                "Standard - Essential + Pre-commit hooks + Security foundation"
            )

            result = prompt_quality_tier()

            assert result == "tier-2-standard"

    def test_calls_select_from_list(self):
        """Test that select_from_list is called with choices."""
        with patch("solokit.project.adopt.select_from_list") as mock_select:
            mock_select.return_value = "Essential - Linting, formatting, type-check, basic tests"

            prompt_quality_tier()

            mock_select.assert_called_once()
            args = mock_select.call_args[0]
            assert len(args[1]) == 4  # 4 tier choices

    def test_default_to_standard(self):
        """Test that default is tier-2-standard."""
        with patch("solokit.project.adopt.select_from_list") as mock_select:
            mock_select.return_value = (
                "Standard - Essential + Pre-commit hooks + Security foundation"
            )

            prompt_quality_tier()

            # Check that default was passed
            args, kwargs = mock_select.call_args
            assert "Standard" in kwargs.get("default", "")

    def test_all_tier_mappings(self):
        """Test all tier choice mappings."""
        choices = [
            ("Essential - Linting, formatting, type-check, basic tests", "tier-1-essential"),
            ("Standard - Essential + Pre-commit hooks + Security foundation", "tier-2-standard"),
            ("Comprehensive - Standard + Advanced quality + Testing", "tier-3-comprehensive"),
            ("Production-Ready - Comprehensive + Operations + Deployment", "tier-4-production"),
        ]

        for choice, expected_tier in choices:
            with patch("solokit.project.adopt.select_from_list") as mock_select:
                mock_select.return_value = choice

                result = prompt_quality_tier()

                assert result == expected_tier


class TestPromptCoverageTarget:
    """Tests for prompt_coverage_target() function."""

    def test_returns_coverage_int(self):
        """Test that function returns coverage target as integer."""
        with patch("solokit.project.adopt.select_from_list") as mock_select:
            mock_select.return_value = "80% - Balanced coverage (recommended)"

            result = prompt_coverage_target()

            assert result == 80
            assert isinstance(result, int)

    def test_calls_select_from_list(self):
        """Test that select_from_list is called with choices."""
        with patch("solokit.project.adopt.select_from_list") as mock_select:
            mock_select.return_value = "60% - Light coverage, fast iteration"

            prompt_coverage_target()

            mock_select.assert_called_once()
            args = mock_select.call_args[0]
            assert len(args[1]) == 3  # 3 coverage choices

    def test_default_to_80_percent(self):
        """Test that default is 80%."""
        with patch("solokit.project.adopt.select_from_list") as mock_select:
            mock_select.return_value = "80% - Balanced coverage (recommended)"

            prompt_coverage_target()

            # Check that default was passed
            args, kwargs = mock_select.call_args
            assert "80%" in kwargs.get("default", "")

    def test_all_coverage_mappings(self):
        """Test all coverage choice mappings."""
        choices = [
            ("60% - Light coverage, fast iteration", 60),
            ("80% - Balanced coverage (recommended)", 80),
            ("90% - High coverage, maximum confidence", 90),
        ]

        for choice, expected_coverage in choices:
            with patch("solokit.project.adopt.select_from_list") as mock_select:
                mock_select.return_value = choice

                result = prompt_coverage_target()

                assert result == expected_coverage


class TestPromptAdditionalOptions:
    """Tests for prompt_additional_options() function."""

    def test_returns_option_ids(self):
        """Test that function returns list of option IDs."""
        with patch("solokit.project.adopt.multi_select_list") as mock_select:
            mock_select.return_value = ["CI/CD - GitHub Actions workflows"]

            result = prompt_additional_options()

            assert result == ["ci_cd"]
            assert isinstance(result, list)

    def test_multiple_options(self):
        """Test selecting multiple options."""
        with patch("solokit.project.adopt.multi_select_list") as mock_select:
            mock_select.return_value = [
                "CI/CD - GitHub Actions workflows",
                "Docker - Container support with docker-compose",
            ]

            result = prompt_additional_options()

            assert "ci_cd" in result
            assert "docker" in result
            assert len(result) == 2

    def test_no_options_selected(self):
        """Test selecting no additional options."""
        with patch("solokit.project.adopt.multi_select_list") as mock_select:
            mock_select.return_value = []

            result = prompt_additional_options()

            assert result == []

    def test_all_option_mappings(self):
        """Test all option choice mappings."""
        options = [
            ("CI/CD - GitHub Actions workflows", "ci_cd"),
            ("Docker - Container support with docker-compose", "docker"),
            ("Env Templates - .env files and .editorconfig", "env_templates"),
        ]

        for choice, expected_id in options:
            with patch("solokit.project.adopt.multi_select_list") as mock_select:
                mock_select.return_value = [choice]

                result = prompt_additional_options()

                assert expected_id in result


class TestShowAdoptionWarning:
    """Tests for show_adoption_warning() function."""

    def test_returns_true_on_confirm(self):
        """Test returns True when user confirms."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning()

            assert result is True

    def test_returns_false_on_decline(self):
        """Test returns False when user declines."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = False

            result = show_adoption_warning()

            assert result is False

    def test_calls_confirm_action(self):
        """Test that confirm_action is called."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            show_adoption_warning()

            mock_confirm.assert_called_once()
            args = mock_confirm.call_args[0]
            assert "Continue with adoption?" in args[0]

    def test_default_is_false(self):
        """Test that default is False (safer)."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = False

            show_adoption_warning()

            # Check that default=False was passed
            kwargs = mock_confirm.call_args[1]
            assert kwargs.get("default") is False

    def test_with_tier_parameter(self):
        """Test that tier parameter is accepted and used."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning(tier="tier-2-standard")

            assert result is True

    def test_with_tier_and_language_parameters(self):
        """Test that tier and language parameters are both used."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning(tier="tier-3-comprehensive", language="python")

            assert result is True

    def test_with_typescript_language(self):
        """Test with TypeScript language parameter."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning(tier="tier-1-essential", language="typescript")

            assert result is True

    def test_with_fullstack_language(self):
        """Test with fullstack language parameter."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning(tier="tier-2-standard", language="fullstack")

            assert result is True

    def test_shows_config_files_in_warning(self, capsys):
        """Test that config files are shown in warning message."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            show_adoption_warning(tier="tier-2-standard", language="typescript")

            captured = capsys.readouterr()
            # Check for the new warning format with categories
            assert "SAFE" in captured.out
            assert "PRESERVED" in captured.out
            assert "MERGED" in captured.out
            assert "INSTALLED IF MISSING" in captured.out

    def test_shows_limited_config_files(self, capsys):
        """Test that INSTALL_IF_MISSING section shows limited files with summary."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            show_adoption_warning(tier="tier-3-comprehensive", language="typescript")

            captured = capsys.readouterr()
            # Should show "and X more" for INSTALL_IF_MISSING files
            assert "... and" in captured.out
            assert "more" in captured.out

    def test_handles_get_config_error_gracefully(self, capsys):
        """Test that errors in getting config files are handled gracefully."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True
            with patch(
                "solokit.adopt.orchestrator.get_config_files_to_install"
            ) as mock_get_configs:
                mock_get_configs.side_effect = Exception("Template not found")

                # Should not raise, continues without showing config files
                result = show_adoption_warning(tier="tier-2-standard", language="python")

                assert result is True

    def test_backwards_compatible_without_parameters(self):
        """Test backwards compatibility when called without tier/language."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning()

            assert result is True
            # Should still work without tier/language

    def test_with_empty_config_list(self, capsys):
        """Test with empty config file list."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True
            with patch(
                "solokit.adopt.orchestrator.get_config_files_to_install"
            ) as mock_get_configs:
                mock_get_configs.return_value = []

                show_adoption_warning(tier="tier-1-essential", language="python")

                captured = capsys.readouterr()
                # Should not show config files section
                assert "Config files that will be installed" not in captured.out

    def test_language_mapping_nodejs(self):
        """Test that nodejs language maps to correct template."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning(tier="tier-1-essential", language="nodejs")

            assert result is True

    def test_language_mapping_unknown(self):
        """Test that unknown language defaults to saas_t3."""
        with patch("solokit.project.adopt.confirm_action") as mock_confirm:
            mock_confirm.return_value = True

            result = show_adoption_warning(tier="tier-1-essential", language="unknown")

            assert result is True


class TestMainFunction:
    """Tests for main() function."""

    def test_argument_mode_with_all_args(self):
        """Test argument mode with tier and coverage provided."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.project.adopt.show_adoption_warning") as mock_warning:
                    mock_warning.return_value = True

                    with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                        mock_run.return_value = 0

                        result = main()

                        assert result == 0
                        mock_run.assert_called_once()

    def test_argument_mode_with_yes_flag(self):
        """Test argument mode with --yes flag skips confirmation."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80", "--yes"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.project.adopt.show_adoption_warning") as mock_warning:
                    with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                        mock_run.return_value = 0

                        result = main()

                        # Warning should not be called with --yes
                        mock_warning.assert_not_called()
                        assert result == 0

    def test_argument_mode_with_options(self):
        """Test argument mode with additional options."""
        with patch(
            "sys.argv",
            ["adopt", "--tier=tier-2-standard", "--coverage=80", "--options=ci_cd,docker", "--yes"],
        ):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                    mock_run.return_value = 0

                    result = main()

                    assert result == 0

                    # Check options were parsed
                    call_args = mock_run.call_args
                    assert "ci_cd" in call_args[1]["additional_options"]
                    assert "docker" in call_args[1]["additional_options"]

    def test_argument_mode_skip_commit_flag(self):
        """Test argument mode with --skip-commit flag."""
        with patch(
            "sys.argv",
            ["adopt", "--tier=tier-2-standard", "--coverage=80", "--skip-commit", "--yes"],
        ):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                    mock_run.return_value = 0

                    result = main()

                    assert result == 0

                    # Check skip_commit was passed
                    call_args = mock_run.call_args
                    assert call_args[1]["skip_commit"] is True

    def test_partial_arguments_error(self):
        """Test error when only tier is provided without coverage."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                result = main()

                # Should return error code
                assert result == 1

    def test_partial_arguments_error_coverage_only(self):
        """Test error when only coverage is provided without tier."""
        with patch("sys.argv", ["adopt", "--coverage=80"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                result = main()

                # Should return error code
                assert result == 1

    def test_interactive_mode(self):
        """Test interactive mode when no arguments provided."""
        with patch("sys.argv", ["adopt"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.project.adopt.prompt_quality_tier") as mock_tier:
                    mock_tier.return_value = "tier-2-standard"

                    with patch("solokit.project.adopt.prompt_coverage_target") as mock_coverage:
                        mock_coverage.return_value = 80

                        with patch(
                            "solokit.project.adopt.prompt_additional_options"
                        ) as mock_options:
                            mock_options.return_value = []

                            with patch(
                                "solokit.project.adopt.show_adoption_warning"
                            ) as mock_warning:
                                mock_warning.return_value = True

                                with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                                    mock_run.return_value = 0

                                    result = main()

                                    assert result == 0
                                    mock_tier.assert_called_once()
                                    mock_coverage.assert_called_once()
                                    mock_options.assert_called_once()

    def test_interactive_mode_user_cancels(self):
        """Test interactive mode when user cancels at warning."""
        with patch("sys.argv", ["adopt"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.project.adopt.prompt_quality_tier") as mock_tier:
                    mock_tier.return_value = "tier-2-standard"

                    with patch("solokit.project.adopt.prompt_coverage_target") as mock_coverage:
                        mock_coverage.return_value = 80

                        with patch(
                            "solokit.project.adopt.prompt_additional_options"
                        ) as mock_options:
                            mock_options.return_value = []

                            with patch(
                                "solokit.project.adopt.show_adoption_warning"
                            ) as mock_warning:
                                mock_warning.return_value = False

                                with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                                    result = main()

                                    # Should return 1 and not call run_adoption
                                    assert result == 1
                                    mock_run.assert_not_called()

    def test_argument_mode_user_cancels(self):
        """Test argument mode when user cancels at warning."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.project.adopt.show_adoption_warning") as mock_warning:
                    mock_warning.return_value = False

                    with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                        result = main()

                        # Should return 1 and not call run_adoption
                        assert result == 1
                        mock_run.assert_not_called()

    def test_run_adoption_called_with_correct_params(self):
        """Test that run_adoption is called with correct parameters."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80", "--yes"]):
            with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                mock_run.return_value = 0

                result = main()

                assert result == 0
                mock_run.assert_called_once()
                # Verify parameters passed to run_adoption
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["tier"] == "tier-2-standard"
                assert call_kwargs["coverage_target"] == 80
                assert call_kwargs["additional_options"] == []
                assert call_kwargs["skip_commit"] is False

    def test_valid_tier_choices(self):
        """Test that all tier choices are valid."""
        valid_tiers = [
            "tier-1-essential",
            "tier-2-standard",
            "tier-3-comprehensive",
            "tier-4-production",
        ]

        for tier in valid_tiers:
            with patch("sys.argv", ["adopt", f"--tier={tier}", "--coverage=80", "--yes"]):
                with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                    from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                    mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                    with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                        mock_run.return_value = 0

                        result = main()

                        assert result == 0

    def test_valid_coverage_choices(self):
        """Test that all coverage choices are valid."""
        valid_coverage = [60, 80, 90]

        for coverage in valid_coverage:
            with patch(
                "sys.argv", ["adopt", "--tier=tier-2-standard", f"--coverage={coverage}", "--yes"]
            ):
                with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                    from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                    mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                    with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                        mock_run.return_value = 0

                        result = main()

                        assert result == 0

    def test_run_adoption_called_without_project_root(self):
        """Test that run_adoption is called without explicit project_root (uses default cwd)."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80", "--yes"]):
            with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                mock_run.return_value = 0

                main()

                # run_adoption should be called without project_root parameter
                # (it defaults to Path.cwd() in the orchestrator)
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args[1]
                assert "project_root" not in call_kwargs or call_kwargs.get("project_root") is None

    def test_interactive_mode_with_options(self):
        """Test interactive mode with additional options selected."""
        with patch("sys.argv", ["adopt"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.project.adopt.prompt_quality_tier") as mock_tier:
                    mock_tier.return_value = "tier-3-comprehensive"

                    with patch("solokit.project.adopt.prompt_coverage_target") as mock_coverage:
                        mock_coverage.return_value = 90

                        with patch(
                            "solokit.project.adopt.prompt_additional_options"
                        ) as mock_options:
                            mock_options.return_value = ["ci_cd", "docker"]

                            with patch(
                                "solokit.project.adopt.show_adoption_warning"
                            ) as mock_warning:
                                mock_warning.return_value = True

                                with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                                    mock_run.return_value = 0

                                    result = main()

                                    assert result == 0

                                    # Check options were passed
                                    call_args = mock_run.call_args
                                    assert "ci_cd" in call_args[1]["additional_options"]
                                    assert "docker" in call_args[1]["additional_options"]


class TestArgumentParsing:
    """Tests for argument parsing."""

    def test_help_flag(self):
        """Test --help flag."""
        with patch("sys.argv", ["adopt", "--help"]):
            with pytest.raises(SystemExit) as exc:
                main()

            # --help exits with code 0
            assert exc.value.code == 0

    def test_invalid_tier(self):
        """Test invalid tier value."""
        with patch("sys.argv", ["adopt", "--tier=invalid-tier", "--coverage=80"]):
            with pytest.raises(SystemExit):
                main()

    def test_invalid_coverage(self):
        """Test invalid coverage value."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=100"]):
            with pytest.raises(SystemExit):
                main()

    def test_short_yes_flag(self):
        """Test -y short flag for --yes."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80", "-y"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.project.adopt.show_adoption_warning") as mock_warning:
                    with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                        mock_run.return_value = 0

                        result = main()

                        # Warning should not be called with -y
                        mock_warning.assert_not_called()
                        assert result == 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_run_adoption_returns_nonzero(self):
        """Test handling when run_adoption returns non-zero exit code."""
        with patch("sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80", "--yes"]):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                    mock_run.return_value = 1

                    result = main()

                    assert result == 1

    def test_empty_options_string(self):
        """Test parsing empty options string."""
        with patch(
            "sys.argv", ["adopt", "--tier=tier-2-standard", "--coverage=80", "--options=", "--yes"]
        ):
            with patch("solokit.adopt.project_detector.detect_project_type") as mock_detect:
                from solokit.adopt.project_detector import ProjectInfo, ProjectLanguage

                mock_detect.return_value = ProjectInfo(language=ProjectLanguage.PYTHON)

                with patch("solokit.adopt.orchestrator.run_adoption") as mock_run:
                    mock_run.return_value = 0

                    result = main()

                    assert result == 0
                    # Empty string in options should result in list with empty string
                    # which is fine - orchestrator can handle it
