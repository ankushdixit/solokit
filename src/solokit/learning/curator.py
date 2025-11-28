#!/usr/bin/env python3
"""
Learning curation orchestrator

Coordinates learning curation using specialized modules:
1. Categorization - Auto-categorize learnings
2. Similarity detection - Merge similar learnings
3. Archiving - Archive old learnings
4. Extraction - Extract learnings from various sources
5. Repository - Data persistence and CRUD
6. Reporter - Reports and statistics
7. Validator - Learning validation
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from solokit.core.argparse_helpers import HelpfulArgumentParser
from solokit.core.constants import MAX_LEARNING_AGE_SESSIONS
from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.learning.archiver import LearningArchiver
from solokit.learning.categorizer import LearningCategorizer
from solokit.learning.extractor import LearningExtractor
from solokit.learning.reporter import LearningReporter
from solokit.learning.repository import LearningRepository
from solokit.learning.similarity import LearningSimilarityEngine
from solokit.learning.validator import LearningValidator

logger = get_logger(__name__)
output = get_output()


class LearningsCurator:
    """Main orchestrator for learning curation - delegates to specialized modules"""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize LearningsCurator with dependency injection

        Args:
            project_root: Path to project root directory
        """
        if project_root is None:
            project_root = Path.cwd()

        self.project_root = project_root
        self.session_dir = project_root / ".session"

        # Initialize all components
        self.repository = LearningRepository(self.session_dir)
        self.similarity_engine = LearningSimilarityEngine()
        self.categorizer = LearningCategorizer()
        self.archiver = LearningArchiver(self.session_dir)
        self.extractor = LearningExtractor(self.session_dir, self.project_root)
        self.reporter = LearningReporter(self.repository)
        self.validator = LearningValidator()

    @log_errors()
    def curate(self, dry_run: bool = False) -> None:
        """
        Curate learnings - main orchestration method

        Orchestrates the entire curation workflow:
        1. Load existing learnings
        2. Categorize uncategorized learnings
        3. Merge similar learnings
        4. Archive old learnings
        5. Update metadata
        6. Save results (unless dry_run)

        Args:
            dry_run: If True, show changes without saving

        Raises:
            FileOperationError: If reading/writing learnings file fails
            ValidationError: If learning data is invalid
        """
        logger.info("Starting learning curation (dry_run=%s)", dry_run)
        output.section("Learning Curation")

        # Load existing learnings
        learnings = self.repository.load_learnings()
        initial_count = self.repository.count_all_learnings(learnings)
        output.info(f"Initial learnings: {initial_count}\n")

        # Categorize uncategorized learnings
        categorized = self._categorize_learnings(learnings)
        output.info(f"✓ Categorized {categorized} learnings")

        # Merge similar learnings
        merged = self.similarity_engine.merge_similar_learnings(learnings)
        output.info(f"✓ Merged {merged} duplicate learnings")

        # Archive old learnings
        archived = self.archiver.archive_old_learnings(learnings)
        output.info(f"✓ Archived {archived} old learnings")

        # Update metadata
        learnings["last_curated"] = datetime.now().isoformat()
        learnings["curator"] = "session_curator"
        self.repository.update_total_learnings(learnings)

        final_count = self.repository.count_all_learnings(learnings)
        output.info(f"\nFinal learnings: {final_count}\n")

        if not dry_run:
            self.repository.save_learnings(learnings)
            output.success("Learnings saved\n")
        else:
            output.info("Dry run - no changes saved\n")

    def _categorize_learnings(self, learnings: dict) -> int:
        """
        Categorize uncategorized learnings using extractor and categorizer

        Args:
            learnings: Learnings dictionary

        Returns:
            Number of learnings categorized
        """
        categorized_count = 0

        # Extract learnings from session summaries
        # Use the wrapper method for test compatibility
        new_learnings = self._extract_learnings_from_sessions()

        for learning in new_learnings:
            # Auto-categorize using categorizer
            category = self.categorizer.categorize_learning(learning)

            # Add to appropriate category
            categories = learnings.setdefault("categories", {})
            if category not in categories:
                categories[category] = []

            # Check if already exists using similarity engine
            if not self.repository.learning_exists(
                categories[category], learning, self.similarity_engine
            ):
                categories[category].append(learning)
                categorized_count += 1

        logger.info(f"Categorized {categorized_count} learnings")
        return categorized_count

    def auto_curate_if_needed(self) -> bool:
        """
        Auto-curate based on configuration and last curation time

        Returns:
            True if curation was performed, False otherwise
        """
        config = self.repository.get_curation_config()

        if not config.auto_curate:
            return False

        learnings = self.repository.load_learnings()
        last_curated = learnings.get("last_curated")

        if not last_curated:
            # Never curated, do it now
            output.info("Auto-curating (first time)...\n")
            self.curate(dry_run=False)
            return True

        # Check frequency
        last_date = datetime.fromisoformat(last_curated)
        days_since = (datetime.now() - last_date).days

        frequency_days = config.frequency

        if days_since >= frequency_days:
            output.info(f"Auto-curating (last curated {days_since} days ago)...\n")
            self.curate(dry_run=False)
            return True

        return False

    # Delegate methods to appropriate components

    @log_errors()
    def add_learning(
        self,
        content: str,
        category: str,
        session: int | None = None,
        tags: list | None = None,
        context: str | None = None,
    ) -> str:
        """Add a new learning (delegates to repository)"""
        return self.repository.add_learning(content, category, session, tags, context)

    def add_learning_if_new(self, learning_dict: dict) -> bool:
        """Add learning if it doesn't already exist (delegates to repository)"""
        return self.repository.add_learning_if_new(learning_dict, self.similarity_engine)

    def search_learnings(self, query: str) -> None:
        """Search learnings by keyword (delegates to reporter)"""
        self.reporter.search_learnings(query)

    def show_learnings(
        self,
        category: str | None = None,
        tag: str | None = None,
        session: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_archived: bool = False,
    ) -> None:
        """Show learnings with optional filters (delegates to reporter)"""
        self.reporter.show_learnings(category, tag, session, date_from, date_to, include_archived)

    def generate_report(self) -> None:
        """Generate learning summary report (delegates to reporter)"""
        self.reporter.generate_report()

    def show_statistics(self) -> None:
        """Display learning statistics (delegates to reporter)"""
        self.reporter.show_statistics()

    def generate_statistics(self) -> dict:
        """Generate learning statistics (delegates to reporter)"""
        return self.reporter.generate_statistics()

    def show_timeline(self, sessions: int = 10) -> None:
        """Show learning timeline (delegates to reporter)"""
        self.reporter.show_timeline(sessions)

    @log_errors()
    def extract_from_session_summary(self, session_file: Path) -> list[dict]:
        """Extract learnings from session summary file (delegates to extractor)"""
        return self.extractor.extract_from_session_summary(session_file, self.validator)

    @log_errors()
    def extract_from_git_commits(
        self, since_session: int = 0, session_id: str | None = None
    ) -> list[dict]:
        """Extract learnings from git commit messages (delegates to extractor)"""
        return self.extractor.extract_from_git_commits(since_session, session_id, self.validator)

    @log_errors()
    def extract_from_code_comments(
        self, changed_files: list[Path] | None = None, session_id: str | None = None
    ) -> list[dict]:
        """Extract learnings from inline code comments (delegates to extractor)"""
        return self.extractor.extract_from_code_comments(changed_files, session_id, self.validator)

    def is_valid_learning(self, content: str) -> bool:
        """Check if content is a valid learning (delegates to validator)"""
        return self.validator.is_valid_learning(content)

    def create_learning_entry(
        self,
        content: str,
        source: str,
        session_id: str | None = None,
        context: str | None = None,
        timestamp: str | None = None,
        learning_id: str | None = None,
    ) -> dict:
        """Create standardized learning entry (delegates to validator)"""
        return self.validator.create_learning_entry(
            content, source, session_id, context, timestamp, learning_id
        )

    def validate_learning(self, learning: dict) -> bool:
        """Validate learning entry against schema (delegates to validator)"""
        return self.validator.validate_learning(learning)

    def get_related_learnings(self, learning_id: str, limit: int = 5) -> list[dict]:
        """Get similar learnings (delegates to similarity engine)"""
        learnings = self.repository.load_learnings()
        return self.similarity_engine.get_related_learnings(learnings, learning_id, limit)

    # ========================================================================
    # Compatibility wrapper methods for tests
    # These delegate to the refactored modules
    # ========================================================================

    def _count_all_learnings(self, learnings: dict) -> int:
        """Count all learnings (compatibility wrapper for tests)"""
        return self.repository.count_all_learnings(learnings)

    def _update_total_learnings(self, learnings: dict) -> None:
        """Update total learnings metadata (compatibility wrapper for tests)"""
        self.repository.update_total_learnings(learnings)

    def _keyword_score(self, text: str, keywords: list[str]) -> int:
        """Calculate keyword score (compatibility wrapper for tests)"""
        return self.categorizer._keyword_score(text, keywords)

    def _auto_categorize_learning(self, learning: dict) -> str:
        """Auto-categorize learning (compatibility wrapper for tests)"""
        return self.categorizer.categorize_learning(learning)

    def _are_similar(self, learning_a: dict, learning_b: dict) -> bool:
        """Check if two learnings are similar (compatibility wrapper for tests)"""
        return self.similarity_engine.are_similar(learning_a, learning_b)

    def _learning_exists(self, cat_learnings: list[dict], new_learning: dict) -> bool:
        """Check if learning exists in category (compatibility wrapper for tests)"""
        return self.repository.learning_exists(cat_learnings, new_learning, self.similarity_engine)

    def _merge_similar_learnings(self, learnings: dict) -> int:
        """Merge similar learnings (compatibility wrapper for tests)"""
        return self.similarity_engine.merge_similar_learnings(learnings)

    def _archive_old_learnings(
        self, learnings: dict, max_age_sessions: int = MAX_LEARNING_AGE_SESSIONS
    ) -> int:
        """Archive old learnings (compatibility wrapper for tests)"""
        return self.archiver.archive_old_learnings(learnings, max_age_sessions)

    def _extract_session_number(self, session_id: str) -> int:
        """Extract session number from session ID (compatibility wrapper for tests)"""
        return self.archiver._extract_session_number(session_id)

    def _get_current_session_number(self) -> int:
        """Get current session number (compatibility wrapper for tests)"""
        return self.archiver._get_current_session_number()

    def _extract_learnings_from_sessions(self) -> list[dict]:
        """Extract learnings from session summaries (compatibility wrapper for tests)"""
        return self.extractor.extract_from_sessions()

    def _load_learnings(self) -> dict:
        """Load learnings from file (compatibility wrapper for tests)"""
        return self.repository.load_learnings()


