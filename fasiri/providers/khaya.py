"""
Fasiri - Khaya AI direct provider adapter.

GhanaNLP's Khaya API v2 for West and East African language translation.

Register and get your key:
    1. Go to https://translation.ghananlp.org/signup
    2. Create an account
    3. Go to your dashboard and copy your subscription key

Supported languages:
    yo (Yoruba), tw (Twi), ee (Ewe), gaa (Ga), fat (Fante),
    dag (Dagbani), gur (Gurune), ki (Kikuyu), luo (Luo),
    mer (Kimeru), kus (Kusaal), en (English)

Auth: Ocp-Apim-Subscription-Key header (NOT a Bearer token)

Docs: https://translation.ghananlp.org/apis
"""
from __future__ import annotations

import time

import httpx

from .base import BaseDirectProvider, DirectTranslationResult


# AfriLang (src, tgt) -> Khaya lang code
_PAIR_MAP: dict[tuple[str, str], str] = {
    # English -> African
    ("en", "yo"):  "en-yo",
    ("en", "tw"):  "en-tw",
    ("en", "ee"):  "en-ee",
    ("en", "gaa"): "en-gaa",
    ("en", "fat"): "en-fat",
    ("en", "dag"): "en-dag",
    ("en", "gur"): "en-gur",
    ("en", "ki"):  "en-ki",
    ("en", "luo"): "en-luo",
    ("en", "mer"): "en-mer",
    ("en", "kus"): "en-kus",
    # African -> English
    ("yo",  "en"): "yo-en",
    ("tw",  "en"): "tw-en",
    ("ee",  "en"): "ee-en",
    ("gaa", "en"): "gaa-en",
    ("fat", "en"): "fat-en",
    ("dag", "en"): "dag-en",
    ("gur", "en"): "gur-en",
    ("ki",  "en"): "ki-en",
    ("luo", "en"): "luo-en",
    ("mer", "en"): "mer-en",
    ("kus", "en"): "kus-en",
}

_BASE_URL = "https://translation-api.ghananlp.org/v2/translate"
_MAX_CHARS = 1000


class KhayaProvider(BaseDirectProvider):
    """
    Direct adapter for GhanaNLP / Khaya AI Translation API v2.

    Parameters
    ----------
    api_key : str
        Your Khaya subscription key from translation.ghananlp.org
    timeout : int
        Request timeout in seconds. Default: 30

    Note
    ----
    Khaya uses Ocp-Apim-Subscription-Key header, not a Bearer token.

    Example
    -------
    ::

        from fasiri.providers import KhayaProvider

        provider = KhayaProvider(api_key="your-subscription-key")
        result = provider.translate("Good morning", target_lang="yo")
        print(result)  # Bawo ni
    """

    def __init__(self, api_key: str, timeout: int = 30) -> None:
        if not api_key:
            raise ValueError(
                "KhayaProvider requires an api_key.\n"
                "Get one at: https://translation.ghananlp.org/signup"
            )
        self._key     = api_key
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "khaya"

    @property
    def supported_languages(self) -> set[str]:
        return {lang for pair in _PAIR_MAP for lang in pair}

    @property
    def supported_pairs(self) -> set[tuple[str, str]]:
        return set(_PAIR_MAP.keys())

    def _headers(self) -> dict[str, str]:
        return {
            "Ocp-Apim-Subscription-Key": self._key,
            "Content-Type": "application/json",
        }

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """
        Translate text using Khaya AI.

        Parameters
        ----------
        text : str
            Text to translate. Maximum 1,000 characters.
        target_lang : str
            Target language code e.g. "yo", "tw", "ee", "dag".
        source_lang : str
            Source language code. Default: "en".

        Returns
        -------
        DirectTranslationResult
        """
        pair = (source_lang, target_lang)
        lang_code = _PAIR_MAP.get(pair)

        if not lang_code:
            supported = sorted(_PAIR_MAP.keys())
            raise ValueError(
                f"Khaya does not support '{source_lang}' -> '{target_lang}'. "
                f"Supported pairs: {supported}"
            )

        # Enforce Khaya's character limit
        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS]

        t0 = time.monotonic()

        resp = httpx.post(
            _BASE_URL,
            json={"in": text, "lang": lang_code},
            headers=self._headers(),
            timeout=self._timeout,
        )

        if resp.status_code in {401, 403}:
            raise PermissionError(
                "Khaya authentication failed. Check your subscription key.\n"
                "Get one at: https://translation.ghananlp.org/signup"
            )

        if resp.status_code == 400:
            body = resp.json() if resp.content else {}
            raise ValueError(
                f"Khaya rejected the request for '{lang_code}': "
                f"{body.get('message', resp.text)}"
            )

        resp.raise_for_status()

        # Khaya returns a plain string (strip surrounding quotes if present)
        translated = resp.text.strip().strip('"')
        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectTranslationResult(
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model_used="khaya/translate-v2",
            provider="khaya",
            quality_score=0.85,
            latency_ms=latency_ms,
        )

    async def async_translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """Async version of translate()."""
        pair = (source_lang, target_lang)
        lang_code = _PAIR_MAP.get(pair)

        if not lang_code:
            raise ValueError(
                f"Khaya does not support '{source_lang}' -> '{target_lang}'."
            )

        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS]

        t0 = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                _BASE_URL,
                json={"in": text, "lang": lang_code},
                headers=self._headers(),
            )

        if resp.status_code in {401, 403}:
            raise PermissionError("Khaya authentication failed.")

        resp.raise_for_status()

        translated = resp.text.strip().strip('"')
        latency_ms = int((time.monotonic() - t0) * 1000)

        return DirectTranslationResult(
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model_used="khaya/translate-v2",
            provider="khaya",
            quality_score=0.85,
            latency_ms=latency_ms,
        )
