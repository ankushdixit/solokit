"""Unit tests for adopt/orchestrator module.

Tests the main adoption flow orchestration and configuration file installation.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from solokit.adopt.orchestrator import (
    _create_adoption_commit,
    _get_language_gitignore_entries,
    _get_template_id_for_language,
    _get_tier_order,
    _get_tiers_up_to,
    _install_config_file,
    _is_config_file,
    _update_gitignore_for_adoption,
    get_config_files_to_install,
    install_tier_configs,
    run_adoption,
)
from solokit.adopt.project_detector import (
    PackageManager,
    ProjectFramework,
    ProjectInfo,
    ProjectLanguage,
)
from solokit.core.exceptions import FileOperationError


class TestGetTemplateIdForLanguage:
    """Tests for _get_template_id_for_language function."""

    def test_nodejs_maps_to_saas_t3(self):
        """Test Node.js maps to saas_t3 template."""
        result = _get_template_id_for_language(ProjectLanguage.NODEJS)
        assert result == "saas_t3"

    def test_typescript_maps_to_saas_t3(self):
        """Test TypeScript maps to saas_t3 template."""
        result = _get_template_id_for_language(ProjectLanguage.TYPESCRIPT)
        assert result == "saas_t3"

    def test_python_maps_to_ml_ai_fastapi(self):
        """Test Python maps to ml_ai_fastapi template."""
        result = _get_template_id_for_language(ProjectLanguage.PYTHON)
        assert result == "ml_ai_fastapi"

    def test_fullstack_maps_to_fullstack_nextjs(self):
        """Test fullstack maps to fullstack_nextjs template."""
        result = _get_template_id_for_language(ProjectLanguage.FULLSTACK)
        assert result == "fullstack_nextjs"

    def test_unknown_maps_to_default_saas_t3(self):
        """Test unknown language maps to default saas_t3 template."""
        result = _get_template_id_for_language(ProjectLanguage.UNKNOWN)
        assert result == "saas_t3"


class TestGetTierOrder:
    """Tests for _get_tier_order function."""

    def test_returns_tiers_in_correct_order(self):
        """Test tiers are returned in correct order."""
        result = _get_tier_order()
        assert result == [
            "tier-1-essential",
            "tier-2-standard",
            "tier-3-comprehensive",
            "tier-4-production",
        ]

    def test_returns_list(self):
        """Test returns a list."""
        result = _get_tier_order()
        assert isinstance(result, list)

    def test_contains_four_tiers(self):
        """Test contains exactly 4 tiers."""
        result = _get_tier_order()
        assert len(result) == 4


class TestGetTiersUpTo:
    """Tests for _get_tiers_up_to function."""

    def test_tier_1_returns_single_tier(self):
        """Test tier-1 returns only tier-1."""
        result = _get_tiers_up_to("tier-1-essential")
        assert result == ["tier-1-essential"]

    def test_tier_2_returns_cumulative_tiers(self):
        """Test tier-2 returns tiers 1 and 2."""
        result = _get_tiers_up_to("tier-2-standard")
        assert result == ["tier-1-essential", "tier-2-standard"]

    def test_tier_3_returns_all_up_to_three(self):
        """Test tier-3 returns tiers 1, 2, and 3."""
        result = _get_tiers_up_to("tier-3-comprehensive")
        assert result == [
            "tier-1-essential",
            "tier-2-standard",
            "tier-3-comprehensive",
        ]

    def test_tier_4_returns_all_tiers(self):
        """Test tier-4 returns all tiers."""
        result = _get_tiers_up_to("tier-4-production")
        assert result == [
            "tier-1-essential",
            "tier-2-standard",
            "tier-3-comprehensive",
            "tier-4-production",
        ]

    def test_invalid_tier_defaults_to_tier_1(self):
        """Test invalid tier defaults to tier-1."""
        result = _get_tiers_up_to("invalid-tier")
        assert result == ["tier-1-essential"]

    def test_empty_string_defaults_to_tier_1(self):
        """Test empty string defaults to tier-1."""
        result = _get_tiers_up_to("")
        assert result == ["tier-1-essential"]


class TestIsConfigFile:
    """Tests for _is_config_file function."""

    def test_recognizes_direct_config_file(self, tmp_path):
        """Test recognizes files in ADOPT_CONFIG_FILES."""
        file_path = tmp_path / "tsconfig.json"
        result = _is_config_file(file_path)
        assert result is True

    def test_recognizes_template_file(self, tmp_path):
        """Test recognizes template files."""
        file_path = tmp_path / "package.json.tier1.template"
        result = _is_config_file(file_path)
        assert result is True

    def test_rejects_non_config_file(self, tmp_path):
        """Test rejects non-config files."""
        file_path = tmp_path / "main.ts"
        result = _is_config_file(file_path)
        assert result is False

    def test_rejects_source_code_file(self, tmp_path):
        """Test rejects source code files."""
        file_path = tmp_path / "index.js"
        result = _is_config_file(file_path)
        assert result is False


class TestInstallConfigFile:
    """Tests for _install_config_file function."""

    def test_installs_direct_config_file(self, tmp_path):
        """Test installs config file without processing."""
        # Arrange
        src_path = tmp_path / "src" / "tsconfig.json"
        src_path.parent.mkdir(parents=True)
        src_path.write_text('{"compilerOptions": {}}')

        project_root = tmp_path / "project"
        relative_path = Path("tsconfig.json")
        replacements = {}

        # Act
        result = _install_config_file(src_path, project_root, relative_path, replacements)

        # Assert
        assert result is True
        output_path = project_root / "tsconfig.json"
        assert output_path.exists()
        assert output_path.read_text() == '{"compilerOptions": {}}'

    def test_processes_template_file(self, tmp_path):
        """Test processes template files with replacements."""
        # Arrange
        src_path = tmp_path / "src" / "package.json.template"
        src_path.parent.mkdir(parents=True)
        src_path.write_text('{"name": "{project_name}"}')

        project_root = tmp_path / "project"
        relative_path = Path("package.json.template")
        replacements = {"project_name": "test-project"}

        # Act
        result = _install_config_file(src_path, project_root, relative_path, replacements)

        # Assert
        assert result is True
        output_path = project_root / "package.json"
        assert output_path.exists()
        assert output_path.read_text() == '{"name": "test-project"}'

    def test_processes_tier_template_file(self, tmp_path):
        """Test processes tier-specific template files."""
        # Arrange
        src_path = tmp_path / "src" / "package.json.tier3.template"
        src_path.parent.mkdir(parents=True)
        src_path.write_text('{"name": "{project_name}"}')

        project_root = tmp_path / "project"
        relative_path = Path("package.json.tier3.template")
        replacements = {"project_name": "test-project"}

        # Act
        result = _install_config_file(src_path, project_root, relative_path, replacements)

        # Assert
        assert result is True
        output_path = project_root / "package.json"
        assert output_path.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test creates parent directories when needed."""
        # Arrange
        src_path = tmp_path / "src" / "config.json"
        src_path.parent.mkdir(parents=True)
        src_path.write_text("{}")

        project_root = tmp_path / "project"
        relative_path = Path("subdir") / "config.json"
        replacements = {}

        # Act
        result = _install_config_file(src_path, project_root, relative_path, replacements)

        # Assert
        assert result is True
        output_path = project_root / "subdir" / "config.json"
        assert output_path.exists()

    def test_handles_installation_error(self, tmp_path):
        """Test handles errors during installation gracefully."""
        # Arrange
        src_path = tmp_path / "src" / "config.json"
        # Don't create the source file

        project_root = tmp_path / "project"
        relative_path = Path("config.json")
        replacements = {}

        # Act
        result = _install_config_file(src_path, project_root, relative_path, replacements)

        # Assert
        assert result is False


