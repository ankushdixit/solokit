"""Caching layer for frequently accessed data"""

import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class Cache:
    """Thread-safe cache with TTL"""

    def __init__(self, default_ttl: int = 300):
        """Initialize cache with default TTL (seconds)"""
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Get value from cache"""
        with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if datetime.now() < expires_at:
                    return value
                else:
                    # Expired
                    del self._cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        with self._lock:
            self._cache[key] = (value, expires_at)

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self._cache.clear()


# Global cache instance
_global_cache = Cache(default_ttl=60)  # 1 minute default


def get_cache() -> Cache:
    """Get global cache instance"""
    return _global_cache


class FileCache:
    """Cache for JSON files with modification tracking"""

    def __init__(self, cache: Cache | None = None):
        """Initialize file cache"""
        self.cache = cache or get_cache()

    def load_json(self, file_path: Path, loader_func: Callable[[Path], Any]) -> Any:
        """
        Load JSON with caching

        Args:
            file_path: Path to JSON file
            loader_func: Function to load file if not cached

        Returns:
            Loaded data (from cache or file)
        """
        cache_key = f"file:{file_path}"

        # Check modification time
        if file_path.exists():
            mtime = file_path.stat().st_mtime
            mtime_key = f"{cache_key}:mtime"

            # Check cache
            cached_mtime = self.cache.get(mtime_key)
            if cached_mtime == mtime:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data

            # Load and cache
            data = loader_func(file_path)
            self.cache.set(cache_key, data, ttl=300)  # 5 min TTL
            self.cache.set(mtime_key, mtime, ttl=300)
            return data
        else:
            return loader_func(file_path)

    def invalidate(self, file_path: Path) -> None:
        """Invalidate cache for file"""
        cache_key = f"file:{file_path}"
        self.cache.invalidate(cache_key)
        self.cache.invalidate(f"{cache_key}:mtime")
