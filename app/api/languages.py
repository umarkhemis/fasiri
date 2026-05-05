"""
Fasiri - Languages endpoint.

GET /api/v1/languages  - list all supported languages with capabilities
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.registry import LANGUAGE_REGISTRY, get_model_fast
from app.schemas.translate import LanguageDetail, LanguagesResponse
router = APIRouter(prefix="/languages", tags=["Languages"])

_STT_LANGS = {"lug", "nyn", "lgg", "ach", "teo", "sw", "en", "rw", "xog", "myx"}

_TTS_VOICE_IDS: dict[str, int] = {
    "ach": 241, "teo": 242, "nyn": 243,
    "lgg": 245, "sw": 246, "lug": 248,
}


@router.get(
    "",
    response_model=LanguagesResponse,
    summary="List supported languages",
    description=(
        "Returns all languages supported by Fasiri with details on "
        "translation, speech-to-text, and text-to-speech capabilities."
    ),
)
async def list_languages() -> LanguagesResponse:
    details = []
    for code, info in LANGUAGE_REGISTRY.items():
        # Get best model for this language (en → lang as representative pair)
        try:
            entry = get_model_fast("en", code) if code != "en" else get_model_fast("sw", "en")
        except Exception:
            entry = None

        details.append(
            LanguageDetail(
                code=code,
                name=info.name,
                native_name=info.native_name,
                region=info.region,
                family=info.family,
                supports_translation=True,
                supports_stt=code in _STT_LANGS,
                supports_tts=code in _TTS_VOICE_IDS,
                tts_voice_id=_TTS_VOICE_IDS.get(code),
                best_provider=entry.provider if entry else "huggingface",
                quality_score=entry.quality_score if entry else 0.60,
            )
        )

    # Sort: best quality first, then alphabetically
    details.sort(key=lambda d: (-d.quality_score, d.name))

    return LanguagesResponse(languages=details, total=len(details))