class TestInstallTierConfigs:
    """Tests for install_tier_configs function."""

    @patch("solokit.init.template_installer.get_template_directory")
    def test_installs_tier_1_configs(self, mock_get_template, tmp_path):
        """Test installs tier-1 configuration files."""
        # Arrange
        template_dir = tmp_path / "template"
        base_dir = template_dir / "base"
        base_dir.mkdir(parents=True)

        # Create a config file
        config_file = base_dir / "tsconfig.json"
        config_file.write_text('{"compilerOptions": {}}')

        mock_get_template.return_value = template_dir

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Act
        count, files = install_tier_configs("saas_t3", "tier-1-essential", project_root, 80)

        # Assert
        assert count == 1
        assert len(files) == 1

    @patch("solokit.init.template_installer.get_template_directory")
    def test_skips_source_directories(self, mock_get_template, tmp_path):
        """Test skips files in source directories."""
        # Arrange
        template_dir = tmp_path / "template"
        base_dir = template_dir / "base"
        src_dir = base_dir / "src"
        src_dir.mkdir(parents=True)

        # Create a file in src directory (should be skipped)
        src_file = src_dir / "index.ts"
        src_file.write_text("console.log('hello');")

        mock_get_template.return_value = template_dir

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Act
        count, files = install_tier_configs("saas_t3", "tier-1-essential", project_root, 80)

        # Assert
        assert count == 0
        assert len(files) == 0

    @patch("solokit.init.template_installer.get_template_directory")
    def test_installs_cumulative_tiers(self, mock_get_template, tmp_path):
        """Test installs configs from all tiers up to target."""
        # Arrange
        template_dir = tmp_path / "template"
        base_dir = template_dir / "base"
        tier1_dir = template_dir / "tier-1-essential"
        tier2_dir = template_dir / "tier-2-standard"

        base_dir.mkdir(parents=True)
        tier1_dir.mkdir(parents=True)
        tier2_dir.mkdir(parents=True)

        # Create config files in each tier
        (base_dir / "tsconfig.json").write_text("{}")
        (tier1_dir / "eslint.config.mjs").write_text("export default {};")
        (tier2_dir / "jest.config.ts").write_text("export default {};")

        mock_get_template.return_value = template_dir

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Act
        count, files = install_tier_configs("saas_t3", "tier-2-standard", project_root, 80)

        # Assert
        assert count == 3  # base + tier1 + tier2

    @patch("solokit.init.template_installer.get_template_directory")
    def test_replaces_template_placeholders(self, mock_get_template, tmp_path):
        """Test replaces template placeholders correctly."""
        # Arrange
        template_dir = tmp_path / "template"
        tier1_dir = template_dir / "tier-1-essential"
        tier1_dir.mkdir(parents=True)

        # Create template file with placeholder (using correct filename from ADOPT_TEMPLATE_FILES)
        template_file = tier1_dir / "package.json.tier1.template"
        template_file.write_text('{"name": "{project_name}"}')

        mock_get_template.return_value = template_dir

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Act
        count, files = install_tier_configs("saas_t3", "tier-1-essential", project_root, 80)

        # Assert
        assert count == 1
        output_file = project_root / "package.json"
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content["name"] == "project"  # project_root.name


