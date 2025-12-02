"""
Caching utilities for the BDD Test Generator.
Provides LRU caching and memoization for expensive operations.
"""

import asyncio
import hashlib
from functools import wraps
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.
    """
    
    def __init__(self, maxsize: int = 100, ttl_seconds: int = 300):
        self.maxsize = maxsize
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, tuple] = {}  # key -> (value, timestamp)
        self._order: list = []  # Track access order
        self._lock = asyncio.Lock()
    
    def _is_expired(self, timestamp: datetime) -> bool:
        return datetime.now() - timestamp > self.ttl
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if not self._is_expired(timestamp):
                    # Move to end (most recently used)
                    self._order.remove(key)
                    self._order.append(key)
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]
                    self._order.remove(key)
            return None
    
    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            if key in self._cache:
                self._order.remove(key)
            elif len(self._cache) >= self.maxsize:
                # Remove least recently used
                oldest = self._order.pop(0)
                del self._cache[oldest]
            
            self._cache[key] = (value, datetime.now())
            self._order.append(key)
    
    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            self._order.clear()
    
    def size(self) -> int:
        return len(self._cache)


# Global cache instances
_element_cache = LRUCache(maxsize=200, ttl_seconds=60)
_llm_cache = LRUCache(maxsize=50, ttl_seconds=600)


def hash_content(content: str) -> str:
    """Generate a hash for content caching."""
    return hashlib.md5(content.encode()).hexdigest()


def async_cache(cache: LRUCache):
    """
    Decorator for caching async function results.
    
    Usage:
        @async_cache(_element_cache)
        async def expensive_operation(url: str) -> Result:
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hash_content(":".join(key_parts))
            
            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            # Execute and cache
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result)
            logger.debug(f"Cached result for {func.__name__}")
            return result
        
        return wrapper
    return decorator


def sync_cache(maxsize: int = 100):
    """
    Simple synchronous LRU cache decorator.
    
    Usage:
        @sync_cache(maxsize=50)
        def parse_html(content: str) -> ParsedResult:
            ...
    """
    def decorator(func: Callable):
        cache: Dict[str, Any] = {}
        order: list = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [func.__name__]
            key_parts.extend(str(arg)[:100] for arg in args)
            key_parts.extend(f"{k}={str(v)[:100]}" for k, v in sorted(kwargs.items()))
            cache_key = hash_content(":".join(key_parts))
            
            if cache_key in cache:
                order.remove(cache_key)
                order.append(cache_key)
                return cache[cache_key]
            
            result = func(*args, **kwargs)
            
            if len(cache) >= maxsize:
                oldest = order.pop(0)
                del cache[oldest]
            
            cache[cache_key] = result
            order.append(cache_key)
            return result
        
        wrapper.cache_clear = lambda: (cache.clear(), order.clear())
        return wrapper
    
    return decorator


# Export cache instances for use in other modules
element_cache = _element_cache
llm_cache = _llm_cache
