"""Simple LRU cache implementation for game names and Discord app IDs"""

from typing import Any, Dict, Optional


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache with maximum size.

    When the cache is full, the oldest entry is removed to make space for new ones.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries to store
        """
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if key in self._cache:
            # Move to end (most recently used)
            value = self._cache.pop(key)
            self._cache[key] = value
            return value
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Add or update value in cache.

        Args:
            key: Cache key
            value: Value to store
        """
        if key in self._cache:
            # Remove old entry
            del self._cache[key]
        elif len(self._cache) >= self.max_size:
            # Remove oldest entry (first in dict)
            first_key = next(iter(self._cache))
            del self._cache[first_key]

        # Add new entry (most recent)
        self._cache[key] = value

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache

    def __len__(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)
