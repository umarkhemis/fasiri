
"""
Fasiri - GhanaNLP / Khaya AI provider adapter.

API spec: khaya-translation-api-v2.json (OpenAPI 3.0.1)
Register:  https://translation.ghananlp.org/signup

Translation endpoint:
  POST https://translation-api.ghananlp.org/v2/translate
  Auth (either):
    Header:  Ocp-Apim-Subscription-Key: <key>
    Query:   ?subscription-key=<key>
  Body:
    { "in": "<text>", "lang": "<src>-<tgt>" }
    Max input length: 1000 characters
  Response:
    Plain string - the translated text (not a JSON object)
  Errors:
    400: { "type": "...", "message": "..." }

Supported language codes (from /v2/languages):
  en  - English
  tw  - Twi
  ee  - Ewe
  gaa - Ga
  fat - Fante
  yo  - Yoruba
  dag - Dagbani
  ki  - Kikuyu
  gur - Gurune
  luo - Luo
  mer - Kimeru
  kus - Kusaal

Authentication:
  Set KHAYA_API_KEY to the subscription key from your Khaya dashboard.
"""
from __future__ import annotations

import asyncio
import logging
import time

import httpx

from app.core.config import settings
from app.services.providers.base import BaseProvider, TranslationResult

logger = logging.getLogger(__name__)

_BASE_URL = "https://translation-api.ghananlp.org/v2/translate"
_MAX_RETRIES = 3
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_INPUT_LENGTH = 1000  # enforced by API

# ── Language pair map ─────────────────────────────────────────────────────────
# Fasiri (src, tgt) → Khaya lang code string
# All pairs confirmed from official API spec /v2/languages endpoint.
_LANG_PAIR_MAP: dict[tuple[str, str], str] = {
    # English → African languages
    ("en", "tw"):  "en-tw",   # Twi
    ("en", "ee"):  "en-ee",   # Ewe
    ("en", "gaa"): "en-gaa",  # Ga
    ("en", "fat"): "en-fat",  # Fante
    ("en", "yo"):  "en-yo",   # Yoruba
    ("en", "dag"): "en-dag",  # Dagbani
    ("en", "ki"):  "en-ki",   # Kikuyu
    ("en", "gur"): "en-gur",  # Gurune
    ("en", "luo"): "en-luo",  # Luo
    ("en", "mer"): "en-mer",  # Kimeru
    ("en", "kus"): "en-kus",  # Kusaal
    # African languages → English
    ("tw",  "en"): "tw-en",
    ("ee",  "en"): "ee-en",
    ("gaa", "en"): "gaa-en",
    ("fat", "en"): "fat-en",
    ("yo",  "en"): "yo-en",
    ("dag", "en"): "dag-en",
    ("ki",  "en"): "ki-en",
    ("gur", "en"): "gur-en",
    ("luo", "en"): "luo-en",
    ("mer", "en"): "mer-en",
    ("kus", "en"): "kus-en",
}

# All languages Khaya supports (used for routing decisions)
KHAYA_LANGS: set[str] = {lang for pair in _LANG_PAIR_MAP for lang in pair}


def supports_pair(source_lang: str, target_lang: str) -> bool:
    """Return True if Khaya can handle this language pair."""
    return (source_lang, target_lang) in _LANG_PAIR_MAP


