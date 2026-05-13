"""
Fasiri - Sunbird AI direct provider adapter.

Sunbird AI provides translation, STT, and TTS for Ugandan languages.

Register and get your token:
    1. POST https://api.sunbird.ai/auth/register
       body: { "username": "...", "email": "...", "password": "..." }

    2. POST https://api.sunbird.ai/auth/token
       body (form): username=your@email.com&password=yourpassword

    3. Copy the access_token - it starts with "ey..." (JWT)

Supported languages: Luganda (lug), Acholi (ach), Ateso (teo),
                     Runyankore (nyn), Lugbara (lgg), English (en)

Docs: https://api.sunbird.ai/docs
"""
from __future__ import annotations

import time
from typing import Optional

import httpx

from .base import BaseDirectProvider, DirectSTTResult, DirectTranslationResult, DirectTTSResult


# AfriLang code -> Sunbird code
_LANG_MAP: dict[str, str] = {
    "en":  "eng",
    "lug": "lug",
    "ach": "ach",
    "teo": "teo",
    "nyn": "nyn",
    "lgg": "lgg",
}

# AfriLang code -> Sunbird TTS speaker ID
_TTS_VOICES: dict[str, int] = {
    "ach": 241,
    "teo": 242,
    "nyn": 243,
    "lgg": 245,
    "lug": 248,
}

_SUPPORTED_LANGS = set(_LANG_MAP.keys())
_SUPPORTED_PAIRS = {
    (src, tgt)
    for src in _SUPPORTED_LANGS
    for tgt in _SUPPORTED_LANGS
    if src != tgt
}


