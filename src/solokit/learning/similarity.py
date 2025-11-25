"""Learning similarity detection engine with pluggable algorithms"""

from typing import Any, Protocol

from solokit.core.logging_config import get_logger
from solokit.core.performance import measure_time

logger = get_logger(__name__)


# English stopwords for similarity comparison
ENGLISH_STOPWORDS: set[str] = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "should",
    "could",
    "may",
    "might",
    "can",
    "shall",
}


class SimilarityAlgorithm(Protocol):
    """Protocol for similarity algorithms"""

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute similarity score between two texts (0.0 to 1.0)"""
        ...


class JaccardContainmentSimilarity:
    """Jaccard + Containment similarity with stopword filtering"""

    def __init__(
        self,
        stopwords: set[str] | None = None,
        jaccard_threshold: float = 0.6,
        containment_threshold: float = 0.8,
    ) -> None:
        """
        Initialize similarity algorithm

        Args:
            stopwords: Set of words to ignore (default: ENGLISH_STOPWORDS)
            jaccard_threshold: Threshold for Jaccard similarity (default: 0.6)
            containment_threshold: Threshold for containment similarity (default: 0.8)
        """
        self.stopwords = stopwords or ENGLISH_STOPWORDS
        self.jaccard_threshold = jaccard_threshold
        self.containment_threshold = containment_threshold

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute combined Jaccard + containment similarity

        Returns:
            Similarity score 0.0-1.0
        """
        # Normalize text
        text_a = text_a.lower()
        text_b = text_b.lower()

        # Exact match
        if text_a == text_b:
            return 1.0

        # Extract meaningful words (remove stopwords)
        words_a = self._extract_words(text_a)
        words_b = self._extract_words(text_b)

        if len(words_a) == 0 or len(words_b) == 0:
            return 0.0

        # Calculate both metrics
        jaccard = self._jaccard_similarity(words_a, words_b)
        containment = self._containment_similarity(words_a, words_b)

        # Return max of the two metrics (high score from either indicates similarity)
        return max(jaccard, containment)

    def are_similar(self, text_a: str, text_b: str) -> bool:
        """Check if two texts are similar based on thresholds"""
        # Extract words for threshold checking
        text_a = text_a.lower()
        text_b = text_b.lower()

        # Exact match
        if text_a == text_b:
            return True

        words_a = self._extract_words(text_a)
        words_b = self._extract_words(text_b)

        if len(words_a) == 0 or len(words_b) == 0:
            return False

        jaccard = self._jaccard_similarity(words_a, words_b)
        containment = self._containment_similarity(words_a, words_b)

        # Similar if either threshold is met
        return jaccard > self.jaccard_threshold or containment > self.containment_threshold

    def _extract_words(self, text: str) -> set[str]:
        """Extract meaningful words by removing stopwords"""
        return set(w for w in text.split() if w not in self.stopwords)

    def _jaccard_similarity(self, words_a: set[str], words_b: set[str]) -> float:
        """Calculate Jaccard similarity (intersection over union)"""
        overlap = len(words_a & words_b)
        total = len(words_a | words_b)
        return overlap / total if total > 0 else 0.0

    def _containment_similarity(self, words_a: set[str], words_b: set[str]) -> float:
        """Calculate containment similarity (one contains the other)"""
        overlap = len(words_a & words_b)
        min_size = min(len(words_a), len(words_b))
        return overlap / min_size if min_size > 0 else 0.0


