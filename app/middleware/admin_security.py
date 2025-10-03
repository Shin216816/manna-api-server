"""
Admin Security Middleware

Production-ready security middleware for admin API endpoints with:
- Rate limiting per IP and user
- Request validation and sanitization
- Security headers
- Audit logging
- IP whitelisting
- Admin action monitoring
"""

import time
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone, timedelta
from functools import wraps
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from redis import Redis
from ipaddress import ip_address, ip_network
import re
from urllib.parse import unquote

from app.utils.database import get_db
from app.model.m_admin_audit_log import AdminAuditLog
from app.model.m_admin_user import AdminUser
from app.config import config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Redis for rate limiting (fallback to in-memory if Redis not available)
try:
    redis_client = Redis(
        host=getattr(config, 'REDIS_HOST', 'localhost'),
        port=getattr(config, 'REDIS_PORT', 6379),
        db=getattr(config, 'REDIS_DB', 0),
        decode_responses=True
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    # Fallback to in-memory storage
    rate_limit_cache: Dict[str, Dict] = {}

# Rate limiting configurations
RATE_LIMITS = {
    'login': {'requests': 5, 'window': 300},  # 5 attempts per 5 minutes
    'default': {'requests': 100, 'window': 60},  # 100 requests per minute
    'sensitive': {'requests': 10, 'window': 60},  # 10 requests per minute for sensitive operations
    'export': {'requests': 5, 'window': 300},  # 5 export requests per 5 minutes
}

# IP whitelist for admin access (configurable)
ADMIN_IP_WHITELIST = getattr(config, 'ADMIN_IP_WHITELIST', [])

# Security patterns
SUSPICIOUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'vbscript:',
    r'onload\s*=',
    r'onerror\s*=',
    r'<iframe',
    r'<object',
    r'<embed',
    r'eval\(',
    r'setTimeout\(',
    r'setInterval\(',
    r'Function\(',
    r'\.\./.*\.\.',  # Path traversal
    r'union\s+select',  # SQL injection
    r'drop\s+table',
    r'insert\s+into',
    r'delete\s+from',
    r'update\s+.*\s+set',
]

class SecurityValidator:
    """Request security validator"""

    @staticmethod
    def validate_input(data: Any, field_name: str = "") -> bool:
        """Validate input for security threats"""
        if data is None:
            return True

        text_data = str(data).lower()

        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_data, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected in {field_name}: {pattern}")
                return False

        # Check for excessive length
        if len(text_data) > 10000:  # 10KB limit
            logger.warning(f"Input too long in {field_name}: {len(text_data)} characters")
            return False

        return True

    @staticmethod
    def sanitize_input(data: Any) -> Any:
        """Sanitize input data"""
        if isinstance(data, str):
            # URL decode
            data = unquote(data)
            # Remove null bytes
            data = data.replace('\x00', '')
            # Limit length
            if len(data) > 10000:
                data = data[:10000]
        elif isinstance(data, dict):
            return {k: SecurityValidator.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [SecurityValidator.sanitize_input(item) for item in data]

        return data

class RateLimiter:
    """Rate limiting functionality"""

    @staticmethod
    def get_client_id(request: Request, user_id: Optional[int] = None) -> str:
        """Get unique client identifier"""
        # Use user ID if available, otherwise IP
        if user_id:
            return f"user:{user_id}"

        # Get real IP from headers (considering proxies)
        real_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
            request.headers.get("x-real-ip", "") or
            request.client.host
        )
        return f"ip:{real_ip}"

    @staticmethod
    def is_rate_limited(client_id: str, endpoint: str, limit_type: str = 'default') -> tuple[bool, Dict]:
        """Check if client is rate limited"""
        limit_config = RATE_LIMITS.get(limit_type, RATE_LIMITS['default'])
        window = limit_config['window']
        max_requests = limit_config['requests']

        current_time = int(time.time())
        window_start = current_time - window
        key = f"rate_limit:{client_id}:{endpoint}:{limit_type}"

        if REDIS_AVAILABLE:
            try:
                # Use Redis for distributed rate limiting
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zadd(key, {current_time: current_time})
                pipe.zcard(key)
                pipe.expire(key, window)
                results = pipe.execute()

                request_count = results[2]
                remaining = max(0, max_requests - request_count)

                return request_count > max_requests, {
                    'limit': max_requests,
                    'remaining': remaining,
                    'reset': current_time + window
                }
            except Exception as e:
                logger.error(f"Redis rate limiting error: {e}")
                # Fallback to in-memory
                pass

        # In-memory fallback
        if key not in rate_limit_cache:
            rate_limit_cache[key] = []

        # Clean old requests
        rate_limit_cache[key] = [
            req_time for req_time in rate_limit_cache[key]
            if req_time > window_start
        ]

        # Add current request
        rate_limit_cache[key].append(current_time)

        request_count = len(rate_limit_cache[key])
        remaining = max(0, max_requests - request_count)

        return request_count > max_requests, {
            'limit': max_requests,
            'remaining': remaining,
            'reset': current_time + window
        }

class AdminAuditor:
    """Admin action auditing"""

    @staticmethod
    def log_admin_action(
        db: Session,
        admin_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ):
        """Log admin action for audit trail"""
        try:
            audit_log = AdminAuditLog(
                admin_id=admin_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")

def check_ip_whitelist(request: Request) -> bool:
    """Check if request IP is in whitelist"""
    if not ADMIN_IP_WHITELIST:
        return True  # No whitelist configured

    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
        request.headers.get("x-real-ip", "") or
        request.client.host
    )

    try:
        client_ip_obj = ip_address(client_ip)
        for allowed in ADMIN_IP_WHITELIST:
            if '/' in allowed:  # CIDR notation
                if client_ip_obj in ip_network(allowed):
                    return True
            else:  # Single IP
                if client_ip_obj == ip_address(allowed):
                    return True
        return False
    except Exception as e:
        logger.error(f"IP whitelist check error: {e}")
        return False

