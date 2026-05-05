"""
Fasiri - Provider diagnostics endpoint.

GET /api/v1/debug/providers  - live connectivity check for all providers
GET /api/v1/debug/env        - show which env vars are set (values masked)

Only available when DEBUG=true in .env
"""
from __future__ import annotations

import time

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings

router = APIRouter(prefix="/debug", tags=["Debug"])


def _require_debug():
    if not settings.debug:
        raise HTTPException(
            status_code=404,
            detail="Debug endpoints are disabled. Set DEBUG=true in .env to enable."
        )


@router.get("/env", summary="Show environment config (masked)")
async def show_env():
    _require_debug()

    def mask(val: str) -> str:
        if not val:
            return "NOT SET"
        if len(val) <= 8:
            return "***"
        return val[:8] + "..." + val[-4:]

    return {
        "huggingface_api_key": mask(settings.huggingface_api_key),
        "huggingface_base_url": settings.huggingface_base_url,
        "sunbird_api_key": mask(settings.sunbird_api_key),
        "sunbird_base_url": settings.sunbird_base_url,
        "sunbird_key_looks_like_jwt": settings.sunbird_api_key.startswith("ey"),
        "default_model_id": settings.default_model_id,
        "rate_limit_rpm": settings.rate_limit_rpm,
        "debug": settings.debug,
    }


@router.get("/providers", summary="Live provider connectivity check")
async def check_providers():
    _require_debug()

    results = {}

    # ── HuggingFace ───────────────────────────────────────────────────────────
    hf_model = "Helsinki-NLP/opus-mt-en-ha"
    hf_url = f"{settings.huggingface_base_url}/{hf_model}"
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                hf_url,
                json={"inputs": "Hello"},
                headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
            )
        latency_ms = int((time.monotonic() - t0) * 1000)
        if resp.status_code == 200:
            data = resp.json()
            translated = data[0].get("translation_text", "") if isinstance(data, list) else str(data)
            results["huggingface"] = {
                "status": "ok",
                "http_status": 200,
                "latency_ms": latency_ms,
                "model_tested": hf_model,
                "url": hf_url,
                "sample_translation": translated,
            }
        elif resp.status_code == 503:
            results["huggingface"] = {
                "status": "loading",
                "http_status": 503,
                "latency_ms": latency_ms,
                "model_tested": hf_model,
                "message": "Model is cold-starting - retry in 20s",
                "hf_body": resp.json() if resp.content else {},
            }
        else:
            results["huggingface"] = {
                "status": "error",
                "http_status": resp.status_code,
                "latency_ms": latency_ms,
                "model_tested": hf_model,
                "url": hf_url,
                "body": resp.text[:300],
                "fix": (
                    "404 → wrong URL. Check HUGGINGFACE_BASE_URL in .env - "
                    "must be https://router.huggingface.co/hf-inference/models\n"
                    "401 → bad token. Check HUGGINGFACE_API_KEY in .env"
                ),
            }
    except Exception as exc:
        results["huggingface"] = {
            "status": "error",
            "latency_ms": int((time.monotonic() - t0) * 1000),
            "error": str(exc),
        }

    # ── Sunbird ───────────────────────────────────────────────────────────────
    sb_url = f"{settings.sunbird_base_url}/tasks/nllb_translate"
    sb_key = settings.sunbird_api_key
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                sb_url,
                json={"source_language": "eng", "target_language": "lug", "text": "Hello"},
                headers={
                    "Authorization": f"Bearer {sb_key}",
                    "Content-Type": "application/json",
                },
            )
        latency_ms = int((time.monotonic() - t0) * 1000)
        if resp.status_code == 200:
            data = resp.json()
            output = data.get("output", {})
            results["sunbird"] = {
                "status": "ok",
                "http_status": 200,
                "latency_ms": latency_ms,
                "url": sb_url,
                "sample_translation": output.get("translated_text", ""),
            }
        elif resp.status_code == 405:
            results["sunbird"] = {
                "status": "auth_error",
                "http_status": 405,
                "latency_ms": latency_ms,
                "url": sb_url,
                "diagnosis": (
                    "405 on Sunbird = your JWT token is missing, expired, or malformed. "
                    "Sunbird's middleware returns 405 (not 401) when auth fails."
                ),
                "key_set": bool(sb_key),
                "key_looks_like_jwt": sb_key.startswith("ey") if sb_key else False,
                "fix": (
                    "Run: curl -X POST https://api.sunbird.ai/auth/token "
                    "-H 'Content-Type: application/x-www-form-urlencoded' "
                    "-d 'username=you@example.com&password=yourpassword' "
                    "then copy access_token into SUNBIRD_API_KEY in your .env"
                ),
            }
        else:
            results["sunbird"] = {
                "status": "error",
                "http_status": resp.status_code,
                "latency_ms": latency_ms,
                "body": resp.text[:300],
            }
    except Exception as exc:
        results["sunbird"] = {
            "status": "error",
            "latency_ms": int((time.monotonic() - t0) * 1000),
            "error": str(exc),
        }

    overall = "ok" if all(r["status"] == "ok" for r in results.values()) else "degraded"
    return {"overall": overall, "providers": results}
