"""
Tests for quality checkers base classes.

Validates CheckResult and QualityChecker abstract base class.
"""

from pathlib import Path

from solokit.quality.checkers.base import CheckResult, QualityChecker


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_check_result_details_with_warnings(self):
        """Test that CheckResult.details includes warnings when present."""
        result = CheckResult(
            checker_name="test-checker",
            passed=True,
            status="passed",
            errors=[],
            warnings=["Warning 1", "Warning 2"],
            info={"extra": "info"},
        )

        details = result.details
        assert "warnings" in details
        assert details["warnings"] == ["Warning 1", "Warning 2"]
        assert details["status"] == "passed"
        assert details["passed"] is True
        assert details["extra"] == "info"

    def test_check_result_details_without_warnings(self):
        """Test that CheckResult.details omits warnings when not present."""
        result = CheckResult(
            checker_name="test-checker", passed=True, status="passed", info={"extra": "info"}
        )

        details = result.details
        assert "warnings" not in details
        assert details["status"] == "passed"
        assert details["passed"] is True


class TestQualityChecker:
    """Tests for QualityChecker abstract base class."""

    def test_quality_checker_initialization(self):
        """Test QualityChecker initialization with concrete implementation."""

        class ConcreteChecker(QualityChecker):
            def name(self) -> str:
                return "concrete-checker"

            def is_enabled(self) -> bool:
                return True

            def run(self) -> CheckResult:
                return CheckResult(checker_name=self.name(), passed=True, status="passed")

        config = {"enabled": True}
        project_root = Path("/test/project")

        checker = ConcreteChecker(config, project_root)

        assert checker.config == config
        assert checker.project_root == project_root
        assert checker.name() == "concrete-checker"
        assert checker.is_enabled() is True

    def test_quality_checker_uses_cwd_when_project_root_none(self):
        """Test that QualityChecker uses cwd when project_root is None."""

        class ConcreteChecker(QualityChecker):
            def name(self) -> str:
                return "concrete-checker"

            def is_enabled(self) -> bool:
                return True

            def run(self) -> CheckResult:
                return CheckResult(checker_name=self.name(), passed=True, status="passed")

        config = {"enabled": True}

        checker = ConcreteChecker(config, None)

        assert checker.config == config
        assert checker.project_root == Path.cwd()

    def test_create_skipped_result(self):
        """Test _create_skipped_result helper method."""

        class ConcreteChecker(QualityChecker):
            def name(self) -> str:
                return "concrete-checker"

            def is_enabled(self) -> bool:
                return False

            def run(self) -> CheckResult:
                return self._create_skipped_result("not enabled")

        checker = ConcreteChecker({}, Path("/test/project"))
        result = checker._create_skipped_result("test reason")

        assert result.checker_name == "concrete-checker"
        assert result.passed is True
        assert result.status == "skipped"
        assert result.info["reason"] == "test reason"
        assert result.execution_time == 0.0
