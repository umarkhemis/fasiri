"""
Fasiri – FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload

Interactive docs:
    http://localhost:8000/docs     (Swagger UI)
    http://localhost:8000/redoc    (ReDoc)
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
from app.core.security import get_dev_key

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)
logger = logging.getLogger("fasiri")


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    dev_key = get_dev_key()
    logger.info("=" * 60)
    logger.info("Fasiri API starting up")
    logger.info("Docs:    %s/docs", settings.base_url)
    logger.info("Dev key: %s", dev_key)

    # ── Provider diagnostics ──────────────────────────────────────────────────
    hf_key  = settings.huggingface_api_key
    sb_key  = settings.sunbird_api_key
    kh_key  = settings.khaya_api_key

    if hf_key:
        logger.info("HuggingFace: ✓ key set (%s...)", hf_key[:8])
    else:
        logger.warning(
            "HuggingFace: ✗ HUGGINGFACE_API_KEY not set – running in stub mode.\n"
            "  → Get a free token at: https://huggingface.co/settings/tokens"
        )

    if sb_key:
        if sb_key.startswith("ey"):
            logger.info("Sunbird: ✓ JWT token set (%s...)", sb_key[:12])
        else:
            logger.error(
                "Sunbird: ✗ SUNBIRD_API_KEY is set but does NOT look like a JWT "
                "(should start with 'ey...').\n"
                "  → This will cause HTTP 405 errors.\n"
                "  → Run: curl -X POST https://api.sunbird.ai/auth/token \\\n"
                "           -H 'Content-Type: application/x-www-form-urlencoded' \\\n"
                "           -d 'username=you@example.com&password=yourpassword'\n"
                "  → Copy the access_token into SUNBIRD_API_KEY in your .env"
            )
    else:
        logger.warning(
            "Sunbird: ✗ SUNBIRD_API_KEY not set – running in stub mode.\n"
            "  → Register at https://api.sunbird.ai/auth/register"
        )

    if kh_key:
        logger.info("Khaya: ✓ key set (%s...)", kh_key[:8])
    else:
        logger.warning(
            "Khaya: ✗ KHAYA_API_KEY not set – West African language translation unavailable.\n"
            "  → Register at https://translation.ghananlp.org/signup"
        )

    logger.info("=" * 60)
    yield
    logger.info("Fasiri API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fasiri API",
    description=(
        "**Fasiri** – Unified translation and speech API for African languages.\n\n"
        "A single endpoint to translate, transcribe, and synthesise speech across "
        "30+ African languages, powered by Sunbird AI (Ugandan languages), "
        "Khaya AI (West African languages), and Helsinki-NLP (global fallback).\n\n"
        "## Authentication\n"
        "All endpoints (except `POST /api/v1/auth/keys`) require an API key:\n"
        "```\nAuthorization: Bearer fsri_<your-key>\n```\n\n"
        "## Quick start\n"
        "1. Issue a key: `POST /api/v1/auth/keys`\n"
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
    allow_origins=["*"],   # tighten in production
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
