"""
fasiri-sdk - Official Python client for the Fasiri African Language API.

Two modes of operation:

1. Fasiri Cloud (default) - calls the hosted Fasiri API::

    from fasiri import Fasiri

    client = Fasiri(api_key="fsri_...")
    result = client.translate("Good morning", target="lug")
    print(result)  # Wasuze otya

2. Direct mode - calls providers directly with your own keys (free, no Fasiri account)::

    from fasiri import Fasiri
    from fasiri.providers import SunbirdProvider, KhayaProvider, HuggingFaceProvider

    client = Fasiri(
        providers=[
            SunbirdProvider(api_key="eyJ..."),        # your Sunbird JWT
            KhayaProvider(api_key="your-khaya-key"),   # your Khaya subscription key
            HuggingFaceProvider(api_key="hf_..."),     # your HuggingFace token
        ]
    )
    result = client.translate("Good morning", target="lug")
    print(result)  # Wasuze otya
    print(result.provider)  # "sunbird"

In direct mode, requests go straight to the provider from your machine.
Fasiri is just the routing and abstraction layer - you handle provider billing.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import httpx


# ── Data classes ──────────────────────────────────────────────────────────────

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
    def __init__(self, message: str, code: str = "UNKNOWN", status_code: int = 0):
        super().__init__(message)
        self.code        = code
        self.status_code = status_code


class AuthenticationError(FasiriError):
    """Raised when the API key is invalid or expired."""


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
    Fasiri API client.

    Supports two modes:

    **Cloud mode** (default) - use the hosted Fasiri API::

        client = Fasiri(api_key="fsri_...")

    **Direct mode** - call providers directly with your own keys::

        from fasiri.providers import SunbirdProvider, KhayaProvider

        client = Fasiri(
            providers=[
                SunbirdProvider(api_key="eyJ..."),
                KhayaProvider(api_key="your-khaya-key"),
            ]
        )

    In direct mode the interface is identical - same methods, same return types.
    Requests go straight from your machine to the provider. Fasiri is just the
    routing layer. You handle your own provider billing.

    Parameters
    ----------
    api_key : str, optional
        Fasiri Cloud API key (``fsri_...``). Required for cloud mode.
        Falls back to ``FASIRI_API_KEY`` environment variable.
    providers : list, optional
        List of direct provider instances for direct mode.
        When provided, ``api_key`` is not required.
    base_url : str, optional
        Fasiri API base URL. Default: ``https://fasiri-bu9u.onrender.com``.
        Falls back to ``FASIRI_BASE_URL`` environment variable.
    timeout : int, optional
        HTTP timeout in seconds. Default: 30.
    """

    # DEFAULT_BASE_URL = "https://fasiri-bu9u.onrender.com"
    DEFAULT_BASE_URL = "https://api.fasiri-ai.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        providers: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self._timeout   = timeout
        self._providers = providers  # direct mode provider list
        self._router    = None       # lazy-initialised direct router

        if providers:
            # ── Direct mode ──────────────────────────────────────────────────
            # Validate provider types
            from .providers.base import BaseDirectProvider
            for p in providers:
                if not isinstance(p, BaseDirectProvider):
                    raise TypeError(
                        f"Expected a provider instance (SunbirdProvider, KhayaProvider, etc.), "
                        f"got {type(p).__name__}. "
                        f"Example: Fasiri(providers=[SunbirdProvider(api_key='...')])"
                    )
            self._mode    = "direct"
            self.api_key  = None
            self.base_url = None

        else:
            # ── Cloud mode ───────────────────────────────────────────────────
            self.api_key = (
                api_key
                or os.environ.get("FASIRI_API_KEY", "")
            )
            if not self.api_key:
                raise AuthenticationError(
                    "No API key provided.\n"
                    "Option 1 - Fasiri Cloud: get a free key at https://api.fasiri-ai.com\n"
                    "           then pass: Fasiri(api_key='fsri_...')\n"
                    "Option 2 - Direct mode: use your own provider keys:\n"
                    "           from fasiri.providers import SunbirdProvider\n"
                    "           Fasiri(providers=[SunbirdProvider(api_key='eyJ...')])",
                    code="MISSING_API_KEY",
                )
            self._mode    = "cloud"
            self.base_url = (
                base_url
                or os.environ.get("FASIRI_BASE_URL", self.DEFAULT_BASE_URL)
            ).rstrip("/")

        self._async_client: Optional[httpx.AsyncClient] = None

    # ── Direct mode router (lazy init) ───────────────────────────────────────

    def _get_router(self):
        if self._router is None:
            from .providers.router import DirectRouter
            self._router = DirectRouter(self._providers)
        return self._router

    # ── Context manager (async) ───────────────────────────────────────────────

    async def __aenter__(self) -> "Fasiri":
        if self._mode == "cloud":
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers(),
                timeout=self._timeout,
            )
        return self

    async def __aexit__(self, *args) -> None:
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    # ── Internal helpers (cloud mode) ─────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
            "User-Agent":    "fasiri-python-sdk/1.1.0",
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
                body.get("message", "Provider error - please retry"),
                code=body.get("code", "PROVIDER_ERROR"),
                status_code=resp.status_code,
            )
        resp.raise_for_status()

    def _sync_post(self, path: str, json: Dict) -> Dict:
        with httpx.Client(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self._timeout,
        ) as client:
            resp = client.post(path, json=json)
        self._raise_for_error(resp)
        return resp.json()

    def _sync_get(self, path: str) -> Dict:
        with httpx.Client(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self._timeout,
        ) as client:
            resp = client.get(path)
        self._raise_for_error(resp)
        return resp.json()

    async def _async_post(self, path: str, json: Dict) -> Dict:
        client = self._async_client or httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self._timeout,
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
        Translate text to the target language.

        Works in both cloud and direct mode. In direct mode, the ``provider``
        parameter is ignored - routing is handled automatically based on which
        providers you configured.

        Parameters
        ----------
        text : str
            Text to translate. Max 5,000 characters (cloud) or 1,000 (Khaya direct).
        target : str
            Target language code e.g. ``"lug"``, ``"yo"``, ``"sw"``.
        source : str, optional
            Source language code. Auto-detected if omitted.
        provider : str, optional
            Cloud mode only: ``"auto"``, ``"sunbird"``, ``"khaya"``, or ``"huggingface"``.

        Returns
        -------
        TranslationResult

        Examples
        --------
        Cloud mode::

            result = client.translate("Good morning", target="lug")
            print(result)          # Wasuze otya
            print(result.provider) # sunbird

        Direct mode::

            result = client.translate("Good morning", target="lug")
            print(result)          # Wasuze otya
            print(result.provider) # sunbird
        """
        if self._mode == "direct":
            return self._direct_translate(text, target, source or "en")

        data = self._sync_post("/api/v1/translate", {
            "text":        text,
            "target_lang": target,
            "source_lang": source,
            "provider":    provider,
        })
        return self._parse_translation(data)

    def _direct_translate(
        self, text: str, target: str, source: str
    ) -> TranslationResult:
        """Translate using direct providers and normalise to TranslationResult."""
        result = self._get_router().translate(text, target, source)
        return TranslationResult(
            translated_text=result.translated_text,
            detected_source_lang=result.source_lang,
            target_lang=result.target_lang,
            model_used=result.model_used,
            provider=result.provider,
            quality_score=result.quality_score,
            latency_ms=result.latency_ms,
            characters_translated=len(text),
        )

    async def async_translate(
        self,
        text: str,
        target: str,
        source: Optional[str] = None,
        provider: str = "auto",
    ) -> TranslationResult:
        """Async version of :meth:`translate`."""
        if self._mode == "direct":
            result = await self._get_router().async_translate(
                text, target, source or "en"
            )
            return TranslationResult(
                translated_text=result.translated_text,
                detected_source_lang=result.source_lang,
                target_lang=result.target_lang,
                model_used=result.model_used,
                provider=result.provider,
                quality_score=result.quality_score,
                latency_ms=result.latency_ms,
                characters_translated=len(text),
            )

        data = await self._async_post("/api/v1/translate", {
            "text":        text,
            "target_lang": target,
            "source_lang": source,
            "provider":    provider,
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
        Translate multiple texts in a single call.

        In direct mode, each item is translated individually using the
        provider router (parallel async calls in async mode).

        Parameters
        ----------
        items : list of dict
            Each dict must have ``"id"``, ``"text"``, ``"target"``.
            Optionally include ``"source"`` for known source language.
        provider : str
            Cloud mode only. Default: ``"auto"``.

        Returns
        -------
        BatchResult

        Example
        -------
        ::

            results = client.translate_batch([
                {"id": "1", "text": "Hello",    "target": "lug"},
                {"id": "2", "text": "Thank you", "target": "yo"},
            ])
            for r in results.successful():
                print(r.id, r.translated_text)
        """
        if self._mode == "direct":
            return self._direct_batch(items)

        payload_items = [
            {
                "id":          item["id"],
                "text":        item["text"],
                "target_lang": item.get("target") or item.get("target_lang"),
                "source_lang": item.get("source") or item.get("source_lang"),
            }
            for item in items
        ]
        data = self._sync_post("/api/v1/translate/batch", {
            "items":    payload_items,
            "provider": provider,
        })
        return self._parse_batch(data)

    def _direct_batch(self, items: List[Dict]) -> BatchResult:
        """Sequential batch translation in direct mode."""
        t0 = time.monotonic()
        results = []
        succeeded = 0
        failed    = 0

        for item in items:
            item_id     = item["id"]
            text        = item["text"]
            target      = item.get("target") or item.get("target_lang", "")
            source      = item.get("source") or item.get("source_lang", "en")

            try:
                r = self._direct_translate(text, target, source)
                results.append(BatchItemResult(
                    id=item_id,
                    translated_text=r.translated_text,
                    detected_source_lang=r.detected_source_lang,
                    target_lang=r.target_lang,
                    model_used=r.model_used,
                    provider=r.provider,
                    quality_score=r.quality_score,
                    error=None,
                ))
                succeeded += 1
            except Exception as exc:
                results.append(BatchItemResult(
                    id=item_id,
                    translated_text=None,
                    detected_source_lang=None,
                    target_lang=target,
                    model_used=None,
                    provider=None,
                    quality_score=None,
                    error=str(exc),
                ))
                failed += 1

        total_ms = int((time.monotonic() - t0) * 1000)
        return BatchResult(
            results=results,
            total=len(items),
            succeeded=succeeded,
            failed=failed,
            total_latency_ms=total_ms,
        )

    async def async_translate_batch(
        self,
        items: List[Dict[str, str]],
        provider: str = "auto",
    ) -> BatchResult:
        """Async batch translation. Direct mode runs items concurrently."""
        if self._mode == "direct":
            return await self._async_direct_batch(items)

        payload_items = [
            {
                "id":          item["id"],
                "text":        item["text"],
                "target_lang": item.get("target") or item.get("target_lang"),
                "source_lang": item.get("source") or item.get("source_lang"),
            }
            for item in items
        ]
        data = await self._async_post("/api/v1/translate/batch", {
            "items":    payload_items,
            "provider": provider,
        })
        return self._parse_batch(data)

    async def _async_direct_batch(self, items: List[Dict]) -> BatchResult:
        """Concurrent async batch in direct mode."""
        import asyncio
        t0 = time.monotonic()

        async def _one(item: Dict) -> BatchItemResult:
            item_id = item["id"]
            text    = item["text"]
            target  = item.get("target") or item.get("target_lang", "")
            source  = item.get("source") or item.get("source_lang", "en")
            try:
                r = await self._get_router().async_translate(text, target, source)
                return BatchItemResult(
                    id=item_id,
                    translated_text=r.translated_text,
                    detected_source_lang=r.source_lang,
                    target_lang=r.target_lang,
                    model_used=r.model_used,
                    provider=r.provider,
                    quality_score=r.quality_score,
                    error=None,
                )
            except Exception as exc:
                return BatchItemResult(
                    id=item_id,
                    translated_text=None,
                    detected_source_lang=None,
                    target_lang=target,
                    model_used=None,
                    provider=None,
                    quality_score=None,
                    error=str(exc),
                )

        results   = await asyncio.gather(*[_one(item) for item in items])
        succeeded = sum(1 for r in results if r.success)
        failed    = sum(1 for r in results if not r.success)
        total_ms  = int((time.monotonic() - t0) * 1000)

        return BatchResult(
            results=list(results),
            total=len(items),
            succeeded=succeeded,
            failed=failed,
            total_latency_ms=total_ms,
        )

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

        In direct mode, only SunbirdProvider supports STT.

        Parameters
        ----------
        audio : bytes or str
            Raw audio bytes, or a file path to a WAV/MP3 file.
        language : str
            Language code of the audio e.g. ``"lug"``, ``"ach"``.

        Returns
        -------
        STTResult
        """
        import os as _os
        if isinstance(audio, str):
            filename = _os.path.basename(audio)
            with open(audio, "rb") as f:
                audio_bytes = f.read()
        else:
            audio_bytes = audio
            filename    = "audio.wav"

        if self._mode == "direct":
            # Find a provider that supports STT
            for p in self._providers:
                try:
                    r = p.speech_to_text(audio_bytes, language, filename)
                    return STTResult(
                        transcript=r.transcript,
                        detected_lang=r.detected_lang,
                        language=r.language,
                        model_used=r.model_used,
                        provider=r.provider,
                        latency_ms=r.latency_ms,
                    )
                except NotImplementedError:
                    continue
            raise NotImplementedError(
                "None of your configured providers support Speech-to-Text. "
                "Add SunbirdProvider to enable STT."
            )

        with httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "User-Agent": "fasiri-python-sdk/1.1.0"},
            timeout=max(self._timeout, 60),
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

        In direct mode, only SunbirdProvider supports TTS.

        Parameters
        ----------
        text : str
            Text to synthesise.
        language : str
            Language code e.g. ``"lug"``, ``"ach"``.
        voice_id : int, optional
            Sunbird voice ID. Auto-selected if omitted.

        Returns
        -------
        TTSResult
        """
        if self._mode == "direct":
            for p in self._providers:
                try:
                    r = p.text_to_speech(text, language)
                    return TTSResult(
                        audio_url=r.audio_url,
                        audio_base64=r.audio_base64,
                        content_type=r.content_type,
                        language=r.language,
                        model_used=r.model_used,
                        provider=r.provider,
                        latency_ms=r.latency_ms,
                    )
                except NotImplementedError:
                    continue
            raise NotImplementedError(
                "None of your configured providers support Text-to-Speech. "
                "Add SunbirdProvider to enable TTS."
            )

        data = self._sync_post("/api/v1/speech/tts", {
            "text":     text,
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

    # American spelling alias
    synthesize = synthesise

    # ── Languages ─────────────────────────────────────────────────────────────

    def languages(self) -> List[Language]:
        """
        Return all supported languages with their capabilities.

        In direct mode, returns the combined language list of all
        configured providers.

        Returns
        -------
        list of Language
        """
        if self._mode == "direct":
            return self._direct_languages()

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

    def _direct_languages(self) -> List[Language]:
        """Build a language list from direct provider capabilities."""
        seen: Dict[str, Language] = {}
        for p in self._providers:
            for code in p.supported_languages:
                if code not in seen:
                    seen[code] = Language(
                        code=code,
                        name=code.upper(),
                        native_name=code,
                        region="Africa",
                        family="",
                        supports_translation=True,
                        supports_stt=False,
                        supports_tts=False,
                        tts_voice_id=None,
                        best_provider=p.name,
                        quality_score=0.80,
                    )
        return list(seen.values())

    def translation_languages(self) -> List[Language]:
        """Return only languages that support translation."""
        return [l for l in self.languages() if l.supports_translation]

    def speech_languages(self) -> List[Language]:
        """Return only languages that support STT or TTS."""
        return [l for l in self.languages() if l.supports_stt or l.supports_tts]

    # ── Repr ─────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        if self._mode == "direct":
            names = [p.name for p in self._providers]
            return f"<Fasiri direct mode providers={names}>"
        return f"<Fasiri cloud mode key={self.api_key[:12]}...>"
