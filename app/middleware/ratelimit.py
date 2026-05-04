"""
Fasiri – Production Rate Limiter

Uses Redis sliding-window when REDIS_URL is set (production).
Falls back to in-memory sliding-window for local dev.

Redis key: rl:{key_name}:{endpoint_group}
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Dict
import logging

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None
_redis_failed = False


def _get_redis():
    global _redis_client, _redis_failed
    if _redis_failed:
        return None
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        import redis
        client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        _redis_client = client
        logger.info("Rate limiter: connected to Redis at %s", settings.redis_url)
        return _redis_client
    except Exception as exc:
        _redis_failed = True
        logger.warning("Redis unavailable (%s) - using in-memory rate limiting", exc)
        return None


_WINDOWS: Dict[str, deque] = defaultdict(deque)


def _memory_check(bucket: str, limit: int, window: int = 60) -> None:
    now = time.monotonic()
    q = _WINDOWS[bucket]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        retry = int(window - (now - q[0])) + 1
        _raise_429(limit, retry)
    q.append(now)


def _redis_check(r, bucket: str, limit: int, window: int = 60) -> None:
    now = time.time()
    key = f"rl:{bucket}"
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window + 1)
    results = pipe.execute()
    count = results[2]
    if count > limit:
        oldest = r.zrange(key, 0, 0, withscores=True)
        retry = int(window - (now - oldest[0][1])) + 1 if oldest else window
        _raise_429(limit, retry)


def _raise_429(limit: int, retry: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(retry)},
        detail={
            "code": "RATE_LIMIT_EXCEEDED",
            "message": (
                f"Rate limit of {limit} requests/minute exceeded. "
                f"Retry after {retry} seconds."
            ),
            "retry_after_seconds": retry,
        },
    )


def check_rate_limit(key_record: dict, endpoint_group: str = "default") -> None:
    name = key_record.get("name", "unknown")
    bucket = f"{name}:{endpoint_group}"
    limits = {
        "translate": settings.rate_limit_rpm,
        "batch":     settings.rate_limit_batch_rpm,
        "speech":    settings.rate_limit_rpm,
        "default":   settings.rate_limit_rpm,
    }
    limit = limits.get(endpoint_group, settings.rate_limit_rpm)
    r = _get_redis()
    if r:
        try:
            _redis_check(r, bucket, limit)
            return
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Redis rate-limit check failed: %s - falling back", exc)
    _memory_check(bucket, limit)
