"""
Fasiri - API key security helpers.

Keys are structured as:  fsri_<random_hex_40>
We store only a SHA-256 hash of the key in the database (or in-memory store).
The plain-text key is returned once on creation and never again.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Optional

from app.core.config import settings


PREFIX = "fsri_"


def generate_api_key() -> str:
    """Generate a new plain-text Fasiri API key."""
    return PREFIX + os.urandom(20).hex()


def hash_api_key(plain_key: str) -> str:
    """One-way SHA-256 hash of a key for safe storage."""
    return hashlib.sha256(plain_key.encode()).hexdigest()


def verify_api_key(plain_key: str, stored_hash: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    expected = hash_api_key(plain_key)
    return hmac.compare_digest(expected, stored_hash)


def is_valid_key_format(key: str) -> bool:
    return key.startswith(PREFIX) and len(key) == len(PREFIX) + 40


# ── In-memory key store (replace with DB/Redis in production) ────────────────
# Structure: { hashed_key: { "name": str, "created_at": float, "expires_at": float } }

_KEY_STORE: dict = {}


def create_key(name: str) -> str:
    """Issue a new API key, store its hash, return the plain-text key once."""
    plain = generate_api_key()
    h = hash_api_key(plain)
    _KEY_STORE[h] = {
        "name": name,
        "created_at": time.time(),
        "expires_at": time.time() + settings.api_key_ttl_seconds,
        "requests_total": 0,
    }
    return plain


def lookup_key(plain_key: str) -> Optional[dict]:
    """Return the stored metadata if the key is valid and not expired, else None."""
    if not is_valid_key_format(plain_key):
        return None
    h = hash_api_key(plain_key)
    record = _KEY_STORE.get(h)
    if record is None:
        return None
    if time.time() > record["expires_at"]:
        return None   # expired
    return record


def increment_key_counter(plain_key: str) -> None:
    h = hash_api_key(plain_key)
    if h in _KEY_STORE:
        _KEY_STORE[h]["requests_total"] += 1


# Pre-seed a dev key so the server is usable out of the box.
# The key is printed at startup (see main.py).
_DEV_KEY = create_key("dev-default")

def get_dev_key() -> str:
    return _DEV_KEY
