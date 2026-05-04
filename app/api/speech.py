"""
Fasiri – Speech endpoints.

POST /api/v1/speech/stt  – Speech-to-Text  (multipart audio upload)
POST /api/v1/speech/tts  – Text-to-Speech  (returns audio URL or base64)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.middleware.auth import require_api_key
from app.middleware.ratelimit import check_rate_limit
from app.schemas.translate import (
    SpeechToTextResponse,
    TextToSpeechRequest,
    TextToSpeechResponse,
)
from app.services.providers.sunbird import SunbirdProvider

router = APIRouter(prefix="/speech", tags=["Speech"])
logger = logging.getLogger(__name__)

# Speech is Sunbird-only for now
_provider = SunbirdProvider()

_SUPPORTED_STT = {"lug", "nyn", "lgg", "ach", "teo", "sw", "en", "rw", "xog", "myx"}
_SUPPORTED_TTS = {"ach", "teo", "nyn", "lgg", "sw", "lug"}
_SUPPORTED_AUDIO = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/webm"}
_MAX_AUDIO_MB = 10


# ── STT ───────────────────────────────────────────────────────────────────────

@router.post(
    "/stt",
    response_model=SpeechToTextResponse,
    summary="Speech to Text",
    description=(
        "Transcribe an audio file in a supported African language. "
        f"Supported languages: {sorted(_SUPPORTED_STT)}. "
        f"Max file size: {_MAX_AUDIO_MB} MB. "
        "Accepts WAV, MP3, OGG, WebM."
    ),
)
async def speech_to_text(
    audio: UploadFile = File(..., description="Audio file to transcribe."),
    language: str = Form(..., description="Language code of the audio, e.g. 'lug'."),
    key_record: dict = Depends(require_api_key),
) -> SpeechToTextResponse:
    check_rate_limit(key_record, "speech")

    # Validate language
    if language not in _SUPPORTED_STT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNSUPPORTED_LANGUAGE",
                "message": f"STT is not supported for '{language}'. "
                           f"Supported: {sorted(_SUPPORTED_STT)}",
            },
        )

    # Validate content type
    ct = audio.content_type or ""
    if ct not in _SUPPORTED_AUDIO and not ct.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "UNSUPPORTED_MEDIA_TYPE",
                "message": f"Unsupported audio format '{ct}'. "
                           f"Supported: WAV, MP3, OGG, WebM.",
            },
        )

    audio_bytes = await audio.read()

    # Validate file size
    if len(audio_bytes) > _MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"Audio file exceeds {_MAX_AUDIO_MB} MB limit.",
            },
        )

    try:
        result = await _provider.speech_to_text(
            audio_bytes=audio_bytes,
            language=language,
            filename=audio.filename or "audio.wav",
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "NOT_IMPLEMENTED",
                    "message": "STT not available for this provider."},
        )
    except Exception as exc:
        logger.error("STT error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "PROVIDER_ERROR", "message": str(exc)},
        )

    return SpeechToTextResponse(
        transcript=result.transcript,
        detected_lang=result.detected_lang,
        language=language,
        model_used=result.model_used,
        provider=result.provider,
        latency_ms=result.latency_ms,
    )


# ── TTS ───────────────────────────────────────────────────────────────────────

@router.post(
    "/tts",
    response_model=TextToSpeechResponse,
    summary="Text to Speech",
    description=(
        "Convert text to audio in a supported African language. "
        f"Supported languages: {sorted(_SUPPORTED_TTS)}. "
        "Returns a signed audio URL or base64-encoded audio."
    ),
)
async def text_to_speech(
    body: TextToSpeechRequest,
    key_record: dict = Depends(require_api_key),
) -> TextToSpeechResponse:
    check_rate_limit(key_record, "speech")

    if body.language not in _SUPPORTED_TTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNSUPPORTED_LANGUAGE",
                "message": f"TTS is not supported for '{body.language}'. "
                           f"Supported: {sorted(_SUPPORTED_TTS)}",
            },
        )

    try:
        result = await _provider.text_to_speech(
            text=body.text,
            language=body.language,
            voice_id=body.voice_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_VOICE", "message": str(exc)},
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "NOT_IMPLEMENTED",
                    "message": "TTS not available for this provider."},
        )
    except Exception as exc:
        logger.error("TTS error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "PROVIDER_ERROR", "message": str(exc)},
        )

    return TextToSpeechResponse(
        audio_url=result.audio_url,
        audio_base64=result.audio_base64,
        content_type=result.content_type,
        language=body.language,
        model_used=result.model_used,
        provider=result.provider,
        latency_ms=result.latency_ms,
    )
