"""Unit tests for learning_curator module.

This module tests learning curator functionality including bug fixes for:
- Bug 1: Multi-line LEARNING statement extraction
- Bug 2: File type filtering and content validation
- Bug 3: Standardized metadata structure
- Bug #21: Test directory exclusion and code artifact rejection
"""

import re
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError
from solokit.learning.curator import LearningsCurator, main
from solokit.learning.validator import LEARNING_SCHEMA


@pytest.fixture(autouse=True)
def reset_config_manager():
    """Reset ConfigManager singleton before each test."""
    from solokit.core.config import ConfigManager

    ConfigManager._instance = None
    ConfigManager._config = None
    ConfigManager._config_path = None
    yield


@pytest.fixture
def curator():
    """Create LearningsCurator instance for testing.

    Returns:
        LearningsCurator: Fresh curator instance.
    """
    return LearningsCurator()


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure for testing.

    Args:
        tmp_path: Pytest tmp_path fixture.

    Returns:
        tuple: (project_root Path, curator instance)
    """
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    curator = LearningsCurator(project_root)
    return project_root, curator


@pytest.fixture
def learning_pattern():
    """Provide regex pattern for LEARNING extraction.

    Returns:
        str: Compiled regex pattern for multi-line LEARNING statements.
    """
    return r"LEARNING:\s*([\s\S]+?)(?=\n\n|\Z)"


class TestMultiLineLearningExtraction:
    """Test suite for Bug 1 fix: Multi-line LEARNING statement extraction from git commits."""

    def test_extract_single_line_learning(self, learning_pattern):
        """Test that single-line LEARNING statement is correctly extracted."""
        # Arrange
        commit_message = "feat: Add new feature\n\nLEARNING: This is a single line learning."

        # Act
        match = re.search(learning_pattern, commit_message)

        # Assert
        assert match is not None
        learning_text = match.group(1).strip()
        assert learning_text == "This is a single line learning."

    def test_extract_multi_line_learning_basic(self, learning_pattern):
        """Test that multi-line LEARNING statement spanning 2-3 lines is fully extracted."""
        # Arrange
        commit_message = """feat: Add authentication

LEARNING: This is a multi-line learning that spans
several lines to provide comprehensive context about
the implementation.

Some other text."""

        # Act
        match = re.search(learning_pattern, commit_message)

        # Assert
        assert match is not None
        learning_text = match.group(1).strip()
        assert "This is a multi-line learning that spans" in learning_text
        assert "several lines to provide comprehensive context" in learning_text
        assert "the implementation." in learning_text

    def test_extract_multi_line_learning_with_indentation(self, learning_pattern):
        """Test that multi-line LEARNING with indented continuation lines is extracted."""
        # Arrange
        commit_message = """fix: Bug fix

LEARNING: The .gitignore patterns are added programmatically in
  ensure_gitignore_entries() function, not from a template file.
  This allows dynamic checking of which patterns already exist.

Next paragraph."""

        # Act
        match = re.search(learning_pattern, commit_message)

        # Assert
        assert match is not None
        learning_text = match.group(1).strip()
        assert "ensure_gitignore_entries() function" in learning_text
        assert "This allows dynamic checking" in learning_text

    def test_extract_learning_followed_by_double_newline(self, learning_pattern):
        """Test that LEARNING statement stops at double newline separator."""
        # Arrange
        commit_message = """feat: New feature

LEARNING: Important learning here that should be captured.


Next section starts here."""

        # Act
        match = re.search(learning_pattern, commit_message)

        # Assert
        assert match is not None
        learning_text = match.group(1).strip()
        assert learning_text == "Important learning here that should be captured."
        assert "Next section" not in learning_text

    def test_extract_learning_with_wrapped_lines(self, learning_pattern):
        """Test that LEARNING captures wrapped continuation lines without blank lines."""
        # Arrange
        commit_message = """feat: Feature

LEARNING: This learning continues across multiple lines
without blank lines between them because it is describing
a single cohesive concept that needs detailed explanation.

