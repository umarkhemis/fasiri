"""
Fasiri - Sunbird AI provider adapter.

Correct endpoints (from https://salt.sunbird.ai/API/ and https://docs.sunbird.ai):

  Translation  → POST /tasks/nllb_translate
                 body: { source_language, target_language, text }
                 response: { id, status, output: { translated_text, ... } }

  STT          → POST /tasks/stt   (multipart/form-data)
                 fields: audio (file), language, adapter
                 response: { audio_transcription, language, ... }

  TTS          → POST /tasks/tts
                 body: { text, speaker_id, temperature, max_new_audio_tokens }
                 response: { output: { audio_url, duration_seconds, blob, ... } }

  Language ID  → POST /tasks/language_id
                 body: { text }
                 response: { language }

Authentication:
  SUNBIRD_API_KEY is the Bearer token from your Sunbird dashboard.
  Pass directly as: Authorization: Bearer <token>

nllb_translate supports ONLY: ach, teo, eng, lug, lgg, nyn
For other languages Fasiri falls back to HuggingFace automatically.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import httpx

from app.core.config import settings
from app.services.providers.base import (
    BaseProvider,
    STTResult,
    TTSResult,
    TranslationResult,
)
from app.utils.lang_detect import map_sunbird_lang

logger = logging.getLogger(__name__)

# ── Language code maps ────────────────────────────────────────────────────────

# Fasiri code → Sunbird nllb_translate code
# ONLY these 6 codes are accepted by /tasks/nllb_translate
_NLLB_SUPPORTED: dict[str, str] = {
    "en":  "eng",
    "lug": "lug",
    "nyn": "nyn",
    "lgg": "lgg",
    "ach": "ach",
    "teo": "teo",
}

# Fasiri code → Sunbird STT language code
_STT_LANG_MAP: dict[str, str] = {
    "en":  "eng",
    "sw":  "swa",
    "lug": "lug",
    "nyn": "nyn",
    "lgg": "lgg",
    "ach": "ach",
    "teo": "teo",
    "rw":  "kin",
    "xog": "xog",
    "myx": "myx",
    "laj": "laj",
    "adh": "adh",
}

# Fasiri code → Sunbird TTS speaker_id
# Source: https://salt.sunbird.ai/API/ Supported Languages & Voices table
_TTS_SPEAKER_IDS: dict[str, int] = {
    "ach": 241,   # Acholi     - Female
    "teo": 242,   # Ateso      - Female
    "nyn": 243,   # Runyankole - Female
    "lgg": 245,   # Lugbara    - Female
    "sw":  246,   # Swahili    - Male
    "lug": 248,   # Luganda    - Female (default)
}

_MAX_RETRIES = 3
_RETRY_STATUSES = {429, 500, 502, 503, 504}


def supports_nllb_translate(source_lang: str, target_lang: str) -> bool:
    """Return True if both langs are in Sunbird's nllb_translate supported set."""
    return source_lang in _NLLB_SUPPORTED and target_lang in _NLLB_SUPPORTED