class TestGetConfigFilesToInstall:
    """Tests for get_config_files_to_install function."""

    @patch("solokit.init.template_installer.get_template_directory")
    def test_returns_config_file_names(self, mock_get_template, tmp_path):
        """Test returns list of config file names."""
        # Arrange
        template_dir = tmp_path / "template"
        base_dir = template_dir / "base"
        base_dir.mkdir(parents=True)

        (base_dir / "tsconfig.json").write_text("{}")
        (base_dir / "eslint.config.mjs").write_text("export default {};")

        mock_get_template.return_value = template_dir

        # Act
        result = get_config_files_to_install("saas_t3", "tier-1-essential")

        # Assert
        assert isinstance(result, list)
        assert "tsconfig.json" in result
        assert "eslint.config.mjs" in result

    @patch("solokit.init.template_installer.get_template_directory")
    def test_removes_template_suffix(self, mock_get_template, tmp_path):
        """Test removes .template suffix from filenames."""
        # Arrange
        template_dir = tmp_path / "template"
        tier1_dir = template_dir / "tier-1-essential"
        tier1_dir.mkdir(parents=True)

        # Use a valid template file name from ADOPT_TEMPLATE_FILES
        (tier1_dir / "package.json.tier1.template").write_text("{}")

        mock_get_template.return_value = template_dir

        # Act
        result = get_config_files_to_install("saas_t3", "tier-1-essential")

        # Assert
        assert "package.json" in result
        assert "package.json.tier1.template" not in result

    @patch("solokit.init.template_installer.get_template_directory")
    def test_returns_empty_list_on_error(self, mock_get_template):
        """Test returns empty list on error."""
        # Arrange
        mock_get_template.side_effect = Exception("Template not found")

        # Act
        result = get_config_files_to_install("invalid_template", "tier-1-essential")

        # Assert
        assert result == []