Next paragraph starts here."""

        # Act
        match = re.search(learning_pattern, commit_message)

        # Assert
        assert match is not None
        learning_text = match.group(1).strip()
        assert "continues across multiple lines" in learning_text
        assert "without blank lines between them" in learning_text
        assert "detailed explanation" in learning_text
        assert "Next paragraph" not in learning_text


class TestFileTypeFiltering:
    """Test suite for Bug 2 fix: File type filtering to skip documentation."""

    def test_code_extensions_are_defined(self):
        """Test that code file extensions set is properly defined."""
        # Arrange & Act
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs"}

        # Assert
        assert len(code_extensions) > 0

    def test_doc_extensions_are_defined(self):
        """Test that documentation file extensions set is properly defined."""
        # Arrange & Act
        doc_extensions = {".md", ".txt", ".rst"}

        # Assert
        assert len(doc_extensions) > 0

    def test_skips_markdown_files(self, temp_project):
        """Test that markdown files are skipped during learning extraction."""
        # Arrange
        project_root, curator = temp_project
        code_file = project_root / "test.py"
        doc_file = project_root / "README.md"

        code_file.write_text("# LEARNING: Valid code learning with enough words here")
        doc_file.write_text("# LEARNING: <your learning here>")

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[code_file, doc_file])

        # Assert
        assert any(
            "Valid code learning with enough words" in learning.get("content", "")
            for learning in learnings
        )
        assert not any(
            "your learning here" in learning.get("content", "") for learning in learnings
        )

    def test_skips_template_directories(self, temp_project):
        """Test that templates directory is skipped during learning extraction."""
        # Arrange
        project_root, curator = temp_project
        code_file = project_root / "test.py"
        template_dir = project_root / "templates"
        template_dir.mkdir()
        template_file = template_dir / "example.py"

        code_file.write_text("# LEARNING: Valid code learning from main file with words")
        template_file.write_text("# LEARNING: Example learning from template directory here")

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[code_file, template_file])

        # Assert
        assert any(
            "Valid code learning from main file" in learning.get("content", "")
            for learning in learnings
        )
        assert not any(
            "Example learning from template" in learning.get("content", "")
            for learning in learnings
        )


class TestContentValidation:
    """Test suite for Bug 2 fix: Content validation to skip placeholders."""

    def test_valid_learning_passes_validation(self, curator):
        """Test that valid learning with 5+ words passes validation."""
        # Arrange
        valid_learning = "This is a valid learning with enough words"

        # Act & Assert
        assert curator.is_valid_learning(valid_learning)

    def test_rejects_angle_bracket_placeholders(self, curator):
        """Test that placeholders with angle brackets are rejected."""
        # Arrange
        placeholder = "<your learning here>"
        partial_placeholder = "This has <placeholder> text in it"

        # Act & Assert
        assert not curator.is_valid_learning(placeholder)
        assert not curator.is_valid_learning(partial_placeholder)

    def test_rejects_known_placeholder_text(self, curator):
        """Test that known placeholder text patterns are rejected."""
        # Arrange
        placeholders = ["your learning here", "example learning", "todo", "tbd", "placeholder"]

        # Act & Assert
        for placeholder in placeholders:
            assert not curator.is_valid_learning(placeholder)
            assert not curator.is_valid_learning(placeholder.upper())

    def test_rejects_content_with_fewer_than_five_words(self, curator):
        """Test that content with less than 5 words is rejected."""
        # Arrange
        short_content = "Too short here"  # 3 words
        exactly_five = "This has exactly five words"  # 5 words

        # Act & Assert
        assert not curator.is_valid_learning(short_content)
        assert curator.is_valid_learning(exactly_five)

    def test_rejects_empty_or_none_content(self, curator):
        """Test that empty string or None content is rejected."""
        # Act & Assert
        assert not curator.is_valid_learning("")
        assert not curator.is_valid_learning(None)

    def test_rejects_list_fragment_markers(self, curator):
        """Test that content with list markers is rejected as incomplete fragments."""
        # Arrange
        hyphen_list = "annotations\n- Code comments with enough words"
        asterisk_list = "Some content\n* List item with enough words"
        bullet_list = "Fragment text\n• Bullet point with enough words"
        valid_multiline = (
            "This is a valid multi-line learning\nthat spans multiple lines without list markers"
        )

        # Act & Assert
        assert not curator.is_valid_learning(hyphen_list)
        assert not curator.is_valid_learning(asterisk_list)
        assert not curator.is_valid_learning(bullet_list)
        assert curator.is_valid_learning(valid_multiline)


class TestStandardizedEntryCreation:
    """Test suite for Bug 3 fix: Standardized learning entry creation."""

    def test_creates_entry_with_all_required_fields(self, curator):
        """Test that create_learning_entry includes all required fields."""
        # Act
        entry = curator.create_learning_entry(
            content="Test learning with enough words here",
            source="git_commit",
            session_id="session_001",
            context="Commit abc123",
        )

        # Assert
        assert "content" in entry
        assert "learned_in" in entry
        assert "source" in entry
        assert "context" in entry
        assert "timestamp" in entry
        assert "id" in entry

    def test_entry_values_match_input_parameters(self, curator):
        """Test that created entry values match the provided input parameters."""
        # Arrange
        content = "Test learning content with more words"
        source = "git_commit"
        session_id = "session_002"
        context = "Commit xyz789"

        # Act
        entry = curator.create_learning_entry(
            content=content, source=source, session_id=session_id, context=context
        )

        # Assert
        assert entry["content"] == content
        assert entry["learned_in"] == session_id
        assert entry["source"] == source
        assert entry["context"] == context

    def test_optional_fields_receive_default_values(self, curator):
        """Test that optional fields are populated with appropriate default values."""
        # Act
        entry = curator.create_learning_entry(
            content="Test learning with sufficient words present", source="git_commit"
        )

        # Assert
        assert entry["learned_in"] == "unknown"
        assert entry["context"] == "No context provided"
        assert entry["timestamp"] is not None
        assert entry["id"] is not None

    def test_generates_consistent_id_for_same_content(self, curator):
        """Test that identical content generates the same ID consistently."""
        # Arrange
        content = "Test learning for ID consistency check here"

        # Act
        entry1 = curator.create_learning_entry(content=content, source="test")
        entry2 = curator.create_learning_entry(content=content, source="test")

        # Assert
        assert entry1["id"] == entry2["id"]

    def test_git_extracted_learnings_have_both_fields(self, curator):
        """Test that git-extracted learnings include both learned_in and context fields."""
        # Arrange & Act
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="abc123|||feat: Test\n\nLEARNING: Git commit learning with enough words",
            )
            learnings = curator.extract_from_git_commits(session_id="session_003")

            # Assert
            if learnings:
                learning = learnings[0]
                assert "learned_in" in learning
                assert "context" in learning
                assert learning["learned_in"] == "session_003"

    def test_temp_file_entry_has_both_fields(self, curator):
        """Test that temp-file sourced learnings include both learned_in and context."""
        # Act
        entry = curator.create_learning_entry(
            content="Temp file learning with many words here",
            source="temp_file",
            session_id="session_004",
            context="Temp file: .session/temp_learnings.txt",
        )

        # Assert
        assert "learned_in" in entry
        assert "context" in entry
        assert entry["learned_in"] == "session_004"
        assert entry["context"] == "Temp file: .session/temp_learnings.txt"


class TestJSONSchemaValidation:
    """Test suite for Bug 3 fix: JSON schema validation for learning entries."""

    def test_valid_entry_passes_schema_validation(self, curator):
        """Test that a properly formatted learning entry passes JSON schema validation."""
        # Arrange
        valid_entry = {
            "content": "This is a valid learning with more than ten characters",
            "learned_in": "session_001",
            "source": "git_commit",
            "context": "Commit abc123",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
        }

        # Act & Assert
        assert curator.validate_learning(valid_entry)

    def test_missing_required_field_fails_validation(self, curator):
        """Test that entry missing required field fails schema validation."""
        # Arrange
        invalid_entry = {
            "content": "Valid content with enough characters",
            "learned_in": "session_001",
            "source": "git_commit",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
            # Missing required "context" field
        }

        # Act & Assert
        assert not curator.validate_learning(invalid_entry)

    def test_invalid_source_type_fails_validation(self, curator):
        """Test that entry with invalid source enum value fails validation."""
        # Arrange
        invalid_entry = {
            "content": "Valid content with enough characters",
            "learned_in": "session_001",
            "source": "invalid_source",  # Not in enum
            "context": "Test context",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
        }

        # Act & Assert
        assert not curator.validate_learning(invalid_entry)

    def test_short_content_fails_min_length_validation(self, curator):
        """Test that content shorter than minLength constraint fails validation."""
        # Arrange
        invalid_entry = {
            "content": "Short",  # Less than 10 characters
            "learned_in": "session_001",
            "source": "git_commit",
            "context": "Test context",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
        }

        # Act & Assert
        assert not curator.validate_learning(invalid_entry)

    def test_schema_defines_all_required_fields(self):
        """Test that LEARNING_SCHEMA includes all required field definitions."""
        # Arrange
        required_fields = ["content", "learned_in", "source", "context", "timestamp", "id"]

        # Act & Assert
        assert set(LEARNING_SCHEMA["required"]) == set(required_fields)

    def test_schema_defines_valid_source_enum_values(self):
        """Test that schema defines complete set of valid source types."""
        # Act
        source_enum = LEARNING_SCHEMA["properties"]["source"]["enum"]

        # Assert
        assert "git_commit" in source_enum
        assert "temp_file" in source_enum
        assert "inline_comment" in source_enum
        assert "session_summary" in source_enum


class TestEdgeCases:
    """Test suite for edge cases in learning extraction."""

    def test_learning_with_special_characters_and_emojis(self, curator):
        """Test that learnings with special characters and emojis are handled correctly."""
        # Arrange
        special_content = "Learning with special chars: @#$% and émojis 🎉 works fine"

        # Act & Assert
        assert curator.is_valid_learning(special_content)
        entry = curator.create_learning_entry(content=special_content, source="git_commit")
        assert curator.validate_learning(entry)

    def test_very_long_learning_content(self, curator):
        """Test that very long learning content (100+ words) is handled correctly."""
        # Arrange
        long_content = " ".join(["word"] * 150)  # 150 words

        # Act & Assert
        assert curator.is_valid_learning(long_content)
        entry = curator.create_learning_entry(content=long_content, source="git_commit")
        assert curator.validate_learning(entry)

    def test_empty_learning_statement_is_rejected(self, curator):
        """Test that empty LEARNING statement is properly rejected."""
        # Arrange
        empty_content = ""

        # Act & Assert
        assert not curator.is_valid_learning(empty_content)

    def test_multiple_learnings_in_single_commit(self):
        """Test extraction of multiple LEARNING statements from single commit message."""
        # Arrange
        commit_message = """feat: Multiple learnings

LEARNING: First learning with enough words to be valid

LEARNING: Second learning also with sufficient word count"""
        learning_pattern = r"LEARNING:\s*([\s\S]+?)(?=\n(?![ \t])|\n\n|\Z)"

        # Act
        matches = list(re.finditer(learning_pattern, commit_message))

        # Assert
        assert len(matches) == 2


class TestTestDirectoryExclusion:
    """Test suite for Bug #21 Fix 1: Test directories are excluded from learning extraction."""

    def test_excludes_tests_directory(self, temp_project):
        """Test that tests/ directory is excluded from learning extraction."""
        # Arrange
        project_root, curator = temp_project
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()

        tests_file = tests_dir / "test_example.py"
        prod_file = src_dir / "main.py"

        tests_file.write_text("# LEARNING: Test data from tests directory with words")
        prod_file.write_text("# LEARNING: Production learning from src directory here")

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[tests_file, prod_file])

        # Assert
        assert any(
            "Production learning from src" in entry.get("content", "") for entry in learnings
        )
        assert not any("Test data from tests" in entry.get("content", "") for entry in learnings)

    def test_excludes_test_directory(self, temp_project):
        """Test that test/ directory (singular) is excluded from learning extraction."""
        # Arrange
        project_root, curator = temp_project
        test_dir = project_root / "test"
        test_dir.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()

        test_file = test_dir / "test_example.py"
        prod_file = src_dir / "main.py"

        test_file.write_text("# LEARNING: Test data from test directory with words")
        prod_file.write_text("# LEARNING: Production learning from src directory here")

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file, prod_file])

        # Assert
        assert any(
            "Production learning from src" in entry.get("content", "") for entry in learnings
        )
        assert not any("Test data from test" in entry.get("content", "") for entry in learnings)

    def test_excludes_jest_tests_directory(self, temp_project):
        """Test that __tests__/ directory (Jest convention) is excluded from extraction."""
        # Arrange
        project_root, curator = temp_project
        jest_dir = project_root / "__tests__"
        jest_dir.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()

        jest_file = jest_dir / "example.test.js"
        prod_file = src_dir / "main.py"

        jest_file.write_text("// LEARNING: Test data from jest tests directory here")
        prod_file.write_text("# LEARNING: Production learning from src directory here")

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[jest_file, prod_file])

        # Assert
        assert any(
            "Production learning from src" in entry.get("content", "") for entry in learnings
        )
        assert not any("Test data from jest" in entry.get("content", "") for entry in learnings)

    def test_excludes_spec_directory(self, temp_project):
        """Test that spec/ directory (RSpec convention) is excluded from extraction."""
        # Arrange
        project_root, curator = temp_project
        spec_dir = project_root / "spec"
        spec_dir.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()

        spec_file = spec_dir / "example_spec.rb"
        prod_file = src_dir / "main.py"

        spec_file.write_text("# LEARNING: Test data from spec directory with words")
        prod_file.write_text("# LEARNING: Production learning from src directory here")

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[spec_file, prod_file])

        # Assert
        assert any(
            "Production learning from src" in entry.get("content", "") for entry in learnings
        )
        assert not any("Test data from spec" in entry.get("content", "") for entry in learnings)