def add_security_headers(response: JSONResponse) -> JSONResponse:
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; font-src 'self' data:; connect-src 'self' https://api.plaid.com https://api.stripe.com;"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

async def admin_security_middleware(
    request: Request,
    call_next,
    db: Session = Depends(get_db)
):
    """Main admin security middleware"""

    # Skip security checks for health endpoints
    if request.url.path in ['/health', '/api/v1/health']:
        response = await call_next(request)
        return response

    # Only apply to admin endpoints
    if not request.url.path.startswith('/api/v1/admin'):
        response = await call_next(request)
        return response

    start_time = time.time()

    try:
        # IP Whitelist check
        if ADMIN_IP_WHITELIST and not check_ip_whitelist(request):
            logger.warning(f"IP not in whitelist: {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access denied from this IP address"}
            )

        # Get endpoint and method
        endpoint = request.url.path
        method = request.method

        # Determine rate limit type
        limit_type = 'default'
        if 'login' in endpoint:
            limit_type = 'login'
        elif any(sensitive in endpoint for sensitive in ['kyc', 'payout', 'delete', 'approve', 'reject']):
            limit_type = 'sensitive'
        elif 'export' in endpoint:
            limit_type = 'export'

        # Rate limiting
        client_id = RateLimiter.get_client_id(request)
        is_limited, rate_info = RateLimiter.is_rate_limited(client_id, endpoint, limit_type)

        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_id} on {endpoint}")
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many requests",
                    "retry_after": rate_info.get('reset', 60)
                }
            )
            response.headers["Retry-After"] = str(rate_info.get('reset', 60))
            return add_security_headers(response)

        # Request validation for POST/PUT requests
        if method in ['POST', 'PUT', 'PATCH']:
            try:
                # Get request body
                body = await request.body()
                if body:
                    try:
                        data = json.loads(body.decode())

                        # Validate input
                        for field, value in data.items():
                            if not SecurityValidator.validate_input(value, field):
                                logger.warning(f"Suspicious input detected in {field}")
                                return JSONResponse(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    content={"error": "Invalid input detected"}
                                )

                        # Sanitize input
                        sanitized_data = SecurityValidator.sanitize_input(data)

                        # Replace request body with sanitized data
                        request._body = json.dumps(sanitized_data).encode()

                    except json.JSONDecodeError:
                        pass  # Not JSON, skip validation

            except Exception as e:
                logger.error(f"Request validation error: {e}")

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        if isinstance(response, JSONResponse):
            response.headers["X-RateLimit-Limit"] = str(rate_info['limit'])
            response.headers["X-RateLimit-Remaining"] = str(rate_info['remaining'])
            response.headers["X-RateLimit-Reset"] = str(rate_info['reset'])

        # Add security headers
        response = add_security_headers(response)

        # Log successful request
        processing_time = time.time() - start_time
        logger.info(f"Admin API: {method} {endpoint} - {response.status_code} - {processing_time:.3f}s")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security middleware error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal security error"}
        )

def rate_limit(limit_type: str = 'default'):
    """Decorator for additional rate limiting on specific endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_id = RateLimiter.get_client_id(request)
            endpoint = request.url.path

            is_limited, rate_info = RateLimiter.is_rate_limited(client_id, endpoint, limit_type)

            if is_limited:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(rate_info.get('reset', 60))}
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def audit_action(action: str, resource_type: str):
    """Decorator for auditing admin actions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract common parameters
            request = None
            current_user = None
            resource_id = None
            db = None

            # Find parameters in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, dict) and 'id' in arg:
                    current_user = arg
                elif isinstance(arg, Session):
                    db = arg

            for key, value in kwargs.items():
                if key == 'current_user' and isinstance(value, dict):
                    current_user = value
                elif key == 'db' and isinstance(value, Session):
                    db = value
                elif key in ['church_id', 'user_id', 'id'] and isinstance(value, int):
                    resource_id = value

            success = True
            error_message = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                # Log the action
                if db and current_user:
                    try:
                        ip_address = None
                        user_agent = None

                        if request:
                            ip_address = (
                                request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
                                request.headers.get("x-real-ip", "") or
                                str(request.client.host)
                            )
                            user_agent = request.headers.get("user-agent", "")

                        details = {}
                        if error_message:
                            details['error'] = error_message
                        if resource_id:
                            details['resource_id'] = resource_id

                        AdminAuditor.log_admin_action(
                            db=db,
                            admin_id=current_user.get('id'),
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            details=details,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            success=success
                        )
                    except Exception as audit_error:
                        logger.error(f"Failed to log audit action: {audit_error}")

        return wrapper
    return decorator

# Security configuration
def get_security_config():
    """Get current security configuration"""
    return {
        'rate_limits': RATE_LIMITS,
        'redis_available': REDIS_AVAILABLE,
        'ip_whitelist_enabled': bool(ADMIN_IP_WHITELIST),
        'ip_whitelist_count': len(ADMIN_IP_WHITELIST),
        'suspicious_patterns_count': len(SUSPICIOUS_PATTERNS)
    }
