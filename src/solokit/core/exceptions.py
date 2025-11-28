"""
Comprehensive exception hierarchy for Solokit.

Provides structured exceptions with error codes, categories, and context.
All business logic should raise these exceptions rather than returning error tuples.

Usage:
    from solokit.core.exceptions import WorkItemNotFoundError

    def get_work_item(item_id: str) -> WorkItem:
        if item_id not in work_items:
            raise WorkItemNotFoundError(item_id)
        return work_items[item_id]

    # CLI layer catches and formats
    try:
        item = get_work_item("invalid")
    except WorkItemNotFoundError as e:
        output.info(f"Error: {e}")
        output.info(f"Remediation: {e.remediation}")
        sys.exit(e.exit_code)
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from solokit.core.logging_config import get_logger
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


class ErrorCategory(Enum):
    """Error categories for classification and handling"""

    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    GIT = "git"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    TIMEOUT = "timeout"
    PERMISSION = "permission"


class ErrorCode(Enum):
    """Specific error codes for programmatic handling"""

    # Validation errors (1000-1999)
    INVALID_WORK_ITEM_ID = 1001
    INVALID_WORK_ITEM_TYPE = 1002
    MISSING_REQUIRED_FIELD = 1003
    INVALID_JSON = 1004
    SPEC_VALIDATION_FAILED = 1005
    INVALID_STATUS = 1006
    INVALID_PRIORITY = 1007
    INVALID_COMMAND = 1008
    PROJECT_NOT_BLANK = 1009
    INVALID_CONFIGURATION = 1010

    # Not found errors (2000-2999)
    WORK_ITEM_NOT_FOUND = 2001
    FILE_NOT_FOUND = 2002
    SESSION_NOT_FOUND = 2003
    LEARNING_NOT_FOUND = 2004
    CONFIG_NOT_FOUND = 2005

    # Already exists errors (3000-3999)
    WORK_ITEM_ALREADY_EXISTS = 3001
    FILE_ALREADY_EXISTS = 3002
    SESSION_ALREADY_ACTIVE = 3003

    # Configuration errors (4000-4999)
    CONFIG_FILE_MISSING = 4001
    CONFIG_VALIDATION_FAILED = 4002
    SCHEMA_MISSING = 4003
    INVALID_CONFIG_VALUE = 4004

    # System errors (5000-5999)
    FILE_OPERATION_FAILED = 5001
    SUBPROCESS_FAILED = 5002
    IMPORT_FAILED = 5003
    COMMAND_FAILED = 5004
    MODULE_NOT_FOUND = 5005
    FUNCTION_NOT_FOUND = 5006

    # Git errors (6000-6999)
    NOT_A_GIT_REPO = 6001
    GIT_NOT_FOUND = 6002
    WORKING_DIR_NOT_CLEAN = 6003
    GIT_COMMAND_FAILED = 6004
    BRANCH_NOT_FOUND = 6005
    BRANCH_ALREADY_EXISTS = 6006

    # Dependency errors (7000-7999)
    CIRCULAR_DEPENDENCY = 7001
    UNMET_DEPENDENCY = 7002

    # Security errors (8000-8999)
    SECURITY_SCAN_FAILED = 8001
    VULNERABILITY_FOUND = 8002

    # Timeout errors (9000-9999)
    OPERATION_TIMEOUT = 9001
    SUBPROCESS_TIMEOUT = 9002

    # Quality gate errors (10000-10999)
    TEST_FAILED = 10001
    LINT_FAILED = 10002
    COVERAGE_BELOW_THRESHOLD = 10003
    QUALITY_GATE_FAILED = 10004

    # Deployment errors (11000-11999)
    DEPLOYMENT_FAILED = 11001
    PRE_DEPLOYMENT_CHECK_FAILED = 11002
    SMOKE_TEST_FAILED = 11003
    ROLLBACK_FAILED = 11004
    DEPLOYMENT_STEP_FAILED = 11005

    # API validation errors (12000-12999)
    API_VALIDATION_FAILED = 12001
    SCHEMA_VALIDATION_FAILED = 12002
    CONTRACT_VIOLATION = 12003
    BREAKING_CHANGE_DETECTED = 12004
    INVALID_OPENAPI_SPEC = 12005

    # Performance testing errors (13000-13999)
    PERFORMANCE_TEST_FAILED = 13001
    BENCHMARK_FAILED = 13002
    PERFORMANCE_REGRESSION = 13003
    LOAD_TEST_FAILED = 13004


class SolokitError(Exception):
    """
    Base exception for all Solokit errors.

    Attributes:
        message: Human-readable error message
        code: ErrorCode enum for programmatic handling
        category: ErrorCategory enum for classification
        context: Additional context data (file paths, IDs, etc.)
        remediation: Suggested fix for the user
        cause: Original exception if wrapping another error
        exit_code: Suggested exit code for CLI

    Example:
        >>> error = SolokitError(
        ...     message="Something went wrong",
        ...     code=ErrorCode.FILE_OPERATION_FAILED,
        ...     category=ErrorCategory.SYSTEM,
        ...     context={"file": "/path/to/file"},
        ...     remediation="Check file permissions"
        ... )
        >>> print(error.to_dict())
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        category: ErrorCategory,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.category = category
        self.context = context or {}
        self.remediation = remediation
        self.cause = cause

    @property
    def exit_code(self) -> int:
        """Get CLI exit code based on error category"""
        exit_codes = {
            ErrorCategory.VALIDATION: 2,
            ErrorCategory.NOT_FOUND: 3,
            ErrorCategory.CONFIGURATION: 4,
            ErrorCategory.SYSTEM: 5,
            ErrorCategory.GIT: 6,
            ErrorCategory.DEPENDENCY: 7,
            ErrorCategory.SECURITY: 8,
            ErrorCategory.TIMEOUT: 9,
            ErrorCategory.ALREADY_EXISTS: 10,
            ErrorCategory.PERMISSION: 11,
        }
        return exit_codes.get(self.category, 1)

    def __str__(self) -> str:
        """Format error for display"""
        parts = [self.message]
        if self.remediation:
            parts.append(f"Remediation: {self.remediation}")
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for structured logging"""
        return {
            "message": self.message,
            "code": self.code.value,
            "code_name": self.code.name,
            "category": self.category.value,
            "context": self.context,
            "remediation": self.remediation,
            "cause": str(self.cause) if self.cause else None,
            "exit_code": self.exit_code,
        }


# ============================================================================
# Validation Errors
# ============================================================================


class ValidationError(SolokitError):
    """
    Raised when validation fails.

    Example:
        >>> raise ValidationError(
        ...     message="Invalid work item ID format",
        ...     code=ErrorCode.INVALID_WORK_ITEM_ID,
        ...     context={"work_item_id": "bad-id!"},
        ...     remediation="Use alphanumeric characters and underscores only"
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.MISSING_REQUIRED_FIELD,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class SpecValidationError(ValidationError):
    """
    Raised when spec file validation fails.

    Example:
        >>> raise SpecValidationError(
        ...     work_item_id="my_feature",
        ...     errors=["Missing Overview section", "Missing acceptance criteria"]
        ... )
    """

    def __init__(self, work_item_id: str, errors: list[str], remediation: str | None = None):
        message = f"Spec validation failed for '{work_item_id}'"
        context = {
            "work_item_id": work_item_id,
            "validation_errors": errors,
            "error_count": len(errors),
        }
        super().__init__(
            message=message,
            code=ErrorCode.SPEC_VALIDATION_FAILED,
            context=context,
            remediation=remediation
            or f"Edit .session/specs/{work_item_id}.md to fix validation errors",
        )


# ============================================================================
# Not Found Errors
# ============================================================================


class NotFoundError(SolokitError):
    """
    Raised when a resource is not found.

    Example:
        >>> raise NotFoundError(
        ...     message="Configuration file not found",
        ...     code=ErrorCode.CONFIG_NOT_FOUND,
        ...     context={"path": ".session/config.json"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.NOT_FOUND,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class WorkItemNotFoundError(NotFoundError):
    """
    Raised when work item doesn't exist.

    Example:
        >>> raise WorkItemNotFoundError("nonexistent_feature")
    """

    def __init__(self, work_item_id: str):
        super().__init__(
            message=f"Work item '{work_item_id}' not found",
            code=ErrorCode.WORK_ITEM_NOT_FOUND,
            context={"work_item_id": work_item_id},
            remediation="Use '/work-list' to see available work items",
        )


class FileNotFoundError(NotFoundError):
    """
    Raised when a required file doesn't exist.

    Note: This shadows the built-in FileNotFoundError, but provides
    more structured error information.

    Example:
        >>> raise FileNotFoundError(
        ...     file_path=".session/specs/my_feature.md",
        ...     file_type="spec"
        ... )
    """

    def __init__(self, file_path: str, file_type: str | None = None):
        context = {"file_path": file_path}
        if file_type:
            context["file_type"] = file_type

        remediation_msg = None
        if file_type:
            remediation_msg = f"Create the missing {file_type} file: {file_path}"

        super().__init__(
            message=f"File not found: {file_path}",
            code=ErrorCode.FILE_NOT_FOUND,
            context=context,
            remediation=remediation_msg,
        )


class SessionNotFoundError(NotFoundError):
    """
    Raised when no active session exists.

    Example:
        >>> raise SessionNotFoundError()
    """

    def __init__(self) -> None:
        super().__init__(
            message="No active session found",
            code=ErrorCode.SESSION_NOT_FOUND,
            remediation="Start a session with '/start' or '/start <work_item_id>'",
        )


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(SolokitError):
    """
    Raised when configuration is invalid.

    Example:
        >>> raise ConfigurationError(
        ...     message="Invalid configuration value",
        ...     code=ErrorCode.INVALID_CONFIG_VALUE,
        ...     context={"key": "test_command", "value": None}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CONFIG_VALIDATION_FAILED,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.CONFIGURATION,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class ConfigValidationError(ConfigurationError):
    """
    Raised when config fails schema validation.

    Example:
        >>> raise ConfigValidationError(
        ...     config_path=".session/config.json",
        ...     errors=["Missing 'project_name' field"]
        ... )
    """

    def __init__(self, config_path: str, errors: list[str]):
        message = f"Configuration validation failed: {config_path}"
        context = {
            "config_path": config_path,
            "validation_errors": errors,
            "error_count": len(errors),
        }
        super().__init__(
            message=message,
            code=ErrorCode.CONFIG_VALIDATION_FAILED,
            context=context,
            remediation="Check docs/guides/configuration.md for valid configuration options",
        )


# ============================================================================
# Git Errors
# ============================================================================


class GitError(SolokitError):
    """
    Raised for git-related errors.

    Example:
        >>> raise GitError(
        ...     message="Git command failed",
        ...     code=ErrorCode.GIT_COMMAND_FAILED,
        ...     context={"command": "git status"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.GIT,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class NotAGitRepoError(GitError):
    """
    Raised when operation requires git repo but not in one.

    Example:
        >>> raise NotAGitRepoError()
    """

    def __init__(self, path: str | None = None):
        context = {"path": path} if path else {}
        super().__init__(
            message="Not a git repository",
            code=ErrorCode.NOT_A_GIT_REPO,
            context=context,
            remediation="Run 'git init' to initialize a repository",
        )


class WorkingDirNotCleanError(GitError):
    """
    Raised when working directory has uncommitted changes.

    Example:
        >>> raise WorkingDirNotCleanError(
        ...     changes=["M src/file.py", "?? new_file.py"]
        ... )
    """

    def __init__(self, changes: list[str] | None = None):
        context = {"uncommitted_changes": changes} if changes else {}
        super().__init__(
            message="Working directory not clean (uncommitted changes)",
            code=ErrorCode.WORKING_DIR_NOT_CLEAN,
            context=context,
            remediation="Commit or stash changes before proceeding",
        )


class BranchNotFoundError(GitError):
    """
    Raised when git branch doesn't exist.

    Example:
        >>> raise BranchNotFoundError("feature-branch")
    """

    def __init__(self, branch_name: str):
        super().__init__(
            message=f"Branch '{branch_name}' not found",
            code=ErrorCode.BRANCH_NOT_FOUND,
            context={"branch_name": branch_name},
            remediation="Check branch name or create it with 'git checkout -b <branch>'",
        )


# ============================================================================
# System Errors
# ============================================================================


class SystemError(SolokitError):
    """
    Raised for system-level errors.

    Example:
        >>> raise SystemError(
        ...     message="Failed to write file",
        ...     code=ErrorCode.FILE_OPERATION_FAILED,
        ...     context={"path": "/tmp/file.txt"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.SYSTEM,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class SubprocessError(SystemError):
    """
    Raised when subprocess command fails.

    Example:
        >>> raise SubprocessError(
        ...     command="pytest tests/",
        ...     returncode=1,
        ...     stderr="FAILED tests/test_foo.py"
        ... )
    """

    def __init__(
        self, command: str, returncode: int, stderr: str | None = None, stdout: str | None = None
    ):
        context = {"command": command, "returncode": returncode, "stderr": stderr, "stdout": stdout}
        super().__init__(
            message=f"Command failed with exit code {returncode}: {command}",
            code=ErrorCode.SUBPROCESS_FAILED,
            context=context,
        )


class TimeoutError(SystemError):
    """
    Raised when operation times out.

    Example:
        >>> raise TimeoutError(
        ...     operation="git fetch",
        ...     timeout_seconds=30
        ... )
    """

    def __init__(self, operation: str, timeout_seconds: int, context: dict[str, Any] | None = None):
        ctx = context or {}
        ctx.update({"operation": operation, "timeout_seconds": timeout_seconds})
        super().__init__(
            message=f"Operation timed out after {timeout_seconds}s: {operation}",
            code=ErrorCode.OPERATION_TIMEOUT,
            context=ctx,
        )


class CommandExecutionError(SystemError):
    """
    Raised when a command execution fails.

    This wraps the CommandExecutionError from command_runner for consistency.

    Example:
        >>> raise CommandExecutionError(
        ...     command="npm test",
        ...     returncode=1,
        ...     stderr="Test failed"
        ... )
    """

    def __init__(
        self,
        command: str,
        returncode: int | None = None,
        stderr: str | None = None,
        stdout: str | None = None,
        exit_code: int | None = None,
        context: dict[str, Any] | None = None,
    ):
        # Support both returncode and exit_code for backwards compatibility
        actual_code = exit_code if exit_code is not None else returncode

        # Merge provided context with command details
        ctx = context or {}
        ctx.update(
            {
                "command": command,
                "returncode": actual_code,
                "stderr": stderr,
                "stdout": stdout,
            }
        )

        super().__init__(
            message=f"Command execution failed: {command}",
            code=ErrorCode.COMMAND_FAILED,
            context=ctx,
        )
        # Store returncode for easy access (can't override exit_code which is a property)
        self.returncode = actual_code
        # Store stderr and stdout for easy access
        self.stderr = stderr
        self.stdout = stdout


# ============================================================================
# Dependency Errors
# ============================================================================


class DependencyError(SolokitError):
    """
    Raised for dependency-related errors.

    Example:
        >>> raise DependencyError(
        ...     message="Dependency not met",
        ...     code=ErrorCode.UNMET_DEPENDENCY,
        ...     context={"dependency": "feature_a"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.DEPENDENCY,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class CircularDependencyError(DependencyError):
    """
    Raised when circular dependency detected.

    Example:
        >>> raise CircularDependencyError(["feature_a", "feature_b", "feature_a"])
    """

    def __init__(self, cycle: list[str]):
        cycle_str = " -> ".join(cycle)
        super().__init__(
            message=f"Circular dependency detected: {cycle_str}",
            code=ErrorCode.CIRCULAR_DEPENDENCY,
            context={"cycle": cycle},
            remediation="Break the dependency cycle by reordering work items",
        )


class UnmetDependencyError(DependencyError):
    """
    Raised when dependency not met.

    Example:
        >>> raise UnmetDependencyError("feature_b", "feature_a")
    """

    def __init__(self, work_item_id: str, dependency_id: str):
        super().__init__(
            message=f"Cannot start '{work_item_id}': dependency '{dependency_id}' not completed",
            code=ErrorCode.UNMET_DEPENDENCY,
            context={"work_item_id": work_item_id, "dependency_id": dependency_id},
            remediation=f"Complete '{dependency_id}' before starting '{work_item_id}'",
        )


# ============================================================================
# Already Exists Errors
# ============================================================================


class AlreadyExistsError(SolokitError):
    """
    Raised when resource already exists.

    Example:
        >>> raise AlreadyExistsError(
        ...     message="Work item already exists",
        ...     code=ErrorCode.WORK_ITEM_ALREADY_EXISTS,
        ...     context={"work_item_id": "my_feature"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.ALREADY_EXISTS,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class SessionAlreadyActiveError(AlreadyExistsError):
    """
    Raised when trying to start session while one is active.

    Example:
        >>> raise SessionAlreadyActiveError("current_feature")
    """

    def __init__(self, current_work_item_id: str):
        super().__init__(
            message=f"Session already active for '{current_work_item_id}'",
            code=ErrorCode.SESSION_ALREADY_ACTIVE,
            context={"current_work_item_id": current_work_item_id},
            remediation="Complete current session with '/end' before starting a new one",
        )


class WorkItemAlreadyExistsError(AlreadyExistsError):
    """
    Raised when trying to create work item that already exists.

    Example:
        >>> raise WorkItemAlreadyExistsError("my_feature")
    """

    def __init__(self, work_item_id: str):
        super().__init__(
            message=f"Work item '{work_item_id}' already exists",
            code=ErrorCode.WORK_ITEM_ALREADY_EXISTS,
            context={"work_item_id": work_item_id},
            remediation=f"Use '/work-show {work_item_id}' to view existing work item",
        )


# ============================================================================
# Quality Gate Errors
# ============================================================================


class QualityGateError(SolokitError):
    """
    Raised when quality gate fails.

    Example:
        >>> raise QualityGateError(
        ...     message="Tests failed",
        ...     code=ErrorCode.TEST_FAILED,
        ...     context={"failed_tests": ["test_foo", "test_bar"]}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class QualityTestFailedError(QualityGateError):
    """
    Raised when quality tests fail.

    Example:
        >>> raise QualityTestFailedError(
        ...     failed_count=2,
        ...     total_count=10,
        ...     details=["test_foo failed", "test_bar failed"]
        ... )
    """

    def __init__(self, failed_count: int, total_count: int, details: list[str] | None = None):
        message = f"{failed_count} of {total_count} tests failed"
        context = {"failed_count": failed_count, "total_count": total_count, "details": details}
        super().__init__(
            message=message,
            code=ErrorCode.TEST_FAILED,
            context=context,
            remediation="Fix failing tests before completing session",
        )


# ============================================================================
# File Operation Errors
# ============================================================================


class FileOperationError(SystemError):
    """
    Raised when file operations fail (read, write, parse, etc.).

    Example:
        >>> raise FileOperationError(
        ...     operation="write",
        ...     file_path="/path/to/file.json",
        ...     details="Permission denied"
        ... )
    """

    def __init__(
        self,
        operation: str,
        file_path: str,
        details: str | None = None,
        cause: Exception | None = None,
    ):
        message = f"File {operation} operation failed: {file_path}"
        if details:
            message = f"{message} - {details}"

        context = {"operation": operation, "file_path": file_path, "details": details}
        super().__init__(
            message=message, code=ErrorCode.FILE_OPERATION_FAILED, context=context, cause=cause
        )
        # Store as instance attributes for easy access
        self.operation = operation
        self.file_path = file_path
        self.details = details


# ============================================================================
# Learning Errors
# ============================================================================


class LearningError(ValidationError):
    """
    Raised when learning operations fail (validation, storage, curation).

    Example:
        >>> raise LearningError(
        ...     message="Learning content cannot be empty",
        ...     context={"learning_id": "abc123"}
        ... )
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.MISSING_REQUIRED_FIELD,
            context=context,
            remediation=remediation or "Check learning content and structure",
            cause=cause,
        )


class LearningNotFoundError(NotFoundError):
    """
    Raised when a learning doesn't exist.

    Example:
        >>> raise LearningNotFoundError("abc123")
    """

    def __init__(self, learning_id: str):
        super().__init__(
            message=f"Learning '{learning_id}' not found",
            code=ErrorCode.LEARNING_NOT_FOUND,
            context={"learning_id": learning_id},
            remediation="Use search or list commands to find available learnings",
        )


# ============================================================================
# Deployment Errors
# ============================================================================


class DeploymentError(SolokitError):
    """
    Raised when deployment operations fail.

    Example:
        >>> raise DeploymentError(
        ...     message="Deployment failed",
        ...     code=ErrorCode.DEPLOYMENT_FAILED,
        ...     context={"work_item_id": "deploy-001"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DEPLOYMENT_FAILED,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.SYSTEM,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class PreDeploymentCheckError(DeploymentError):
    """
    Raised when pre-deployment validation checks fail.

    Example:
        >>> raise PreDeploymentCheckError(
        ...     check_name="integration_tests",
        ...     details="3 tests failed"
        ... )
    """

    def __init__(
        self, check_name: str, details: str | None = None, context: dict[str, Any] | None = None
    ):
        message = f"Pre-deployment check '{check_name}' failed"
        if details:
            message = f"{message}: {details}"

        ctx = context or {}
        ctx.update({"check_name": check_name, "details": details})

        super().__init__(
            message=message,
            code=ErrorCode.PRE_DEPLOYMENT_CHECK_FAILED,
            context=ctx,
            remediation=f"Fix {check_name} issues before proceeding with deployment",
        )


class SmokeTestError(DeploymentError):
    """
    Raised when smoke tests fail after deployment.

    Example:
        >>> raise SmokeTestError(
        ...     test_name="health_check",
        ...     details="Endpoint returned 500"
        ... )
    """

    def __init__(
        self, test_name: str, details: str | None = None, context: dict[str, Any] | None = None
    ):
        message = f"Smoke test '{test_name}' failed"
        if details:
            message = f"{message}: {details}"

        ctx = context or {}
        ctx.update({"test_name": test_name, "details": details})

        super().__init__(
            message=message,
            code=ErrorCode.SMOKE_TEST_FAILED,
            context=ctx,
            remediation="Check deployment logs and verify service health",
        )


class RollbackError(DeploymentError):
    """
    Raised when rollback operation fails.

    Example:
        >>> raise RollbackError(
        ...     step="restore_database",
        ...     details="Backup file not found"
        ... )
    """

    def __init__(
        self,
        step: str | None = None,
        details: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        message = "Rollback failed"
        if step:
            message = f"Rollback failed at step '{step}'"
        if details:
            message = f"{message}: {details}"

        ctx = context or {}
        if step:
            ctx["failed_step"] = step
        if details:
            ctx["details"] = details

        super().__init__(
            message=message,
            code=ErrorCode.ROLLBACK_FAILED,
            context=ctx,
            remediation="Manual intervention may be required to restore system state",
        )


class DeploymentStepError(DeploymentError):
    """
    Raised when a deployment step fails.

    Example:
        >>> raise DeploymentStepError(
        ...     step_number=2,
        ...     step_description="Build application",
        ...     details="Compilation failed"
        ... )
    """

    def __init__(
        self,
        step_number: int,
        step_description: str,
        details: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        message = f"Deployment step {step_number} failed: {step_description}"
        if details:
            message = f"{message} - {details}"

        ctx = context or {}
        ctx.update(
            {"step_number": step_number, "step_description": step_description, "details": details}
        )

        super().__init__(
            message=message,
            code=ErrorCode.DEPLOYMENT_STEP_FAILED,
            context=ctx,
            remediation="Review deployment logs and fix the failing step",
        )


# ============================================================================
# Integration Test Errors
# ============================================================================


class IntegrationTestError(SolokitError):
    """
    Base exception for integration test failures.

    Example:
        >>> raise IntegrationTestError(
        ...     message="Integration test failed",
        ...     context={"test_name": "order_processing"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.TEST_FAILED,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.SYSTEM,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class EnvironmentSetupError(IntegrationTestError):
    """
    Raised when integration test environment setup fails.

    Example:
        >>> raise EnvironmentSetupError(
        ...     component="docker-compose",
        ...     details="Failed to start PostgreSQL service"
        ... )
    """

    def __init__(
        self, component: str, details: str | None = None, context: dict[str, Any] | None = None
    ):
        message = f"Environment setup failed: {component}"
        if details:
            message = f"{message} - {details}"

        ctx = context or {}
        ctx.update({"component": component, "details": details})

        super().__init__(
            message=message,
            code=ErrorCode.COMMAND_FAILED,
            context=ctx,
            remediation="Check Docker/docker-compose installation and service configurations",
        )


class IntegrationExecutionError(IntegrationTestError):
    """
    Raised when test execution fails.

    Example:
        >>> raise IntegrationExecutionError(
        ...     test_framework="pytest",
        ...     details="3 tests failed"
        ... )
    """

    def __init__(
        self, test_framework: str, details: str | None = None, context: dict[str, Any] | None = None
    ):
        message = f"Test execution failed: {test_framework}"
        if details:
            message = f"{message} - {details}"

        ctx = context or {}
        ctx.update({"test_framework": test_framework, "details": details})

        super().__init__(
            message=message,
            code=ErrorCode.TEST_FAILED,
            context=ctx,
            remediation="Review test output and fix failing tests",
        )


# ============================================================================
# API Validation Errors
# ============================================================================


class APIValidationError(ValidationError):
    """
    Base exception for API validation errors.

    Example:
        >>> raise APIValidationError(
        ...     message="API validation failed",
        ...     context={"endpoint": "/api/users"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.API_VALIDATION_FAILED,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message, code=code, context=context, remediation=remediation, cause=cause
        )


class SchemaValidationError(APIValidationError):
    """
    Raised when OpenAPI/Swagger schema validation fails.

    Example:
        >>> raise SchemaValidationError(
        ...     contract_file="api/openapi.yaml",
        ...     details="Missing 'paths' field"
        ... )
    """

    def __init__(self, contract_file: str, details: str, context: dict[str, Any] | None = None):
        message = f"Schema validation failed for '{contract_file}': {details}"
        ctx = context or {}
        ctx.update({"contract_file": contract_file, "details": details})

        super().__init__(
            message=message,
            code=ErrorCode.SCHEMA_VALIDATION_FAILED,
            context=ctx,
            remediation=f"Fix schema validation errors in {contract_file}",
        )


class ContractViolationError(APIValidationError):
    """
    Raised when API contract is violated.

    Example:
        >>> raise ContractViolationError(
        ...     path="/api/users",
        ...     method="POST",
        ...     violation_type="removed_required_parameter",
        ...     details="Parameter 'email' is required"
        ... )
    """

    def __init__(
        self,
        path: str,
        method: str,
        violation_type: str,
        details: str,
        severity: str = "high",
        context: dict[str, Any] | None = None,
    ):
        message = f"Contract violation in {method} {path}: {details}"
        ctx = context or {}
        ctx.update(
            {
                "path": path,
                "method": method,
                "violation_type": violation_type,
                "details": details,
                "severity": severity,
            }
        )

        super().__init__(
            message=message,
            code=ErrorCode.CONTRACT_VIOLATION,
            context=ctx,
            remediation="Review API contract changes and update implementation",
        )


class BreakingChangeError(APIValidationError):
    """
    Raised when breaking changes are detected in API contracts.

    Example:
        >>> raise BreakingChangeError(
        ...     breaking_changes=[
        ...         {"type": "removed_endpoint", "path": "/api/old"},
        ...         {"type": "removed_method", "path": "/api/users", "method": "DELETE"}
        ...     ],
        ...     allow_breaking_changes=False
        ... )
    """

    def __init__(
        self,
        breaking_changes: list[dict],
        allow_breaking_changes: bool = False,
        context: dict[str, Any] | None = None,
    ):
        change_count = len(breaking_changes)
        message = f"{change_count} breaking change{'s' if change_count != 1 else ''} detected"
        if not allow_breaking_changes:
            message = f"{message} (not allowed)"

        ctx = context or {}
        ctx.update(
            {
                "breaking_changes": breaking_changes,
                "breaking_change_count": change_count,
                "allow_breaking_changes": allow_breaking_changes,
            }
        )

        super().__init__(
            message=message,
            code=ErrorCode.BREAKING_CHANGE_DETECTED,
            context=ctx,
            remediation=(
                "Review breaking changes and either: "
                "1) Fix them to maintain backward compatibility, or "
                "2) Set 'allow_breaking_changes: true' if intentional"
            ),
        )


class InvalidOpenAPISpecError(APIValidationError):
    """
    Raised when OpenAPI/Swagger specification is invalid.

    Example:
        >>> raise InvalidOpenAPISpecError(
        ...     contract_file="api/openapi.yaml",
        ...     details="Not a valid OpenAPI/Swagger specification"
        ... )
    """

    def __init__(self, contract_file: str, details: str, context: dict[str, Any] | None = None):
        message = f"Invalid OpenAPI/Swagger spec: {contract_file}"
        ctx = context or {}
        ctx.update({"contract_file": contract_file, "details": details})

        super().__init__(
            message=message,
            code=ErrorCode.INVALID_OPENAPI_SPEC,
            context=ctx,
            remediation=f"Ensure {contract_file} is a valid OpenAPI/Swagger specification with 'openapi' or 'swagger' field",
        )


# ============================================================================
# Performance Testing Errors
# ============================================================================


class PerformanceTestError(SolokitError):
    """
    Base class for performance testing errors.

    Example:
        >>> raise PerformanceTestError(
        ...     message="Performance test failed",
        ...     code=ErrorCode.PERFORMANCE_TEST_FAILED,
        ...     context={"work_item_id": "perf-001"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.PERFORMANCE_TEST_FAILED,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class BenchmarkFailedError(PerformanceTestError):
    """
    Raised when a performance benchmark fails to meet requirements.

    Example:
        >>> raise BenchmarkFailedError(
        ...     metric="p95_latency",
        ...     actual=150.5,
        ...     expected=100.0,
        ...     unit="ms"
        ... )
    """

    def __init__(self, metric: str, actual: float, expected: float, unit: str = "ms"):
        message = f"Benchmark failed: {metric} {actual}{unit} exceeds requirement {expected}{unit}"
        context = {
            "metric": metric,
            "actual_value": actual,
            "expected_value": expected,
            "unit": unit,
            "delta": actual - expected,
            "percentage_over": ((actual / expected - 1) * 100) if expected > 0 else 0,
        }
        super().__init__(
            message=message,
            code=ErrorCode.BENCHMARK_FAILED,
            context=context,
            remediation=f"Optimize performance to meet {metric} requirement of {expected}{unit}",
        )


class PerformanceRegressionError(PerformanceTestError):
    """
    Raised when performance regression is detected against baseline.

    Example:
        >>> raise PerformanceRegressionError(
        ...     metric="p50_latency",
        ...     current=55.0,
        ...     baseline=50.0,
        ...     threshold_percent=10.0
        ... )
    """

    def __init__(
        self, metric: str, current: float, baseline: float, threshold_percent: float = 10.0
    ):
        regression_percent = ((current / baseline - 1) * 100) if baseline > 0 else 0
        message = (
            f"Performance regression detected: {metric} increased from "
            f"{baseline}ms to {current}ms ({regression_percent:.1f}% slower, "
            f"threshold: {threshold_percent}%)"
        )
        context = {
            "metric": metric,
            "current_value": current,
            "baseline_value": baseline,
            "regression_percent": regression_percent,
            "threshold_percent": threshold_percent,
        }
        super().__init__(
            message=message,
            code=ErrorCode.PERFORMANCE_REGRESSION,
            context=context,
            remediation="Investigate recent changes that may have caused performance degradation",
        )


class LoadTestFailedError(PerformanceTestError):
    """
    Raised when load test execution fails.

    Example:
        >>> raise LoadTestFailedError(
        ...     endpoint="http://localhost:8000/api",
        ...     details="Connection refused"
        ... )
    """

    def __init__(
        self, endpoint: str, details: str | None = None, context: dict[str, Any] | None = None
    ):
        message = f"Load test failed for endpoint: {endpoint}"
        if details:
            message = f"{message} - {details}"

        ctx = context or {}
        ctx.update({"endpoint": endpoint, "details": details})

        super().__init__(
            message=message,
            code=ErrorCode.LOAD_TEST_FAILED,
            context=ctx,
            remediation="Verify the endpoint is accessible and the service is running",
        )


# ============================================================================
# Project Initialization Errors
# ============================================================================


class ProjectInitializationError(SolokitError):
    """
    Base exception for project initialization errors.

    Example:
        >>> raise ProjectInitializationError(
        ...     message="Project initialization failed",
        ...     context={"reason": "Missing template files"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.FILE_OPERATION_FAILED,
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.SYSTEM,
            context=context,
            remediation=remediation,
            cause=cause,
        )


class DirectoryNotEmptyError(AlreadyExistsError):
    """
    Raised when attempting to initialize in a directory that already has Solokit structure.

    Example:
        >>> raise DirectoryNotEmptyError(".session")
    """

    def __init__(self, directory: str):
        super().__init__(
            message=f"Directory '{directory}' already exists",
            code=ErrorCode.FILE_ALREADY_EXISTS,
            context={"directory": directory},
            remediation=f"Remove '{directory}' directory or run initialization in a different location",
        )


class TemplateNotFoundError(FileNotFoundError):
    """
    Raised when a required template file is not found.

    Example:
        >>> raise TemplateNotFoundError(
        ...     template_name="package.json.template",
        ...     template_path="/path/to/templates"
        ... )
    """

    def __init__(self, template_name: str, template_path: str):
        super().__init__(file_path=f"{template_path}/{template_name}", file_type="template")
        self.context["template_name"] = template_name
        self.template_name = template_name
        self.template_path = template_path
        self.remediation = (
            f"Ensure Solokit is properly installed and template file exists: {template_name}"
        )