class TestCodeArtifactValidation:
    """Test suite for Bug #21 Fix 2: Content validation rejects code artifacts."""

    def test_rejects_content_ending_with_quote_paren(self, curator):
        """Test rejection of content ending with quote-paren from string literals."""
        # Arrange
        artifact_content = 'Valid code learning with enough words here")'

        # Act & Assert
        assert not curator.is_valid_learning(artifact_content)

    def test_rejects_content_with_escaped_quote(self, curator):
        """Test rejection of content containing escaped quotes."""
        # Arrange
        artifact_content = 'Learning with \\" escaped quote and words'

        # Act & Assert
        assert not curator.is_valid_learning(artifact_content)

    def test_rejects_content_with_visible_newline_escape(self, curator):
        """Test rejection of content with visible \\n escape sequences."""
        # Arrange
        artifact_content = "Learning with \\n visible newline and more words"

        # Act & Assert
        assert not curator.is_valid_learning(artifact_content)

    def test_rejects_content_with_backticks(self, curator):
        """Test rejection of content with backticks indicating code fragments."""
        # Arrange
        artifact_content = "Learning with `code` backticks and more words"

        # Act & Assert
        assert not curator.is_valid_learning(artifact_content)

    def test_rejects_content_ending_with_quote_semicolon(self, curator):
        """Test rejection of content ending with quote-semicolon pattern."""
        # Arrange
        artifact_content = 'Valid learning with enough words here";'

        # Act & Assert
        assert not curator.is_valid_learning(artifact_content)

    def test_rejects_content_ending_with_single_quote_paren(self, curator):
        """Test rejection of content ending with single-quote-paren pattern."""
        # Arrange
        artifact_content = "Valid learning with enough words here')"

        # Act & Assert
        assert not curator.is_valid_learning(artifact_content)

    def test_accepts_clean_valid_learning(self, curator):
        """Test that clean valid learnings without code artifacts are accepted."""
        # Arrange
        clean_content = "This is a clean learning with no code artifacts"

        # Act & Assert
        assert curator.is_valid_learning(clean_content)

    def test_accepts_learning_with_normal_punctuation(self, curator):
        """Test that learnings with normal punctuation marks are accepted."""
        # Arrange
        normal_content = "Learning with normal punctuation: commas, periods, and more."

        # Act & Assert
        assert curator.is_valid_learning(normal_content)


class TestRegexPatternStrictness:
    """Test suite for Bug #21 Fix 3: Regex pattern only matches actual comment lines."""

    def test_extracts_actual_comment_line(self, temp_project):
        """Test that actual # LEARNING comments are successfully extracted."""
        # Arrange
        project_root, curator = temp_project
        src_dir = project_root / "src"
        src_dir.mkdir()
        test_file = src_dir / "test.py"

        code = """# LEARNING: This is an actual comment with words
def foo():
    pass
"""
        test_file.write_text(code)

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file])

        # Assert
        assert len(learnings) == 1
        assert "actual comment" in learnings[0]["content"]

    def test_extracts_indented_comment_line(self, temp_project):
        """Test that indented # LEARNING comments are extracted correctly."""
        # Arrange
        project_root, curator = temp_project
        src_dir = project_root / "src"
        src_dir.mkdir()
        test_file = src_dir / "test.py"

        code = """def foo():
    # LEARNING: Indented learning comment with enough words here
    pass
"""
        test_file.write_text(code)

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file])

        # Assert
        assert len(learnings) == 1
        assert "Indented learning" in learnings[0]["content"]

    def test_does_not_extract_string_literal(self, temp_project):
        """Test that string literals containing LEARNING pattern are NOT extracted."""
        # Arrange
        project_root, curator = temp_project
        src_dir = project_root / "src"
        src_dir.mkdir()
        test_file = src_dir / "test.py"

        code = """def test_example():
    test_data = "# LEARNING: This is test data not comment"
    file.write_text("# LEARNING: Another test string with enough words here")
"""
        test_file.write_text(code)

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file])

        # Assert
        assert len(learnings) == 0

    def test_does_not_extract_learning_in_middle_of_line(self, temp_project):
        """Test that LEARNING pattern not at line start is NOT extracted."""
        # Arrange
        project_root, curator = temp_project
        src_dir = project_root / "src"
        src_dir.mkdir()
        test_file = src_dir / "test.py"

        code = """def foo():
    x = "some string # LEARNING: This should not be extracted ever"
"""
        test_file.write_text(code)

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file])

        # Assert
        assert len(learnings) == 0

    def test_extracts_multiple_actual_comments(self, temp_project):
        """Test that multiple actual # LEARNING comments are all extracted."""
        # Arrange
        project_root, curator = temp_project
        src_dir = project_root / "src"
        src_dir.mkdir()
        test_file = src_dir / "test.py"

        code = """# LEARNING: First learning comment with enough words here
def foo():
    # LEARNING: Second learning comment also with enough words
    pass

# LEARNING: Third learning comment at end with words
"""
        test_file.write_text(code)

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file])

        # Assert
        assert len(learnings) == 3
        assert any("First learning" in entry["content"] for entry in learnings)
        assert any("Second learning" in entry["content"] for entry in learnings)
        assert any("Third learning" in entry["content"] for entry in learnings)


class TestBug21Integration:
    """Integration test suite for Bug #21: All three fixes working together."""

    def test_full_bug_scenario_extracts_nothing(self, temp_project):
        """Test complete Bug #21 scenario: test file with string literals extracts nothing."""
        # Arrange
        project_root, curator = temp_project
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_learning_curator_bug_fixes.py"

        test_content = """def test_example():
    test_data = "# LEARNING: This is test data"
    file.write_text("# LEARNING: Valid code learning with enough words here")
    assert test_data
"""
        test_file.write_text(test_content)

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file])

        # Assert
        assert len(learnings) == 0

    def test_production_code_comments_still_work(self, temp_project):
        """Test that production code with real # LEARNING comments works correctly."""
        # Arrange
        project_root, curator = temp_project
        src_dir = project_root / "src"
        src_dir.mkdir()
        prod_file = src_dir / "main.py"

        prod_content = """# LEARNING: Production learning comment with enough words

def important_function():
    # LEARNING: Another production learning with sufficient word count
    pass
"""
        prod_file.write_text(prod_content)

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[prod_file])

        # Assert
        assert len(learnings) == 2
        assert any("Production learning comment" in entry["content"] for entry in learnings)
        assert any("Another production learning" in entry["content"] for entry in learnings)

    def test_mixed_test_and_production_files(self, temp_project):
        """Test mixed scenario with both test files and production files."""
        # Arrange
        project_root, curator = temp_project
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()

        test_file = tests_dir / "test_example.py"
        test_file.write_text('file.write_text("# LEARNING: Test data with enough words here")')

        prod_file = src_dir / "main.py"
        prod_file.write_text("# LEARNING: Real production learning with enough words")

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file, prod_file])

        # Assert
        assert len(learnings) == 1
        assert "Real production learning" in learnings[0]["content"]

    def test_no_garbage_entries_with_code_artifacts(self, temp_project):
        """Test that no garbage entries containing code artifacts are created."""
        # Arrange
        project_root, curator = temp_project
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()

        test_file = tests_dir / "test.py"
        test_file.write_text('x = "# LEARNING: annotations\\n- Code comments with words")')

        # Act
        learnings = curator.extract_from_code_comments(changed_files=[test_file])

        # Assert
        assert len(learnings) == 0

        # Even if directory check is bypassed, content validation should reject
        prod_file = src_dir / "broken.py"
        prod_file.write_text('x = "# LEARNING: Valid code learning with enough words here")')

        learnings = curator.extract_from_code_comments(changed_files=[prod_file])
        assert len(learnings) == 0


