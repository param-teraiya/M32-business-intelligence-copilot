"""
Rate Limiting for M32 Business Intelligence System
Implements rate limiting to prevent API abuse and manage costs.
"""

import asyncio
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
from functools import wraps
import redis.asyncio as redis
import json

from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting."""
    
    # Rate limits per endpoint (requests per minute)
    RATE_LIMITS = {
        "/api/chat": 30,           # Chat requests
        "/api/chat/stream": 20,    # Streaming chat
        "/api/auth/login": 10,     # Login attempts
        "/api/auth/register": 5,   # Registration attempts
        "default": 100             # Default limit
    }
    
    # Burst limits (requests per second)
    BURST_LIMITS = {
        "/api/chat": 3,
        "/api/chat/stream": 2,
        "/api/auth/login": 2,
        "default": 10
    }
    
    # Rate limit windows in seconds
    WINDOW_SIZE = 60  # 1 minute
    BURST_WINDOW = 1  # 1 second


class InMemoryRateLimiter:
    """
    In-memory rate limiter for development and small deployments.
    Uses local memory to track request counts.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.config = RateLimitConfig()
    
    async def is_allowed(self, key: str, endpoint: str) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            key: Unique identifier (user_id, IP address, etc.)
            endpoint: API endpoint being accessed
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        now = time.time()
        rate_key = f"{key}:{endpoint}"
        
        # Get rate limits for endpoint
        rate_limit = self.config.RATE_LIMITS.get(endpoint, self.config.RATE_LIMITS["default"])
        burst_limit = self.config.BURST_LIMITS.get(endpoint, self.config.BURST_LIMITS["default"])
        
        # Initialize if not exists
        if rate_key not in self.requests:
            self.requests[rate_key] = []
        
        # Clean old requests
        self.requests[rate_key] = [
            req_time for req_time in self.requests[rate_key]
            if now - req_time < self.config.WINDOW_SIZE
        ]
        
        # Check burst limit (requests per second)
        recent_requests = [
            req_time for req_time in self.requests[rate_key]
            if now - req_time < self.config.BURST_WINDOW
        ]
        
        if len(recent_requests) >= burst_limit:
            return False, {
                "error": "Burst limit exceeded",
                "limit": burst_limit,
                "window": "1 second",
                "retry_after": 1
            }
        
        # Check rate limit (requests per minute)
        if len(self.requests[rate_key]) >= rate_limit:
            oldest_request = min(self.requests[rate_key])
            retry_after = int(self.config.WINDOW_SIZE - (now - oldest_request)) + 1
            
            return False, {
                "error": "Rate limit exceeded",
                "limit": rate_limit,
                "window": "1 minute",
                "retry_after": retry_after
            }
        
        # Add current request
        self.requests[rate_key].append(now)
        
        return True, {
            "limit": rate_limit,
            "remaining": rate_limit - len(self.requests[rate_key]),
            "reset": int(now + self.config.WINDOW_SIZE),
            "window": "1 minute"
        }


class RedisRateLimiter:
    """
    Redis-based rate limiter for production deployments.
    Uses Redis for distributed rate limiting across multiple instances.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.config = RateLimitConfig()
    
    async def _get_redis(self):
        """Get Redis client connection."""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client
    
    async def is_allowed(self, key: str, endpoint: str) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed using Redis sliding window.
        
        Args:
            key: Unique identifier
            endpoint: API endpoint
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        try:
            redis_client = await self._get_redis()
            now = time.time()
            rate_key = f"rate_limit:{key}:{endpoint}"
            
            # Get limits
            rate_limit = self.config.RATE_LIMITS.get(endpoint, self.config.RATE_LIMITS["default"])
            burst_limit = self.config.BURST_LIMITS.get(endpoint, self.config.BURST_LIMITS["default"])
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(rate_key, 0, now - self.config.WINDOW_SIZE)
            
            # Count current requests
            pipe.zcard(rate_key)
            
            # Check burst (last second)
            pipe.zcount(rate_key, now - self.config.BURST_WINDOW, now)
            
            results = await pipe.execute()
            current_count = results[1]
            burst_count = results[2]
            
            # Check burst limit
            if burst_count >= burst_limit:
                return False, {
                    "error": "Burst limit exceeded",
                    "limit": burst_limit,
                    "window": "1 second",
                    "retry_after": 1
                }
            
            # Check rate limit
            if current_count >= rate_limit:
                # Get oldest request time for retry_after calculation
                oldest = await redis_client.zrange(rate_key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(self.config.WINDOW_SIZE - (now - oldest[0][1])) + 1
                else:
                    retry_after = self.config.WINDOW_SIZE
                
                return False, {
                    "error": "Rate limit exceeded",
                    "limit": rate_limit,
                    "window": "1 minute",
                    "retry_after": retry_after
                }
            
            # Add current request
            await redis_client.zadd(rate_key, {str(now): now})
            await redis_client.expire(rate_key, self.config.WINDOW_SIZE + 10)
            
            return True, {
                "limit": rate_limit,
                "remaining": rate_limit - current_count - 1,
                "reset": int(now + self.config.WINDOW_SIZE),
                "window": "1 minute"
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiter error: {str(e)}")
            # Fail open - allow request if Redis is down
            return True, {
                "error": "Rate limiter unavailable",
                "limit": "unknown",
                "remaining": "unknown"
            }
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


class RateLimitMiddleware:
    """
    FastAPI middleware for rate limiting.
    """
    
    def __init__(self, limiter: Optional[InMemoryRateLimiter] = None):
        self.limiter = limiter or InMemoryRateLimiter()
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/api/health", "/health"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        endpoint = self._normalize_endpoint(request.url.path)
        
        # Check rate limit
        allowed, limit_info = await self.limiter.is_allowed(client_id, endpoint)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {endpoint}: {limit_info}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": limit_info.get("error", "Too many requests"),
                    "retry_after": limit_info.get("retry_after", 60),
                    "limit": limit_info.get("limit"),
                    "window": limit_info.get("window")
                },
                headers={
                    "Retry-After": str(limit_info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(limit_info.get("limit", "unknown")),
                    "X-RateLimit-Remaining": str(limit_info.get("remaining", 0)),
                    "X-RateLimit-Reset": str(limit_info.get("reset", 0))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        if limit_info.get("limit"):
            response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(limit_info.get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(limit_info.get("reset", 0))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        
        # Try to get user ID from JWT token
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for rate limiting."""
        
        # Remove path parameters
        if "/sessions/" in path:
            path = path.split("/sessions/")[0] + "/sessions/*"
        
        # Map to rate limit categories
        if path.startswith("/api/chat"):
            if "stream" in path:
                return "/api/chat/stream"
            return "/api/chat"
        elif path.startswith("/api/auth"):
            if "login" in path:
                return "/api/auth/login"
            elif "register" in path:
                return "/api/auth/register"
            return "/api/auth"
        
        return "default"


def rate_limit(
    requests_per_minute: int = 60,
    burst_requests: int = 10
):
    """
    Decorator for rate limiting specific endpoints.
    
    Args:
        requests_per_minute: Maximum requests per minute
        burst_requests: Maximum burst requests per second
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be implemented if we need per-function rate limiting
            # For now, we use middleware for global rate limiting
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global rate limiter instances
memory_limiter = InMemoryRateLimiter()

def get_rate_limiter(redis_url: Optional[str] = None):
    """Get appropriate rate limiter based on configuration."""
    if redis_url:
        return RedisRateLimiter(redis_url)
    return memory_limiter
