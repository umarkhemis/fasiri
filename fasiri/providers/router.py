"""
Fasiri - Direct provider router.

Selects the best provider from a list for a given language pair,
with automatic fallback if the primary provider fails.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from .base import BaseDirectProvider, DirectTranslationResult

logger = logging.getLogger(__name__)


class DirectRouter:
    """
    Routes translation requests to the best available provider.

    Tries providers in the order they were passed. If a provider does
    not support the language pair, it is skipped. If it supports the
    pair but fails, the next one is tried.

    Parameters
    ----------
    providers : list of BaseDirectProvider
        Providers to route between, in priority order.
    """

    def __init__(self, providers: List[BaseDirectProvider]) -> None:
        if not providers:
            raise ValueError("At least one provider is required.")
        self._providers = providers

    def _candidates(self, source_lang: str, target_lang: str) -> List[BaseDirectProvider]:
        """Return providers that support this language pair, in order."""
        return [
            p for p in self._providers
            if p.supports(source_lang, target_lang)
        ]

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """
        Translate using the best available provider.

        Tries each compatible provider in order. Returns the first
        successful result. Raises if all providers fail.
        """
        candidates = self._candidates(source_lang, target_lang)

        if not candidates:
            available = [p.name for p in self._providers]
            raise ValueError(
                f"No provider supports '{source_lang}' -> '{target_lang}'. "
                f"Configured providers: {available}. "
                f"Check that the language pair is supported by at least one "
                f"of your providers."
            )

        last_error: Optional[Exception] = None

        for provider in candidates:
            try:
                result = provider.translate(text, target_lang, source_lang)
                if len(candidates) > 1:
                    logger.debug(
                        "Direct router: %s -> %s via %s",
                        source_lang, target_lang, provider.name,
                    )
                return result
            except Exception as exc:
                logger.warning(
                    "Direct provider '%s' failed for %s -> %s: %s - trying next",
                    provider.name, source_lang, target_lang, exc,
                )
                last_error = exc

        raise RuntimeError(
            f"All providers failed for '{source_lang}' -> '{target_lang}'. "
            f"Last error: {last_error}"
        ) from last_error

    async def async_translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """Async version of translate()."""
        candidates = self._candidates(source_lang, target_lang)

        if not candidates:
            raise ValueError(
                f"No provider supports '{source_lang}' -> '{target_lang}'."
            )

        last_error: Optional[Exception] = None

        for provider in candidates:
            try:
                return await provider.async_translate(text, target_lang, source_lang)
            except Exception as exc:
                logger.warning(
                    "Direct provider '%s' failed for %s -> %s: %s",
                    provider.name, source_lang, target_lang, exc,
                )
                last_error = exc

        raise RuntimeError(
            f"All providers failed for '{source_lang}' -> '{target_lang}'. "
            f"Last error: {last_error}"
        ) from last_error
