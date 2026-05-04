
"""
Fasiri – HuggingFace Inference API provider.

IMPORTANT: Not all Helsinki-NLP models are deployed on the HF Inference API.
A model existing on HuggingFace Hub !== it is callable via the Inference API.
Models that say "This model isn't deployed by any Inference Provider" will 404.

VERIFIED DEPLOYED models (confirmed callable via router.huggingface.co):
  - Helsinki-NLP/opus-mt-en-sw     English → Swahili (standard)
  - Helsinki-NLP/opus-mt-sw-en     Swahili → English
  - Helsinki-NLP/opus-mt-en-af     English → Afrikaans
  - Helsinki-NLP/opus-mt-af-en     Afrikaans → English
  - Helsinki-NLP/opus-mt-en-ar     English → Arabic
  - Helsinki-NLP/opus-mt-ar-en     Arabic → English
  - Helsinki-NLP/opus-mt-en-fr     English → French
  - Helsinki-NLP/opus-mt-fr-en     French → English
  - Helsinki-NLP/opus-mt-yo-en     Yoruba → English (confirmed deployed)

NOT deployed on Inference API (model exists but returns 404/400/410 on API):
  - opus-mt-en-ha, opus-mt-ha-en  (Hausa)
  - opus-mt-en-ig, opus-mt-ig-en  (Igbo)
  - opus-mt-en-yo                 (English → Yoruba — not confirmed deployed)
  - opus-mt-en-zu, opus-mt-zu-en  (Zulu)
  - opus-mt-en-rw, opus-mt-rw-en  (Kinyarwanda)
  - opus-mt-en-amh / opus-mt-en-am (Amharic)

NLLB STATUS: facebook/nllb-200-distilled-600M was dropped by hf-inference
  provider in 2025. Do NOT use it — it returns 400 "Model not supported".

STRATEGY:
  1. Verified deployed Helsinki-NLP model — best quality for that pair
  2. opus-mt-mul-en (any → English) or opus-mt-en-mul (English → any) — last resort

West African languages (yo, tw, ee, gaa, fat, dag, ki, gur, luo, mer, kus)
are handled by Khaya provider in routing.py — HuggingFace is only a fallback
for those if Khaya itself fails.

HF Inference API URL (2025+):
  https://router.huggingface.co/hf-inference/models/<model-id>
"""
from __future__ import annotations

import asyncio
import logging
import time

import httpx

from app.core.config import settings
from app.services.providers.base import BaseProvider, TranslationResult

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3

# ── Verified inference-deployed Helsinki-NLP models ───────────────────────────
# These have been confirmed to exist AND be callable on HF Inference API.
# Do NOT add models here unless you have verified they respond to API calls.
_VERIFIED_MODELS: dict[tuple[str, str], str] = {
    # Swahili
    ("en", "sw"): "Helsinki-NLP/opus-mt-en-sw",
    ("sw", "en"): "Helsinki-NLP/opus-mt-sw-en",
    # Afrikaans
    ("en", "af"): "Helsinki-NLP/opus-mt-en-af",
    ("af", "en"): "Helsinki-NLP/opus-mt-af-en",
    # Arabic
    ("en", "ar"): "Helsinki-NLP/opus-mt-en-ar",
    ("ar", "en"): "Helsinki-NLP/opus-mt-ar-en",
    # French (useful for Francophone Africa)
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    # Yoruba → English (yo-en confirmed deployed; en-yo handled by Khaya)
    ("yo", "en"): "Helsinki-NLP/opus-mt-yo-en",
}

# Multilingual fallback models
_MUL_EN = "Helsinki-NLP/opus-mt-mul-en"  # any language → English
_EN_MUL = "Helsinki-NLP/opus-mt-en-mul"  # English → many languages

# HF Inference router base URL (2025+)
_HF_BASE = "https://router.huggingface.co/hf-inference/models"


def _pick_strategy(source_lang: str, target_lang: str) -> tuple[str, str]:
    """
    Returns (model_id, strategy) where strategy is:
      'helsinki'  — use verified Helsinki-NLP model directly
      'mul_en'    — use opus-mt-mul-en (any → English)
      'en_mul'    — use opus-mt-en-mul (English → any)

    NOTE: NLLB removed — it is no longer supported by hf-inference provider.
    West African langs (yo, ha, ig etc.) should be routed to Khaya first
    in routing.py; this is the last-resort fallback only.
    """
    # 1. Verified Helsinki model for this exact pair
    if (source_lang, target_lang) in _VERIFIED_MODELS:
        return _VERIFIED_MODELS[(source_lang, target_lang)], "helsinki"

    # 2. Multilingual fallback
    if target_lang == "en":
        return _MUL_EN, "mul_en"

    return _EN_MUL, "en_mul"


