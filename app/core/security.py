"""
Fasiri - API key security helpers.

Keys are structured as:  fsri_<random_hex_40>
We store only a SHA-256 hash of the key in the database (or in-memory store).

IMPORTANT: The current store is in-memory. On Render free tier, the server
sleeps and restarts, which wipes all in-memory keys. To fix this permanently,
set FASIRI_DEMO_KEY in your environment - this key is always valid regardless
of restarts.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Optional

from app.core.config import settings


PREFIX = "fsri_"

# ── Key helpers ────────────────────────────────────────────────────────────────

def generate_api_key() -> str:
    return PREFIX + os.urandom(20).hex()


def hash_api_key(plain_key: str) -> str:
    return hashlib.sha256(plain_key.encode()).hexdigest()


def verify_api_key(plain_key: str, stored_hash: str) -> bool:
    expected = hash_api_key(plain_key)
    return hmac.compare_digest(expected, stored_hash)


def is_valid_key_format(key: str) -> bool:
    return key.startswith(PREFIX) and len(key) == len(PREFIX) + 40


# ── In-memory key store ────────────────────────────────────────────────────────
# { hashed_key: { name, created_at, expires_at (None = never), requests_total } }

_KEY_STORE: dict = {}


def create_key(name: str, never_expire: bool = False) -> str:
    """Issue a new API key. Pass never_expire=True for permanent keys."""
    plain = generate_api_key()
    h = hash_api_key(plain)
    _KEY_STORE[h] = {
        "name": name,
        "created_at": time.time(),
        # None means the key never expires
        "expires_at": None if never_expire else time.time() + settings.api_key_ttl_seconds,
        "requests_total": 0,
    }
    return plain


def register_permanent_key(plain_key: str, name: str) -> None:
    """
    Register an existing key as permanent in the store.
    Used to load keys from environment variables so they survive restarts.
    """
    if not is_valid_key_format(plain_key):
        return
    h = hash_api_key(plain_key)
    if h not in _KEY_STORE:
        _KEY_STORE[h] = {
            "name": name,
            "created_at": time.time(),
            "expires_at": None,   # permanent
            "requests_total": 0,
        }


def lookup_key(plain_key: str) -> Optional[dict]:
    """Return key metadata if valid. None if missing, wrong format, or expired."""
    if not is_valid_key_format(plain_key):
        return None

    # Check environment-pinned demo key first (survives restarts)
    demo_key = settings.fasiri_demo_key
    if demo_key and plain_key == demo_key:
        return {
            "name": "demo",
            "created_at": 0.0,
            "expires_at": None,
            "requests_total": 0,
        }

    h = hash_api_key(plain_key)
    record = _KEY_STORE.get(h)
    if record is None:
        return None

    # None expires_at means permanent
    if record["expires_at"] is not None and time.time() > record["expires_at"]:
        return None

    return record


def increment_key_counter(plain_key: str) -> None:
    h = hash_api_key(plain_key)
    if h in _KEY_STORE:
        _KEY_STORE[h]["requests_total"] += 1


# ── Dev key ────────────────────────────────────────────────────────────────────
# Pre-seeded at startup so the server works out of the box.
# This key is lost on restart - use FASIRI_DEMO_KEY env var for a permanent key.

_DEV_KEY = create_key("dev-default", never_expire=True)


def get_dev_key() -> str:
    return _DEV_KEY
