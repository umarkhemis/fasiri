"""
Fasiri - API key management endpoints.

POST /api/v1/auth/keys          - issue a new API key  (admin only)
GET  /api/v1/auth/keys/me       - inspect the current key's metadata
"""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.security import create_key, lookup_key
from app.middleware.auth import require_api_key
from app.schemas.translate import CreateKeyRequest, CreateKeyResponse, KeyInfoResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _ts(epoch):
    if epoch is None:
        return "never"
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


# ── IP rate limiting for key creation (simple in-memory) ─────────────────────

_ip_key_creation: dict[str, list[float]] = defaultdict(list)
_KEY_CREATION_LIMIT = 5      # max 5 keys per IP
_KEY_CREATION_WINDOW = 3600  # per hour


def _check_ip_key_limit(ip: str) -> None:
    now = time.time()
    window_start = now - _KEY_CREATION_WINDOW
    # Keep only timestamps within the window
    _ip_key_creation[ip] = [t for t in _ip_key_creation[ip] if t > window_start]
    if len(_ip_key_creation[ip]) >= _KEY_CREATION_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "KEY_CREATION_RATE_LIMIT",
                "message": (
                    f"Too many API keys created from this IP. "
                    f"Limit is {_KEY_CREATION_LIMIT} keys per hour."
                ),
            },
        )
    _ip_key_creation[ip].append(now)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/keys",
    response_model=CreateKeyResponse,
    summary="Issue a new API key",
    description=(
        "Creates a new Fasiri API key. "
        "Requires an admin API key in the Authorization header. "
        "**The plain-text key is returned once and never stored. Save it immediately.**"
    ),
    status_code=201,
)
async def create_api_key(
    body: CreateKeyRequest,
    request: Request,
    key_record: dict = Depends(require_api_key),   # ← now protected
) -> CreateKeyResponse:

    # Only admin key can issue new keys
    if key_record["name"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Only admin keys can create new API keys.",
            },
        )

    # IP-level rate limit (secondary guard)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    _check_ip_key_limit(client_ip)

    plain_key = create_key(body.name)
    record = lookup_key(plain_key)

    return CreateKeyResponse(
        api_key=plain_key,
        name=body.name,
        expires_at=_ts(record["expires_at"] if record else None),
    )


@router.get(
    "/keys/me",
    response_model=KeyInfoResponse,
    summary="Inspect current API key",
    description="Returns metadata for the authenticated API key.",
)
async def get_key_info(key_record: dict = Depends(require_api_key)) -> KeyInfoResponse:
    return KeyInfoResponse(
        name=key_record["name"],
        created_at=_ts(key_record["created_at"]),
        expires_at=_ts(key_record.get("expires_at")),
        requests_total=key_record["requests_total"],
    )