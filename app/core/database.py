"""
Fasiri - PostgreSQL key store.

Uses psycopg2 (sync) to keep things simple and compatible with FastAPI's
thread-pool for sync dependencies. No ORM — just plain SQL.

Table created automatically on first startup if it doesn't exist.

Falls back to the original in-memory store if DATABASE_URL is not set,
so local dev without Postgres still works.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

_pool = None          # psycopg2 SimpleConnectionPool
_db_available = False


def init_db(database_url: str) -> None:
    """
    Call once at startup. Creates the connection pool and ensures the
    api_keys table exists.
    """
    global _pool, _db_available

    if not database_url:
        logger.warning(
            "DATABASE_URL not set — falling back to in-memory key store.\n"
            "  Keys will be lost on every server restart.\n"
            "  Add a Postgres database and set DATABASE_URL to fix this."
        )
        return

    try:
        from psycopg2 import pool as pg_pool

        _pool = pg_pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url,
            connect_timeout=5,
        )

        # Create table if it doesn't exist
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS api_keys (
                        key_hash        TEXT PRIMARY KEY,
                        name            TEXT        NOT NULL,
                        created_at      DOUBLE PRECISION NOT NULL,
                        expires_at      DOUBLE PRECISION,          -- NULL = never
                        requests_total  INTEGER     NOT NULL DEFAULT 0
                    );
                """)
            conn.commit()

        _db_available = True
        logger.info("Database: ✓ connected and api_keys table ready")

    except ImportError:
        logger.error(
            "psycopg2 not installed. Run: pip install psycopg2-binary\n"
            "Falling back to in-memory store."
        )
    except Exception as exc:
        logger.error(
            "Database connection failed: %s\nFalling back to in-memory store.", exc
        )


def is_available() -> bool:
    return _db_available


@contextmanager
def _get_conn():
    """Borrow a connection from the pool, return it when done."""
    conn = _pool.getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


# ── DB key operations ─────────────────────────────────────────────────────────

def db_create_key(key_hash: str, name: str, expires_at: Optional[float]) -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (key_hash, name, created_at, expires_at, requests_total)
                VALUES (%s, %s, %s, %s, 0)
                ON CONFLICT (key_hash) DO NOTHING;
                """,
                (key_hash, name, time.time(), expires_at),
            )
        conn.commit()


def db_lookup_key(key_hash: str) -> Optional[dict]:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name, created_at, expires_at, requests_total
                FROM api_keys
                WHERE key_hash = %s;
                """,
                (key_hash,),
            )
            row = cur.fetchone()

    if row is None:
        return None

    name, created_at, expires_at, requests_total = row

    # Check expiry
    if expires_at is not None and time.time() > expires_at:
        return None

    return {
        "name": name,
        "created_at": created_at,
        "expires_at": expires_at,
        "requests_total": requests_total,
    }


def db_increment_counter(key_hash: str) -> None:
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE api_keys SET requests_total = requests_total + 1 WHERE key_hash = %s;",
                    (key_hash,),
                )
            conn.commit()
    except Exception as exc:
        # Non-critical — don't let a counter failure break a request
        logger.warning("Failed to increment request counter: %s", exc)


def db_register_permanent_key(key_hash: str, name: str) -> None:
    """Upsert a permanent key (expires_at = NULL). Used for demo/admin keys."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (key_hash, name, created_at, expires_at, requests_total)
                VALUES (%s, %s, %s, NULL, 0)
                ON CONFLICT (key_hash) DO UPDATE
                    SET name = EXCLUDED.name,
                        expires_at = NULL;
                """,
                (key_hash, name, time.time()),
            )
        conn.commit()