class LearningSimilarityEngine:
    """
    Main similarity engine with caching and pluggable algorithms

    Supports multiple similarity algorithms and caches results for performance.
    """

    def __init__(self, algorithm: SimilarityAlgorithm | None = None) -> None:
        """
        Initialize similarity engine

        Args:
            algorithm: Similarity algorithm to use (default: JaccardContainmentSimilarity)
        """
        self.algorithm = algorithm or JaccardContainmentSimilarity()
        self._cache: dict[tuple[str, str], float] = {}
        self._word_cache: dict[int, set[str]] = {}  # Cache word sets for merge operations

    def are_similar(self, learning_a: dict, learning_b: dict) -> bool:
        """
        Check if two learnings are similar

        Args:
            learning_a: First learning dict with 'content' key
            learning_b: Second learning dict with 'content' key

        Returns:
            True if learnings are similar, False otherwise
        """
        content_a = learning_a.get("content", "")
        content_b = learning_b.get("content", "")

        # Use cached result if available
        if isinstance(self.algorithm, JaccardContainmentSimilarity):
            return self.algorithm.are_similar(content_a, content_b)
        else:
            # For other algorithms, use threshold of 0.7
            score = self.get_similarity_score(learning_a, learning_b)
            return score > 0.7

    def get_similarity_score(self, learning_a: dict, learning_b: dict) -> float:
        """
        Get similarity score between two learnings

        Args:
            learning_a: First learning dict
            learning_b: Second learning dict

        Returns:
            Similarity score 0.0-1.0
        """
        content_a = learning_a.get("content", "")
        content_b = learning_b.get("content", "")

        # Check cache
        cache_key = self._make_cache_key(content_a, content_b)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Compute similarity
        score = self.algorithm.compute_similarity(content_a, content_b)

        # Cache result
        self._cache[cache_key] = score

        return score

    @measure_time("similarity_merge")
    def merge_similar_learnings(self, learnings: dict) -> int:
        """
        Find and merge similar learnings within each category

        Optimized with word set caching to avoid redundant word extraction
        during similarity comparisons.

        Args:
            learnings: Learnings dict with 'categories' key

        Returns:
            Number of learnings merged
        """
        merged_count = 0
        categories = learnings.get("categories", {})

        for category_name, category_learnings in categories.items():
            # Clear word cache for new category
            self._word_cache.clear()

            # Pre-compute word sets for all learnings in this category
            # This optimization converts O(n²) word extraction to O(n)
            for i, learning in enumerate(category_learnings):
                content = learning.get("content", "").lower()
                if isinstance(self.algorithm, JaccardContainmentSimilarity):
                    words = self.algorithm._extract_words(content)
                    self._word_cache[i] = words

            to_remove = []

            for i, learning_a in enumerate(category_learnings):
                if i in to_remove:
                    continue

                for j in range(i + 1, len(category_learnings)):
                    if j in to_remove:
                        continue

                    learning_b = category_learnings[j]

                    if self.are_similar(learning_a, learning_b):
                        self._merge_learning(learning_a, learning_b)
                        to_remove.append(j)
                        merged_count += 1
                        logger.debug(
                            f"Merged similar learnings in '{category_name}': "
                            f"{learning_a.get('id')} <- {learning_b.get('id')}"
                        )

            # Remove merged learnings
            for idx in sorted(to_remove, reverse=True):
                category_learnings.pop(idx)

        logger.info(f"Merged {merged_count} similar learnings")
        return merged_count

    def get_related_learnings(
        self, learnings: dict, learning_id: str, limit: int = 5
    ) -> list[dict]:
        """
        Find learnings related to a specific learning

        Args:
            learnings: All learnings dict
            learning_id: ID of target learning
            limit: Maximum number of related learnings to return

        Returns:
            List of related learnings with similarity scores
        """
        # Find target learning
        target_learning = self._find_learning_by_id(learnings, learning_id)
        if not target_learning:
            return []

        # Calculate similarity scores for all other learnings
        similarities = []
        categories = learnings.get("categories", {})

        for category_learnings in categories.values():
            for learning in category_learnings:
                if learning.get("id") != learning_id:
                    score = self.get_similarity_score(target_learning, learning)
                    if score > 0.3:  # Only include somewhat similar learnings
                        similarities.append((score, learning))

        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [{**learning, "similarity_score": score} for score, learning in similarities[:limit]]

    def clear_cache(self) -> None:
        """Clear the similarity cache"""
        self._cache.clear()
        self._word_cache.clear()
        logger.debug("Similarity cache cleared")

    def _make_cache_key(self, text_a: str, text_b: str) -> tuple[str, str]:
        """Create cache key for two texts (order-independent)"""
        # Use sorted tuple for order-independent caching
        sorted_texts = sorted([text_a, text_b])
        return (sorted_texts[0], sorted_texts[1])

    def _merge_learning(self, target: dict, source: dict) -> None:
        """Merge source learning into target"""
        # Merge applies_to
        target_applies = set(target.get("applies_to", []))
        source_applies = set(source.get("applies_to", []))
        target["applies_to"] = list(target_applies | source_applies)

        # Merge tags
        target_tags = set(target.get("tags", []))
        source_tags = set(source.get("tags", []))
        target["tags"] = list(target_tags | source_tags)

        # Use longer content
        if len(source.get("content", "")) > len(target.get("content", "")):
            target["content"] = source["content"]

    def _find_learning_by_id(
        self, learnings: dict[str, Any], learning_id: str
    ) -> dict[str, Any] | None:
        """Find a learning by its ID"""
        categories = learnings.get("categories", {})
        for category_learnings in categories.values():
            for learning in category_learnings:
                if learning.get("id") == learning_id:
                    return learning  # type: ignore[no-any-return]
        return None
