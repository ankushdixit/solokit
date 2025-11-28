"""Unit tests for exception hierarchy"""

from solokit.core.exceptions import (
    BranchNotFoundError,
    CircularDependencyError,
    CommandExecutionError,
    ConfigurationError,
    ConfigValidationError,
    ErrorCategory,
    ErrorCode,
    FileNotFoundError,
    GitError,
    NotAGitRepoError,
    QualityTestFailedError,
    SessionAlreadyActiveError,
    SessionNotFoundError,
    SolokitError,
    SpecValidationError,
    SubprocessError,
    SystemError,
    TimeoutError,
    UnmetDependencyError,
    ValidationError,
    WorkingDirNotCleanError,
    WorkItemAlreadyExistsError,
    WorkItemNotFoundError,
)


class TestSolokitError:
    """Test base SolokitError class"""

    def test_basic_error_creation(self):
        """Test creating a basic SolokitError"""
        error = SolokitError(
            message="Test error",
            code=ErrorCode.FILE_OPERATION_FAILED,
            category=ErrorCategory.SYSTEM,
        )

        assert error.message == "Test error"
        assert error.code == ErrorCode.FILE_OPERATION_FAILED
        assert error.category == ErrorCategory.SYSTEM
        assert error.context == {}
        assert error.remediation is None
        assert error.cause is None

    def test_error_with_context(self):
        """Test error with context data"""
        error = SolokitError(
            message="Test error",
            code=ErrorCode.FILE_OPERATION_FAILED,
            category=ErrorCategory.SYSTEM,
            context={"file": "/path/to/file", "operation": "write"},
        )

        assert error.context["file"] == "/path/to/file"
        assert error.context["operation"] == "write"

    def test_error_with_remediation(self):
        """Test error with remediation"""
        error = SolokitError(
            message="Test error",
            code=ErrorCode.FILE_OPERATION_FAILED,
            category=ErrorCategory.SYSTEM,
            remediation="Check file permissions",
        )

        assert error.remediation == "Check file permissions"
        assert "Check file permissions" in str(error)

    def test_error_with_cause(self):
        """Test error with cause chain"""
        original = ValueError("Original error")
        error = SolokitError(
            message="Test error",
            code=ErrorCode.FILE_OPERATION_FAILED,
            category=ErrorCategory.SYSTEM,
            cause=original,
        )

        assert error.cause is original

    def test_error_to_dict(self):
        """Test converting error to dictionary"""
        error = SolokitError(
            message="Test error",
            code=ErrorCode.FILE_OPERATION_FAILED,
            category=ErrorCategory.SYSTEM,
            context={"file": "/path/to/file"},
            remediation="Check permissions",
        )

        error_dict = error.to_dict()
        assert error_dict["message"] == "Test error"
        assert error_dict["code"] == ErrorCode.FILE_OPERATION_FAILED.value
        assert error_dict["code_name"] == "FILE_OPERATION_FAILED"
        assert error_dict["category"] == "system"
        assert error_dict["context"]["file"] == "/path/to/file"
        assert error_dict["remediation"] == "Check permissions"

    def test_exit_code_mapping(self):
        """Test exit codes map correctly to categories"""
        validation_error = ValidationError("test")
        assert validation_error.exit_code == 2

        not_found_error = WorkItemNotFoundError("test")
        assert not_found_error.exit_code == 3

        config_error = ConfigurationError("test")
        assert config_error.exit_code == 4

        system_error = SystemError("test", code=ErrorCode.FILE_OPERATION_FAILED)
        assert system_error.exit_code == 5

        git_error = GitError("test", code=ErrorCode.GIT_COMMAND_FAILED)
        assert git_error.exit_code == 6


