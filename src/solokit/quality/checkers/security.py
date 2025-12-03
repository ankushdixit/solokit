#!/usr/bin/env python3
"""
Security vulnerability scanner.

Runs security scans using Bandit (Python) and Safety (Python dependencies),
or npm audit (JavaScript/TypeScript).
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import QUALITY_CHECK_LONG_TIMEOUT
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker

logger = get_logger(__name__)


class SecurityChecker(QualityChecker):
    """Security vulnerability scanning for Python and JavaScript/TypeScript."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        language: str | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize security checker.

        Args:
            config: Security configuration
            project_root: Project root directory
            language: Programming language (python, javascript, typescript)
            runner: Optional CommandRunner instance (for testing)
        """
        super().__init__(config, project_root)
        self.runner = (
            runner
            if runner is not None
            else CommandRunner(default_timeout=QUALITY_CHECK_LONG_TIMEOUT)
        )
        self.language = language or self._detect_language()

    def name(self) -> str:
        """Return checker name."""
        return "security"

    def is_enabled(self) -> bool:
        """Check if security scanning is enabled."""
        return bool(self.config.get("enabled", True))

    def _detect_language(self) -> str:
        """Detect primary project language."""
        if (self.project_root / "pyproject.toml").exists() or (
            self.project_root / "setup.py"
        ).exists():
            return "python"
        elif (self.project_root / "package.json").exists():
            if (self.project_root / "tsconfig.json").exists():
                return "typescript"
            return "javascript"
        return "python"  # default

    def run(self) -> CheckResult:
        """Run security vulnerability scan."""
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result()

        logger.info(f"Running security scan for {self.language}")

        if self.language == "python":
            results = self._scan_python()
        elif self.language in ["javascript", "typescript"]:
            results = self._scan_javascript()
        else:
            return self._create_skipped_result(reason=f"unsupported language: {self.language}")

        # Check if passed based on fail_on threshold
        fail_on = self.config.get("fail_on", "high").upper()
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        if fail_on not in severity_levels:
            fail_on = "HIGH"

        fail_threshold = severity_levels.index(fail_on)

        passed = True
        for severity, count in results.get("by_severity", {}).items():
            if (
                severity in severity_levels
                and severity_levels.index(severity) >= fail_threshold
                and count > 0
            ):
                passed = False
                break

        execution_time = time.time() - start_time

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=results.get("vulnerabilities", []),
            warnings=[],
            info={
                "by_severity": results.get("by_severity", {}),
                "fail_threshold": fail_on,
                "language": self.language,
            },
            execution_time=execution_time,
        )

    def _scan_python(self) -> dict[str, Any]:
        """Run Python security scans (Bandit + Safety)."""
        results: dict[str, Any] = {"vulnerabilities": [], "by_severity": {}}

        # Run Bandit
        bandit_results = self._run_bandit()
        if bandit_results:
            results["bandit"] = bandit_results
            # Count by severity
            for issue in bandit_results.get("results", []):
                severity = issue.get("issue_severity", "LOW")
                results["by_severity"][severity] = results["by_severity"].get(severity, 0) + 1
                # Add to vulnerabilities list
                results["vulnerabilities"].append(
                    {
                        "source": "bandit",
                        "file": issue.get("filename", ""),
                        "line": issue.get("line_number", 0),
                        "issue": issue.get("issue_text", ""),
                        "severity": severity,
                        "confidence": issue.get("issue_confidence", ""),
                    }
                )

        # Run Safety
        safety_results = self._run_safety()
        if safety_results:
            results["safety"] = safety_results
            results["vulnerabilities"].extend(safety_results)

        return results

    def _run_bandit(self) -> dict[str, Any] | None:
        """Run Bandit security scanner."""
        try:
            # Create temporary file for report
            fd, bandit_report_path = tempfile.mkstemp(suffix=".json")
            os.close(fd)

            try:
                src_dir = self.project_root / "src"
                if not src_dir.exists():
                    logger.debug("No src/ directory found, skipping Bandit")
                    return None

                # Build bandit command
                bandit_cmd = [
                    "bandit",
                    "-r",
                    str(src_dir),
                    "-f",
                    "json",
                    "-o",
                    bandit_report_path,
                ]

                # Use pyproject.toml config if it exists
                pyproject_path = self.project_root / "pyproject.toml"
                if pyproject_path.exists():
                    bandit_cmd.extend(["-c", str(pyproject_path)])

                self.runner.run(
                    bandit_cmd,
                    timeout=QUALITY_CHECK_LONG_TIMEOUT,
                )

                if Path(bandit_report_path).exists():
                    try:
                        with open(bandit_report_path) as f:
                            content = f.read().strip()
                            if content:
                                return json.loads(content)  # type: ignore[no-any-return]
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse bandit report: {e}")
                    except OSError as e:
                        logger.warning(f"Failed to read bandit report: {e}")
            finally:
                # Clean up temporary file
                try:
                    Path(bandit_report_path).unlink()
                except OSError:
                    pass

        except (ImportError, OSError) as e:
            logger.debug(f"Bandit not available: {e}")

        return None

    def _run_safety(self) -> list[dict[str, Any]]:
        """Run Safety dependency scanner."""
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            logger.debug("No requirements.txt found, skipping Safety")
            return []

        result = self.runner.run(
            ["safety", "check", "--file", str(requirements_file), "--json"],
            timeout=QUALITY_CHECK_LONG_TIMEOUT,
        )

        if result.success and result.stdout:
            try:
                # Safety may prefix JSON with deprecation warnings, so find the first JSON marker
                json_start = min(
                    (
                        pos
                        for pos in [result.stdout.find("{"), result.stdout.find("[")]
                        if pos != -1
                    ),
                    default=-1,
                )
                if json_start != -1:
                    return json.loads(result.stdout[json_start:])  # type: ignore[no-any-return]
                return json.loads(result.stdout)  # type: ignore[no-any-return]
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse safety output: {e}")
                logger.debug(f"Safety output: {result.stdout[:200]}")

        return []

    def _scan_javascript(self) -> dict[str, Any]:
        """Run JavaScript/TypeScript security scans (npm audit)."""
        results: dict[str, Any] = {"vulnerabilities": [], "by_severity": {}}

        package_json = self.project_root / "package.json"
        if not package_json.exists():
            logger.debug("No package.json found, skipping npm audit")
            return results

        audit_result = self.runner.run(
            ["npm", "audit", "--json"], timeout=QUALITY_CHECK_LONG_TIMEOUT
        )

        if audit_result.success and audit_result.stdout:
            try:
                audit_data = json.loads(audit_result.stdout)
                results["npm_audit"] = audit_data

                # Count by severity
                for vuln in audit_data.get("vulnerabilities", {}).values():
                    severity = vuln.get("severity", "low").upper()
                    results["by_severity"][severity] = results["by_severity"].get(severity, 0) + 1

            except json.JSONDecodeError:
                logger.warning("Failed to parse npm audit output")

        return results
