"""
Cache management system for Discovery Assistant.

Provides LRU cache with TTL and automatic DDL-based invalidation.
"""

import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from .models import DiscoveryResult


@dataclass
class CacheEntry:
    """Cached discovery result with metadata."""

    result: DiscoveryResult
    table_last_ddl: str
    cached_at: datetime
    access_count: int = 0

    def is_valid(self, current_ddl: str, ttl_seconds: int) -> bool:
        """
        Check if cache entry is still valid.

        Args:
            current_ddl: Current LAST_DDL timestamp from table
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if entry is valid, False otherwise
        """
        # Check DDL hasn't changed
        if self.table_last_ddl != current_ddl:
            return False

        # Check TTL
        age = (datetime.utcnow() - self.cached_at).total_seconds()
        if age > ttl_seconds:
            return False

        return True


class LRUCache:
    """Thread-safe LRU cache with size limit."""

    def __init__(self, maxsize: int = 100):
        """
        Initialize LRU cache.

        Args:
            maxsize: Maximum number of entries (default: 100)
        """
        self.maxsize = maxsize
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Get item from cache, moving it to end (most recently used).

        Args:
            key: Cache key

        Returns:
            CacheEntry if found, None otherwise
        """
        with self.lock:
            if key not in self.cache:
                return None

            # Move to end (most recent)
            entry = self.cache.pop(key)
            entry.access_count += 1
            self.cache[key] = entry
            return entry

    def put(self, key: str, entry: CacheEntry) -> None:
        """
        Add item to cache, evicting oldest if necessary.

        Args:
            key: Cache key
            entry: CacheEntry to store
        """
        with self.lock:
            # Remove if already exists
            if key in self.cache:
                self.cache.pop(key)

            # Add new entry
            self.cache[key] = entry

            # Evict oldest if over capacity
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)  # Remove first (oldest)

    def invalidate(self, key: str) -> None:
        """
        Remove entry from cache.

        Args:
            key: Cache key to invalidate
        """
        with self.lock:
            self.cache.pop(key, None)

    def clear(self) -> None:
        """Clear entire cache."""
        with self.lock:
            self.cache.clear()

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            total_accesses = sum(e.access_count for e in self.cache.values())
            return {
                "size": len(self.cache),
                "maxsize": self.maxsize,
                "total_accesses": total_accesses,
                "avg_accesses": total_accesses / len(self.cache) if self.cache else 0,
            }


class DiscoveryCacheManager:
    """
    Manages caching for table discovery results.

    Features:
    - LRU eviction (max 100 entries)
    - TTL-based expiration (1 hour default)
    - Automatic LAST_DDL invalidation
    - DDL check caching (1 minute) to reduce metadata queries
    """

    def __init__(
        self, maxsize: int = 100, ttl_seconds: int = 3600, ddl_check_ttl: int = 60
    ):
        """
        Initialize cache manager.

        Args:
            maxsize: Maximum number of cached entries (default: 100)
            ttl_seconds: Time-to-live in seconds (default: 3600 = 1 hour)
            ddl_check_ttl: DDL check cache TTL in seconds (default: 60 = 1 minute)
        """
        self.cache = LRUCache(maxsize=maxsize)
        self.ttl_seconds = ttl_seconds

        # Secondary cache for DDL timestamps (reduces metadata queries)
        self.ddl_cache: Dict[str, Tuple[str, datetime]] = {}
        self.ddl_check_ttl = ddl_check_ttl
        self.lock = threading.RLock()

    def _get_cache_key(
        self,
        table_name: str,
        include_relationships: bool,
        include_ai_analysis: bool,
    ) -> str:
        """
        Generate cache key from parameters.

        Args:
            table_name: Fully-qualified table name
            include_relationships: Whether relationships were included
            include_ai_analysis: Whether AI analysis was included

        Returns:
            Cache key string
        """
        return f"{table_name}:ai={include_ai_analysis}:rel={include_relationships}"

    def get_cached_result(
        self,
        table_name: str,
        include_relationships: bool,
        include_ai_analysis: bool,
        current_ddl_getter: Callable[[], str],
        force_refresh: bool = False,
    ) -> Optional[DiscoveryResult]:
        """
        Retrieve cached result if valid.

        Args:
            table_name: Table to look up
            include_relationships: Whether relationships were included
            include_ai_analysis: Whether AI analysis was included
            current_ddl_getter: Callable that returns current LAST_DDL timestamp
            force_refresh: If True, bypass cache

        Returns:
            Cached DiscoveryResult if valid, None otherwise
        """
        if force_refresh:
            return None

        cache_key = self._get_cache_key(
            table_name, include_relationships, include_ai_analysis
        )

        # Check main cache
        entry = self.cache.get(cache_key)
        if not entry:
            return None

        # Check if we recently verified this table's DDL
        with self.lock:
            if table_name in self.ddl_cache:
                cached_ddl, cached_at = self.ddl_cache[table_name]
                age = (datetime.utcnow() - cached_at).total_seconds()

                if age < self.ddl_check_ttl:
                    # Recent DDL check, trust it
                    if entry.is_valid(cached_ddl, self.ttl_seconds):
                        return entry.result

        # Need to verify DDL hasn't changed
        try:
            current_ddl = current_ddl_getter()
        except Exception:
            # If DDL check fails, invalidate cache entry
            self.cache.invalidate(cache_key)
            return None

        # Update DDL cache
        with self.lock:
            self.ddl_cache[table_name] = (current_ddl, datetime.utcnow())

        # Check if entry is still valid
        if entry.is_valid(current_ddl, self.ttl_seconds):
            return entry.result
        else:
            # Invalidate stale entry
            self.cache.invalidate(cache_key)
            return None

    def cache_result(
        self,
        table_name: str,
        result: DiscoveryResult,
        include_relationships: bool,
        include_ai_analysis: bool,
        table_last_ddl: str,
    ) -> None:
        """
        Cache a discovery result.

        Args:
            table_name: Table name
            result: DiscoveryResult to cache
            include_relationships: Whether relationships were included
            include_ai_analysis: Whether AI analysis was included
            table_last_ddl: LAST_DDL timestamp from table
        """
        cache_key = self._get_cache_key(
            table_name, include_relationships, include_ai_analysis
        )

        entry = CacheEntry(
            result=result, table_last_ddl=table_last_ddl, cached_at=datetime.utcnow()
        )

        self.cache.put(cache_key, entry)

        # Update DDL cache
        with self.lock:
            self.ddl_cache[table_name] = (table_last_ddl, datetime.utcnow())

    def invalidate_table(self, table_name: str) -> None:
        """
        Invalidate all cache entries for a specific table.

        Args:
            table_name: Table name to invalidate
        """
        # Invalidate from all possible parameter combinations
        for include_rel in [True, False]:
            for include_ai in [True, False]:
                cache_key = self._get_cache_key(table_name, include_rel, include_ai)
                self.cache.invalidate(cache_key)

        # Invalidate DDL cache
        with self.lock:
            self.ddl_cache.pop(table_name, None)

    def clear(self) -> None:
        """Clear all caches."""
        self.cache.clear()
        with self.lock:
            self.ddl_cache.clear()

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "main_cache": self.cache.stats(),
            "ddl_cache_size": len(self.ddl_cache),
        }


# Global cache instance
_cache_manager: Optional[DiscoveryCacheManager] = None


def get_cache_manager() -> DiscoveryCacheManager:
    """
    Get or create global cache manager singleton.

    Returns:
        Global DiscoveryCacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DiscoveryCacheManager()
    return _cache_manager
