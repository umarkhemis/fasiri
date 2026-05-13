"""
Fasiri - API key management endpoints.

POST /api/v1/auth/keys          - issue a new API key
GET  /api/v1/auth/keys/me       - inspect the current key's metadata
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.core.security import create_key
from app.middleware.auth import require_api_key
from app.schemas.translate import CreateKeyRequest, CreateKeyResponse, KeyInfoResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])



def _ts(epoch):
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


@router.post(
    "/keys",
    response_model=CreateKeyResponse,
    summary="Issue a new API key",
    description=(
        "Creates a new Fasiri API key. "
        "**The plain-text key is returned once and never stored. "
        "Save it immediately.**"
    ),
    status_code=201,
)
async def create_api_key(body: CreateKeyRequest) -> CreateKeyResponse:

    plain_key = create_key(body.name)

    # Compute expiry for the response
    from app.core.security import _KEY_STORE, hash_api_key
    record = _KEY_STORE[hash_api_key(plain_key)]

    return CreateKeyResponse(
        api_key=plain_key,
        name=body.name,
        expires_at=_ts(record["expires_at"]),
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
        expires_at=_ts(key_record["expires_at"]),
        requests_total=key_record["requests_total"],
    )