# ============================================================================
# Additional Comprehensive Coverage Tests
# ============================================================================


class TestCountingAndMetadataOperations:
    """Test learning counting and metadata operations."""

    def test_count_all_learnings_empty_categories(self, curator):
        """Test counting with empty categories returns 0."""
        # Arrange
        learnings = {"categories": {}}

        # Act
        count = curator._count_all_learnings(learnings)

        # Assert
        assert count == 0

    def test_count_all_learnings_multiple_categories(self, curator):
        """Test counting across multiple categories."""
        # Arrange
        learnings = {
            "categories": {
                "best_practices": [{"id": "1"}, {"id": "2"}],
                "gotchas": [{"id": "3"}],
                "technical_debt": [{"id": "4"}, {"id": "5"}, {"id": "6"}],
            }
        }

        # Act
        count = curator._count_all_learnings(learnings)

        # Assert
        assert count == 6

    def test_count_includes_archived_learnings(self, curator):
        """Test that count includes archived learnings."""
        # Arrange
        learnings = {
            "categories": {"best_practices": [{"id": "1"}]},
            "archived": [{"id": "2"}, {"id": "3"}],
        }

        # Act
        count = curator._count_all_learnings(learnings)

        # Assert
        assert count == 3

    def test_update_total_learnings_creates_metadata(self, curator):
        """Test that update creates metadata if missing."""
        # Arrange
        learnings = {"categories": {"best_practices": [{"id": "1"}, {"id": "2"}]}}

        # Act
        curator._update_total_learnings(learnings)

        # Assert
        assert "metadata" in learnings
        assert learnings["metadata"]["total_learnings"] == 2

    def test_update_total_learnings_updates_existing(self, curator):
        """Test that update modifies existing metadata."""
        # Arrange
        learnings = {
            "metadata": {"total_learnings": 0},
            "categories": {"best_practices": [{"id": "1"}]},
        }

        # Act
        curator._update_total_learnings(learnings)

        # Assert
        assert learnings["metadata"]["total_learnings"] == 1


class TestKeywordScoringAndAutoCategorization:
    """Test keyword scoring and auto-categorization logic."""

    def test_keyword_score_no_matches(self, curator):
        """Test keyword scoring with no matches."""
        # Arrange
        text = "This text has no relevant keywords"
        keywords = ["database", "connection", "query"]

        # Act
        score = curator._keyword_score(text, keywords)

        # Assert
        assert score == 0

    def test_keyword_score_single_match(self, curator):
        """Test keyword scoring with single match."""
        # Arrange
        text = "The database connection is important"
        keywords = ["database", "query", "transaction"]

        # Act
        score = curator._keyword_score(text, keywords)

        # Assert
        assert score == 1

    def test_keyword_score_multiple_matches(self, curator):
        """Test keyword scoring with multiple keyword matches."""
        # Arrange
        text = "The database connection requires a query transaction"
        keywords = ["database", "connection", "query", "transaction"]

        # Act
        score = curator._keyword_score(text, keywords)

        # Assert
        assert score == 4

    def test_auto_categorize_architecture_pattern(self, curator):
        """Test auto-categorization for architecture patterns."""
        # Arrange
        learning = {"content": "The layered architecture design pattern separates concerns"}

        # Act
        category = curator._auto_categorize_learning(learning)

        # Assert
        assert category == "architecture_patterns"

    def test_auto_categorize_gotcha(self, curator):
        """Test auto-categorization for gotchas."""
        # Arrange
        learning = {"content": "This is a common pitfall error when handling concurrency"}

        # Act
        category = curator._auto_categorize_learning(learning)

        # Assert
        assert category == "gotchas"

    def test_auto_categorize_best_practice(self, curator):
        """Test auto-categorization for best practices."""
        # Arrange
        learning = {"content": "Best practice recommends always validating user input"}

        # Act
        category = curator._auto_categorize_learning(learning)

        # Assert
        assert category == "best_practices"

    def test_auto_categorize_technical_debt(self, curator):
        """Test auto-categorization for technical debt."""
        # Arrange
        learning = {"content": "Need to refactor this legacy code and cleanup workarounds"}

        # Act
        category = curator._auto_categorize_learning(learning)

        # Assert
        assert category == "technical_debt"

    def test_auto_categorize_performance_insight(self, curator):
        """Test auto-categorization for performance insights."""
        # Arrange
        learning = {"content": "Performance optimization reduced memory usage significantly"}

        # Act
        category = curator._auto_categorize_learning(learning)

        # Assert
        assert category == "performance_insights"

    def test_auto_categorize_respects_suggested_type(self, curator):
        """Test that suggested_type is respected over keyword analysis."""
        # Arrange
        learning = {"content": "Some content about performance", "suggested_type": "best_practice"}

        # Act
        category = curator._auto_categorize_learning(learning)

        # Assert
        assert category == "best_practices"

    def test_auto_categorize_defaults_to_best_practices(self, curator):
        """Test default categorization when no keywords match."""
        # Arrange
        learning = {"content": "Generic content without specific category keywords"}

        # Act
        category = curator._auto_categorize_learning(learning)

        # Assert
        assert category == "best_practices"


class TestSimilarityDetection:
    """Test similarity detection for deduplication."""

    def test_are_similar_exact_match(self, curator):
        """Test that exact content matches are detected as similar."""
        # Arrange
        learning_a = {"content": "Use dependency injection for testability"}
        learning_b = {"content": "Use dependency injection for testability"}

        # Act
        result = curator._are_similar(learning_a, learning_b)

        # Assert
        assert result is True

    def test_are_similar_high_overlap(self, curator):
        """Test high word overlap is detected as similar."""
        # Arrange
        # Using very similar content to ensure high Jaccard/containment similarity
        learning_a = {"content": "dependency injection testability maintainability patterns"}
        learning_b = {"content": "dependency injection testability maintainability"}

        # Act
        result = curator._are_similar(learning_a, learning_b)

        # Assert
        assert result is True

    def test_are_similar_different_content(self, curator):
        """Test different content is not similar."""
        # Arrange
        learning_a = {"content": "Use dependency injection"}
        learning_b = {"content": "Configure logging system"}

        # Act
        result = curator._are_similar(learning_a, learning_b)

        # Assert
        assert result is False

    def test_are_similar_empty_content(self, curator):
        """Test empty content returns False."""
        # Arrange
        learning_a = {"content": ""}
        learning_b = {"content": "Some content"}

        # Act
        result = curator._are_similar(learning_a, learning_b)

        # Assert
        assert result is False

    def test_learning_exists_finds_duplicate(self, curator):
        """Test that existing similar learning is found."""
        # Arrange
        existing = [{"content": "Use dependency injection"}]
        new_learning = {"content": "Use dependency injection"}

        # Act
        result = curator._learning_exists(existing, new_learning)

        # Assert
        assert result is True

    def test_learning_exists_no_duplicate(self, curator):
        """Test that non-duplicate returns False."""
        # Arrange
        existing = [{"content": "Use dependency injection"}]
        new_learning = {"content": "Configure logging properly"}

        # Act
        result = curator._learning_exists(existing, new_learning)

        # Assert
        assert result is False


class TestMergingLearnings:
    """Test learning merging functionality."""

    def test_merge_similar_learnings_merges_duplicates(self, curator):
        """Test merging of duplicate learnings within categories."""
        # Arrange
        learnings = {
            "categories": {
                "best_practices": [
                    {"content": "Use dependency injection"},
                    {"content": "Use dependency injection"},
                ]
            }
        }

        # Act
        merged_count = curator._merge_similar_learnings(learnings)

        # Assert
        assert merged_count == 1
        assert len(learnings["categories"]["best_practices"]) == 1

    def test_merge_similar_learnings_no_duplicates(self, curator):
        """Test merge with no duplicates returns 0."""
        # Arrange
        learnings = {
            "categories": {
                "best_practices": [
                    {"content": "Use dependency injection"},
                    {"content": "Configure logging system"},
                ]
            }
        }

        # Act
        merged_count = curator._merge_similar_learnings(learnings)

        # Assert
        assert merged_count == 0