class TestValidationErrors:
    """Test validation error hierarchy"""

    def test_validation_error(self):
        """Test basic ValidationError"""
        error = ValidationError(
            message="Invalid input",
            code=ErrorCode.INVALID_WORK_ITEM_ID,
            context={"work_item_id": "bad-id"},
            remediation="Use alphanumeric characters",
        )

        assert error.category == ErrorCategory.VALIDATION
        assert error.code == ErrorCode.INVALID_WORK_ITEM_ID
        assert "Invalid input" in str(error)

    def test_spec_validation_error(self):
        """Test SpecValidationError"""
        errors = ["Missing Overview section", "Missing acceptance criteria"]
        error = SpecValidationError(work_item_id="my_feature", errors=errors)

        assert error.category == ErrorCategory.VALIDATION
        assert error.code == ErrorCode.SPEC_VALIDATION_FAILED
        assert error.context["work_item_id"] == "my_feature"
        assert error.context["validation_errors"] == errors
        assert error.context["error_count"] == 2
        assert ".session/specs/my_feature.md" in error.remediation


class TestNotFoundErrors:
    """Test not found error hierarchy"""

    def test_work_item_not_found_error(self):
        """Test WorkItemNotFoundError"""
        error = WorkItemNotFoundError("nonexistent_item")

        assert error.category == ErrorCategory.NOT_FOUND
        assert error.code == ErrorCode.WORK_ITEM_NOT_FOUND
        assert "nonexistent_item" in error.message
        assert "/work-list" in error.remediation

    def test_file_not_found_error(self):
        """Test FileNotFoundError"""
        error = FileNotFoundError(file_path=".session/config.json", file_type="configuration")

        assert error.category == ErrorCategory.NOT_FOUND
        assert error.code == ErrorCode.FILE_NOT_FOUND
        assert error.context["file_path"] == ".session/config.json"
        assert error.context["file_type"] == "configuration"
        assert ".session/config.json" in error.message

    def test_session_not_found_error(self):
        """Test SessionNotFoundError"""
        error = SessionNotFoundError()

        assert error.category == ErrorCategory.NOT_FOUND
        assert error.code == ErrorCode.SESSION_NOT_FOUND
        assert "/start" in error.remediation


class TestConfigurationErrors:
    """Test configuration error hierarchy"""

    def test_configuration_error(self):
        """Test basic ConfigurationError"""
        error = ConfigurationError(
            message="Invalid config value",
            code=ErrorCode.INVALID_CONFIG_VALUE,
            context={"key": "test_command", "value": None},
        )

        assert error.category == ErrorCategory.CONFIGURATION
        assert error.code == ErrorCode.INVALID_CONFIG_VALUE

    def test_config_validation_error(self):
        """Test ConfigValidationError"""
        errors = ["Missing 'project_name' field", "Invalid 'version' value"]
        error = ConfigValidationError(config_path=".session/config.json", errors=errors)

        assert error.category == ErrorCategory.CONFIGURATION
        assert error.code == ErrorCode.CONFIG_VALIDATION_FAILED
        assert error.context["config_path"] == ".session/config.json"
        assert error.context["error_count"] == 2
        assert "configuration.md" in error.remediation


class TestGitErrors:
    """Test git error hierarchy"""

    def test_not_a_git_repo_error(self):
        """Test NotAGitRepoError"""
        error = NotAGitRepoError()

        assert error.category == ErrorCategory.GIT
        assert error.code == ErrorCode.NOT_A_GIT_REPO
        assert "git init" in error.remediation

    def test_not_a_git_repo_error_with_path(self):
        """Test NotAGitRepoError with path"""
        error = NotAGitRepoError(path="/some/path")

        assert error.context["path"] == "/some/path"

    def test_working_dir_not_clean_error(self):
        """Test WorkingDirNotCleanError"""
        changes = ["M src/file.py", "?? new_file.py"]
        error = WorkingDirNotCleanError(changes=changes)

        assert error.category == ErrorCategory.GIT
        assert error.code == ErrorCode.WORKING_DIR_NOT_CLEAN
        assert error.context["uncommitted_changes"] == changes
        assert "stash" in error.remediation.lower()

    def test_branch_not_found_error(self):
        """Test BranchNotFoundError"""
        error = BranchNotFoundError("feature-branch")

        assert error.category == ErrorCategory.GIT
        assert error.code == ErrorCode.BRANCH_NOT_FOUND
        assert "feature-branch" in error.message
        assert error.context["branch_name"] == "feature-branch"