class SunbirdProvider(BaseProvider):
    """
    Adapter for the Sunbird AI public API.

    Set SUNBIRD_API_KEY to the Bearer token from your Sunbird dashboard
    (register at https://api.sunbird.ai/register).
    """

    def __init__(self) -> None:
        self._base = settings.sunbird_base_url.rstrip("/")
        self._token = settings.sunbird_api_key
        self._stub = not bool(self._token)
        if self._stub:
            logger.warning(
                "SUNBIRD_API_KEY not set - Sunbird provider in stub mode.\n"
                "To get a token:\n"
                "  1. Register: POST https://api.sunbird.ai/auth/register\n"
                "  2. Login:    POST https://api.sunbird.ai/auth/token\n"
                "               body: username=your@email.com&password=yourpassword\n"
                "               (Content-Type: application/x-www-form-urlencoded)\n"
                "  3. Copy access_token into SUNBIRD_API_KEY in your .env"
            )
        elif not self._token.startswith("ey"):
            logger.warning(
                "SUNBIRD_API_KEY looks wrong - it should be a JWT starting with 'ey...'. "
                "A 405 error from Sunbird usually means your token is missing or invalid. "
                "Re-run: POST https://api.sunbird.ai/auth/token to get a fresh JWT."
            )

    def _json_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _multipart_headers(self) -> dict[str, str]:
        # No Content-Type here - httpx sets the multipart boundary automatically
        return {"Authorization": f"Bearer {self._token}"}

    # ── Retry helper ─────────────────────────────────────────────────────────

    async def _post_json_retry(
        self,
        path: str,
        payload: dict,
        timeout: int = settings.http_timeout,
    ) -> dict:
        url = f"{self._base}{path}"
        last_exc: Exception = RuntimeError("no attempts made")

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        url, json=payload, headers=self._json_headers()
                    )

                # 405 = Method Not Allowed - almost always a bad/missing token
                # Sunbird's auth middleware returns 405 before the route handler
                # when auth fails. Do NOT retry - fail immediately with clear message.
                if resp.status_code == 405:
                    raise httpx.HTTPStatusError(
                        f"HTTP 405 on {path} - this usually means your "
                        f"SUNBIRD_API_KEY is missing, expired, or not a valid JWT. "
                        f"Get a fresh token: POST https://api.sunbird.ai/auth/token",
                        request=resp.request, response=resp,
                    )

                # 401/403 = explicit auth failure
                if resp.status_code in {401, 403}:
                    raise httpx.HTTPStatusError(
                        f"HTTP {resp.status_code} - Sunbird auth failed. "
                        f"Check your SUNBIRD_API_KEY in .env",
                        request=resp.request, response=resp,
                    )

                if resp.status_code in _RETRY_STATUSES:
                    wait = 2 ** attempt
                    logger.warning(
                        "Sunbird %s HTTP %s (attempt %d/%d) - retrying in %ds",
                        path, resp.status_code, attempt, _MAX_RETRIES, wait,
                    )
                    await asyncio.sleep(wait)
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request, response=resp,
                    )
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.HTTPStatusError:
                raise   # don't swallow - let routing fallback handle it
            except httpx.RequestError as exc:
                logger.error("Sunbird network error on %s: %s", path, exc)
                last_exc = exc
                await asyncio.sleep(2 ** attempt)

        raise last_exc

    # ── Translation ───────────────────────────────────────────────────────────

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model_id: str,
    ) -> TranslationResult:
        """
        POST /tasks/nllb_translate
        Supported language pairs: any combination of ach, teo, eng, lug, lgg, nyn.
        """
        t0 = time.monotonic()

        if self._stub:
            return TranslationResult(
                translated_text=f"[SUNBIRD-STUB] {text} → ({target_lang})",
                model_used=model_id,
                provider="sunbird",
                quality_score=0.0,
                latency_ms=0,
            )

        src = _NLLB_SUPPORTED.get(source_lang, source_lang)
        tgt = _NLLB_SUPPORTED.get(target_lang, target_lang)

        payload = {
            "source_language": src,
            "target_language": tgt,
            "text": text,
        }

        data = await self._post_json_retry("/tasks/translate", payload)

        # Response: { id, status, executionTime, output: { translated_text, Error, ... } }
        output = data.get("output", {})
        error_msg = output.get("Error") or output.get("error")
        if error_msg:
            raise RuntimeError(f"Sunbird translation error: {error_msg}")

        translated = (
            output.get("translated_text")
            or output.get("text")
            or ""
        )
        latency_ms = int((time.monotonic() - t0) * 1000)

        return TranslationResult(
            translated_text=translated,
            model_used=model_id,
            provider="sunbird",
            quality_score=0.92,
            latency_ms=latency_ms,
        )

    # ── Speech-to-Text ────────────────────────────────────────────────────────

    async def speech_to_text(
        self,
        audio_bytes: bytes,
        language: str,
        filename: str = "audio.wav",
    ) -> STTResult:
        """
        POST /tasks/stt  (multipart/form-data)
        Fields: audio (file), language, adapter, recognise_speakers, whisper
        Response: { audio_transcription, language, was_audio_trimmed, ... }
        """
        t0 = time.monotonic()

        if self._stub:
            return STTResult(
                transcript="[SUNBIRD-STUB] Set SUNBIRD_API_KEY to enable STT.",
                detected_lang=language,
                model_used="sunbird/stt",
                provider="sunbird",
                latency_ms=0,
            )

        sunbird_lang = _STT_LANG_MAP.get(language, language)
        url = f"{self._base}/tasks/stt"
        last_exc: Exception = RuntimeError("no attempts made")
        resp = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.http_timeout_stt) as client:
                    resp = await client.post(
                        url,
                        files={"audio": (filename, audio_bytes, "audio/mpeg")},
                        data={
                            "language": sunbird_lang,
                            "adapter":  sunbird_lang,
                            "recognise_speakers": "false",
                            "whisper": "false",
                        },
                        headers=self._multipart_headers(),
                    )

                if resp.status_code in _RETRY_STATUSES:
                    wait = 2 ** attempt
                    logger.warning(
                        "Sunbird /tasks/stt HTTP %s (attempt %d) retrying in %ds",
                        resp.status_code, attempt, wait,
                    )
                    await asyncio.sleep(wait)
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request, response=resp,
                    )
                    continue

                resp.raise_for_status()
                break

            except httpx.RequestError as exc:
                logger.error("Sunbird STT network error: %s", exc)
                last_exc = exc
                await asyncio.sleep(2 ** attempt)
        else:
            raise last_exc

        # Response: { audio_transcription, language, diarization_output, ... }
        body = resp.json()
        transcript = body.get("audio_transcription") or body.get("transcript") or ""
        detected = map_sunbird_lang(body.get("language", language))
        latency_ms = int((time.monotonic() - t0) * 1000)

        if body.get("was_audio_trimmed"):
            logger.warning(
                "Sunbird STT: audio was trimmed to 10 min "
                "(original: %.1f min)", body.get("original_duration_minutes", 0)
            )

        return STTResult(
            transcript=transcript,
            detected_lang=detected,
            model_used="sunbird/stt",
            provider="sunbird",
            latency_ms=latency_ms,
        )

    # ── Text-to-Speech ────────────────────────────────────────────────────────

    async def text_to_speech(
        self,
        text: str,
        language: str,
        voice_id: Optional[int] = None,
    ) -> TTSResult:
        """
        POST /tasks/tts
        Body: { text, speaker_id, temperature, max_new_audio_tokens }
        Response: { output: { audio_url, duration_seconds, blob, format, ... } }

        IMPORTANT: audio_url is a signed GCS URL that expires in ~2 minutes.
        Download it immediately or store the blob field for re-signing.
        """
        t0 = time.monotonic()

        if self._stub:
            return TTSResult(
                audio_url=None,
                audio_base64=None,
                content_type="audio/mpeg",
                model_used="sunbird/tts",
                provider="sunbird",
                latency_ms=0,
            )

        speaker_id = voice_id or _TTS_SPEAKER_IDS.get(language)
        if speaker_id is None:
            raise ValueError(
                f"No TTS voice for '{language}'. "
                f"Supported: {list(_TTS_SPEAKER_IDS.keys())}"
            )

        payload = {
            "text": text,
            "speaker_id": speaker_id,
            "temperature": 0.7,
            "max_new_audio_tokens": 2000,
        }

        data = await self._post_json_retry("/tasks/tts", payload)

        # Response: { output: { audio_url, duration_seconds, blob, ... } }
        output = data.get("output", {})
        audio_url = output.get("audio_url") or output.get("url")
        latency_ms = int((time.monotonic() - t0) * 1000)

        logger.info(
            "Sunbird TTS: speaker_id=%s duration=%.1fs latency=%dms",
            speaker_id,
            output.get("duration_seconds", 0),
            latency_ms,
        )

        return TTSResult(
            audio_url=audio_url,
            audio_base64=None,
            content_type="audio/mpeg",
            model_used="sunbird/tts",
            provider="sunbird",
            latency_ms=latency_ms,
        )
