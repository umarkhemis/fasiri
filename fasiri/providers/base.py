"""
Fasiri - Base class for direct provider adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DirectTranslationResult:
    translated_text: str
    source_lang: str
    target_lang: str
    model_used: str
    provider: str
    quality_score: float
    latency_ms: int

    def __str__(self) -> str:
        return self.translated_text


@dataclass
class DirectSTTResult:
    transcript: str
    detected_lang: Optional[str]
    language: str
    model_used: str
    provider: str
    latency_ms: int

    def __str__(self) -> str:
        return self.transcript


@dataclass
class DirectTTSResult:
    audio_url: Optional[str]
    audio_base64: Optional[str]
    content_type: str
    language: str
    model_used: str
    provider: str
    latency_ms: int


class BaseDirectProvider(ABC):
    """
    Abstract base class for direct provider adapters.

    All providers must implement translate(). STT and TTS are optional -
    providers that do not support them should raise NotImplementedError.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name e.g. 'sunbird', 'khaya', 'huggingface'."""

    @property
    @abstractmethod
    def supported_languages(self) -> set[str]:
        """Set of AfriLang language codes this provider supports."""

    @property
    @abstractmethod
    def supported_pairs(self) -> set[tuple[str, str]]:
        """
        Set of (source, target) pairs this provider supports.
        Return an empty set if the provider supports all pairs for its languages.
        """

    def supports(self, source_lang: str, target_lang: str) -> bool:
        """Return True if this provider can translate this pair."""
        pairs = self.supported_pairs
        if pairs:
            return (source_lang, target_lang) in pairs
        return source_lang in self.supported_languages or target_lang in self.supported_languages

    @abstractmethod
    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """Translate text. Must be implemented by all providers."""

    async def async_translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> DirectTranslationResult:
        """Async translate. Default implementation runs sync version."""
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self.translate, text, target_lang, source_lang
        )

    def speech_to_text(self, audio: bytes, language: str) -> DirectSTTResult:
        raise NotImplementedError(f"{self.name} does not support Speech-to-Text.")

    def text_to_speech(self, text: str, language: str) -> DirectTTSResult:
        raise NotImplementedError(f"{self.name} does not support Text-to-Speech.")
