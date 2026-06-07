"""
Fasiri - API key security helpers.

Keys are structured as:  fsri_<random_hex_40>
We store only a SHA-256 hash of the key (never the plain text).

Storage priority:
  1. PostgreSQL (DATABASE_URL set)  — keys survive restarts  ✓
  2. In-memory dict (fallback)      — keys lost on restart   ✗

Set DATABASE_URL in your environment to enable persistent storage.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Optional

from app.core.config import settings
from app.core import database as db


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


# ── In-memory fallback (used when DATABASE_URL is not set) ────────────────────
_KEY_STORE: dict = {}


def create_key(name: str, never_expire: bool = False) -> str:
    """Issue a new API key and persist it."""
    plain = generate_api_key()
    h = hash_api_key(plain)
    expires_at = None if never_expire else time.time() + settings.api_key_ttl_seconds

    if db.is_available():
        db.db_create_key(h, name, expires_at)
    else:
        _KEY_STORE[h] = {
            "name": name,
            "created_at": time.time(),
            "expires_at": expires_at,
            "requests_total": 0,
        }

    return plain


def register_permanent_key(plain_key: str, name: str) -> None:
    """
    Register an existing key as permanent.
    Used to load FASIRI_DEMO_KEY / FASIRI_ADMIN_KEY from env on startup
    so they survive restarts in both DB and memory modes.
    """
    if not is_valid_key_format(plain_key):
        return
    h = hash_api_key(plain_key)

    if db.is_available():
        db.db_register_permanent_key(h, name)
    else:
        if h not in _KEY_STORE:
            _KEY_STORE[h] = {
                "name": name,
                "created_at": time.time(),
                "expires_at": None,
                "requests_total": 0,
            }


def lookup_key(plain_key: str) -> Optional[dict]:
    """Return key metadata if valid. None if missing, wrong format, or expired."""
    if not is_valid_key_format(plain_key):
        return None

    # Always check env-pinned special keys first (works in both modes)
    for env_key, label in [
        (settings.fasiri_demo_key,  "demo"),
        (settings.fasiri_admin_key, "admin"),
    ]:
        if env_key and plain_key == env_key:
            return {
                "name": label,
                "created_at": 0.0,
                "expires_at": None,
                "requests_total": 0,
            }

    h = hash_api_key(plain_key)

    if db.is_available():
        return db.db_lookup_key(h)

    # In-memory fallback
    record = _KEY_STORE.get(h)
    if record is None:
        return None
    if record["expires_at"] is not None and time.time() > record["expires_at"]:
        return None
    return record


def increment_key_counter(plain_key: str) -> None:
    h = hash_api_key(plain_key)

    if db.is_available():
        db.db_increment_counter(h)
    else:
        if h in _KEY_STORE:
            _KEY_STORE[h]["requests_total"] += 1


# ── Dev key (local development only) ──────────────────────────────────────────
# Pre-seeded so the server works out of the box without any env vars.
# In production use FASIRI_DEMO_KEY and FASIRI_ADMIN_KEY env vars instead.

_DEV_KEY = create_key("dev-default", never_expire=True)


def get_dev_key() -> str:
    return _DEV_KEY
