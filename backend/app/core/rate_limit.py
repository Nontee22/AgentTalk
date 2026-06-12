# -*- coding: utf-8 -*-
"""Simple in-memory rate limiter for login endpoint."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    """Sliding-window rate limiter. Not shared across workers — sufficient for single-process dev."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        """Raise 429 if rate limit exceeded."""
        now = time.monotonic()
        attempts = self._attempts[key]

        # Prune old entries
        cutoff = now - self.window_seconds
        self._attempts[key] = [t for t in attempts if t > cutoff]
        attempts = self._attempts[key]

        if len(attempts) >= self.max_attempts:
            raise HTTPException(
                status_code=429,
                detail=f"登录尝试过于频繁，请 {self.window_seconds // 60} 分钟后再试",
            )

    def record(self, key: str) -> None:
        """Record a failed attempt."""
        self._attempts[key].append(time.monotonic())


# Global instance: 5 failed attempts per IP within 5 minutes
login_limiter = RateLimiter(max_attempts=5, window_seconds=300)


def get_client_ip(request: Request) -> str:
    """Extract client IP, considering X-Forwarded-For behind proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
