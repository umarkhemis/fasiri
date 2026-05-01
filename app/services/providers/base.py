"""
Fasiri – Base provider interface.

All provider adapters must extend BaseProvider and implement translate().
Speech methods are optional – providers that don't support them raise NotImplementedError.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TranslationResult:
    translated_text: str
    model_used: str
    provider: str
    quality_score: float
    latency_ms: int


@dataclass
class STTResult:
    transcript: str
    detected_lang: Optional[str]
    model_used: str
    provider: str
    latency_ms: int


@dataclass
class TTSResult:
    audio_url: Optional[str]
    audio_base64: Optional[str]
    content_type: str
    model_used: str
    provider: str
    latency_ms: int


class BaseProvider(ABC):
    """Abstract base for all translation/speech providers."""

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model_id: str,
    ) -> TranslationResult:
        ...

    async def speech_to_text(
        self,
        audio_bytes: bytes,
        language: str,
        filename: str = "audio.wav",
    ) -> STTResult:
        raise NotImplementedError(f"{self.__class__.__name__} does not support STT")

    async def text_to_speech(
        self,
        text: str,
        language: str,
        voice_id: Optional[int] = None,
    ) -> TTSResult:
        raise NotImplementedError(f"{self.__class__.__name__} does not support TTS")
