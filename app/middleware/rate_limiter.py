"""
Advanced Rate Limiting Middleware

Implements:
- Redis-based distributed rate limiting
- Sliding window algorithm
- Per-user and per-IP rate limits
- Burst protection
- Rate limit headers
"""

import time
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.responses import ResponseFactory

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory rate limiting")

class RateLimiter:
    """Advanced rate limiter with Redis support"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict] = {}
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
                logger.info("Redis rate limiting enabled")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory cache")
                self.redis_client = None
        
        # Rate limit configurations
        self.limits = {
            'default': {'requests': 100, 'window': 60, 'burst': 20},
            'auth': {'requests': 10, 'window': 60, 'burst': 3},
            'api': {'requests': 1000, 'window': 3600, 'burst': 100},
            'donation': {'requests': 20, 'window': 60, 'burst': 5},
            'upload': {'requests': 10, 'window': 60, 'burst': 2},
            'admin': {'requests': 500, 'window': 60, 'burst': 50},
        }
    
    def is_rate_limited(
        self, 
        key: str, 
        limit_type: str = 'default',
        user_id: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """Check if request is rate limited using sliding window algorithm"""
        
        config = self.limits.get(limit_type, self.limits['default'])
        current_time = time.time()
        
        # Add user context to key if available
        if user_id:
            key = f"{key}:user:{user_id}"
        
        # Use Redis if available, otherwise memory
        if self.redis_client:
            return self._check_redis_rate_limit(key, config, current_time)
        else:
            return self._check_memory_rate_limit(key, config, current_time)
    
    def _check_redis_rate_limit(self, key: str, config: Dict, current_time: float) -> Tuple[bool, Dict]:
        """Check rate limit using Redis with sliding window"""
        window = config['window']
        max_requests = config['requests']
        burst_limit = config['burst']
        
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        cutoff_time = current_time - window
        pipe.zremrangebyscore(key, 0, cutoff_time)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(key, window + 10)
        
        results = pipe.execute()
        current_count = results[1]
        
        # Check burst limit
        if current_count >= burst_limit:
            # Check if we're in burst mode (recent requests)
            recent_cutoff = current_time - 10  # Last 10 seconds
            recent_count = self.redis_client.zcount(key, recent_cutoff, current_time)
            
            if recent_count > burst_limit:
                retry_after = 10  # Wait 10 seconds for burst
                return True, {
                    'retry_after': retry_after,
                    'limit': max_requests,
                    'window': window,
                    'current_requests': current_count,
                    'burst_exceeded': True
                }
        
        # Check regular limit
        if current_count > max_requests:
            # Get oldest request time
            oldest_requests = self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_requests:
                oldest_time = oldest_requests[0][1]
                retry_after = int(window - (current_time - oldest_time)) + 1
            else:
                retry_after = window
            
            return True, {
                'retry_after': retry_after,
                'limit': max_requests,
                'window': window,
                'current_requests': current_count,
                'burst_exceeded': False
            }
        
        return False, {
            'limit': max_requests,
            'window': window,
            'current_requests': current_count,
            'remaining': max_requests - current_count
        }
    
    def _check_memory_rate_limit(self, key: str, config: Dict, current_time: float) -> Tuple[bool, Dict]:
        """Check rate limit using memory cache with sliding window"""
        window = config['window']
        max_requests = config['requests']
        burst_limit = config['burst']
        
        # Initialize key if not exists
        if key not in self.memory_cache:
            self.memory_cache[key] = {
                'requests': [],
                'last_cleanup': current_time
            }
        
        cache = self.memory_cache[key]
        
        # Cleanup old entries periodically
        if current_time - cache['last_cleanup'] > 60:  # Cleanup every minute
            cutoff_time = current_time - window
            cache['requests'] = [req_time for req_time in cache['requests'] if req_time > cutoff_time]
            cache['last_cleanup'] = current_time
        
        # Remove old entries
        cutoff_time = current_time - window
        cache['requests'] = [req_time for req_time in cache['requests'] if req_time > cutoff_time]
        
        current_count = len(cache['requests'])
        
        # Check burst limit
        if current_count >= burst_limit:
            recent_cutoff = current_time - 10  # Last 10 seconds
            recent_count = sum(1 for req_time in cache['requests'] if req_time > recent_cutoff)
            
            if recent_count > burst_limit:
                retry_after = 10
                return True, {
                    'retry_after': retry_after,
                    'limit': max_requests,
                    'window': window,
                    'current_requests': current_count,
                    'burst_exceeded': True
                }
        
        # Check regular limit
        if current_count >= max_requests:
            if cache['requests']:
                oldest_time = min(cache['requests'])
                retry_after = int(window - (current_time - oldest_time)) + 1
            else:
                retry_after = window
            
            return True, {
                'retry_after': retry_after,
                'limit': max_requests,
                'window': window,
                'current_requests': current_count,
                'burst_exceeded': False
            }
        
        # Add current request
        cache['requests'].append(current_time)
        
        return False, {
            'limit': max_requests,
            'window': window,
            'current_requests': current_count + 1,
            'remaining': max_requests - (current_count + 1)
        }
    
    def get_rate_limit_info(self, key: str, limit_type: str = 'default') -> Dict:
        """Get current rate limit information without consuming a request"""
        config = self.limits.get(limit_type, self.limits['default'])
        current_time = time.time()
        
        if self.redis_client:
            # Get current count from Redis
            cutoff_time = current_time - config['window']
            current_count = self.redis_client.zcount(key, cutoff_time, current_time)
        else:
            # Get current count from memory
            if key in self.memory_cache:
                cutoff_time = current_time - config['window']
                cache = self.memory_cache[key]
                current_count = sum(1 for req_time in cache['requests'] if req_time > cutoff_time)
            else:
                current_count = 0
        
        return {
            'limit': config['requests'],
            'window': config['window'],
            'current_requests': current_count,
            'remaining': max(0, config['requests'] - current_count),
            'reset_time': current_time + config['window']
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, redis_url: Optional[str] = None):
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis_url)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ['/health', '/health/detailed']:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Determine rate limit type
        limit_type = self._get_rate_limit_type(request)
        
        # Check rate limit
        is_limited, rate_info = self.rate_limiter.is_rate_limited(
            client_id, 
            limit_type,
            getattr(request.state, 'user_id', None)
        )
        
        if is_limited:
            return self._create_rate_limit_response(rate_info, request)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, rate_info)
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier"""
        # Get IP address
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return client_ip
    
    def _get_rate_limit_type(self, request: Request) -> str:
        """Determine rate limit type based on request"""
        path = request.url.path
        method = request.method
        
        if '/auth/' in path or '/login' in path:
            return 'auth'
        elif '/donation' in path or '/roundup' in path:
            return 'donation'
        elif '/upload' in path:
            return 'upload'
        elif '/admin/' in path:
            return 'admin'
        elif path.startswith('/api/v1/'):
            return 'api'
        else:
            return 'default'
    
    def _create_rate_limit_response(self, rate_info: Dict, request: Request) -> JSONResponse:
        """Create rate limit exceeded response"""
        error_response = ResponseFactory.error(
            message=f"Rate limit exceeded. Try again in {rate_info['retry_after']} seconds",
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                'retry_after': rate_info['retry_after'],
                'limit': rate_info['limit'],
                'window': rate_info['window'],
                'current_requests': rate_info['current_requests'],
                'burst_exceeded': rate_info.get('burst_exceeded', False)
            }
        )
        
        response = JSONResponse(
            status_code=200,  # Always return 200 for consistency
            content=error_response.model_dump(mode='json')
        )
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, rate_info)
        
        return response
    
    def _add_rate_limit_headers(self, response: JSONResponse, rate_info: Dict):
        """Add rate limit headers to response"""
        response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(rate_info.get('remaining', 0))
        response.headers['X-RateLimit-Reset'] = str(int(rate_info.get('reset_time', time.time())))
        
        if 'retry_after' in rate_info:
            response.headers['Retry-After'] = str(rate_info['retry_after'])


def setup_rate_limiting(app, redis_url: Optional[str] = None):
    """Setup rate limiting middleware"""
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url)