class KhayaProvider(BaseProvider):
    """
    Adapter for GhanaNLP / Khaya AI Translation API (v2).

    Set KHAYA_API_KEY to the subscription key from your Khaya dashboard
    (register at https://translation.ghananlp.org/signup).

    Note: Uses Ocp-Apim-Subscription-Key header - NOT a Bearer token.
    """

    def __init__(self) -> None:
        self._key = settings.khaya_api_key
        self._stub = not bool(self._key)
        if self._stub:
            logger.warning(
                "KHAYA_API_KEY not set - Khaya provider in stub mode.\n"
                "To get a key:\n"
                "  1. Register: https://translation.ghananlp.org/signup\n"
                "  2. Copy your subscription key into KHAYA_API_KEY in your .env"
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Ocp-Apim-Subscription-Key": self._key,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model_id: str,
    ) -> TranslationResult:
        """
        POST https://translation-api.ghananlp.org/v2/translate
        Body: { "in": text, "lang": "en-yo" }
        Response: plain translated string
        """
        t0 = time.monotonic()

        if self._stub:
            return TranslationResult(
                translated_text=f"[KHAYA-STUB] {text} → ({target_lang})",
                model_used="khaya/translate-v2",
                provider="khaya",
                quality_score=0.0,
                latency_ms=0,
            )

        lang_code = _LANG_PAIR_MAP.get((source_lang, target_lang))
        if not lang_code:
            raise ValueError(
                f"Khaya does not support {source_lang}→{target_lang}. "
                f"Supported pairs: {sorted(_LANG_PAIR_MAP.keys())}"
            )

        # Enforce API character limit
        if len(text) > _MAX_INPUT_LENGTH:
            logger.warning(
                "Khaya input truncated from %d to %d characters",
                len(text), _MAX_INPUT_LENGTH,
            )
            text = text[:_MAX_INPUT_LENGTH]

        payload = {
            "in": text,
            "lang": lang_code,
        }

        last_exc: Exception = RuntimeError("no attempts made")

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                    resp = await client.post(
                        _BASE_URL,
                        json=payload,
                        headers=self._headers(),
                    )

                # 401/403 = bad API key - don't retry
                if resp.status_code in {401, 403}:
                    raise httpx.HTTPStatusError(
                        f"HTTP {resp.status_code} - Khaya auth failed. "
                        f"Check your KHAYA_API_KEY in .env",
                        request=resp.request,
                        response=resp,
                    )

                # 400 = bad request - don't retry, log body for diagnosis
                if resp.status_code == 400:
                    logger.error(
                        "Khaya 400 Bad Request - payload: %s - body: %s",
                        payload, resp.text,
                    )
                    raise httpx.HTTPStatusError(
                        f"HTTP 400 - Khaya rejected request for '{lang_code}'. "
                        f"Body: {resp.text}",
                        request=resp.request,
                        response=resp,
                    )

                # Retryable server errors
                if resp.status_code in _RETRY_STATUSES:
                    wait = 2 ** attempt
                    logger.warning(
                        "Khaya HTTP %s (attempt %d/%d) - retrying in %ds",
                        resp.status_code, attempt, _MAX_RETRIES, wait,
                    )
                    await asyncio.sleep(wait)
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                    continue

                # Log unexpected failures
                if not resp.is_success:
                    logger.error(
                        "Khaya unexpected %s - body: %s",
                        resp.status_code, resp.text,
                    )

                resp.raise_for_status()

                # Response is a plain string e.g. "Ẹ káàárọ̀"
                # Strip surrounding quotes if present
                translated = resp.text.strip().strip('"')
                latency_ms = int((time.monotonic() - t0) * 1000)

                logger.info(
                    "Khaya translated %s→%s in %dms",
                    source_lang, target_lang, latency_ms,
                )

                return TranslationResult(
                    translated_text=translated,
                    model_used="khaya/translate-v2",
                    provider="khaya",
                    quality_score=0.85,  # purpose-built for these languages
                    latency_ms=latency_ms,
                )

            except (httpx.HTTPStatusError, ValueError):
                raise  # don't retry auth/validation errors
            except httpx.RequestError as exc:
                logger.error(
                    "Khaya network error (attempt %d/%d): %s",
                    attempt, _MAX_RETRIES, exc,
                )
                last_exc = exc
                await asyncio.sleep(2 ** attempt)

        raise last_exc




































# """
# Fasiri - GhanaNLP / Khaya AI provider adapter.

# API docs: https://translation.ghananlp.org/
# Register:  https://translation.ghananlp.org/signup

# Translation endpoint:
#   POST https://translation-api.ghananlp.org/v1/translate
#   Headers:
#     Ocp-Apim-Subscription-Key: <your_key>
#     Content-Type: application/json
#   Body:
#     { "in": "<text>", "lang": "<src>-<tgt>" }
#   Response:
#     "translated text string"   (plain string, not JSON object)

# Supported language pairs (all en↔ and inter-African where available):
#   en-tw   English → Twi
#   en-gaa  English → Ga
#   en-ee   English → Ewe
#   en-fat  English → Fante
#   en-dag  English → Dagbani
#   en-gur  English → Gurene
#   en-yo   English → Yoruba
#   tw-en   Twi → English
#   ee-en   Ewe → English
#   (reverse pairs where supported)

# Authentication:
#   Set KHAYA_API_KEY to the subscription key from your Khaya dashboard.
#   Passed as: Ocp-Apim-Subscription-Key header (NOT Bearer token).
# """
# from __future__ import annotations

# import asyncio
# import logging
# import time
# from typing import Optional

# import httpx

# from app.core.config import settings
# from app.services.providers.base import BaseProvider, TranslationResult

# logger = logging.getLogger(__name__)

# _BASE_URL = "https://translation-api.ghananlp.org/v1/translate"
# _MAX_RETRIES = 3
# _RETRY_STATUSES = {429, 500, 502, 503, 504}

# # ── Language pair map ─────────────────────────────────────────────────────────
# # Fasiri (src, tgt) → Khaya lang code (e.g. "en-yo")
# # Only confirmed supported pairs are listed.
# # Khaya uses short codes: tw=Twi, gaa=Ga, ee=Ewe, fat=Fante,
# #                          dag=Dagbani, gur=Gurene, yo=Yoruba
# _LANG_PAIR_MAP: dict[tuple[str, str], str] = {
#     # English → West African
#     ("en", "yo"):  "en-yo",
#     ("en", "tw"):  "en-tw",
#     ("en", "gaa"): "en-gaa",
#     ("en", "ee"):  "en-ee",
#     ("en", "fat"): "en-fat",
#     ("en", "dag"): "en-dag",
#     ("en", "gur"): "en-gur",
#     # West African → English
#     ("yo", "en"):  "yo-en",
#     ("tw", "en"):  "tw-en",
#     ("ee", "en"):  "ee-en",
# }

