"""
fasiri-sdk – Official Python client for the Fasiri African Language API.

Install:
    pip install fasiri

Usage:
    from fasiri import Fasiri

    client = Fasiri(api_key="fsri_...")

    # Single translation
    result = client.translate("Hello, how are you?", target="sw")
    print(result.translated_text)  # "Habari, ukoje?"

    # Batch
    results = client.translate_batch([
        {"id": "1", "text": "Good morning", "target": "lug"},
        {"id": "2", "text": "Thank you",    "target": "yo"},
    ])

    # Async
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="ha")
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import httpx


# ── Data classes returned to the caller ──────────────────────────────────────

@dataclass
class TranslationResult:
    translated_text: str
    detected_source_lang: str
    target_lang: str
    model_used: str
    provider: str
    quality_score: float
    latency_ms: int
    characters_translated: int

    def __str__(self) -> str:
        return self.translated_text


@dataclass
class BatchItemResult:
    id: str
    translated_text: Optional[str]
    detected_source_lang: Optional[str]
    target_lang: str
    model_used: Optional[str]
    provider: Optional[str]
    quality_score: Optional[float]
    error: Optional[str]

    @property
    def success(self) -> bool:
        return self.error is None

    def __str__(self) -> str:
        return self.translated_text or f"[ERROR] {self.error}"


@dataclass
class BatchResult:
    results: List[BatchItemResult]
    total: int
    succeeded: int
    failed: int
    total_latency_ms: int

    def __iter__(self):
        return iter(self.results)

    def __len__(self) -> int:
        return self.total

    def successful(self) -> List[BatchItemResult]:
        return [r for r in self.results if r.success]

    def errors(self) -> List[BatchItemResult]:
        return [r for r in self.results if not r.success]


@dataclass
class STTResult:
    transcript: str
    detected_lang: Optional[str]
    language: str
    model_used: str
    provider: str
    latency_ms: int

    def __str__(self) -> str:
        return self.transcript


@dataclass
class TTSResult:
    audio_url: Optional[str]
    audio_base64: Optional[str]
    content_type: str
    language: str
    model_used: str
    provider: str
    latency_ms: int


@dataclass
class Language:
    code: str
    name: str
    native_name: str
    region: str
    family: str
    supports_translation: bool
    supports_stt: bool
    supports_tts: bool
    tts_voice_id: Optional[int]
    best_provider: str
    quality_score: float

    def __repr__(self) -> str:
        caps = []
        if self.supports_translation: caps.append("translate")
        if self.supports_stt:         caps.append("stt")
        if self.supports_tts:         caps.append("tts")
        return f"<Language {self.code}: {self.name} [{', '.join(caps)}]>"


# ── Exceptions ────────────────────────────────────────────────────────────────

class FasiriError(Exception):
    """Base exception for all Fasiri SDK errors."""
    def __init__(self, message: str, code: str = "UNKNOWN", status_code: int = 0):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class AuthenticationError(FasiriError):
    """Raised when the API key is missing, invalid, or expired."""


class RateLimitError(FasiriError):
    """Raised when the rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429)
        self.retry_after = retry_after


class UnsupportedLanguageError(FasiriError):
    """Raised when a language pair is not supported."""


class ProviderError(FasiriError):
    """Raised when all providers fail."""


# ── Main client ───────────────────────────────────────────────────────────────

