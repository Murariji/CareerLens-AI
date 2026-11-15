"""Anonymous usage stats: page visits and analyses. Never stores resume text or personal data.

What is recorded per event:
- visit:    date/time and a one-way hash of (day, IP, browser) so unique visitors can be counted
            per day without storing the IP. The hash changes every day and can't be reversed.
- analysis: date/time, a broad role category (e.g. "ML / AI", never the typed role),
            the match score, and whether AI was used.

Storage is pluggable:
- MemoryStatsStore (default): counts since the server last started. No setup.
- SupabaseStatsStore: permanent counts in a free Supabase Postgres database. Enabled when
  CAREERLENS_SUPABASE_URL, CAREERLENS_SUPABASE_KEY and CAREERLENS_STATS_TOKEN are set.
  The SQL to create it is in docs/supabase/careerlens_stats.sql.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)

ROLE_CATEGORIES: list[tuple[str, str]] = [
    ("ML / AI", r"\b(?:ml|ai|machine learning|deep learning|data scien\w*|nlp|computer vision|llm|genai|gen ai)\b"),
    ("Data & analytics", r"\b(?:data|analyst|analytics|bi|business intelligence)\b"),
    ("Cloud & DevOps", r"\b(?:devops|cloud|sre|site reliability|platform|infrastructure|mlops)\b"),
    ("Software engineering", r"\b(?:software|developer|engineer|sde|backend|frontend|front end|full[\s-]?stack|web|mobile|android|ios)\b"),
    ("Product & design", r"\b(?:product|designer|design|ux|ui)\b"),
]


def role_category(target_role: str) -> str:
    lowered = target_role.lower()
    for name, pattern in ROLE_CATEGORIES:
        if re.search(pattern, lowered):
            return name
    return "Other"


@dataclass(frozen=True)
class StatsEvent:
    kind: str  # "visit" | "analysis"
    visitor: str | None = None
    role_category: str | None = None
    score: int | None = None
    ai: bool | None = None
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StatsStore(Protocol):
    persistent: bool

    async def record(self, event: StatsEvent) -> None: ...

    async def summary(self) -> dict[str, Any]: ...


def _empty_summary(storage: str, persistent: bool) -> dict[str, Any]:
    return {
        "storage": storage,
        "persistent": persistent,
        "visits": 0,
        "unique_visitors": 0,
        "analyses": 0,
        "ai_analyses": 0,
        "average_score": None,
        "roles": {},
        "last_30_days": [],
    }


class MemoryStatsStore:
    """Counts since the last server start. Good for local development and as a fallback."""

    persistent = False

    def __init__(self) -> None:
        self.events: list[StatsEvent] = []

    async def record(self, event: StatsEvent) -> None:
        self.events.append(event)
        if len(self.events) > 50_000:
            del self.events[: len(self.events) - 50_000]

    async def summary(self) -> dict[str, Any]:
        result = _empty_summary("memory", False)
        visits = [e for e in self.events if e.kind == "visit"]
        analyses = [e for e in self.events if e.kind == "analysis"]
        scores = [e.score for e in analyses if e.score is not None]
        result.update(
            visits=len(visits),
            unique_visitors=len({(e.at.date(), e.visitor) for e in visits if e.visitor}),
            analyses=len(analyses),
            ai_analyses=sum(1 for e in analyses if e.ai),
            average_score=round(sum(scores) / len(scores)) if scores else None,
            roles=dict(Counter(e.role_category or "Other" for e in analyses).most_common()),
        )
        start = datetime.now(timezone.utc).date() - timedelta(days=29)
        days = [start + timedelta(days=i) for i in range(30)]
        result["last_30_days"] = [
            {
                "day": day.isoformat(),
                "visits": sum(1 for e in visits if e.at.date() == day),
                "analyses": sum(1 for e in analyses if e.at.date() == day),
            }
            for day in days
        ]
        return result


class SupabaseStatsStore:
    """Permanent stats through two Postgres functions exposed by Supabase's REST API.

    The functions check a secret token, so only this backend can write events.
    """

    persistent = True

    def __init__(self, url: str, key: str, token: str, http: httpx.AsyncClient | None = None) -> None:
        self.base = url.rstrip("/") + "/rest/v1/rpc"
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self.token = token
        self.http = http

    async def _post(self, function: str, payload: dict[str, Any]) -> Any:
        client = self.http or httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        try:
            response = await client.post(f"{self.base}/{function}", json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json() if response.content else None
        finally:
            if self.http is None:
                await client.aclose()

    async def record(self, event: StatsEvent) -> None:
        await self._post(
            "careerlens_record_event",
            {
                "p_token": self.token,
                "p_kind": event.kind,
                "p_visitor": event.visitor,
                "p_role_category": event.role_category,
                "p_score": event.score,
                "p_ai": event.ai,
            },
        )

    async def summary(self) -> dict[str, Any]:
        data = await self._post("careerlens_stats", {}) or {}
        result = _empty_summary("supabase", True)
        result.update({key: value for key, value in data.items() if key in result})
        return result


class StatsService:
    """Records events without ever failing a user request, and caches the summary briefly."""

    def __init__(self, store: StatsStore, salt: str, cache_seconds: int = 60) -> None:
        self.store = store
        self.salt = salt.encode()
        self.cache_seconds = cache_seconds
        self._cached: tuple[float, dict[str, Any]] | None = None

    def visitor_hash(self, ip: str, user_agent: str, day: date | None = None) -> str:
        message = f"{(day or datetime.now(timezone.utc).date()).isoformat()}|{ip}|{user_agent}".encode()
        return hmac.new(self.salt, message, hashlib.sha256).hexdigest()[:20]

    async def record(self, event: StatsEvent) -> None:
        try:
            await self.store.record(event)
            self._cached = None
        except Exception as error:  # Stats must never break the app.
            logger.warning("Could not record %s event: %r", event.kind, error)

    async def summary(self) -> dict[str, Any]:
        if self._cached and time.monotonic() - self._cached[0] < self.cache_seconds:
            return self._cached[1]
        try:
            result = await self.store.summary()
        except Exception as error:
            logger.warning("Could not load stats: %r", error)
            result = _empty_summary("unavailable", False)
        self._cached = (time.monotonic(), result)
        return result


def build_stats_service() -> StatsService:
    url = os.environ.get("CAREERLENS_SUPABASE_URL", "").strip()
    key = os.environ.get("CAREERLENS_SUPABASE_KEY", "").strip()
    token = os.environ.get("CAREERLENS_STATS_TOKEN", "").strip()
    if url and key and token:
        logger.info("Usage stats: Supabase (permanent).")
        return StatsService(SupabaseStatsStore(url, key, token), salt=token)
    logger.info("Usage stats: in memory (resets on restart). Set CAREERLENS_SUPABASE_* to keep them.")
    return StatsService(MemoryStatsStore(), salt=token or secrets.token_hex(16))


stats_service = build_stats_service()
