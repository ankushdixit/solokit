"""Learning reporting and statistics module"""

from __future__ import annotations

import re
from typing import Any

from solokit.core.logging_config import get_logger
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


class LearningReporter:
    """Handles learning reports, statistics, searches, and display functionality"""

    def __init__(self, repository: Any):
        """
        Initialize reporter

        Args:
            repository: LearningRepository instance for data access
        """
        self.repository = repository

    def generate_report(self) -> None:
        """Generate learning summary report"""
        output.section("Learning Summary Report")

        learnings = self.repository.load_learnings()

        # Create table
        output.info("Learnings by Category:")
        output.info("-" * 40)

        categories = learnings.get("categories", {})
        total = 0

        for category_name, category_learnings in categories.items():
            count = len(category_learnings)
            total += count
            formatted_name = category_name.replace("_", " ").title()
            output.info(f"{formatted_name:<30} {count:>5}")

        # Add archived
        archived_count = len(learnings.get("archived", []))
        if archived_count > 0:
            output.info(f"{'Archived':<30} {archived_count:>5}")

        # Add total
        output.info("-" * 40)
        output.info(f"{'Total':<30} {total:>5}")
        output.info("")

        # Show last curated
        last_curated = learnings.get("last_curated")
        if last_curated:
            output.info(f"Last curated: {last_curated}\n")
        else:
            output.info("Never curated\n")

    def search_learnings(self, query: str) -> None:
        """
        Search learnings by keyword

        Args:
            query: Search query string
        """
        learnings = self.repository.load_learnings()
        categories = learnings.get("categories", {})

        query_lower = query.lower()
        matches = []

        # Search through all learnings
        for category_name, category_learnings in categories.items():
            for learning in category_learnings:
                # Search in content
                content = learning.get("content", "").lower()
                tags = learning.get("tags", [])
                context = learning.get("context", "").lower()

                if (
                    query_lower in content
                    or query_lower in context
                    or any(query_lower in tag.lower() for tag in tags)
                ):
                    matches.append({**learning, "category": category_name})

        # Display results
        if not matches:
            output.info(f"\n⚠️ No learnings found matching '{query}'\n")
            output.info("Try different keywords or use '/learn-show' to browse all learnings.")
            output.info("")
            return

        output.info(f"\n=== Search Results for '{query}' ===\n")
        output.info(f"Found {len(matches)} matching learning(s):\n")

        for i, learning in enumerate(matches, 1):
            output.info(f"{i}. [{learning['category'].replace('_', ' ').title()}]")
            output.info(f"   {learning['content']}")

            if "tags" in learning:
                output.info(f"   Tags: {', '.join(learning['tags'])}")

            output.info(f"   Session: {learning.get('learned_in', 'unknown')}")
            output.info(f"   ID: {learning.get('id', 'N/A')}")
            output.info("")

    def show_learnings(
        self,
        category: str | None = None,
        tag: str | None = None,
        session: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_archived: bool = False,
    ) -> None:
        """
        Show learnings with optional filters

        Args:
            category: Filter by category name
            tag: Filter by tag
            session: Filter by session number
            date_from: Filter by start date
            date_to: Filter by end date
            include_archived: Include archived learnings
        """
        learnings = self.repository.load_learnings()
        categories = learnings.get("categories", {})

        # Apply filters
        filtered = []
        for category_name, category_learnings in categories.items():
            # Category filter
            if category and category_name != category:
                continue

            for learning in category_learnings:
                # Tag filter
                if tag and tag not in learning.get("tags", []):
                    continue

                # Session filter
                if session:
                    learned_in = learning.get("learned_in", "")
                    session_num = self._extract_session_number(learned_in)
                    if session_num != session:
                        continue

                # Date range filter
                if date_from or date_to:
                    learning_date = learning.get("timestamp", "")
                    if date_from and learning_date < date_from:
                        continue
                    if date_to and learning_date > date_to:
                        continue

                filtered.append({**learning, "category": category_name})

        # Display results
        if not filtered:
            output.info("\n⚠️ No learnings found matching your filters\n")
            output.info("To see all learnings:")
            output.info("  1. Remove filters: /learn-show")
            output.info("  2. Search for keywords: /learn-search <query>")
            output.info("  3. Capture a new learning: /learn\n")
            output.info("💡 Learnings are captured automatically during /end sessions")
            return

        if category:
            # Show specific category
            output.info(f"\n{category.replace('_', ' ').title()}\n")
            output.info("=" * 50)

            for i, learning in enumerate(filtered, 1):
                output.info(f"\n{i}. {learning.get('content', 'N/A')}")
                if "tags" in learning:
                    output.info(f"   Tags: {', '.join(learning['tags'])}")
                if "learned_in" in learning:
                    output.info(f"   Learned in: {learning['learned_in']}")
                if "timestamp" in learning:
                    output.info(f"   Date: {learning['timestamp']}")
                output.info(f"   ID: {learning.get('id', 'N/A')}")
        else:
            # Show all categories
            grouped: dict[str, list[Any]] = {}
            for learning in filtered:
                cat = learning["category"]
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(learning)

            for category_name, category_learnings in grouped.items():
                output.info(f"\n{category_name.replace('_', ' ').title()}")
                output.info(f"Count: {len(category_learnings)}\n")

                # Show first 3
                for learning in category_learnings[:3]:
                    output.info(f"  • {learning.get('content', 'N/A')}")
                    if "tags" in learning:
                        output.info(f"    Tags: {', '.join(learning['tags'])}")

                if len(category_learnings) > 3:
                    output.info(f"  ... and {len(category_learnings) - 3} more")

                output.info("")

    def generate_statistics(self) -> dict[str, Any]:
        """
        Generate learning statistics

        Returns:
            Dictionary with statistics (total, by_category, by_tag, top_tags, by_session)
        """
        learnings = self.repository.load_learnings()
        categories = learnings.get("categories", {})

        stats: dict[str, Any] = {
            "total": 0,
            "by_category": {},
            "by_tag": {},
            "top_tags": [],
            "by_session": {},
        }

        # Count by category
        for cat, items in categories.items():
            count = len(items)
            stats["by_category"][cat] = count
            stats["total"] += count

        # Count by tag and session
        tag_counts: dict[str, int] = {}
        session_counts: dict[int, int] = {}

        for items in categories.values():
            for learning in items:
                # Tag counts
                for tag in learning.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Session counts
                learned_in = learning.get("learned_in", "unknown")
                session_num = self._extract_session_number(learned_in)
                if session_num > 0:
                    session_counts[session_num] = session_counts.get(session_num, 0) + 1

        # Top tags
        stats["top_tags"] = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        stats["by_tag"] = tag_counts
        stats["by_session"] = session_counts

        return stats

    def show_statistics(self) -> None:
        """Display learning statistics"""
        stats = self.generate_statistics()

        output.section("Learning Statistics")

        # Total
        output.info(f"Total learnings: {stats['total']}\n")

        # By category
        output.info("By Category:")
        output.info("-" * 40)
        for cat, count in stats["by_category"].items():
            cat_name = cat.replace("_", " ").title()
            output.info(f"  {cat_name:<30} {count:>5}")

        # Top tags
        if stats["top_tags"]:
            output.info("\nTop Tags:")
            output.info("-" * 40)
            for tag, count in stats["top_tags"]:
                output.info(f"  {tag:<30} {count:>5}")

        # Sessions with most learnings
        if stats["by_session"]:
            top_sessions = sorted(stats["by_session"].items(), key=lambda x: x[1], reverse=True)[:5]
            output.info("\nSessions with Most Learnings:")
            output.info("-" * 40)
            for session_num, count in top_sessions:
                output.info(f"  Session {session_num:<22} {count:>5}")

        output.info("")

    def show_timeline(self, sessions: int = 10) -> None:
        """
        Show learning timeline for recent sessions

        Args:
            sessions: Number of recent sessions to display
        """
        learnings = self.repository.load_learnings()
        categories = learnings.get("categories", {})

        # Group by session
        by_session: dict[int, list[Any]] = {}
        for items in categories.values():
            for learning in items:
                learned_in = learning.get("learned_in", "unknown")
                session = self._extract_session_number(learned_in)
                if session > 0:
                    if session not in by_session:
                        by_session[session] = []
                    by_session[session].append(learning)

        if not by_session:
            output.info("\nNo session timeline available\n")
            return

        # Display recent sessions
        recent = sorted(by_session.keys(), reverse=True)[:sessions]

        output.info(f"\n=== Learning Timeline (Last {min(len(recent), sessions)} Sessions) ===\n")

        for session in recent:
            session_learnings = by_session[session]
            count = len(session_learnings)

            output.info(f"Session {session:03d}: {count} learning(s)")

            # Show first 3 learnings
            for learning in session_learnings[:3]:
                content = learning.get("content", "")
                # Truncate long learnings
                if len(content) > 60:
                    content = content[:57] + "..."
                output.info(f"  - {content}")

            if len(session_learnings) > 3:
                output.info(f"  ... and {len(session_learnings) - 3} more")

            output.info("")

    def _extract_session_number(self, session_id: str) -> int:
        """
        Extract numeric session number from session ID

        Args:
            session_id: Session ID string

        Returns:
            Extracted session number or 0
        """
        try:
            match = re.search(r"\d+", session_id)
            if match:
                return int(match.group())
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to extract session number from '{session_id}': {e}")
            return 0
        return 0
