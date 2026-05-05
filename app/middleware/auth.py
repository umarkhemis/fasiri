"""
Fasiri - Authentication dependency.

Every protected endpoint injects `require_api_key` as a FastAPI dependency.
The client sends the key in the Authorization header:

    Authorization: Bearer fsri_<...>
"""
from __future__ import annotations

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import lookup_key, increment_key_counter

_bearer = HTTPBearer(auto_error=False)


def require_api_key(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """
    FastAPI dependency that validates a Fasiri API key.
    Returns the key metadata dict on success.
    Raises HTTP 401 on missing / invalid / expired key.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_API_KEY",
                "message": (
                    "Authentication required. Pass your Fasiri API key in the "
                    "Authorization header: Bearer fsri_<your-key>"
                ),
            },
        )

    plain_key = credentials.credentials
    record = lookup_key(plain_key)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_API_KEY",
                "message": "The provided API key is invalid or has expired.",
            },
        )

    increment_key_counter(plain_key)
    return record
