"""
Rate limiting middleware using Redis.

Implements token bucket algorithm for API rate limiting.
"""

from __future__ import annotations

import time
from typing import Callable

try:
    from fastapi import Request, Response, HTTPException, status
    from starlette.middleware.base import BaseHTTPMiddleware
    import redis.asyncio as redis
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False
    Request = None  # type: ignore
    Response = None  # type: ignore
    BaseHTTPMiddleware = None  # type: ignore
    redis = None  # type: ignore

from koocad.backend.config import get_settings

settings = get_settings()


if MIDDLEWARE_AVAILABLE:

    class RateLimitMiddleware(BaseHTTPMiddleware):
        """Rate limiting middleware using token bucket algorithm."""

        def __init__(self, app, redis_url: str | None = None):
            """Initialize rate limiter.

            Args:
                app: FastAPI application.
                redis_url: Redis connection URL.
            """
            super().__init__(app)
            self.redis_url = redis_url or settings.redis_url
            self.redis_client: redis.Redis | None = None
            self.rate_limit = settings.rate_limit_per_minute
            self.burst_limit = settings.rate_limit_burst

        async def dispatch(
            self, request: Request, call_next: Callable
        ) -> Response:
            """Process request with rate limiting.

            Args:
                request: HTTP request.
                call_next: Next middleware/handler.

            Returns:
                HTTP response.

            Raises:
                HTTPException: If rate limit exceeded.
            """
            # Skip rate limiting for health checks
            if request.url.path in ["/health", "/ready", "/"]:
                return await call_next(request)

            # Get client identifier (user ID or IP)
            client_id = self._get_client_id(request)

            # Check rate limit
            try:
                allowed = await self._check_rate_limit(client_id)
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later.",
                        headers={"Retry-After": "60"},
                    )
            except Exception as e:
                # If Redis is down, allow request (fail open)
                print(f"Rate limit check failed: {e}")

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(
                await self._get_remaining(client_id)
            )

            return response

        def _get_client_id(self, request: Request) -> str:
            """Get client identifier for rate limiting.

            Args:
                request: HTTP request.

            Returns:
                Client identifier (user ID or IP).
            """
            # Try to get user ID from auth header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Extract user ID from token (simplified)
                # In production, decode JWT to get user ID
                token = auth_header[7:]
                return f"user:{token[:16]}"

            # Fall back to IP address
            client_ip = request.client.host if request.client else "unknown"
            return f"ip:{client_ip}"

        async def _check_rate_limit(self, client_id: str) -> bool:
            """Check if client has exceeded rate limit.

            Args:
                client_id: Client identifier.

            Returns:
                True if request is allowed, False if rate limit exceeded.
            """
            if not self.redis_client:
                self.redis_client = redis.from_url(self.redis_url)

            key = f"rate_limit:{client_id}"
            current_time = int(time.time())
            window_start = current_time - 60  # 1 minute window

            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            request_count = await self.redis_client.zcard(key)

            if request_count >= self.rate_limit:
                return False

            # Add current request
            await self.redis_client.zadd(key, {str(current_time): current_time})
            await self.redis_client.expire(key, 60)

            return True

        async def _get_remaining(self, client_id: str) -> int:
            """Get remaining requests for client.

            Args:
                client_id: Client identifier.

            Returns:
                Number of remaining requests.
            """
            if not self.redis_client:
                return self.rate_limit

            key = f"rate_limit:{client_id}"
            current_time = int(time.time())
            window_start = current_time - 60

            await self.redis_client.zremrangebyscore(key, 0, window_start)
            request_count = await self.redis_client.zcard(key)

            return max(0, self.rate_limit - request_count)

else:

    class RateLimitMiddleware:
        """Placeholder when dependencies not available."""

        def __init__(self, app, redis_url: str | None = None):
            """Initialize placeholder."""
            pass