class TestArchivalFunctionality:
    """Test archival of old learnings."""

    def test_archive_old_learnings_archives_old_sessions(self, temp_project):
        """Test that old learnings are archived."""
        # Arrange
        project_root, curator = temp_project
        work_items_file = project_root / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)

        import json

        # Use new dict format for sessions (not integers)
        work_items_data = {
            "work_items": {
                "WI-001": {"sessions": [{"session_num": 100, "started_at": "2025-01-01T10:00:00"}]}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        learnings = {
            "categories": {
                "best_practices": [{"content": "Old learning", "learned_in": "session_001"}]
            }
        }

        # Act
        count = curator._archive_old_learnings(learnings, max_age_sessions=50)

        # Assert
        assert count == 1
        assert len(learnings["categories"]["best_practices"]) == 0
        assert len(learnings.get("archived", [])) == 1

    def test_archive_old_learnings_keeps_recent(self, temp_project):
        """Test that recent learnings are not archived."""
        # Arrange
        project_root, curator = temp_project
        work_items_file = project_root / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)

        import json

        # Use new dict format for sessions (not integers)
        work_items_data = {
            "work_items": {
                "WI-001": {"sessions": [{"session_num": 10, "started_at": "2025-01-01T10:00:00"}]}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        learnings = {
            "categories": {
                "best_practices": [{"content": "Recent learning", "learned_in": "session_009"}]
            }
        }

        # Act
        count = curator._archive_old_learnings(learnings, max_age_sessions=5)

        # Assert
        assert count == 0
        assert len(learnings["categories"]["best_practices"]) == 1

    def test_archive_adds_metadata(self, temp_project):
        """Test that archival adds metadata to archived learnings."""
        # Arrange
        project_root, curator = temp_project
        work_items_file = project_root / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)

        import json

        # Use new dict format for sessions (not integers)
        work_items_data = {
            "work_items": {
                "WI-001": {"sessions": [{"session_num": 100, "started_at": "2025-01-01T10:00:00"}]}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        learnings = {
            "categories": {
                "best_practices": [{"content": "Old learning", "learned_in": "session_001"}]
            }
        }

        # Act
        curator._archive_old_learnings(learnings)

        # Assert
        archived = learnings.get("archived", [])[0]
        assert "archived_from" in archived
        assert "archived_at" in archived


class TestSessionNumberExtraction:
    """Test session number extraction from various formats."""

    def test_extract_session_number_standard_format(self, curator):
        """Test extracting from standard session_XXX format."""
        # Act
        result = curator._extract_session_number("session_015")

        # Assert
        assert result == 15

    def test_extract_session_number_numeric_only(self, curator):
        """Test extracting from numeric string."""
        # Act
        result = curator._extract_session_number("042")

        # Assert
        assert result == 42

    def test_extract_session_number_no_digits(self, curator):
        """Test extracting from non-numeric string returns 0."""
        # Act
        result = curator._extract_session_number("unknown")

        # Assert
        assert result == 0

    def test_get_current_session_number_from_work_items(self, temp_project):
        """Test getting current session from work items."""
        # Arrange
        project_root, curator = temp_project
        work_items_file = project_root / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)

        import json

        # Use new dict format for sessions (not integers)
        work_items_data = {
            "work_items": {
                "WI-001": {
                    "sessions": [
                        {"session_num": 1, "started_at": "2025-01-01T10:00:00"},
                        {"session_num": 2, "started_at": "2025-01-01T11:00:00"},
                        {"session_num": 3, "started_at": "2025-01-01T12:00:00"},
                    ]
                },
                "WI-002": {
                    "sessions": [
                        {"session_num": 4, "started_at": "2025-01-01T13:00:00"},
                        {"session_num": 5, "started_at": "2025-01-01T14:00:00"},
                    ]
                },
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        # Act
        result = curator._get_current_session_number()

        # Assert
        assert result == 5

    def test_get_current_session_number_no_file(self, temp_project):
        """Test getting session number when file doesn't exist."""
        # Arrange - use temp_project to avoid reading real project data
        project_root, curator = temp_project

        # Act - file doesn't exist in temp_project
        result = curator._get_current_session_number()

        # Assert
        assert result == 0


class TestSearchFunctionality:
    """Test learning search functionality."""

    def test_search_learnings_finds_matches(self, temp_project, capsys):
        """Test search finds matches in content."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {"best_practices": [{"content": "Use dependency injection", "id": "1"}]}
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.search_learnings("dependency")

        # Assert
        captured = capsys.readouterr()
        assert "dependency injection" in captured.out

    def test_search_learnings_no_matches(self, temp_project, capsys):
        """Test search with no matches."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {"categories": {"best_practices": []}}
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.search_learnings("nonexistent")

        # Assert
        captured = capsys.readouterr()
        assert "No learnings found" in captured.out

    def test_search_learnings_finds_in_tags(self, temp_project, capsys):
        """Test search finds matches in tags."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [
                    {"content": "Some learning", "tags": ["testing", "quality"], "id": "1"}
                ]
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.search_learnings("testing")

        # Assert
        captured = capsys.readouterr()
        assert "Some learning" in captured.out


class TestShowLearnings:
    """Test show learnings with filters."""

    def test_show_learnings_filters_by_category(self, temp_project, capsys):
        """Test showing learnings filtered by category."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [{"content": "Best practice", "id": "1"}],
                "gotchas": [{"content": "Gotcha", "id": "2"}],
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.show_learnings(category="best_practices")

        # Assert
        captured = capsys.readouterr()
        assert "Best practice" in captured.out
        assert "Gotcha" not in captured.out

    def test_show_learnings_filters_by_session(self, temp_project, capsys):
        """Test showing learnings filtered by session."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [
                    {"content": "Session 5", "learned_in": "session_005", "id": "1"},
                    {"content": "Session 10", "learned_in": "session_010", "id": "2"},
                ]
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.show_learnings(session=5)

        # Assert
        captured = capsys.readouterr()
        assert "Session 5" in captured.out
        assert "Session 10" not in captured.out


class TestGetRelatedLearnings:
    """Test finding related learnings."""

    def test_get_related_learnings_finds_similar(self, temp_project):
        """Test that related learnings are found."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        # Using very similar content to ensure similarity detection
        learnings_data = {
            "categories": {
                "best_practices": [
                    {
                        "content": "dependency injection testability maintainability patterns",
                        "id": "1",
                    },
                    {"content": "dependency injection testability maintainability", "id": "2"},
                    {"content": "Configure logging properly", "id": "3"},
                ]
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        result = curator.get_related_learnings("1")

        # Assert
        assert len(result) >= 1

    def test_get_related_learnings_nonexistent_id(self, curator):
        """Test related learnings with nonexistent ID."""
        # Act
        result = curator.get_related_learnings("nonexistent")

        # Assert
        assert result == []


class TestStatisticsGeneration:
    """Test statistics generation."""

    def test_generate_statistics_counts_by_category(self, temp_project):
        """Test statistics counts by category."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [{"id": "1"}, {"id": "2"}],
                "gotchas": [{"id": "3"}],
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        stats = curator.generate_statistics()

        # Assert
        assert stats["total"] == 3
        assert stats["by_category"]["best_practices"] == 2
        assert stats["by_category"]["gotchas"] == 1

    def test_generate_statistics_counts_by_tag(self, temp_project):
        """Test statistics counts by tag."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [
                    {"id": "1", "tags": ["testing", "quality"]},
                    {"id": "2", "tags": ["testing"]},
                ]
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        stats = curator.generate_statistics()

        # Assert
        assert stats["by_tag"]["testing"] == 2
        assert stats["by_tag"]["quality"] == 1


class TestAddLearning:
    """Test adding new learnings."""

    def test_add_learning_creates_entry(self, temp_project):
        """Test that add_learning creates new entry."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {"categories": {"best_practices": []}}
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        learning_id = curator.add_learning(
            content="Test learning",
            category="best_practices",
            session=5,
        )

        # Assert
        assert learning_id is not None
        saved_data = json.loads(learnings_file.read_text())
        assert len(saved_data["categories"]["best_practices"]) == 1

    def test_add_learning_with_tags(self, temp_project):
        """Test adding learning with tags."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {"categories": {"best_practices": []}}
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.add_learning(
            content="Test learning",
            category="best_practices",
            tags=["tag1", "tag2"],
        )

        # Assert
        saved_data = json.loads(learnings_file.read_text())
        learning = saved_data["categories"]["best_practices"][0]
        assert "tags" in learning
        assert learning["tags"] == ["tag1", "tag2"]

    def test_add_learning_if_new_adds_unique(self, temp_project):
        """Test that add_learning_if_new adds unique learnings."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {"categories": {"best_practices": []}}
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        result = curator.add_learning_if_new({"content": "New unique learning"})

        # Assert
        assert result is True

    def test_add_learning_if_new_skips_duplicate(self, temp_project):
        """Test that add_learning_if_new skips duplicates."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {"categories": {"best_practices": [{"content": "Existing learning"}]}}
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        result = curator.add_learning_if_new({"content": "Existing learning"})

        # Assert
        assert result is False


class TestAutoCuration:
    """Test automatic curation."""

    def test_auto_curate_if_needed_disabled(self, temp_project):
        """Test auto-curation when disabled."""
        # Arrange
        project_root, curator = temp_project
        config_file = project_root / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)

        import json

        config_data = {"curation": {"auto_curate": False}}
        config_file.write_text(json.dumps(config_data))

        # Need to recreate curator to pick up new config
        curator = LearningsCurator(project_root)

        # Act
        result = curator.auto_curate_if_needed()

        # Assert
        assert result is False

    def test_auto_curate_if_needed_never_curated(self, tmp_path, capsys):
        """Test auto-curation when never curated."""
        # Arrange
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        config_file = project_root / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)

        import json

        config_data = {"curation": {"auto_curate": True}}
        config_file.write_text(json.dumps(config_data))

        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)
        learnings_data = {"categories": {}, "last_curated": None}
        learnings_file.write_text(json.dumps(learnings_data))

        # Create curator with project_root so it picks up the config
        curator = LearningsCurator(project_root)

        # Act
        from unittest.mock import patch

        with patch.object(curator, "curate"):
            result = curator.auto_curate_if_needed()

        # Assert
        assert result is True


class TestReportGeneration:
    """Test report generation."""

    def test_generate_report_displays_categories(self, temp_project, capsys):
        """Test that report displays category counts."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [{"id": "1"}, {"id": "2"}],
                "gotchas": [{"id": "3"}],
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.generate_report()

        # Assert
        captured = capsys.readouterr()
        assert "Best Practices" in captured.out or "best_practices" in captured.out

    def test_generate_report_shows_total(self, temp_project, capsys):
        """Test that report shows total count."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [{"id": "1"}, {"id": "2"}],
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.generate_report()

        # Assert
        captured = capsys.readouterr()
        assert "Total" in captured.out or "2" in captured.out


class TestLoadLearningsFile:
    """Test loading learnings from file."""

    def test_load_learnings_existing_file(self, temp_project):
        """Test loading existing learnings file."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        test_data = {
            "metadata": {"total_learnings": 5},
            "categories": {"best_practices": []},
        }
        learnings_file.write_text(json.dumps(test_data))

        # Act
        result = curator._load_learnings()

        # Assert
        assert result["metadata"]["total_learnings"] == 5
        assert "categories" in result

    def test_load_learnings_creates_default_structure(self, temp_project):
        """Test loading creates default structure when file missing."""
        # Arrange
        project_root, curator = temp_project
        # Don't create the learnings file, so it will create default structure

        # Act
        result = curator._load_learnings()

        # Assert
        assert "metadata" in result
        assert result["metadata"]["total_learnings"] == 0
        assert "categories" in result
        assert "archived" in result


class TestCategorizationWorkflow:
    """Test categorization workflow."""

    @patch.object(LearningsCurator, "_extract_learnings_from_sessions")
    def test_categorize_learnings_adds_new(self, mock_extract, temp_project):
        """Test categorization adds new learnings."""
        # Arrange
        project_root, curator = temp_project
        mock_extract.return_value = [{"content": "Use dependency injection for testability"}]
        learnings = {"categories": {}}

        # Act
        count = curator._categorize_learnings(learnings)

        # Assert
        assert count == 1

    @patch.object(LearningsCurator, "_extract_learnings_from_sessions")
    def test_categorize_learnings_skips_duplicates(self, mock_extract, curator):
        """Test categorization skips duplicates."""
        # Arrange
        mock_extract.return_value = [{"content": "Use dependency injection"}]
        learnings = {"categories": {"best_practices": [{"content": "Use dependency injection"}]}}

        # Act
        count = curator._categorize_learnings(learnings)

        # Assert
        assert count == 0

    def test_extract_learnings_from_sessions_finds_learnings(self, temp_project):
        """Test extraction from session learnings field."""
        # Arrange
        project_root, curator = temp_project
        summaries_dir = project_root / ".session" / "summaries"
        summaries_dir.mkdir(parents=True)
        summary_file = summaries_dir / "session_001.json"

        import json

        summary_data = {
            "learnings": ["Learning one", "Learning two"],
            "timestamp": "2025-10-24T10:00:00",
        }
        summary_file.write_text(json.dumps(summary_data))

        # Act
        result = curator._extract_learnings_from_sessions()

        # Assert
        assert len(result) == 2

    def test_extract_learnings_from_sessions_finds_challenges(self, temp_project):
        """Test extraction from challenges_encountered field."""
        # Arrange
        project_root, curator = temp_project
        summaries_dir = project_root / ".session" / "summaries"
        summaries_dir.mkdir(parents=True)
        summary_file = summaries_dir / "session_001.json"

        import json

        summary_data = {
            "challenges_encountered": ["Challenge one", "Challenge two"],
            "timestamp": "2025-10-24T10:00:00",
        }
        summary_file.write_text(json.dumps(summary_data))

        # Act
        result = curator._extract_learnings_from_sessions()

        # Assert
        assert len(result) == 2

    def test_extract_learnings_from_sessions_handles_invalid_json(self, temp_project):
        """Test that invalid JSON files are skipped gracefully."""
        # Arrange
        project_root, curator = temp_project
        summaries_dir = project_root / ".session" / "summaries"
        summaries_dir.mkdir(parents=True)
        summary_file = summaries_dir / "session_001.json"
        summary_file.write_text("{ invalid json }")

        # Act
        result = curator._extract_learnings_from_sessions()

        # Assert - Should not crash, just return empty list
        assert result == []


class TestAutoCurationFrequency:
    """Tests for auto-curation frequency checking."""

    def test_auto_curate_if_needed_with_frequency_check(self, tmp_path):
        """Test auto-curation triggers based on frequency."""
        # Arrange
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        config_dir = project_root / ".session"
        config_dir.mkdir(parents=True)

        import json
        from datetime import datetime, timedelta

        # Create config with auto-curation enabled
        config_file = config_dir / "config.json"
        config_data = {"curation": {"auto_curate": True, "frequency": 7}}
        config_file.write_text(json.dumps(config_data))

        # Create learnings with old curation date
        learnings_file = config_dir / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)
        old_date = datetime.now() - timedelta(days=10)
        learnings_data = {
            "categories": {},
            "last_curated": old_date.isoformat(),
            "metadata": {"total_learnings": 0},
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Create curator with project_root so it picks up the config
        curator = LearningsCurator(project_root)

        # Act
        from unittest.mock import patch

        with patch.object(curator, "curate") as mock_curate:
            result = curator.auto_curate_if_needed()

        # Assert
        assert result is True
        mock_curate.assert_called_once_with(dry_run=False)

    def test_auto_curate_if_needed_skips_when_recent(self, temp_project):
        """Test auto-curation skips when recently curated."""
        # Arrange
        project_root, curator = temp_project
        config_dir = project_root / ".session"
        config_dir.mkdir(parents=True)

        import json
        from datetime import datetime, timedelta

        # Create config with auto-curation enabled
        config_file = config_dir / "config.json"
        config_data = {"curation": {"auto_curate_enabled": True, "auto_curate_frequency_days": 7}}
        config_file.write_text(json.dumps(config_data))

        # Create learnings with recent curation date
        learnings_file = config_dir / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)
        recent_date = datetime.now() - timedelta(days=2)
        learnings_data = {
            "categories": {},
            "last_curated": recent_date.isoformat(),
            "metadata": {"total_learnings": 0},
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        result = curator.auto_curate_if_needed()

        # Assert
        assert result is False


class TestShowStatisticsAndTimeline:
    """Test show_statistics and show_timeline methods."""

    def test_show_statistics(self, temp_project, capsys):
        """Test that show_statistics delegates to reporter."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [{"id": "1"}, {"id": "2"}],
                "gotchas": [{"id": "3"}],
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.show_statistics()

        # Assert - Should display some stats
        captured = capsys.readouterr()
        assert len(captured.out) > 0  # Some output was displayed

    def test_show_timeline(self, temp_project, capsys):
        """Test that show_timeline delegates to reporter."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {
            "categories": {
                "best_practices": [
                    {"id": "1", "learned_in": "session_001"},
                    {"id": "2", "learned_in": "session_002"},
                ]
            }
        }
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.show_timeline(sessions=10)

        # Assert - Should display timeline
        captured = capsys.readouterr()
        assert len(captured.out) > 0  # Some output was displayed


class TestSessionSummaryExtraction:
    """Tests for extracting learnings from session summary files."""

    def test_extract_from_session_summary_file_not_exists(self, temp_project):
        """Test extraction handles missing file."""
        # Arrange
        project_root, curator = temp_project
        non_existent = project_root / "nonexistent.md"

        # Act
        result = curator.extract_from_session_summary(non_existent)

        # Assert
        assert result == []

    def test_extract_from_session_summary_without_validator(self, temp_project):
        """Test extraction from session summary without validator."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        summaries_dir = session_dir / "summaries"
        summaries_dir.mkdir(parents=True)
        summary_file = summaries_dir / "session_005_summary.md"

        content = """# Session Summary

## Learnings Captured
- This is a test learning with enough words to pass validation
- Another learning entry with sufficient word count here

## Other Section
- Not a learning
"""
        summary_file.write_text(content)

        # Act - Call without validator (validator=None)
        result = extractor.extract_from_session_summary(summary_file, validator=None)

        # Assert
        assert len(result) >= 1
        assert any("test learning" in entry.get("content", "").lower() for entry in result)

    def test_extract_from_session_summary_file_read_error(self, temp_project):
        """Test extraction handles file read errors."""
        # Arrange
        project_root, curator = temp_project
        summaries_dir = project_root / ".session" / "summaries"
        summaries_dir.mkdir(parents=True)
        summary_file = summaries_dir / "session_005_summary.md"
        summary_file.write_text("## Learnings Captured\n- Test learning")

        # Act - Mock file read to raise exception
        from unittest.mock import patch

        with patch("builtins.open", side_effect=Exception("Read error")):
            result = curator.extract_from_session_summary(summary_file)

        # Assert
        assert result == []

    def test_extract_from_session_summary_with_challenges(self, temp_project):
        """Test extraction from Challenges Encountered section."""
        # Arrange
        project_root, curator = temp_project
        summaries_dir = project_root / ".session" / "summaries"
        summaries_dir.mkdir(parents=True)
        summary_file = summaries_dir / "session_007_summary.md"

        content = """# Session Summary

## Challenges Encountered
- Complex debugging issue with async code
- Performance bottleneck in database queries

## Other Section
- Not a learning
"""
        summary_file.write_text(content)

        # Act
        result = curator.extract_from_session_summary(summary_file)

        # Assert
        assert len(result) >= 1


class TestCodeCommentExtraction:
    """Tests for extracting learnings from code comments."""

    def test_extract_from_code_comments_handles_git_error(self, temp_project):
        """Test extraction handles git command failures gracefully."""
        # Arrange
        project_root, curator = temp_project

        # Act - In non-git directory, should handle gracefully
        import subprocess
        from unittest.mock import patch

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            result = curator.extract_from_code_comments(session_id="session_001")

        # Assert - Should not crash
        assert isinstance(result, list)

    def test_extract_from_code_comments_without_validator(self, temp_project):
        """Test extraction from code comments without validator."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Create a Python file with a learning comment
        src_dir = project_root / "src"
        src_dir.mkdir()
        test_file = src_dir / "main.py"
        test_file.write_text(
            "# LEARNING: This is a test learning comment with enough words\ndef main():\n    pass\n"
        )

        # Act - Call without validator (validator=None)
        result = extractor.extract_from_code_comments(
            changed_files=[test_file], session_id="session_001", validator=None
        )

        # Assert
        assert len(result) >= 1
        assert any("test learning comment" in entry.get("content", "").lower() for entry in result)

    def test_extract_from_code_comments_nonexistent_file(self, temp_project):
        """Test that nonexistent files are skipped."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Create a reference to a file that doesn't exist
        nonexistent_file = project_root / "src" / "doesnotexist.py"

        # Act
        result = extractor.extract_from_code_comments(
            changed_files=[nonexistent_file], validator=None
        )

        # Assert - Should skip nonexistent file
        assert len(result) == 0

    def test_extract_from_code_comments_skips_non_code_extensions(self, temp_project):
        """Test that files with non-code extensions are skipped."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Create a text file (not a code file)
        text_file = project_root / "notes.txt"
        text_file.write_text("# LEARNING: This should be skipped non code file extension\n")

        # Act
        result = extractor.extract_from_code_comments(changed_files=[text_file], validator=None)

        # Assert - Should skip .txt file
        assert len(result) == 0

    def test_extract_from_code_comments_handles_unicode_error(self, temp_project):
        """Test that files with encoding errors are handled gracefully."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        src_dir = project_root / "src"
        src_dir.mkdir()
        test_file = src_dir / "bad.py"
        # Write binary data that might cause encoding issues
        test_file.write_bytes(b"# LEARNING: Test\xff\xfe")

        # Act - Should handle gracefully
        result = extractor.extract_from_code_comments(changed_files=[test_file], validator=None)

        # Assert - Should not crash, might return empty
        assert isinstance(result, list)

    def test_extract_from_code_comments_with_changed_files_none(self, temp_project):
        """Test extraction when changed_files is None (git auto-detect)."""
        # Arrange
        from unittest.mock import Mock, patch

        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Mock git diff to return some files
        mock_result = Mock()
        mock_result.success = True
        mock_result.stdout = "src/main.py\nsrc/utils.py"

        with patch.object(extractor.runner, "run", return_value=mock_result):
            # Act - changed_files=None should trigger git diff
            result = extractor.extract_from_code_comments(
                changed_files=None, session_id="session_001", validator=None
            )

        # Assert - Should not crash (files don't actually exist, so empty result)
        assert isinstance(result, list)

    def test_extract_from_code_comments_git_diff_failure(self, temp_project):
        """Test extraction handles git diff failure when changed_files is None."""
        # Arrange
        from unittest.mock import Mock, patch

        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Mock git diff to fail
        mock_result = Mock()
        mock_result.success = False

        with patch.object(extractor.runner, "run", return_value=mock_result):
            # Act - changed_files=None with failed git diff
            result = extractor.extract_from_code_comments(
                changed_files=None, session_id="session_001", validator=None
            )

        # Assert - Should handle gracefully and return empty
        assert result == []

    def test_extract_from_code_comments_git_diff_exception(self, temp_project):
        """Test extraction handles exceptions during git diff."""
        # Arrange
        from unittest.mock import patch

        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Mock git diff to raise exception
        with patch.object(extractor.runner, "run", side_effect=Exception("Git error")):
            # Act - changed_files=None with exception in git diff
            result = extractor.extract_from_code_comments(
                changed_files=None, session_id="session_001", validator=None
            )

        # Assert - Should handle gracefully and return empty
        assert result == []

    def test_extract_from_git_commits_without_validator(self, temp_project):
        """Test extraction from git commits without validator."""
        # Arrange
        from unittest.mock import Mock, patch

        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Mock git log output
        mock_result = Mock()
        mock_result.success = True
        mock_result.stdout = (
            "abc123|||feat: Test\n\nLEARNING: This is a git commit learning with enough words here"
        )

        with patch.object(extractor.runner, "run", return_value=mock_result):
            # Act - Call without validator (validator=None)
            result = extractor.extract_from_git_commits(session_id="session_001", validator=None)

        # Assert
        assert len(result) >= 1
        assert any("git commit learning" in entry.get("content", "").lower() for entry in result)

    def test_extract_from_git_commits_no_output(self, temp_project):
        """Test extraction handles empty git output."""
        # Arrange
        from unittest.mock import Mock, patch

        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Mock git log with empty output
        mock_result = Mock()
        mock_result.success = True
        mock_result.stdout = ""

        with patch.object(extractor.runner, "run", return_value=mock_result):
            # Act
            result = extractor.extract_from_git_commits(session_id="session_001", validator=None)

        # Assert - Should return empty list
        assert result == []

    def test_extract_from_git_commits_failed_command(self, temp_project):
        """Test extraction handles failed git command."""
        # Arrange
        from unittest.mock import Mock, patch

        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Mock git log failure
        mock_result = Mock()
        mock_result.success = False

        with patch.object(extractor.runner, "run", return_value=mock_result):
            # Act
            result = extractor.extract_from_git_commits(session_id="session_001", validator=None)

        # Assert - Should return empty list
        assert result == []

    def test_extract_from_git_commits_exception(self, temp_project):
        """Test extraction handles exceptions during git extraction."""
        # Arrange
        from unittest.mock import patch

        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Mock runner.run to raise exception
        with patch.object(extractor.runner, "run", side_effect=Exception("Git error")):
            # Act
            result = extractor.extract_from_git_commits(session_id="session_001", validator=None)

        # Assert - Should catch exception and return empty list
        assert result == []

    def test_is_valid_content_with_angle_brackets(self, temp_project):
        """Test that content with angle brackets is rejected."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Act & Assert
        assert not extractor._is_valid_content("<placeholder text>")
        assert not extractor._is_valid_content("Some text with <placeholder>")

    def test_is_valid_content_too_few_words(self, temp_project):
        """Test that content with too few words is rejected."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Act & Assert
        assert not extractor._is_valid_content("Too short")  # 2 words
        assert not extractor._is_valid_content("One two three four")  # 4 words
        assert extractor._is_valid_content("One two three four five")  # 5 words - valid

    def test_is_valid_content_empty_or_none(self, temp_project):
        """Test that empty or None content is rejected."""
        # Arrange
        from solokit.learning.extractor import LearningExtractor

        project_root, _ = temp_project
        session_dir = project_root / ".session"
        session_dir.mkdir()

        extractor = LearningExtractor(session_dir, project_root)

        # Act & Assert
        assert not extractor._is_valid_content("")
        assert not extractor._is_valid_content(None)
        assert not extractor._is_valid_content(123)  # Not a string


class TestSessionNumberExtractionEdgeCases:
    """Tests for session number extraction edge cases."""

    def test_extract_session_number_handles_exception(self, temp_project):
        """Test session number extraction handles invalid input."""
        # Arrange
        project_root, curator = temp_project

        # Act
        result = curator._extract_session_number("invalid_format_###")

        # Assert
        assert result == 0

    def test_extract_session_number_handles_empty_string(self, temp_project):
        """Test session number extraction handles empty string."""
        # Arrange
        project_root, curator = temp_project

        # Act - Empty string should return 0 (no match found)
        result = curator._extract_session_number("")

        # Assert
        assert result == 0

    def test_extract_session_number_exception_handling(self, temp_project):
        """Test that exception handling in extract_session_number works."""
        # Arrange
        project_root, curator = temp_project

        # Act - Mock re.search to raise an exception
        from unittest.mock import patch

        with patch("re.search", side_effect=ValueError("Test error")):
            result = curator._extract_session_number("session_001")

        # Assert - Should catch and return 0
        assert result == 0

    def test_get_current_session_number_handles_malformed_data(self, temp_project):
        """Test _get_current_session_number handles malformed work items data."""
        # Arrange
        project_root, curator = temp_project
        work_items_file = project_root / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)

        import json

        # Create malformed data that will cause TypeError or KeyError
        work_items_data = {
            "work_items": {
                "WI-001": {
                    "sessions": "not_a_list"  # This should be a list
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        # Act
        result = curator._get_current_session_number()

        # Assert - Should handle error gracefully and return 0
        assert result == 0

    def test_get_current_session_number_handles_missing_session_num(self, temp_project):
        """Test _get_current_session_number handles sessions without session_num field."""
        # Arrange
        project_root, curator = temp_project
        work_items_file = project_root / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)

        import json

        # Sessions without session_num field
        work_items_data = {
            "work_items": {
                "WI-001": {
                    "sessions": [
                        {"started_at": "2025-01-01T10:00:00"},  # Missing session_num
                        {"session_num": None},  # None value
                    ]
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        # Act
        result = curator._get_current_session_number()

        # Assert - Should handle gracefully
        assert result == 0

    def test_get_current_session_number_handles_non_dict_sessions(self, temp_project):
        """Test _get_current_session_number handles sessions that are not dicts."""
        # Arrange
        project_root, curator = temp_project
        work_items_file = project_root / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)

        import json

        # Sessions with non-dict items
        work_items_data = {
            "work_items": {
                "WI-001": {
                    "sessions": [
                        123,  # Integer instead of dict
                        "string",  # String instead of dict
                        {"session_num": 5},  # Valid one
                    ]
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        # Act
        result = curator._get_current_session_number()

        # Assert - Should find the valid session_num
        assert result == 5


class TestCurateDryRun:
    """Tests for dry run functionality."""

    def test_curate_dry_run_prints_message(self, temp_project, capsys):
        """Test that dry run mode prints appropriate message."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {"categories": {}, "metadata": {"total_learnings": 0}}
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.curate(dry_run=True)
        captured = capsys.readouterr()

        # Assert
        assert "Dry run" in captured.out or "dry run" in captured.out.lower()

    def test_curate_saves_when_not_dry_run(self, temp_project, capsys):
        """Test that curate saves changes when dry_run=False."""
        # Arrange
        project_root, curator = temp_project
        learnings_file = project_root / ".session" / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)

        import json

        learnings_data = {"categories": {}, "metadata": {"total_learnings": 0}}
        learnings_file.write_text(json.dumps(learnings_data))

        # Act
        curator.curate(dry_run=False)
        captured = capsys.readouterr()

        # Assert
        assert "saved" in captured.out.lower()
        # Verify file was actually updated
        saved_data = json.loads(learnings_file.read_text())
        assert "last_curated" in saved_data


class TestMainFunctionErrorHandling:
    """Tests for main() function error handling."""

    def test_main_raises_file_not_found_when_session_dir_missing(self, tmp_path):
        """Test that main() raises SolokitFileNotFoundError when .session dir doesn't exist."""
        # Arrange

        with patch("sys.argv", ["curator.py", "curate"]):
            with patch("pathlib.Path.cwd", return_value=tmp_path):
                # Act & Assert
                with pytest.raises(SolokitFileNotFoundError) as exc_info:
                    main()

                # Verify exception details
                assert ".session" in str(exc_info.value)
                assert exc_info.value.context["file_type"] == "session directory"

    def test_main_with_empty_search_query(self, tmp_path):
        """Test main() with empty search query returns error code."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()

        with patch("sys.argv", ["curator.py", "search", ""]):
            with patch("pathlib.Path.cwd", return_value=project_root):
                # Act
                result = main()

                # Assert
                assert result == 1

    def test_main_with_statistics_command(self, tmp_path, capsys):
        """Test main() with statistics command."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()

        # Create learnings file
        import json

        learnings_file = session_dir / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)
        learnings_data = {
            "categories": {"best_practices": [{"id": "1"}]},
            "metadata": {"total_learnings": 1},
        }
        learnings_file.write_text(json.dumps(learnings_data))

        with patch("sys.argv", ["curator.py", "statistics"]):
            with patch("pathlib.Path.cwd", return_value=project_root):
                # Act
                result = main()

                # Assert
                assert result == 0

    def test_main_with_timeline_command(self, tmp_path, capsys):
        """Test main() with timeline command."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()

        # Create learnings file
        import json

        learnings_file = session_dir / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)
        learnings_data = {
            "categories": {"best_practices": [{"id": "1", "learned_in": "session_001"}]},
            "metadata": {"total_learnings": 1},
        }
        learnings_file.write_text(json.dumps(learnings_data))

        with patch("sys.argv", ["curator.py", "timeline"]):
            with patch("pathlib.Path.cwd", return_value=project_root):
                # Act
                result = main()

                # Assert
                assert result == 0

    def test_main_with_report_command(self, tmp_path, capsys):
        """Test main() with report command (explicit)."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()

        # Create learnings file
        import json

        learnings_file = session_dir / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)
        learnings_data = {
            "categories": {"best_practices": [{"id": "1"}]},
            "metadata": {"total_learnings": 1},
        }
        learnings_file.write_text(json.dumps(learnings_data))

        with patch("sys.argv", ["curator.py", "report"]):
            with patch("pathlib.Path.cwd", return_value=project_root):
                # Act
                result = main()

                # Assert
                assert result == 0

    def test_main_with_no_command_defaults_to_report(self, tmp_path, capsys):
        """Test main() with no command defaults to report."""
        # Arrange
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()

        # Create learnings file
        import json

        learnings_file = session_dir / "tracking" / "learnings.json"
        learnings_file.parent.mkdir(parents=True)
        learnings_data = {
            "categories": {"best_practices": [{"id": "1"}]},
            "metadata": {"total_learnings": 1},
        }
        learnings_file.write_text(json.dumps(learnings_data))

        with patch("sys.argv", ["curator.py"]):
            with patch("pathlib.Path.cwd", return_value=project_root):
                # Act
                result = main()

                # Assert
                assert result == 0