class SunbirdProvider(BaseDirectProvider):
    """
    Direct adapter for Sunbird AI.

    Parameters
    ----------
    api_key : str
        Your Sunbird JWT token (starts with "ey...").
        Get one at https://api.sunbird.ai/auth/token
    base_url : str
        Sunbird API base URL. Default: https://api.sunbird.ai
    timeout : int
        Request timeout in seconds. Default: 30

    Example
    -------
    ::

        from fasiri.providers import SunbirdProvider

        provider = SunbirdProvider(api_key="eyJ...")
        result = provider.translate("Good morning", target_lang="lug")
        print(result)  # Wasuze otya
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.sunbird.ai",
        timeout: int = 30,
    ) -> None:
        if not api_key:
            raise ValueError(
                "SunbirdProvider requires an api_key.\n"
                "Get one at: POST https://api.sunbird.ai/auth/token\n"
                "  body (form): username=your@email.com&password=yourpassword"
            )
        if not api_key.startswith("ey"):
            raise ValueError(
                "SunbirdProvider api_key should be a JWT starting with 'ey...'.\n"
                "Get a fresh token: POST https://api.sunbird.ai/auth/token"
            )
        self._key     = api_key
        self._base    = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "sunbird"

    @property
    def supported_languages(self) -> set[str]:
        return _SUPPORTED_LANGS

    @property
    def supported_pairs(self) -> set[tuple[str, str]]:
        return _SUPPORTED_PAIRS

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """
        Translate text using Sunbird AI.

        Parameters
        ----------
        text : str
            Text to translate.
        target_lang : str
            Target language code e.g. "lug", "ach", "teo", "nyn", "lgg".
        source_lang : str
            Source language code. Default: "en".

        Returns
        -------
        DirectTranslationResult
        """
        if source_lang not in _LANG_MAP:
            raise ValueError(
                f"Sunbird does not support source language '{source_lang}'. "
                f"Supported: {sorted(_LANG_MAP.keys())}"
            )
        if target_lang not in _LANG_MAP:
            raise ValueError(
                f"Sunbird does not support target language '{target_lang}'. "
                f"Supported: {sorted(_LANG_MAP.keys())}"
            )

        t0 = time.monotonic()

        resp = httpx.post(
            f"{self._base}/tasks/translate",
            json={
                "source_language": _LANG_MAP[source_lang],
                "target_language": _LANG_MAP[target_lang],
                "text": text,
            },
            headers=self._headers(),
            timeout=self._timeout,
        )

        if resp.status_code == 401:
            raise PermissionError(
                "Sunbird authentication failed. Your token may be expired.\n"
                "Get a new one: POST https://api.sunbird.ai/auth/token"
            )

        resp.raise_for_status()
        data   = resp.json()
        output = data.get("output", {})

        if err := (output.get("Error") or output.get("error")):
            raise RuntimeError(f"Sunbird translation error: {err}")

        translated = output.get("translated_text") or output.get("text") or ""
        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectTranslationResult(
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model_used="sunbird/translate",
            provider="sunbird",
            quality_score=0.92,
            latency_ms=latency_ms,
        )

    def speech_to_text(
        self,
        audio: bytes,
        language: str,
        filename: str = "audio.wav",
    ) -> DirectSTTResult:
        """
        Transcribe audio using Sunbird AI STT.

        Parameters
        ----------
        audio : bytes
            Raw audio bytes (WAV, MP3, or OGG).
        language : str
            Language code of the audio e.g. "lug", "ach".
        filename : str
            Filename hint for the audio format.

        Returns
        -------
        DirectSTTResult
        """
        sunbird_lang = _LANG_MAP.get(language, language)
        t0 = time.monotonic()

        resp = httpx.post(
            f"{self._base}/tasks/stt",
            files={"audio": (filename, audio, "audio/wav")},
            data={
                "language":           sunbird_lang,
                "adapter":            sunbird_lang,
                "recognise_speakers": "false",
                "whisper":            "false",
            },
            headers={"Authorization": f"Bearer {self._key}"},
            timeout=max(self._timeout, 60),
        )

        resp.raise_for_status()
        body = resp.json()

        transcript = body.get("audio_transcription") or body.get("transcript") or ""
        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectSTTResult(
            transcript=transcript,
            detected_lang=language,
            language=language,
            model_used="sunbird/stt",
            provider="sunbird",
            latency_ms=latency_ms,
        )

    def text_to_speech(
        self,
        text: str,
        language: str,
        voice_id: Optional[int] = None,
    ) -> DirectTTSResult:
        """
        Synthesise speech using Sunbird AI TTS.

        Parameters
        ----------
        text : str
            Text to synthesise.
        language : str
            Language code e.g. "lug", "ach", "teo", "nyn", "lgg".
        voice_id : int, optional
            Sunbird voice ID. Auto-selected if omitted.

        Returns
        -------
        DirectTTSResult
        """
        vid = voice_id or _TTS_VOICES.get(language)
        if vid is None:
            raise ValueError(
                f"No TTS voice available for '{language}'. "
                f"Supported: {sorted(_TTS_VOICES.keys())}"
            )

        t0 = time.monotonic()

        resp = httpx.post(
            f"{self._base}/tasks/tts",
            json={
                "text":               text,
                "speaker_id":         vid,
                "temperature":        0.9,
                "max_new_audio_tokens": 4096,
            },
            headers=self._headers(),
            timeout=max(self._timeout, 60),
        )

        resp.raise_for_status()
        data   = resp.json()
        output = data.get("output", {})

        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectTTSResult(
            audio_url=output.get("audio_url"),
            audio_base64=output.get("blob"),
            content_type="audio/mpeg",
            language=language,
            model_used=f"sunbird/tts/voice-{vid}",
            provider="sunbird",
            latency_ms=latency_ms,
        )

    async def async_translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """Async version of translate()."""
        import httpx as _httpx

        if source_lang not in _LANG_MAP:
            raise ValueError(f"Sunbird does not support source language '{source_lang}'.")
        if target_lang not in _LANG_MAP:
            raise ValueError(f"Sunbird does not support target language '{target_lang}'.")

        t0 = time.monotonic()

        async with _httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base}/tasks/translate",
                json={
                    "source_language": _LANG_MAP[source_lang],
                    "target_language": _LANG_MAP[target_lang],
                    "text": text,
                },
                headers=self._headers(),
            )

        if resp.status_code == 401:
            raise PermissionError("Sunbird authentication failed. Token may be expired.")

        resp.raise_for_status()
        data   = resp.json()
        output = data.get("output", {})
        translated = output.get("translated_text") or output.get("text") or ""
        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectTranslationResult(
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model_used="sunbird/translate",
            provider="sunbird",
            quality_score=0.92,
            latency_ms=latency_ms,
        )
