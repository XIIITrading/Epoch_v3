"""
File-based caching for API responses.
Reduces API calls and improves performance.
"""
import json
import hashlib
import logging
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

from config import DATA_DIR, CACHE_TTL_DAILY, CACHE_TTL_INTRADAY

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages file-based caching of API responses.
    Supports DataFrame caching (parquet) and object caching (pickle).
    """

    def __init__(self, cache_dir: Path = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files (uses config default if not provided)
        """
        self.cache_dir = cache_dir or DATA_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_cache_key(self, *args, **kwargs) -> str:
        """
        Generate a unique cache key from arguments.

        Args:
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            16-character hex hash string
        """
        key_parts = [str(a) for a in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "_".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def _get_cache_path(self, key: str, extension: str = "pkl") -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.{extension}"

    def _is_valid(self, cache_path: Path, ttl_seconds: int) -> bool:
        """
        Check if a cache file is still valid (not expired).

        Args:
            cache_path: Path to cache file
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_path.exists():
            return False

        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age.total_seconds() < ttl_seconds

    # =========================================================================
    # DATAFRAME CACHING (Parquet format)
    # =========================================================================

    def get_dataframe(
        self,
        key: str,
        ttl_seconds: int = CACHE_TTL_DAILY
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve a cached DataFrame.

        Args:
            key: Cache key
            ttl_seconds: Time-to-live in seconds

        Returns:
            DataFrame if cache hit, None otherwise
        """
        cache_path = self._get_cache_path(key, "parquet")

        if self._is_valid(cache_path, ttl_seconds):
            try:
                df = pd.read_parquet(cache_path)
                logger.debug(f"Cache hit: {key}")
                return df
            except Exception as e:
                logger.warning(f"Cache read error for {key}: {e}")
                return None

        logger.debug(f"Cache miss: {key}")
        return None

    def set_dataframe(self, key: str, df: pd.DataFrame) -> bool:
        """
        Cache a DataFrame.

        Args:
            key: Cache key
            df: DataFrame to cache

        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key, "parquet")
        try:
            df.to_parquet(cache_path)
            logger.debug(f"Cached DataFrame: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
            return False

    # =========================================================================
    # OBJECT CACHING (Pickle format)
    # =========================================================================

    def get_object(
        self,
        key: str,
        ttl_seconds: int = CACHE_TTL_DAILY
    ) -> Optional[Any]:
        """
        Retrieve a cached Python object.

        Args:
            key: Cache key
            ttl_seconds: Time-to-live in seconds

        Returns:
            Object if cache hit, None otherwise
        """
        cache_path = self._get_cache_path(key, "pkl")

        if self._is_valid(cache_path, ttl_seconds):
            try:
                with open(cache_path, 'rb') as f:
                    obj = pickle.load(f)
                logger.debug(f"Cache hit: {key}")
                return obj
            except Exception as e:
                logger.warning(f"Cache read error for {key}: {e}")
                return None

        logger.debug(f"Cache miss: {key}")
        return None

    def set_object(self, key: str, obj: Any) -> bool:
        """
        Cache a Python object.

        Args:
            key: Cache key
            obj: Object to cache

        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key, "pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(obj, f)
            logger.debug(f"Cached object: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
            return False

    # =========================================================================
    # JSON CACHING
    # =========================================================================

    def get_json(
        self,
        key: str,
        ttl_seconds: int = CACHE_TTL_DAILY
    ) -> Optional[dict]:
        """
        Retrieve cached JSON data.

        Args:
            key: Cache key
            ttl_seconds: Time-to-live in seconds

        Returns:
            Dictionary if cache hit, None otherwise
        """
        cache_path = self._get_cache_path(key, "json")

        if self._is_valid(cache_path, ttl_seconds):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Cache hit: {key}")
                return data
            except Exception as e:
                logger.warning(f"Cache read error for {key}: {e}")
                return None

        logger.debug(f"Cache miss: {key}")
        return None

    def set_json(self, key: str, data: dict) -> bool:
        """
        Cache JSON data.

        Args:
            key: Cache key
            data: Dictionary to cache

        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key, "json")
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Cached JSON: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
            return False

    # =========================================================================
    # CACHE MANAGEMENT
    # =========================================================================

    def clear(self, pattern: str = "*") -> int:
        """
        Clear cache files matching a pattern.

        Args:
            pattern: Glob pattern for files to clear

        Returns:
            Number of files deleted
        """
        count = 0
        for path in self.cache_dir.glob(pattern):
            try:
                path.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Could not delete {path}: {e}")
        logger.info(f"Cleared {count} cache files matching '{pattern}'")
        return count

    def clear_expired(self, ttl_seconds: int = CACHE_TTL_DAILY) -> int:
        """
        Remove all expired cache files.

        Args:
            ttl_seconds: Files older than this are expired

        Returns:
            Number of files deleted
        """
        count = 0
        for path in self.cache_dir.iterdir():
            if path.is_file() and not self._is_valid(path, ttl_seconds):
                try:
                    path.unlink()
                    count += 1
                except Exception:
                    pass
        logger.info(f"Cleared {count} expired cache files")
        return count

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        files = list(self.cache_dir.iterdir())
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        return {
            'cache_dir': str(self.cache_dir),
            'file_count': len(files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_file': min(
                (f.stat().st_mtime for f in files if f.is_file()),
                default=None
            ),
            'newest_file': max(
                (f.stat().st_mtime for f in files if f.is_file()),
                default=None
            )
        }


# Global cache instance
cache = CacheManager()


def get_cache_key(*args, **kwargs) -> str:
    """
    Convenience function to generate cache keys.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    return cache._generate_cache_key(*args, **kwargs)
