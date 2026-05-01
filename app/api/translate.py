"""
Fasiri – Translation endpoints.

POST /api/v1/translate        – single translation
POST /api/v1/translate/batch  – batch translation (up to 50 items)
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import require_api_key
from app.middleware.ratelimit import check_rate_limit
from app.schemas.translate import (
    BatchItemResult,
    BatchTranslateRequest,
    BatchTranslateResponse,
    TranslateRequest,
    TranslateResponse,
)
from app.services.routing import route_translation
from app.utils.lang_detect import detect_language

router = APIRouter(prefix="/translate", tags=["Translation"])
logger = logging.getLogger(__name__)


# ── Single translation ────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=TranslateResponse,
    summary="Translate text",
    description=(
        "Translate text between any supported African language pair. "
        "Source language is auto-detected if not supplied."
    ),
)
async def translate(
    body: TranslateRequest,
    key_record: dict = Depends(require_api_key),
) -> TranslateResponse:
    check_rate_limit(key_record, "translate")

    # Resolve source language
    source_lang = body.source_lang or detect_language(body.text)

    if source_lang == body.target_lang:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SAME_LANGUAGE",
                "message": (
                    f"Source and target language are both '{source_lang}'. "
                    "No translation needed."
                ),
            },
        )

    try:
        result = await route_translation(
            text=body.text,
            source_lang=source_lang,
            target_lang=body.target_lang,
            preferred_provider=body.provider,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUPPORTED_LANGUAGE_PAIR", "message": str(exc)},
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "PROVIDER_ERROR", "message": str(exc)},
        )

    return TranslateResponse(
        translated_text=result.translated_text,
        detected_source_lang=source_lang,
        target_lang=body.target_lang,
        model_used=result.model_used,
        provider=result.provider,
        quality_score=result.quality_score,
        latency_ms=result.latency_ms,
        characters_translated=len(body.text),
    )


# ── Batch translation ─────────────────────────────────────────────────────────

@router.post(
    "/batch",
    response_model=BatchTranslateResponse,
    summary="Batch translate",
    description=(
        "Translate up to 50 texts in a single request. "
        "Each item can have a different source/target language pair. "
        "Items are processed concurrently."
    ),
)
async def batch_translate(
    body: BatchTranslateRequest,
    key_record: dict = Depends(require_api_key),
) -> BatchTranslateResponse:
    check_rate_limit(key_record, "batch")

    t_start = time.monotonic()

    async def _translate_one(item) -> BatchItemResult:
        src = item.source_lang or detect_language(item.text)
        try:
            result = await route_translation(
                text=item.text,
                source_lang=src,
                target_lang=item.target_lang,
                preferred_provider=body.provider,
            )
            return BatchItemResult(
                id=item.id,
                translated_text=result.translated_text,
                detected_source_lang=src,
                target_lang=item.target_lang,
                model_used=result.model_used,
                provider=result.provider,
                quality_score=result.quality_score,
                error=None,
            )
        except Exception as exc:
            logger.error("Batch item %s failed: %s", item.id, exc)
            return BatchItemResult(
                id=item.id,
                target_lang=item.target_lang,
                error=str(exc),
            )

    results: List[BatchItemResult] = await asyncio.gather(
        *[_translate_one(item) for item in body.items]
    )

    succeeded = sum(1 for r in results if r.error is None)
    failed = len(results) - succeeded

    return BatchTranslateResponse(
        results=results,
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        total_latency_ms=int((time.monotonic() - t_start) * 1000),
    )
