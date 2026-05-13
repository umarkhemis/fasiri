"""
Fasiri - HuggingFace direct provider adapter.

Uses Helsinki-NLP opus-mt models via the HuggingFace Inference API.

Get a free token:
    1. Go to https://huggingface.co/settings/tokens
    2. Create a new token (read access is enough)
    3. Copy it - starts with "hf_"

Supported language pairs (verified deployed on hf-inference):
    en-sw, sw-en  (Swahili)
    en-fr, fr-en  (French)
    en-ar, ar-en  (Arabic)
    en-af, af-en  (Afrikaans)
    yo-en         (Yoruba -> English only)

Note: facebook/nllb-200-distilled-600M was removed from hf-inference
in 2025 and is no longer available on the free tier.

Docs: https://huggingface.co/docs/api-inference
"""
from __future__ import annotations

import time

import httpx

from .base import BaseDirectProvider, DirectTranslationResult


_HF_BASE = "https://router.huggingface.co/hf-inference/models"

# Verified deployed models on HF free tier
_MODEL_MAP: dict[tuple[str, str], str] = {
    ("en", "sw"): "Helsinki-NLP/opus-mt-en-sw",
    ("sw", "en"): "Helsinki-NLP/opus-mt-sw-en",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("en", "ar"): "Helsinki-NLP/opus-mt-en-ar",
    ("ar", "en"): "Helsinki-NLP/opus-mt-ar-en",
    ("en", "af"): "Helsinki-NLP/opus-mt-en-af",
    ("af", "en"): "Helsinki-NLP/opus-mt-af-en",
    ("yo", "en"): "Helsinki-NLP/opus-mt-yo-en",
}

# Multilingual fallbacks
_EN_TO_MUL = "Helsinki-NLP/opus-mt-en-mul"
_MUL_TO_EN = "Helsinki-NLP/opus-mt-mul-en"


class HuggingFaceProvider(BaseDirectProvider):
    """
    Direct adapter for HuggingFace Inference API (free tier).

    Uses verified Helsinki-NLP opus-mt models. Falls back to multilingual
    models for unsupported pairs.

    Parameters
    ----------
    api_key : str
        Your HuggingFace token (starts with "hf_").
        Get one at https://huggingface.co/settings/tokens
    timeout : int
        Request timeout in seconds. Default: 30

    Example
    -------
    ::

        from fasiri.providers import HuggingFaceProvider

        provider = HuggingFaceProvider(api_key="hf_...")
        result = provider.translate("Good morning", target_lang="sw")
        print(result)  # Habari ya asubuhi
    """

    def __init__(self, api_key: str, timeout: int = 30) -> None:
        if not api_key:
            raise ValueError(
                "HuggingFaceProvider requires an api_key.\n"
                "Get a free token at: https://huggingface.co/settings/tokens"
            )
        self._key     = api_key
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "huggingface"

    @property
    def supported_languages(self) -> set[str]:
        return {lang for pair in _MODEL_MAP for lang in pair}

    @property
    def supported_pairs(self) -> set[tuple[str, str]]:
        return set(_MODEL_MAP.keys())

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}"}

    def _pick_model(self, source_lang: str, target_lang: str) -> tuple[str, float]:
        """Return (model_id, quality_score)."""
        dedicated = _MODEL_MAP.get((source_lang, target_lang))
        if dedicated:
            return dedicated, 0.80
        if target_lang == "en":
            return _MUL_TO_EN, 0.60
        return _EN_TO_MUL, 0.58

    def _parse_response(self, data: list | dict) -> str:
        if isinstance(data, list) and data:
            return data[0].get("translation_text", "")
        if isinstance(data, dict):
            return data.get("translation_text", str(data))
        return str(data)

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """
        Translate text using HuggingFace Helsinki-NLP models.

        Parameters
        ----------
        text : str
            Text to translate.
        target_lang : str
            Target language code e.g. "sw", "fr", "ar", "af".
        source_lang : str
            Source language code. Default: "en".

        Returns
        -------
        DirectTranslationResult
        """
        model, quality = self._pick_model(source_lang, target_lang)
        t0 = time.monotonic()

        resp = httpx.post(
            f"{_HF_BASE}/{model}",
            json={"inputs": text},
            headers=self._headers(),
            timeout=self._timeout,
        )

        if resp.status_code == 401:
            raise PermissionError(
                "HuggingFace authentication failed. Check your token.\n"
                "Get one at: https://huggingface.co/settings/tokens"
            )

        if resp.status_code == 410:
            raise RuntimeError(
                f"Model '{model}' is no longer available on hf-inference. "
                "This model was deprecated by HuggingFace."
            )

        if not resp.is_success:
            body = resp.text
            raise RuntimeError(
                f"HuggingFace returned {resp.status_code}: {body[:200]}"
            )

        data = resp.json()
        translated = self._parse_response(data)
        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectTranslationResult(
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model_used=model,
            provider="huggingface",
            quality_score=quality,
            latency_ms=latency_ms,
        )

    async def async_translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """Async version of translate()."""
        model, quality = self._pick_model(source_lang, target_lang)
        t0 = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{_HF_BASE}/{model}",
                json={"inputs": text},
                headers=self._headers(),
            )

        if resp.status_code == 401:
            raise PermissionError("HuggingFace authentication failed.")

        resp.raise_for_status()

        data = resp.json()
        translated = self._parse_response(data)
        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectTranslationResult(
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model_used=model,
            provider="huggingface",
            quality_score=quality,
            latency_ms=latency_ms,
        )