class HuggingFaceProvider(BaseProvider):
    """
    HuggingFace Inference API adapter.

    Routing priority:
      1. Verified deployed Helsinki-NLP model (best quality for that pair)
      2. opus-mt-en-mul / opus-mt-mul-en (multilingual last resort)

    Note: West African languages are handled by KhayaProvider in routing.py.
    HuggingFace is only used as a last-resort fallback for those.
    """

    def __init__(self) -> None:
        self._key = settings.huggingface_api_key
        self._stub = not bool(self._key)
        if self._stub:
            logger.warning(
                "HUGGINGFACE_API_KEY not set – HuggingFace provider in stub mode.\n"
                "  → Get a free token: https://huggingface.co/settings/tokens"
            )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}"}

    async def _call_hf(
        self,
        model_id: str,
        payload: dict,
        timeout: int = settings.http_timeout,
    ) -> list | dict:
        """POST to HF Inference router with retries."""
        url = f"{_HF_BASE}/{model_id}"
        last_exc: Exception = RuntimeError("no attempts made")

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        url, json=payload, headers=self._headers()
                    )

                # Model loading (cold start)
                if resp.status_code == 503:
                    try:
                        body = resp.json()
                        wait = min(float(body.get("estimated_time", 20)), 30)
                    except Exception:
                        wait = 20
                    logger.info(
                        "HF model '%s' loading – waiting %.0fs (attempt %d/%d)",
                        model_id, wait, attempt, _MAX_RETRIES,
                    )
                    await asyncio.sleep(wait)
                    last_exc = httpx.HTTPStatusError(
                        "503 loading", request=resp.request, response=resp
                    )
                    continue

                # Rate limited
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 10))
                    logger.warning("HF rate limited – waiting %ds", retry_after)
                    await asyncio.sleep(retry_after)
                    last_exc = httpx.HTTPStatusError(
                        "429 rate limited", request=resp.request, response=resp
                    )
                    continue

                # Other retryable errors
                if resp.status_code in {500, 502, 504}:
                    wait = 2 ** attempt
                    logger.warning(
                        "HF HTTP %s on %s (attempt %d) – retrying in %ds",
                        resp.status_code, model_id, attempt, wait,
                    )
                    await asyncio.sleep(wait)
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request, response=resp,
                    )
                    continue

                # Log body on unexpected failures before raising
                if not resp.is_success:
                    logger.error(
                        "HF %s returned %s — body: %s",
                        model_id, resp.status_code, resp.text,
                    )

                resp.raise_for_status()
                return resp.json()

            except httpx.RequestError as exc:
                logger.error("HF network error on %s: %s", model_id, exc)
                last_exc = exc
                await asyncio.sleep(2 ** attempt)

        raise last_exc

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model_id: str,
    ) -> TranslationResult:
        t0 = time.monotonic()

        if self._stub:
            return TranslationResult(
                translated_text=f"[HF-STUB] {text} → ({target_lang})",
                model_used=model_id,
                provider="huggingface",
                quality_score=0.0,
                latency_ms=0,
            )

        # Always re-pick strategy based on actual language pair
        actual_model, strategy = _pick_strategy(source_lang, target_lang)

        # All strategies use plain text input — NLLB special params no longer needed
        payload = {"inputs": text}

        # Try primary model
        try:
            data = await self._call_hf(actual_model, payload)
        except Exception as primary_exc:
            logger.error(
                "HF primary model '%s' failed: %s — trying mul fallback",
                actual_model, primary_exc,
            )
            # Fallback to multilingual model
            fallback = _MUL_EN if target_lang == "en" else _EN_MUL
            if actual_model != fallback:
                data = await self._call_hf(fallback, {"inputs": text})
            else:
                raise

        latency_ms = int((time.monotonic() - t0) * 1000)

        # Parse HF response
        if isinstance(data, list) and len(data) > 0:
            translated = data[0].get("translation_text", "")
        elif isinstance(data, dict):
            translated = data.get("translation_text", str(data))
        else:
            translated = str(data)

        # Quality scores by strategy
        quality_map = {
            "helsinki": 0.80,
            "mul_en":   0.60,
            "en_mul":   0.58,
        }
        quality = quality_map.get(strategy, 0.60)

        return TranslationResult(
            translated_text=translated,
            model_used=actual_model,
            provider="huggingface",
            quality_score=quality,
            latency_ms=latency_ms,
        )
