"""
Fasiri - Pydantic request / response schemas.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Any

from pydantic import BaseModel, Field, field_validator


# ── Shared enums ─────────────────────────────────────────────────────────────

class Provider(str, Enum):
    sunbird = "sunbird"
    huggingface = "huggingface"
    auto = "auto"   # let Fasiri choose


# ── Translation ───────────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000,
                      description="Text to translate (max 5 000 chars).")
    target_lang: str = Field(..., description="BCP-47 target language code, e.g. 'sw'.")
    source_lang: Optional[str] = Field(
        default=None,
        description="Source language code. Omit to auto-detect."
    )
    provider: Provider = Field(
        default=Provider.auto,
        description="Force a specific provider, or 'auto' for best-model routing."
    )

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class TranslateResponse(BaseModel):
    translated_text: str
    detected_source_lang: str
    target_lang: str
    model_used: str
    provider: str
    quality_score: float = Field(ge=0.0, le=1.0)
    latency_ms: int
    characters_translated: int


# ── Batch translation ─────────────────────────────────────────────────────────

class BatchItem(BaseModel):
    id: str = Field(..., description="Client-supplied ID to match results to inputs.")
    text: str = Field(..., min_length=1, max_length=5000)
    target_lang: str
    source_lang: Optional[str] = None


class BatchTranslateRequest(BaseModel):
    items: List[BatchItem] = Field(..., min_length=1, max_length=50,
                                   description="Up to 50 translation items per batch.")
    provider: Provider = Field(default=Provider.auto)


class BatchItemResult(BaseModel):
    id: str
    translated_text: Optional[str] = None
    detected_source_lang: Optional[str] = None
    target_lang: str
    model_used: Optional[str] = None
    provider: Optional[str] = None
    quality_score: Optional[float] = None
    error: Optional[str] = None   # null on success


class BatchTranslateResponse(BaseModel):
    results: List[BatchItemResult]
    total: int
    succeeded: int
    failed: int
    total_latency_ms: int


# ── Speech ────────────────────────────────────────────────────────────────────

class SpeechToTextResponse(BaseModel):
    transcript: str
    detected_lang: Optional[str] = None
    language: str
    model_used: str
    provider: str
    latency_ms: int
    audio_duration_seconds: Optional[float] = None


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(..., description="Language code, e.g. 'lug'.")
    voice_id: Optional[int] = Field(
        default=None,
        description="Sunbird TTS voice ID (see /languages endpoint for IDs)."
    )


class TextToSpeechResponse(BaseModel):
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    content_type: str = "audio/mpeg"
    language: str
    model_used: str
    provider: str
    latency_ms: int


# ── Languages ─────────────────────────────────────────────────────────────────

class LanguageDetail(BaseModel):
    code: str
    name: str
    native_name: str
    region: str
    family: str
    supports_translation: bool
    supports_stt: bool
    supports_tts: bool
    tts_voice_id: Optional[int] = None
    best_provider: str
    quality_score: float


class LanguagesResponse(BaseModel):
    languages: List[LanguageDetail]
    total: int


# ── API key management ────────────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100,
                      description="A human-readable label for this key.")


class CreateKeyResponse(BaseModel):
    api_key: str = Field(...,
        description="Your API key. Store it securely - it will not be shown again.")
    name: str
    expires_at: str
    note: str = "Store this key securely. It will NOT be shown again."


class KeyInfoResponse(BaseModel):
    name: str
    created_at: str
    expires_at: str
    requests_total: int


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
