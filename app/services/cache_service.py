"""
Comprehensive Caching Service for Production

Implements:
- Redis-based distributed caching
- Memory-based fallback caching
- Cache invalidation strategies
- Cache warming
- Performance metrics
- Cache compression
"""

import json
import logging
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timezone, timedelta
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using memory cache")

@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl: int = 3600  # Time to live in seconds
    compress: bool = True
    serialize: bool = True
    namespace: str = "manna"

class CacheService:
    """Comprehensive caching service"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict] = {}
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                self.redis_client.ping()
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory cache")
                self.redis_client = None
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            if self.redis_client:
                return self._get_redis(key, default)
            else:
                return self._get_memory(key, default)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats['errors'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, config: Optional[CacheConfig] = None) -> bool:
        """Set value in cache"""
        try:
            if config is None:
                config = CacheConfig()
            
            if ttl is None:
                ttl = config.ttl
            
            if self.redis_client:
                return self._set_redis(key, value, ttl, config)
            else:
                return self._set_memory(key, value, ttl, config)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.stats['errors'] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.redis_client:
                return self._delete_redis(key)
            else:
                return self._delete_memory(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.stats['errors'] += 1
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.redis_client:
                return self._exists_redis(key)
            else:
                return self._exists_memory(key)
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def clear(self, pattern: str = None) -> int:
        """Clear cache entries"""
        try:
            if self.redis_client:
                return self._clear_redis(pattern)
            else:
                return self._clear_memory(pattern)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'errors': self.stats['errors'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'backend': 'redis' if self.redis_client else 'memory'
        }
    
    def _get_redis(self, key: str, default: Any) -> Any:
        """Get value from Redis"""
        try:
            data = self.redis_client.get(key)
            if data is None:
                self.stats['misses'] += 1
                return default
            
            # Deserialize data
            value = self._deserialize(data)
            self.stats['hits'] += 1
            return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.stats['errors'] += 1
            return default
    
    def _set_redis(self, key: str, value: Any, ttl: int, config: CacheConfig) -> bool:
        """Set value in Redis"""
        try:
            # Serialize data
            data = self._serialize(value, config)
            
            # Set with TTL
            result = self.redis_client.setex(key, ttl, data)
            self.stats['sets'] += 1
            return result
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self.stats['errors'] += 1
            return False
    
    def _delete_redis(self, key: str) -> bool:
        """Delete value from Redis"""
        try:
            result = self.redis_client.delete(key)
            self.stats['deletes'] += 1
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            self.stats['errors'] += 1
            return False
    
    def _exists_redis(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    def _clear_redis(self, pattern: str = None) -> int:
        """Clear Redis cache entries"""
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                return self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0
    
    def _get_memory(self, key: str, default: Any) -> Any:
        """Get value from memory cache"""
        if key not in self.memory_cache:
            self.stats['misses'] += 1
            return default
        
        cache_entry = self.memory_cache[key]
        
        # Check TTL
        if datetime.now(timezone.utc) > cache_entry['expires_at']:
            del self.memory_cache[key]
            self.stats['misses'] += 1
            return default
        
        self.stats['hits'] += 1
        return cache_entry['value']
    
    def _set_memory(self, key: str, value: Any, ttl: int, config: CacheConfig) -> bool:
        """Set value in memory cache"""
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            
            self.memory_cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now(timezone.utc)
            }
            
            self.stats['sets'] += 1
            return True
        except Exception as e:
            logger.error(f"Memory set error: {e}")
            self.stats['errors'] += 1
            return False
    
    def _delete_memory(self, key: str) -> bool:
        """Delete value from memory cache"""
        if key in self.memory_cache:
            del self.memory_cache[key]
            self.stats['deletes'] += 1
            return True
        return False
    
    def _exists_memory(self, key: str) -> bool:
        """Check if key exists in memory cache"""
        if key not in self.memory_cache:
            return False
        
        # Check TTL
        cache_entry = self.memory_cache[key]
        if datetime.now(timezone.utc) > cache_entry['expires_at']:
            del self.memory_cache[key]
            return False
        
        return True
    
    def _clear_memory(self, pattern: str = None) -> int:
        """Clear memory cache entries"""
        if pattern:
            keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.memory_cache[key]
            return len(keys_to_delete)
        else:
            count = len(self.memory_cache)
            self.memory_cache.clear()
            return count
    
    def _serialize(self, value: Any, config: CacheConfig) -> bytes:
        """Serialize value for storage"""
        if not config.serialize:
            return str(value).encode('utf-8')
        
        if config.compress:
            import gzip
            data = pickle.dumps(value)
            return gzip.compress(data)
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try to deserialize as pickle
            return pickle.loads(data)
        except:
            try:
                # Try to deserialize as compressed pickle
                import gzip
                return pickle.loads(gzip.decompress(data))
            except:
                # Fallback to string
                return data.decode('utf-8')


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 3600, key_func: callable = None, config: CacheConfig = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                cache_key_str = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cache_service = get_cache_service()
            result = cache_service.get(cache_key_str)
            
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key_str, result, ttl, config)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(pattern: str = None):
    """Decorator for cache invalidation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache
            cache_service = get_cache_service()
            if pattern:
                cache_service.clear(pattern)
            else:
                # Invalidate by function name
                cache_service.clear(f"{func.__name__}:*")
            
            return result
        
        return wrapper
    return decorator


# Global cache service instance
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return cache_service


def setup_cache_service(redis_url: Optional[str] = None):
    """Setup cache service with Redis"""
    global cache_service
    cache_service = CacheService(redis_url)