class Fasiri:
    """
    Fasiri API client – synchronous and asynchronous.

    Parameters
    ----------
    api_key : str
        Your Fasiri API key (``fsri_...``).
        Falls back to the ``FASIRI_API_KEY`` environment variable.
    base_url : str
        Override the API base URL (default: ``https://api.fasiri.ai``).
    timeout : int
        HTTP timeout in seconds (default: 30).

    Examples
    --------
    Sync usage::

        client = Fasiri(api_key="fsri_...")
        result = client.translate("Hello", target="sw")
        print(result)  # "Habari"

    Async usage::

        async with Fasiri(api_key="fsri_...") as client:
            result = await client.async_translate("Hello", target="sw")
    """

    DEFAULT_BASE_URL = "https://api.fasiri.ai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.environ.get("FASIRI_API_KEY", "")
        if not self.api_key:
            raise AuthenticationError(
                "No API key provided. Pass api_key= or set FASIRI_API_KEY.",
                code="MISSING_API_KEY",
            )
        self.base_url = (base_url or os.environ.get(
            "FASIRI_BASE_URL", self.DEFAULT_BASE_URL
        )).rstrip("/")
        self.timeout = timeout
        self._async_client: Optional[httpx.AsyncClient] = None

    # ── Context manager (async) ───────────────────────────────────────────────

    async def __aenter__(self) -> "Fasiri":
        self._async_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "fasiri-python-sdk/1.0.0",
        }

    def _raise_for_error(self, resp: httpx.Response) -> None:
        if resp.status_code == 401:
            body = resp.json().get("detail", {})
            raise AuthenticationError(
                body.get("message", "Invalid API key"),
                code=body.get("code", "INVALID_API_KEY"),
                status_code=401,
            )
        if resp.status_code == 429:
            body = resp.json().get("detail", {})
            retry_after = int(resp.headers.get("Retry-After", 60))
            raise RateLimitError(
                body.get("message", "Rate limit exceeded"),
                retry_after=retry_after,
            )
        if resp.status_code == 422:
            body = resp.json().get("detail", {})
            raise UnsupportedLanguageError(
                body.get("message", "Unsupported language or input"),
                code=body.get("code", "UNSUPPORTED"),
                status_code=422,
            )
        if resp.status_code >= 500:
            body = resp.json().get("detail", {}) if resp.content else {}
            raise ProviderError(
                body.get("message", "Provider error – please retry"),
                code=body.get("code", "PROVIDER_ERROR"),
                status_code=resp.status_code,
            )
        resp.raise_for_status()

    def _sync_post(self, path: str, json: Dict) -> Dict:
        with httpx.Client(
            base_url=self.base_url, headers=self._headers(), timeout=self.timeout
        ) as client:
            resp = client.post(path, json=json)
        self._raise_for_error(resp)
        return resp.json()

    def _sync_get(self, path: str) -> Dict:
        with httpx.Client(
            base_url=self.base_url, headers=self._headers(), timeout=self.timeout
        ) as client:
            resp = client.get(path)
        self._raise_for_error(resp)
        return resp.json()

    async def _async_post(self, path: str, json: Dict) -> Dict:
        client = self._async_client or httpx.AsyncClient(
            base_url=self.base_url, headers=self._headers(), timeout=self.timeout
        )
        try:
            resp = await client.post(path, json=json)
        finally:
            if not self._async_client:
                await client.aclose()
        self._raise_for_error(resp)
        return resp.json()

    # ── Translation ───────────────────────────────────────────────────────────

    def translate(
        self,
        text: str,
        target: str,
        source: Optional[str] = None,
        provider: str = "auto",
    ) -> TranslationResult:
        """
        Translate text to a target language.

        Parameters
        ----------
        text : str
            The text to translate (max 5,000 characters).
        target : str
            Target language code, e.g. ``"sw"``, ``"lug"``, ``"yo"``.
        source : str, optional
            Source language code. Auto-detected if omitted.
        provider : str
            ``"auto"`` (default), ``"sunbird"``, ``"khaya"``, or ``"huggingface"``.

        Returns
        -------
        TranslationResult
        """
        data = self._sync_post("/api/v1/translate", {
            "text": text,
            "target_lang": target,
            "source_lang": source,
            "provider": provider,
        })
        return self._parse_translation(data)

    async def async_translate(
        self,
        text: str,
        target: str,
        source: Optional[str] = None,
        provider: str = "auto",
    ) -> TranslationResult:
        """Async version of :meth:`translate`."""
        data = await self._async_post("/api/v1/translate", {
            "text": text,
            "target_lang": target,
            "source_lang": source,
            "provider": provider,
        })
        return self._parse_translation(data)

    @staticmethod
    def _parse_translation(data: Dict) -> TranslationResult:
        return TranslationResult(
            translated_text=data["translated_text"],
            detected_source_lang=data["detected_source_lang"],
            target_lang=data["target_lang"],
            model_used=data["model_used"],
            provider=data["provider"],
            quality_score=data["quality_score"],
            latency_ms=data["latency_ms"],
            characters_translated=data["characters_translated"],
        )

    # ── Batch translation ─────────────────────────────────────────────────────

    def translate_batch(
        self,
        items: List[Dict[str, str]],
        provider: str = "auto",
    ) -> BatchResult:
        """
        Translate multiple texts in a single request.

        Parameters
        ----------
        items : list of dict
            Each dict must have ``"id"``, ``"text"``, ``"target"``.
            Optionally include ``"source"`` for known source languages.
        provider : str
            Provider override (default: ``"auto"``).

        Returns
        -------
        BatchResult

        Example
        -------
        ::

            results = client.translate_batch([
                {"id": "1", "text": "Hello",    "target": "sw"},
                {"id": "2", "text": "Thank you", "target": "yo"},
            ])
            for r in results:
                print(r.id, r.translated_text)
        """
        payload_items = [
            {
                "id": item["id"],
                "text": item["text"],
                "target_lang": item.get("target") or item.get("target_lang"),
                "source_lang": item.get("source") or item.get("source_lang"),
            }
            for item in items
        ]
        data = self._sync_post("/api/v1/translate/batch", {
            "items": payload_items,
            "provider": provider,
        })
        return self._parse_batch(data)

    async def async_translate_batch(
        self,
        items: List[Dict[str, str]],
        provider: str = "auto",
    ) -> BatchResult:
        """Async version of :meth:`translate_batch`."""
        payload_items = [
            {
                "id": item["id"],
                "text": item["text"],
                "target_lang": item.get("target") or item.get("target_lang"),
                "source_lang": item.get("source") or item.get("source_lang"),
            }
            for item in items
        ]
        data = await self._async_post("/api/v1/translate/batch", {
            "items": payload_items,
            "provider": provider,
        })
        return self._parse_batch(data)

    @staticmethod
    def _parse_batch(data: Dict) -> BatchResult:
        results = [
            BatchItemResult(
                id=r["id"],
                translated_text=r.get("translated_text"),
                detected_source_lang=r.get("detected_source_lang"),
                target_lang=r["target_lang"],
                model_used=r.get("model_used"),
                provider=r.get("provider"),
                quality_score=r.get("quality_score"),
                error=r.get("error"),
            )
            for r in data["results"]
        ]
        return BatchResult(
            results=results,
            total=data["total"],
            succeeded=data["succeeded"],
            failed=data["failed"],
            total_latency_ms=data["total_latency_ms"],
        )

    # ── Speech ────────────────────────────────────────────────────────────────

    def transcribe(
        self,
        audio: Union[bytes, str],
        language: str,
    ) -> STTResult:
        """
        Transcribe audio to text (Speech-to-Text).

        Parameters
        ----------
        audio : bytes or str
            Raw audio bytes, or a file path to a WAV/MP3/OGG file.
        language : str
            Language code of the audio, e.g. ``"lug"``, ``"ach"``.

        Returns
        -------
        STTResult
        """
        if isinstance(audio, str):
            with open(audio, "rb") as f:
                audio_bytes = f.read()
            filename = os.path.basename(audio)
        else:
            audio_bytes = audio
            filename = "audio.wav"

        with httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "User-Agent": "fasiri-python-sdk/1.0.0"},
            timeout=max(self.timeout, 60),
        ) as client:
            resp = client.post(
                "/api/v1/speech/stt",
                files={"audio": (filename, audio_bytes, "audio/wav")},
                data={"language": language},
            )
        self._raise_for_error(resp)
        data = resp.json()
        return STTResult(
            transcript=data["transcript"],
            detected_lang=data.get("detected_lang"),
            language=data["language"],
            model_used=data["model_used"],
            provider=data["provider"],
            latency_ms=data["latency_ms"],
        )

    def synthesise(
        self,
        text: str,
        language: str,
        voice_id: Optional[int] = None,
    ) -> TTSResult:
        """
        Convert text to speech (Text-to-Speech).

        Parameters
        ----------
        text : str
            Text to synthesise (max 2,000 characters).
        language : str
            Language code, e.g. ``"lug"``, ``"sw"``.
        voice_id : int, optional
            Specific Sunbird voice ID. Auto-selected if omitted.

        Returns
        -------
        TTSResult
        """
        data = self._sync_post("/api/v1/speech/tts", {
            "text": text,
            "language": language,
            "voice_id": voice_id,
        })
        return TTSResult(
            audio_url=data.get("audio_url"),
            audio_base64=data.get("audio_base64"),
            content_type=data.get("content_type", "audio/mpeg"),
            language=data["language"],
            model_used=data["model_used"],
            provider=data["provider"],
            latency_ms=data["latency_ms"],
        )

    # Alias for American spelling
    synthesize = synthesise

    # ── Languages ─────────────────────────────────────────────────────────────

    def languages(self) -> List[Language]:
        """
        Return all supported languages with their capabilities.

        Returns
        -------
        list of Language
        """
        data = self._sync_get("/api/v1/languages")
        return [
            Language(
                code=lang["code"],
                name=lang["name"],
                native_name=lang["native_name"],
                region=lang["region"],
                family=lang["family"],
                supports_translation=lang["supports_translation"],
                supports_stt=lang["supports_stt"],
                supports_tts=lang["supports_tts"],
                tts_voice_id=lang.get("tts_voice_id"),
                best_provider=lang["best_provider"],
                quality_score=lang["quality_score"],
            )
            for lang in data["languages"]
        ]

    def translation_languages(self) -> List[Language]:
        """Return only languages that support translation."""
        return [l for l in self.languages() if l.supports_translation]

    def speech_languages(self) -> List[Language]:
        """Return only languages that support STT or TTS."""
        return [l for l in self.languages() if l.supports_stt or l.supports_tts]
