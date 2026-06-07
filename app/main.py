"""
Fasiri - FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload

Interactive docs:
    https://api.fasiri-ai.com/docs     (Swagger UI)
    https://api.fasiri-ai.com/redoc    (ReDoc)
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.debug import router as debug_router
from app.api.languages import router as languages_router
from app.api.speech import router as speech_router
from app.api.translate import router as translate_router
from app.core.config import settings
from app.core import database as db
from app.core.security import get_dev_key, register_permanent_key

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
)
logger = logging.getLogger("fasiri")


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Fasiri API starting up")

    # ── 1. Database ───────────────────────────────────────────────────────────
    db.init_db(settings.database_url)

    if db.is_available():
        logger.info("Key store: ✓ Neon Postgres (keys persist across restarts)")
    else:
        logger.warning(
            "Key store: ✗ in-memory (keys lost on restart)\n"
            "  → Set DATABASE_URL in your environment to fix this."
        )

    # ── 2. Register permanent env-pinned keys ─────────────────────────────────
    # These are upserted into the DB on every startup so they're always valid.
    if settings.fasiri_demo_key:
        register_permanent_key(settings.fasiri_demo_key, "demo")
        logger.info("Demo key: ✓ registered (%s...)", settings.fasiri_demo_key[:12])
    else:
        logger.warning("FASIRI_DEMO_KEY not set — public demo won't work.")

    if settings.fasiri_admin_key:
        register_permanent_key(settings.fasiri_admin_key, "admin")
        logger.info("Admin key: ✓ registered (%s...)", settings.fasiri_admin_key[:12])
    else:
        logger.warning(
            "FASIRI_ADMIN_KEY not set — fasiri_platform cannot issue keys.\n"
            "  → Generate one with: python -c \"import os; print('fsri_'+os.urandom(20).hex())\"\n"
            "  → Add it to Render env vars as FASIRI_ADMIN_KEY\n"
            "  → Add the same value to Vercel env vars as FASIRI_ADMIN_KEY"
        )

    # ── 3. Dev key (local only) ───────────────────────────────────────────────
    dev_key = get_dev_key()
    logger.info("Docs:    %s/docs", settings.base_url)
    if settings.debug:
        logger.info("Dev key: %s", dev_key)

    # ── 4. Provider diagnostics ───────────────────────────────────────────────
    hf_key = settings.huggingface_api_key
    sb_key = settings.sunbird_api_key
    kh_key = settings.khaya_api_key

    if hf_key:
        logger.info("HuggingFace: ✓ key set (%s...)", hf_key[:8])
    else:
        logger.warning(
            "HuggingFace: ✗ HUGGINGFACE_API_KEY not set - running in stub mode.\n"
            "  → Get a free token at: https://huggingface.co/settings/tokens"
        )

    if sb_key:
        if sb_key.startswith("ey"):
            logger.info("Sunbird: ✓ JWT token set (%s...)", sb_key[:12])
        else:
            logger.error(
                "Sunbird: ✗ SUNBIRD_API_KEY does not look like a JWT (should start with 'ey...').\n"
                "  → Re-login: curl -X POST https://api.sunbird.ai/auth/token \\\n"
                "       -H 'Content-Type: application/x-www-form-urlencoded' \\\n"
                "       -d 'username=you@example.com&password=yourpassword'"
            )
    else:
        logger.warning(
            "Sunbird: ✗ SUNBIRD_API_KEY not set - running in stub mode.\n"
            "  → Register at https://api.sunbird.ai/auth/register"
        )

    if kh_key:
        logger.info("Khaya: ✓ key set (%s...)", kh_key[:8])
    else:
        logger.warning(
            "Khaya: ✗ KHAYA_API_KEY not set - West African languages unavailable.\n"
            "  → Register at https://translation.ghananlp.org/signup"
        )

    logger.info("=" * 60)
    yield
    logger.info("Fasiri API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fasiri API",
    description=(
        "**Fasiri** - Unified translation and speech API for African languages.\n\n"
        "A single endpoint to translate, transcribe, and synthesise speech across "
        "30+ African languages, powered by Sunbird AI (Ugandan languages), "
        "Khaya AI (West African languages), and Helsinki-NLP (global fallback).\n\n"
        "## Authentication\n"
        "All endpoints require an API key:\n"
        "```\nAuthorization: Bearer fsri_<your-key>\n```\n\n"
        "## Quick start\n"
        "1. Get a key at https://fasiri-ai.com\n"
        "2. Translate:   `POST /api/v1/translate`\n"
        "3. Batch:       `POST /api/v1/translate/batch`\n"
        "4. Speak:       `POST /api/v1/speech/tts`\n"
        "5. Transcribe:  `POST /api/v1/speech/stt`\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    t0 = time.monotonic()
    response = await call_next(request)
    ms = int((time.monotonic() - t0) * 1000)
    response.headers["X-Process-Time-Ms"] = str(ms)
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            }
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth_router,      prefix=PREFIX)
app.include_router(translate_router, prefix=PREFIX)
app.include_router(speech_router,    prefix=PREFIX)
app.include_router(languages_router, prefix=PREFIX)
app.include_router(debug_router,     prefix=PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "key_store": "postgres" if db.is_available() else "memory",
        "providers": {
            "sunbird":     "live" if settings.sunbird_api_key else "stub",
            "khaya":       "live" if settings.khaya_api_key else "stub",
            "huggingface": "live" if settings.huggingface_api_key else "stub",
        },
    }


@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return {
        "name": "Fasiri API",
        "version": "1.0.0",
        "docs": f"{settings.base_url}/docs",
        "health": f"{settings.base_url}/health",
    }
