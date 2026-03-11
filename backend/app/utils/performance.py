"""
Performance Optimization Utilities

Provides caching, connection pooling, and performance monitoring utilities
to ensure query latency stays under 5 seconds.
"""

import asyncio
import functools
import hashlib
import time
from typing import Any, Callable, Optional, TypeVar, cast
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    
    Used for caching expensive operations like LLM calls and database queries.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._hits += 1
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                # Expired, remove from cache
                del self._cache[key]
        
        self._misses += 1
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl or self._default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
        logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Deleted cache key: {key}")
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Hash-based cache key
    """
    # Create a string representation of arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = "|".join(key_parts)
    
    # Hash for consistent key length
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]


def async_cached(ttl: int = 300, cache_instance: Optional[SimpleCache] = None):
    """
    Decorator for caching async function results.
    
    Args:
        ttl: Time-to-live in seconds
        cache_instance: Cache instance to use (creates new if not provided)
        
    Returns:
        Decorated function
    """
    _cache = cache_instance or SimpleCache(default_ttl=ttl)
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = _cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            _cache.set(key, result, ttl)
            
            return result
        
        # Attach cache instance for external access
        wrapper._cache = _cache  # type: ignore
        return wrapper
    
    return decorator


class PerformanceMonitor:
    """
    Monitor and track performance metrics.
    """
    
    def __init__(self):
        self._metrics: dict[str, list[float]] = {}
        self._thresholds: dict[str, float] = {}
    
    def record(self, operation: str, duration: float) -> None:
        """
        Record operation duration.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        if operation not in self._metrics:
            self._metrics[operation] = []
        
        self._metrics[operation].append(duration)
        
        # Check threshold
        if operation in self._thresholds:
            threshold = self._thresholds[operation]
            if duration > threshold:
                logger.warning(
                    f"Performance threshold exceeded for {operation}: "
                    f"{duration:.3f}s > {threshold:.3f}s"
                )
    
    def set_threshold(self, operation: str, threshold: float) -> None:
        """
        Set performance threshold for operation.
        
        Args:
            operation: Operation name
            threshold: Threshold in seconds
        """
        self._thresholds[operation] = threshold
    
    def get_stats(self, operation: str) -> Optional[dict[str, float]]:
        """
        Get statistics for operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Statistics dictionary or None if no data
        """
        if operation not in self._metrics or not self._metrics[operation]:
            return None
        
        durations = self._metrics[operation]
        durations_sorted = sorted(durations)
        count = len(durations)
        
        return {
            "count": count,
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / count,
            "p50": durations_sorted[count // 2],
            "p95": durations_sorted[int(count * 0.95)],
            "p99": durations_sorted[int(count * 0.99)],
        }
    
    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all operations."""
        result = {}
        for operation in self._metrics:
            stats = self.get_stats(operation)
            if stats is not None:
                result[operation] = stats
        return result
    
    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()


def timed(monitor: Optional[PerformanceMonitor] = None):
    """
    Decorator for timing async function execution.
    
    Args:
        monitor: Performance monitor instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                logger.debug(f"{func.__name__} took {duration:.3f}s")
                
                if monitor:
                    monitor.record(func.__name__, duration)
        
        return wrapper
    
    return decorator


async def run_with_timeout(
    coro: Any,
    timeout: float,
    default: Optional[Any] = None,
) -> Any:
    """
    Run coroutine with timeout.
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        default: Default value to return on timeout
        
    Returns:
        Coroutine result or default value on timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s")
        return default


async def run_parallel(
    tasks: list[Any],
    max_concurrent: int = 10,
) -> list[Any]:
    """
    Run tasks in parallel with concurrency limit.
    
    Args:
        tasks: List of coroutines to run
        max_concurrent: Maximum concurrent tasks
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[bounded_task(task) for task in tasks])


# Global instances
global_cache = SimpleCache(default_ttl=300)
global_monitor = PerformanceMonitor()

# Set default thresholds
global_monitor.set_threshold("process_query", 5.0)  # 5 second target
global_monitor.set_threshold("generate_completion", 3.0)  # 3 second LLM target
global_monitor.set_threshold("execute_query", 1.0)  # 1 second DB target

# Made with Bob
