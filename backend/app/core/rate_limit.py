# -*- coding: utf-8 -*-
"""Redis-backed sliding-window rate limiter for multi-worker deployments.

Uses Redis sorted sets keyed by timestamp for accurate sliding-window counting
across all workers.
"""

import time
import uuid as _uuid

from fastapi import HTTPException, Request

from app.core.database import redis_client


class RateLimiter:
    """Sliding-window rate limiter backed by Redis sorted sets."""

    def __init__(self, name: str, max_attempts: int = 5, window_seconds: int = 300):
        self.name = name
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    def _key(self, identifier: str) -> str:
        return f"ratelimit:{self.name}:{identifier}"

    async def check(self, identifier: str) -> None:
        """Raise 429 if rate limit exceeded."""
        key = self._key(identifier)
        now = time.time()
        cutoff = now - self.window_seconds

        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, "-inf", cutoff)
        pipe.zcard(key)
        results = await pipe.execute()
        count = results[1]

        if count >= self.max_attempts:
            raise HTTPException(
                status_code=429,
                detail=f"登录尝试过于频繁，请 {self.window_seconds // 60} 分钟后再试",
            )

    async def record(self, identifier: str) -> None:
        """Record a failed attempt."""
        key = self._key(identifier)
        now = time.time()
        member = f"{now}:{_uuid.uuid4().hex[:8]}"

        pipe = redis_client.pipeline()
        pipe.zadd(key, {member: now})
        pipe.expire(key, self.window_seconds)
        await pipe.execute()


# Global instance: 5 failed attempts per IP within 5 minutes
login_limiter = RateLimiter("login", max_attempts=5, window_seconds=300)


def get_client_ip(request: Request) -> str:
    """Extract client IP, considering X-Forwarded-For behind proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
