"""A small in-memory rate limiter that protects the free AI quota from abuse.

It counts requests per client IP in a sliding window. State lives in process
memory, which is enough for a single free-tier instance; it resets on restart.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, now: float | None = None) -> int:
        """Record a request; return seconds to wait if the limit is exceeded, else 0."""

        now = time.monotonic() if now is None else now
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            oldest = hits[0] if hits else now
            return int(self.window_seconds - (now - oldest)) + 1
        hits.append(now)
        if len(self._hits) > 10_000:  # Keep memory bounded on a tiny instance.
            for stale in [k for k, v in self._hits.items() if not v]:
                del self._hits[stale]
        return 0


def client_ip(request: Request) -> str:
    # Render sits behind a proxy; the original client is the first X-Forwarded-For entry.
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


analysis_limiter = RateLimiter(
    max_requests=int(os.environ.get("CAREERLENS_RATE_LIMIT_PER_HOUR", "20")),
    window_seconds=3600,
)


def enforce_analysis_limit(request: Request) -> None:
    wait = analysis_limiter.check(client_ip(request))
    if wait:
        minutes = max(1, round(wait / 60))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"You've reached the hourly limit for free analyses. Please try again in about {minutes} minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(wait)},
        )
