#!/usr/bin/env python3
"""
Base reporter interface for quality gate results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Reporter(ABC):
    """Abstract base class for result reporters."""

    @abstractmethod
    def generate(self, aggregated_results: dict[str, Any]) -> str:
        """Generate a report from aggregated results.

        Args:
            aggregated_results: Aggregated results from ResultAggregator

        Returns:
            Formatted report string
        """
        pass  # pragma: no cover