class TestGetLanguageGitignoreEntries:
    """Tests for _get_language_gitignore_entries function."""

    def test_nodejs_entries(self):
        """Test returns Node.js-specific gitignore entries."""
        # Arrange
        project_info = ProjectInfo(
            language=ProjectLanguage.NODEJS,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.NPM,
            confidence=1.0,
        )

        # Act
        result = _get_language_gitignore_entries(project_info)

        # Assert
        assert "coverage/" in result
        assert ".session/briefings/" in result
        assert ".session/history/" in result

    def test_python_entries(self):
        """Test returns Python-specific gitignore entries."""
        # Arrange
        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _get_language_gitignore_entries(project_info)

        # Assert
        assert ".coverage" in result
        assert "htmlcov/" in result
        assert ".session/briefings/" in result

    def test_fullstack_entries(self):
        """Test returns both Node.js and Python entries for fullstack."""
        # Arrange
        project_info = ProjectInfo(
            language=ProjectLanguage.FULLSTACK,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _get_language_gitignore_entries(project_info)

        # Assert
        assert "coverage/" in result  # Node.js
        assert ".coverage" in result  # Python
        assert ".session/briefings/" in result  # Common

    def test_unknown_language_entries(self):
        """Test returns only common entries for unknown language."""
        # Arrange
        project_info = ProjectInfo(
            language=ProjectLanguage.UNKNOWN,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=0.5,
        )

        # Act
        result = _get_language_gitignore_entries(project_info)

        # Assert
        assert ".session/briefings/" in result
        assert ".session/history/" in result
        assert "coverage/" not in result
        assert ".coverage" not in result


class TestUpdateGitignoreForAdoption:
    """Tests for _update_gitignore_for_adoption function."""

    def test_creates_gitignore_if_missing(self, tmp_path):
        """Test creates .gitignore if it doesn't exist."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _update_gitignore_for_adoption(project_info, project_root)

        # Assert
        assert result is True
        gitignore = project_root / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".session/briefings/" in content

    def test_appends_to_existing_gitignore(self, tmp_path):
        """Test appends entries to existing .gitignore."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        gitignore = project_root / ".gitignore"
        gitignore.write_text("node_modules/\n")

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _update_gitignore_for_adoption(project_info, project_root)

        # Assert
        assert result is True
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert ".session/briefings/" in content

    def test_skips_duplicate_entries(self, tmp_path):
        """Test doesn't add duplicate entries."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        gitignore = project_root / ".gitignore"
        # Include all Python-specific entries that would be added
        gitignore.write_text(
            "# Solokit session files\n.session/briefings/\n.session/history/\n# Coverage\n.coverage\nhtmlcov/\ncoverage.xml\n*.cover\n"
        )

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _update_gitignore_for_adoption(project_info, project_root)

        # Assert
        assert result is False  # No changes needed

    def test_raises_on_read_error(self, tmp_path):
        """Test raises FileOperationError on read error."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        gitignore = project_root / ".gitignore"
        gitignore.mkdir()  # Make it a directory instead of file

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act & Assert
        with pytest.raises(FileOperationError):
            _update_gitignore_for_adoption(project_info, project_root)


class TestCreateAdoptionCommit:
    """Tests for _create_adoption_commit function."""

    @patch("solokit.core.command_runner.CommandRunner")
    def test_skips_if_no_git_repo(self, mock_runner_class, tmp_path):
        """Test skips commit if no git repository exists."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _create_adoption_commit("tier-2-standard", project_info, project_root)

        # Assert
        assert result is False

    @patch("solokit.core.command_runner.CommandRunner")
    def test_skips_if_no_changes(self, mock_runner_class, tmp_path):
        """Test skips commit if no changes to commit."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".git").mkdir()

        mock_runner = Mock()
        mock_runner.run.return_value = Mock(success=True, stdout="")
        mock_runner_class.return_value = mock_runner

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _create_adoption_commit("tier-2-standard", project_info, project_root)

        # Assert
        assert result is False

    @patch("solokit.core.command_runner.CommandRunner")
    def test_creates_commit_with_changes(self, mock_runner_class, tmp_path):
        """Test creates commit when changes exist."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".git").mkdir()
        # Create all the files that get staged
        (project_root / ".session").mkdir()
        (project_root / ".claude" / "commands").mkdir(parents=True)
        (project_root / ".gitignore").write_text("# test")
        (project_root / "README.md").write_text("# test")
        (project_root / "CLAUDE.md").write_text("# test")

        mock_runner = Mock()
        # First call: git status --porcelain (has changes)
        # Second-Sixth calls: git add commands (5 files)
        # Seventh call: git diff --cached --quiet (has staged changes, exit 1)
        # Eighth call: git commit
        mock_runner.run.side_effect = [
            Mock(success=True, stdout="M README.md"),  # status
            Mock(success=True, stdout=""),  # add .session/
            Mock(success=True, stdout=""),  # add .claude/commands/
            Mock(success=True, stdout=""),  # add .gitignore
            Mock(success=True, stdout=""),  # add README.md
            Mock(success=True, stdout=""),  # add CLAUDE.md
            Mock(success=False, stdout=""),  # diff --cached (exit 1 = has diff)
            Mock(success=True, stdout="", stderr=""),  # commit
        ]
        mock_runner_class.return_value = mock_runner

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Act
        result = _create_adoption_commit("tier-2-standard", project_info, project_root)

        # Assert
        assert result is True


class TestRunAdoption:
    """Tests for run_adoption main orchestration function."""

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    @patch("solokit.init.claude_commands_installer.install_claude_commands")
    @patch("solokit.adopt.orchestrator.append_to_readme")
    @patch("solokit.adopt.orchestrator.append_to_claude_md")
    @patch("solokit.adopt.orchestrator._update_gitignore_for_adoption")
    @patch("solokit.init.initial_scans.run_initial_scans")
    @patch("solokit.init.git_hooks_installer.install_git_hooks")
    def test_successful_adoption_flow(
        self,
        mock_git_hooks,
        mock_scans,
        mock_gitignore,
        mock_claude_md,
        mock_readme,
        mock_commands,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
    ):
        """Test successful adoption flow."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (5, ["config1", "config2"])
        mock_commands.return_value = ["start", "end"]
        mock_readme.return_value = True
        mock_claude_md.return_value = True
        mock_gitignore.return_value = True
        mock_scans.return_value = {"stack": True, "tree": True}

        # Act
        result = run_adoption(
            tier="tier-2-standard",
            coverage_target=80,
            project_root=project_root,
            skip_commit=True,
        )

        # Assert
        assert result == 0
        mock_detect.assert_called_once()
        mock_tier_configs.assert_called_once()
        mock_session_dirs.assert_called_once()
        mock_tracking.assert_called_once()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_skips_commit_when_flag_set(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_detect,
        tmp_path,
    ):
        """Test skips commit creation when skip_commit=True."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info

        with patch("solokit.adopt.orchestrator.install_tier_configs") as mock_tier:
            mock_tier.return_value = (0, [])
            with patch("solokit.init.claude_commands_installer.install_claude_commands"):
                with patch("solokit.adopt.orchestrator.append_to_readme"):
                    with patch("solokit.adopt.orchestrator.append_to_claude_md"):
                        with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                            with patch(
                                "solokit.init.initial_scans.run_initial_scans"
                            ) as mock_scans:
                                mock_scans.return_value = {}
                                with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                    with patch(
                                        "solokit.adopt.orchestrator._create_adoption_commit"
                                    ) as mock_commit:
                                        # Act
                                        result = run_adoption(
                                            tier="tier-2-standard",
                                            coverage_target=80,
                                            project_root=project_root,
                                            skip_commit=True,
                                        )

                                        # Assert
                                        assert result == 0
                                        mock_commit.assert_not_called()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    @patch("solokit.init.claude_commands_installer.install_claude_commands")
    @patch("solokit.adopt.orchestrator.append_to_readme")
    @patch("solokit.adopt.orchestrator.append_to_claude_md")
    @patch("solokit.adopt.orchestrator._update_gitignore_for_adoption")
    @patch("solokit.init.initial_scans.run_initial_scans")
    @patch("solokit.init.git_hooks_installer.install_git_hooks")
    def test_continues_on_optional_step_failure(
        self,
        mock_git_hooks,
        mock_scans,
        mock_gitignore,
        mock_claude_md,
        mock_readme,
        mock_commands,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
    ):
        """Test continues adoption even if optional steps fail."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])
        mock_commands.side_effect = Exception("Command install failed")
        mock_readme.side_effect = FileOperationError("read", "README.md", "Not found")
        mock_claude_md.side_effect = FileOperationError("read", "CLAUDE.md", "Not found")
        mock_gitignore.side_effect = FileOperationError("read", ".gitignore", "Not found")
        mock_scans.side_effect = Exception("Scans failed")
        mock_git_hooks.side_effect = Exception("Hooks failed")

        # Act
        result = run_adoption(
            tier="tier-2-standard",
            coverage_target=80,
            project_root=project_root,
            skip_commit=True,
        )

        # Assert
        assert result == 0  # Should still succeed

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    @patch("solokit.init.template_installer.install_additional_option")
    def test_installs_additional_options(
        self,
        mock_additional_option,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
    ):
        """Test installs additional options (CI/CD, Docker)."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])
        mock_additional_option.return_value = 3

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.orchestrator.append_to_readme"):
                with patch("solokit.adopt.orchestrator.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                # Act
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    additional_options=["ci_cd", "docker"],
                                    project_root=project_root,
                                    skip_commit=True,
                                )

                                # Assert
                                assert result == 0
                                assert mock_additional_option.call_count == 2

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    @patch("solokit.init.env_generator.generate_env_files")
    def test_generates_env_files_when_option_selected(
        self,
        mock_env_files,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
    ):
        """Test generates environment files when env_templates option selected."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])
        mock_env_files.return_value = [".env.example", ".editorconfig"]

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                # Act
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    additional_options=["env_templates"],
                                    project_root=project_root,
                                    skip_commit=True,
                                )

                                # Assert
                                assert result == 0
                                mock_env_files.assert_called_once()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_uses_current_directory_as_default(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        monkeypatch,
    ):
        """Test uses current directory when project_root not specified."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                # Act
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    skip_commit=True,
                                )

                                # Assert
                                assert result == 0
                                # Verify detect_project_type was called with Path.cwd()
                                assert mock_detect.call_args[0][0] == Path.cwd()


class TestInstallConfigFileEdgeCases:
    """Tests for edge cases in _install_config_file."""

    def test_install_config_file_with_tier_suffix(self, tmp_path):
        """Test installing config file with tier suffix removes tier from output name."""
        # Create source file with tier suffix in name
        src_dir = tmp_path / "templates"
        src_dir.mkdir()
        src_file = src_dir / "jest.config.tier3.template"
        src_file.write_text("module.exports = { coverage: {coverage_target} };")

        project_root = tmp_path / "project"
        project_root.mkdir()

        relative_path = Path("jest.config.tier3.template")
        replacements = {"coverage_target": "80"}

        result = _install_config_file(src_file, project_root, relative_path, replacements)

        assert result is True
        # Should create jest.config without .tier3.template suffix
        output_file = project_root / "jest.config"
        assert output_file.exists()
        assert "80" in output_file.read_text()


class TestGetConfigFilesToInstallEdgeCases:
    """Tests for edge cases in get_config_files_to_install."""

    def test_get_config_files_skips_directories(self, tmp_path):
        """Test get_config_files_to_install skips directories in path."""
        with patch("solokit.init.template_installer.get_template_directory") as mock_dir:
            # Create mock template structure
            template_dir = tmp_path / "templates"
            template_dir.mkdir()

            base_dir = template_dir / "base"
            base_dir.mkdir()

            # Create a directory to skip
            src_dir = base_dir / "src"
            src_dir.mkdir()
            (src_dir / "index.ts").write_text("// code")

            # Create config files
            (base_dir / "tsconfig.json").write_text("{}")

            mock_dir.return_value = template_dir

            result = get_config_files_to_install("saas_t3", "tier-1-essential")

            # Should not include files from src directory
            assert "index.ts" not in result
            assert "tsconfig.json" in result

    def test_get_config_files_skips_files_in_skip_directories(self, tmp_path):
        """Test config files in SKIP_DIRECTORIES are excluded."""
        with patch("solokit.init.template_installer.get_template_directory") as mock_dir:
            # Create mock template structure
            template_dir = tmp_path / "templates"
            template_dir.mkdir()

            tier_dir = template_dir / "tier-1-essential"
            tier_dir.mkdir()

            # Create config in app directory (should be skipped)
            app_dir = tier_dir / "app"
            app_dir.mkdir()
            (app_dir / "config.json").write_text("{}")

            # Create config at root (should be included)
            (tier_dir / "tsconfig.json").write_text("{}")

            mock_dir.return_value = template_dir

            result = get_config_files_to_install("saas_t3", "tier-1-essential")

            # Config in app directory should be skipped
            assert "tsconfig.json" in result


class TestUpdateGitignoreForAdoptionEdgeCases:
    """Tests for edge cases in _update_gitignore_for_adoption."""

    def test_update_gitignore_adds_newline_when_missing(self, tmp_path):
        """Test adding entries when existing content doesn't end with newline."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create gitignore without trailing newline
        gitignore = project_root / ".gitignore"
        gitignore.write_text("node_modules/")  # No trailing newline

        project_info = ProjectInfo(
            language=ProjectLanguage.NODEJS,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        result = _update_gitignore_for_adoption(project_info, project_root)

        assert result is True
        content = gitignore.read_text()
        # Should have newline between old and new content
        assert "node_modules/" in content
        assert ".session/briefings/" in content

    def test_update_gitignore_write_os_error(self, tmp_path):
        """Test _update_gitignore_for_adoption raises FileOperationError on write failure."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        gitignore = project_root / ".gitignore"
        gitignore.write_text("")

        project_info = ProjectInfo(
            language=ProjectLanguage.NODEJS,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        # Mock open to raise OSError during write
        original_open = open

        def mock_open_func(path, *args, **kwargs):
            if "a" in args or kwargs.get("mode") == "a":
                raise OSError("Permission denied")
            return original_open(path, *args, **kwargs)

        with patch("builtins.open", mock_open_func):
            with pytest.raises(FileOperationError) as exc_info:
                _update_gitignore_for_adoption(project_info, project_root)

            assert exc_info.value.context["operation"] == "write"


class TestCreateAdoptionCommitEdgeCases:
    """Tests for edge cases in _create_adoption_commit."""

    def test_create_adoption_commit_no_solokit_files(self, tmp_path):
        """Test commit creation when no Solokit files were staged."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Initialize git repo
        git_dir = project_root / ".git"
        git_dir.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        with patch("solokit.core.command_runner.CommandRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner_class.return_value = mock_runner

            # First call: git status --porcelain returns changes
            # Second call: git diff --cached --quiet returns 0 (nothing staged)
            mock_runner.run.side_effect = [
                MagicMock(success=True, stdout="M somefile.py"),
                MagicMock(success=True, returncode=0),
            ]

            result = _create_adoption_commit("tier-2-standard", project_info, project_root)

        # Should return False when nothing was staged
        assert result is False


class TestRunAdoptionEdgeCases:
    """Tests for run_adoption edge cases."""

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_run_adoption_shows_framework_when_detected(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption displays framework when detected."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Return project info with framework detected
        project_info = ProjectInfo(
            language=ProjectLanguage.TYPESCRIPT,
            framework=ProjectFramework.NEXTJS,
            package_manager=PackageManager.NPM,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (3, ["tsconfig.json", "jest.config.ts", "eslintrc.json"])

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    project_root=project_root,
                                    skip_commit=True,
                                )

        assert result == 0
        captured = capsys.readouterr()
        assert "Nextjs" in captured.out or "nextjs" in captured.out.lower()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_run_adoption_warns_existing_session_dir(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption warns when .session directory exists."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create existing .session directory
        session_dir = project_root / ".session"
        session_dir.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    project_root=project_root,
                                    skip_commit=True,
                                )

        assert result == 0
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_run_adoption_handles_config_install_exception(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption continues when config installation fails."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.side_effect = RuntimeError("Config install failed")

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    project_root=project_root,
                                    skip_commit=True,
                                )

        # Should still succeed despite config install failure
        assert result == 0
        captured = capsys.readouterr()
        assert "Config install" in captured.out or "failed" in captured.out.lower()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_run_adoption_shows_many_config_files(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption shows '... and X more' when many config files installed."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.TYPESCRIPT,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        # Return more than 5 config files
        mock_tier_configs.return_value = (
            8,
            [
                "tsconfig.json",
                "jest.config.ts",
                "eslintrc.json",
                "prettierrc.json",
                "package.json",
                "babel.config.js",
                "webpack.config.js",
                "vitest.config.ts",
            ],
        )

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    project_root=project_root,
                                    skip_commit=True,
                                )

        assert result == 0
        captured = capsys.readouterr()
        assert "... and 3 more" in captured.out

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    @patch("solokit.init.env_generator.generate_env_files")
    def test_run_adoption_handles_env_generation_failure(
        self,
        mock_env_files,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption continues when env file generation fails."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])
        mock_env_files.side_effect = RuntimeError("Env generation failed")

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    additional_options=["env_templates"],
                                    project_root=project_root,
                                    skip_commit=True,
                                )

        # Should still succeed despite env generation failure
        assert result == 0
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    @patch("solokit.adopt.orchestrator._create_adoption_commit")
    def test_run_adoption_creates_commit_when_not_skipped(
        self,
        mock_commit,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
    ):
        """Test run_adoption creates commit when skip_commit=False."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])
        mock_commit.return_value = True

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    project_root=project_root,
                                    skip_commit=False,
                                )

        assert result == 0
        mock_commit.assert_called_once()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    @patch("solokit.adopt.orchestrator._create_adoption_commit")
    def test_run_adoption_handles_commit_exception(
        self,
        mock_commit,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption continues when commit creation fails."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])
        mock_commit.side_effect = RuntimeError("Git error")

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                result = run_adoption(
                                    tier="tier-2-standard",
                                    coverage_target=80,
                                    project_root=project_root,
                                    skip_commit=False,
                                )

        # Should still succeed despite commit failure
        assert result == 0
        captured = capsys.readouterr()
        assert "commit" in captured.out.lower()

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_run_adoption_shows_additional_option_no_files(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption shows message when additional option has no files."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                with patch(
                                    "solokit.init.template_installer.install_additional_option"
                                ) as mock_option:
                                    mock_option.return_value = 0  # No files installed
                                    result = run_adoption(
                                        tier="tier-2-standard",
                                        coverage_target=80,
                                        additional_options=["ci_cd"],
                                        project_root=project_root,
                                        skip_commit=True,
                                    )

        assert result == 0
        captured = capsys.readouterr()
        assert "No files found" in captured.out

    @patch("solokit.adopt.orchestrator.detect_project_type")
    @patch("solokit.adopt.orchestrator.install_tier_configs")
    @patch("solokit.init.session_structure.create_session_directories")
    @patch("solokit.init.session_structure.initialize_tracking_files")
    def test_run_adoption_handles_additional_option_import_error(
        self,
        mock_tracking,
        mock_session_dirs,
        mock_tier_configs,
        mock_detect,
        tmp_path,
        capsys,
    ):
        """Test run_adoption handles ImportError for template_installer."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_info = ProjectInfo(
            language=ProjectLanguage.PYTHON,
            framework=ProjectFramework.NONE,
            package_manager=PackageManager.UNKNOWN,
            confidence=1.0,
        )

        mock_detect.return_value = project_info
        mock_tier_configs.return_value = (0, [])

        with patch("solokit.init.claude_commands_installer.install_claude_commands"):
            with patch("solokit.adopt.doc_appender.append_to_readme"):
                with patch("solokit.adopt.doc_appender.append_to_claude_md"):
                    with patch("solokit.adopt.orchestrator._update_gitignore_for_adoption"):
                        with patch("solokit.init.initial_scans.run_initial_scans") as mock_scans:
                            mock_scans.return_value = {}
                            with patch("solokit.init.git_hooks_installer.install_git_hooks"):
                                # Patch the import to fail
                                import builtins

                                original_import = builtins.__import__

                                def mock_import(name, *args, **kwargs):
                                    if name == "solokit.init.template_installer":
                                        raise ImportError("Module not found")
                                    return original_import(name, *args, **kwargs)

                                with patch("builtins.__import__", mock_import):
                                    result = run_adoption(
                                        tier="tier-2-standard",
                                        coverage_target=80,
                                        additional_options=["ci_cd"],
                                        project_root=project_root,
                                        skip_commit=True,
                                    )

        # Should still succeed despite import error
        assert result == 0
        captured = capsys.readouterr()
        assert "not available" in captured.out