class TestSystemErrors:
    """Test system error hierarchy"""

    def test_subprocess_error(self):
        """Test SubprocessError"""
        error = SubprocessError(
            command="pytest tests/",
            returncode=1,
            stderr="FAILED tests/test_foo.py",
            stdout="collected 10 items",
        )

        assert error.category == ErrorCategory.SYSTEM
        assert error.code == ErrorCode.SUBPROCESS_FAILED
        assert error.context["command"] == "pytest tests/"
        assert error.context["returncode"] == 1
        assert error.context["stderr"] == "FAILED tests/test_foo.py"

    def test_timeout_error(self):
        """Test TimeoutError"""
        error = TimeoutError(operation="git fetch", timeout_seconds=30)

        assert error.category == ErrorCategory.SYSTEM
        assert error.code == ErrorCode.OPERATION_TIMEOUT
        assert error.context["operation"] == "git fetch"
        assert error.context["timeout_seconds"] == 30
        assert "30s" in error.message

    def test_command_execution_error(self):
        """Test CommandExecutionError"""
        error = CommandExecutionError(command="npm test", returncode=1, stderr="Test failed")

        assert error.category == ErrorCategory.SYSTEM
        assert error.code == ErrorCode.COMMAND_FAILED
        assert error.context["command"] == "npm test"


class TestDependencyErrors:
    """Test dependency error hierarchy"""

    def test_circular_dependency_error(self):
        """Test CircularDependencyError"""
        cycle = ["feature_a", "feature_b", "feature_c", "feature_a"]
        error = CircularDependencyError(cycle)

        assert error.category == ErrorCategory.DEPENDENCY
        assert error.code == ErrorCode.CIRCULAR_DEPENDENCY
        assert error.context["cycle"] == cycle
        assert "feature_a -> feature_b -> feature_c -> feature_a" in error.message

    def test_unmet_dependency_error(self):
        """Test UnmetDependencyError"""
        error = UnmetDependencyError("feature_b", "feature_a")

        assert error.category == ErrorCategory.DEPENDENCY
        assert error.code == ErrorCode.UNMET_DEPENDENCY
        assert error.context["work_item_id"] == "feature_b"
        assert error.context["dependency_id"] == "feature_a"
        assert "feature_a" in error.message
        assert "feature_b" in error.message


class TestAlreadyExistsErrors:
    """Test already exists error hierarchy"""

    def test_session_already_active_error(self):
        """Test SessionAlreadyActiveError"""
        error = SessionAlreadyActiveError("current_feature")

        assert error.category == ErrorCategory.ALREADY_EXISTS
        assert error.code == ErrorCode.SESSION_ALREADY_ACTIVE
        assert error.context["current_work_item_id"] == "current_feature"
        assert "/end" in error.remediation

    def test_work_item_already_exists_error(self):
        """Test WorkItemAlreadyExistsError"""
        error = WorkItemAlreadyExistsError("my_feature")

        assert error.category == ErrorCategory.ALREADY_EXISTS
        assert error.code == ErrorCode.WORK_ITEM_ALREADY_EXISTS
        assert error.context["work_item_id"] == "my_feature"
        assert "work-show" in error.remediation


class TestQualityGateErrors:
    """Test quality gate error hierarchy"""

    def test_quality_test_failed_error(self):
        """Test QualityTestFailedError"""
        details = ["test_foo failed", "test_bar failed"]
        error = QualityTestFailedError(failed_count=2, total_count=10, details=details)

        assert error.code == ErrorCode.TEST_FAILED
        assert error.context["failed_count"] == 2
        assert error.context["total_count"] == 10
        assert error.context["details"] == details
        assert "2 of 10" in error.message