def main() -> int:
    """Main entry point"""
    parser = HelpfulArgumentParser(
        description="Learning curation and management",
        epilog="""
Examples:
  sk learn-show                              # Show all learnings
  sk learn-show --category best_practices    # Show specific category
  sk learn-search "authentication"           # Search learnings
  sk learn-curate                            # Run curation process

💡 Use /learn in Claude Code for interactive learning capture
💡 Learnings are automatically extracted during /end sessions
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Curate command
    curate_parser = subparsers.add_parser("curate", help="Run curation process")
    curate_parser.add_argument("--dry-run", action="store_true", help="Show changes without saving")

    # Show learnings command
    show_parser = subparsers.add_parser("show-learnings", help="Show learnings")
    show_parser.add_argument("--category", type=str, help="Filter by category")
    show_parser.add_argument("--tag", type=str, help="Filter by tag")
    show_parser.add_argument("--session", type=int, help="Filter by session number")

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search learnings by keyword",
        epilog="""
Examples:
  sk learn-search "authentication"
  sk learn-search "database"
  sk learn-search "performance"

💡 Search looks in content, tags, and context fields
💡 Use /learn-show to see all learnings organized by category
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    search_parser.add_argument("query", type=str, help="Search query")

    # Add learning command
    add_parser = subparsers.add_parser("add-learning", help="Add a new learning")
    add_parser.add_argument("--content", type=str, required=True, help="Learning content")
    add_parser.add_argument(
        "--category",
        type=str,
        required=True,
        choices=[
            "architecture_patterns",
            "gotchas",
            "best_practices",
            "technical_debt",
            "performance_insights",
            "security",
        ],
        help="Learning category",
    )
    add_parser.add_argument("--session", type=int, help="Session number")
    add_parser.add_argument("--tags", type=str, help="Comma-separated tags")
    add_parser.add_argument("--context", type=str, help="Additional context")

    # Report command (legacy)
    subparsers.add_parser("report", help="Generate summary report")

    # Statistics command
    subparsers.add_parser("statistics", help="Show learning statistics")

    # Timeline command
    timeline_parser = subparsers.add_parser("timeline", help="Show learning timeline")
    timeline_parser.add_argument(
        "--sessions", type=int, default=10, help="Number of recent sessions to show"
    )

    args = parser.parse_args()

    project_root = Path.cwd()
    session_dir = project_root / ".session"

    if not session_dir.exists():
        raise SolokitFileNotFoundError(file_path=str(session_dir), file_type="session directory")

    curator = LearningsCurator(project_root)

    if args.command == "curate":
        curator.curate(dry_run=args.dry_run)
    elif args.command == "show-learnings":
        curator.show_learnings(category=args.category, tag=args.tag, session=args.session)
    elif args.command == "search":
        # Validate query is not empty
        if not args.query or not args.query.strip():
            output.error("Please provide a search query")
            output.info("\nExample:")
            output.info("  sk learn-search authentication")
            output.info("  sk learn-search database")
            output.info("")
            return 1
        curator.search_learnings(args.query)
    elif args.command == "add-learning":
        tags = args.tags.split(",") if args.tags else None
        curator.add_learning(
            content=args.content,
            category=args.category,
            session=args.session,
            tags=tags,
            context=args.context,
        )
    elif args.command == "report":
        curator.generate_report()
    elif args.command == "statistics":
        curator.show_statistics()
    elif args.command == "timeline":
        curator.show_timeline(sessions=args.sessions)
    else:
        # Default to report if no command specified
        curator.generate_report()

    return 0


if __name__ == "__main__":
    main()