# # Languages Khaya supports (for routing checks)
# KHAYA_LANGS = {lang for pair in _LANG_PAIR_MAP for lang in pair}


# def supports_pair(source_lang: str, target_lang: str) -> bool:
#     """Return True if Khaya can handle this language pair."""
#     return (source_lang, target_lang) in _LANG_PAIR_MAP


# class KhayaProvider(BaseProvider):
#     """
#     Adapter for GhanaNLP / Khaya AI Translation API.

#     Set KHAYA_API_KEY to the subscription key from your Khaya dashboard
#     (register at https://translation.ghananlp.org/signup).

#     Note: Khaya uses Ocp-Apim-Subscription-Key header, NOT Bearer token.
#     """

#     def __init__(self) -> None:
#         self._key = settings.khaya_api_key
#         self._stub = not bool(self._key)
#         if self._stub:
#             logger.warning(
#                 "KHAYA_API_KEY not set - Khaya provider in stub mode.\n"
#                 "To get a key:\n"
#                 "  1. Register: https://translation.ghananlp.org/signup\n"
#                 "  2. Copy your subscription key into KHAYA_API_KEY in your .env"
#             )

#     def _headers(self) -> dict[str, str]:
#         return {
#             "Ocp-Apim-Subscription-Key": self._key,
#             "Content-Type": "application/json",
#             "Cache-Control": "no-cache",
#         }

#     async def translate(
#         self,
#         text: str,
#         source_lang: str,
#         target_lang: str,
#         model_id: str,
#     ) -> TranslationResult:
#         """
#         POST https://translation-api.ghananlp.org/v1/translate
#         Body: { "in": text, "lang": "en-yo" }
#         Response: plain string (the translated text)
#         """
#         t0 = time.monotonic()

#         if self._stub:
#             return TranslationResult(
#                 translated_text=f"[KHAYA-STUB] {text} → ({target_lang})",
#                 model_used="khaya/translate",
#                 provider="khaya",
#                 quality_score=0.0,
#                 latency_ms=0,
#             )

#         lang_code = _LANG_PAIR_MAP.get((source_lang, target_lang))
#         if not lang_code:
#             raise ValueError(
#                 f"Khaya does not support {source_lang}→{target_lang}. "
#                 f"Supported pairs: {list(_LANG_PAIR_MAP.keys())}"
#             )

#         payload = {
#             "in": text,
#             "lang": lang_code,
#         }

#         last_exc: Exception = RuntimeError("no attempts made")

#         for attempt in range(1, _MAX_RETRIES + 1):
#             try:
#                 async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
#                     resp = await client.post(
#                         _BASE_URL,
#                         json=payload,
#                         headers=self._headers(),
#                     )

#                 # 401/403 = bad API key
#                 if resp.status_code in {401, 403}:
#                     raise httpx.HTTPStatusError(
#                         f"HTTP {resp.status_code} - Khaya auth failed. "
#                         f"Check your KHAYA_API_KEY in .env",
#                         request=resp.request,
#                         response=resp,
#                     )

#                 # 400 = bad request - unsupported lang pair or malformed payload
#                 if resp.status_code == 400:
#                     logger.error(
#                         "Khaya 400 Bad Request - payload: %s - body: %s",
#                         payload, resp.text,
#                     )
#                     raise httpx.HTTPStatusError(
#                         f"HTTP 400 - Khaya rejected the request. "
#                         f"Lang pair '{lang_code}' may not be supported. "
#                         f"Body: {resp.text}",
#                         request=resp.request,
#                         response=resp,
#                     )

#                 # Retryable errors
#                 if resp.status_code in _RETRY_STATUSES:
#                     wait = 2 ** attempt
#                     logger.warning(
#                         "Khaya HTTP %s (attempt %d/%d) - retrying in %ds",
#                         resp.status_code, attempt, _MAX_RETRIES, wait,
#                     )
#                     await asyncio.sleep(wait)
#                     last_exc = httpx.HTTPStatusError(
#                         f"HTTP {resp.status_code}",
#                         request=resp.request,
#                         response=resp,
#                     )
#                     continue

#                 # Log body on any unexpected failure
#                 if not resp.is_success:
#                     logger.error(
#                         "Khaya %s - body: %s", resp.status_code, resp.text
#                     )

#                 resp.raise_for_status()

#                 # Khaya returns a plain string (not a JSON object)
#                 # e.g. "Ẹ káàárọ̀"
#                 translated = resp.text.strip().strip('"')
#                 latency_ms = int((time.monotonic() - t0) * 1000)

#                 return TranslationResult(
#                     translated_text=translated,
#                     model_used="khaya/translate",
#                     provider="khaya",
#                     quality_score=0.85,  # Khaya is purpose-built for these langs
#                     latency_ms=latency_ms,
#                 )

#             except httpx.HTTPStatusError:
#                 raise  # don't retry auth/bad-request errors
#             except httpx.RequestError as exc:
#                 logger.error("Khaya network error: %s", exc)
#                 last_exc = exc
#                 await asyncio.sleep(2 ** attempt)

#         raise last_exc
