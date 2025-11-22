"""
Tests for project/init.py main() function.

Validates CLI argument parsing and routing logic.

Run tests:
    pytest tests/unit/init/test_init_main.py -v

Target: 90%+ coverage
"""

import sys
from unittest.mock import patch

import pytest

from solokit.project.init import main


class TestMain:
    """Tests for main() function."""

    def test_template_based_init_with_all_args(self):
        """Test template-based init with all required arguments."""
        test_args = [
            "init",
            "--template=saas_t3",
            "--tier=tier-2-standard",
            "--coverage=80",
            "--options=ci_cd,docker",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_run:
                mock_run.return_value = 0

                result = main()

                assert result == 0
                mock_run.assert_called_once_with(
                    template_id="saas_t3",
                    tier="tier-2-standard",
                    coverage_target=80,
                    additional_options=["ci_cd", "docker"],
                )

    def test_template_without_tier_returns_error(self):
        """Test that --template requires --tier."""
        test_args = ["init", "--template=saas_t3", "--coverage=80"]

        with patch.object(sys, "argv", test_args):
            result = main()

            assert result == 1

    def test_template_without_coverage_returns_error(self):
        """Test that --template requires --coverage."""
        test_args = ["init", "--template=saas_t3", "--tier=tier-1-essential"]

        with patch.object(sys, "argv", test_args):
            result = main()

            assert result == 1

    def test_interactive_init_without_args(self):
        """Test interactive init when no arguments are provided."""
        test_args = ["init"]

        with patch.object(sys, "argv", test_args):
            with patch("solokit.project.init.prompt_template_selection", return_value="saas_t3"):
                with patch(
                    "solokit.project.init.prompt_quality_tier", return_value="tier-2-standard"
                ):
                    with patch("solokit.project.init.prompt_coverage_target", return_value=80):
                        with patch(
                            "solokit.project.init.prompt_additional_options", return_value=["ci_cd"]
                        ):
                            with patch(
                                "solokit.project.init.confirm_action", return_value=True
                            ):  # Confirm prompt
                                with patch(
                                    "solokit.init.orchestrator.run_template_based_init"
                                ) as mock_run:
                                    mock_run.return_value = 0

                                    result = main()

                                    assert result == 0
                                    mock_run.assert_called_once_with(
                                        template_id="saas_t3",
                                        tier="tier-2-standard",
                                        coverage_target=80,
                                        additional_options=["ci_cd"],
                                    )

    def test_parse_multiple_options(self):
        """Test parsing multiple additional options."""
        test_args = [
            "init",
            "--template=saas_t3",
            "--tier=tier-1-essential",
            "--coverage=60",
            "--options=ci_cd,docker,env_templates",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_run:
                mock_run.return_value = 0

                main()

                call_args = mock_run.call_args
                assert call_args[1]["additional_options"] == [
                    "ci_cd",
                    "docker",
                    "env_templates",
                ]

    def test_template_choices_validation(self):
        """Test that template choices are validated by argparse."""
        test_args = [
            "init",
            "--template=invalid_template",
            "--tier=tier-1-essential",
            "--coverage=60",
        ]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit):
                # argparse will exit with error for invalid choice
                main()

    def test_tier_choices_validation(self):
        """Test that tier choices are validated by argparse."""
        test_args = ["init", "--template=saas_t3", "--tier=invalid_tier", "--coverage=60"]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit):
                main()

    def test_coverage_as_integer(self):
        """Test that coverage is parsed as integer."""
        test_args = [
            "init",
            "--template=saas_t3",
            "--tier=tier-1-essential",
            "--coverage=90",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_run:
                mock_run.return_value = 0

                main()

                call_args = mock_run.call_args
                assert call_args[1]["coverage_target"] == 90
                assert isinstance(call_args[1]["coverage_target"], int)

    def test_options_whitespace_stripped(self):
        """Test that whitespace in options is stripped."""
        test_args = [
            "init",
            "--template=saas_t3",
            "--tier=tier-1-essential",
            "--coverage=60",
            "--options=ci_cd , docker , env_templates",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_run:
                mock_run.return_value = 0

                main()

                call_args = mock_run.call_args
                assert call_args[1]["additional_options"] == ["ci_cd", "docker", "env_templates"]

    def test_no_options_passed(self):
        """Test when no additional options are provided."""
        test_args = [
            "init",
            "--template=saas_t3",
            "--tier=tier-1-essential",
            "--coverage=60",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_run:
                mock_run.return_value = 0

                main()

                call_args = mock_run.call_args
                assert call_args[1]["additional_options"] == []
