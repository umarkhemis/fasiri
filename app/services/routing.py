
"""
Fasiri – Routing service.

Selects the best provider + model for a given language pair,
with automatic fallback if the primary provider fails.

Provider priority:
  1. Sunbird   — Ugandan languages (lug, ach, teo, nyn, lgg ↔ en)
  2. Khaya     — West/East African languages (yo, tw, ee, gaa, fat, dag, ki, gur, luo, mer, kus ↔ en)
  3. HuggingFace — Everything else (Helsinki models + multilingual fallback)

Fallback chain:
  - Sunbird fails for Ugandan langs   → HuggingFace (Helsinki mul, poor but last resort)
  - Khaya fails for its langs         → HuggingFace _pick_model() decides
  - HuggingFace fails                 → 503
"""
from __future__ import annotations

import logging
from typing import Optional

from app.core.registry import ModelEntry, get_model_fast
from app.schemas.translate import Provider
from app.services.providers.base import BaseProvider, TranslationResult
from app.services.providers.huggingface import HuggingFaceProvider
from app.services.providers.khaya import KhayaProvider, supports_pair, KHAYA_LANGS
from app.services.providers.sunbird import SunbirdProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

# Ugandan languages owned by Sunbird
_SUNBIRD_LANGS = {"lug", "ach", "teo", "nyn", "lgg", "en"}

# Lazy singleton providers (one instance per process)
_SUNBIRD: Optional[SunbirdProvider] = None
_HUGGINGFACE: Optional[HuggingFaceProvider] = None
_KHAYA: Optional[KhayaProvider] = None


def _sunbird() -> SunbirdProvider:
    global _SUNBIRD
    if _SUNBIRD is None:
        _SUNBIRD = SunbirdProvider()
    return _SUNBIRD


def _huggingface() -> HuggingFaceProvider:
    global _HUGGINGFACE
    if _HUGGINGFACE is None:
        _HUGGINGFACE = HuggingFaceProvider()
    return _HUGGINGFACE


def _khaya() -> KhayaProvider:
    global _KHAYA
    if _KHAYA is None:
        _KHAYA = KhayaProvider()
    return _KHAYA


def _get_provider(provider_id: str) -> BaseProvider:
    if provider_id == "sunbird":
        return _sunbird()
    if provider_id == "khaya":
        return _khaya()
    return _huggingface()


def _is_sunbird_pair(source_lang: str, target_lang: str) -> bool:
    """Both langs are in Sunbird's Ugandan set."""
    return source_lang in _SUNBIRD_LANGS and target_lang in _SUNBIRD_LANGS


def _best_provider_for(source_lang: str, target_lang: str) -> str:
    """
    Return the best provider ID for a language pair,
    used when preferred_provider is Provider.auto.
    """
    if _is_sunbird_pair(source_lang, target_lang):
        return "sunbird"
    if supports_pair(source_lang, target_lang):
        return "khaya"
    return "huggingface"


async def route_translation(
    text: str,
    source_lang: str,
    target_lang: str,
    preferred_provider: Provider = Provider.auto,
) -> TranslationResult:
    """
    Translate text from source_lang to target_lang.

    Provider selection:
      - Provider.auto → best provider for the language pair
      - Otherwise     → caller's choice, with fallback on failure
    """
    # 1. Select primary provider
    if preferred_provider != Provider.auto:
        provider_id = preferred_provider.value
    else:
        # Use registry for model metadata, but override provider with our routing logic
        provider_id = _best_provider_for(source_lang, target_lang)

    entry: ModelEntry = get_model_fast(source_lang, target_lang)
    primary_provider = _get_provider(provider_id)

    # 2. Attempt primary
    try:
        return await primary_provider.translate(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            model_id=entry.model_id,
        )
    except Exception as exc:
        logger.error(
            "Primary provider '%s' failed for %s→%s: %s – falling back",
            provider_id, source_lang, target_lang, exc,
        )

    # 3. Fallback strategy
    try:
        if provider_id == "sunbird":
            # Sunbird is down — try Khaya if it supports the pair, else HuggingFace
            if supports_pair(source_lang, target_lang):
                logger.info("Sunbird down — trying Khaya for %s→%s", source_lang, target_lang)
                return await _khaya().translate(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    model_id=entry.model_id,
                )
            else:
                logger.info("Sunbird down — falling back to HuggingFace for %s→%s", source_lang, target_lang)
                return await _huggingface().translate(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    model_id=settings.default_model_id,
                )

        elif provider_id == "khaya":
            # Khaya is down — fall back to HuggingFace
            logger.info("Khaya down — falling back to HuggingFace for %s→%s", source_lang, target_lang)
            return await _huggingface().translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                model_id=settings.default_model_id,
            )

        else:
            # HuggingFace was primary and failed — nothing left
            raise RuntimeError(f"HuggingFace failed for {source_lang}→{target_lang}")

    except Exception as exc2:
        logger.error(
            "Fallback also failed for %s→%s: %s", source_lang, target_lang, exc2
        )
        raise RuntimeError(
            f"All providers failed for {source_lang}→{target_lang}. "
            f"Last error: {exc2}"
        ) from exc2





























# """
# Fasiri – Routing service.

# Selects the best provider + model for a given language pair,
# with automatic fallback if the primary provider fails.

# Fallback chain:
#   1. Best model for the pair (highest quality_score)
#   2. NLLB-200 via HuggingFace (universal fallback)
# """
# from __future__ import annotations

# import logging
# from typing import Optional

# from app.core.registry import ModelEntry, get_model_fast
# from app.schemas.translate import Provider
# from app.services.providers.base import BaseProvider, TranslationResult
# from app.services.providers.huggingface import HuggingFaceProvider
# from app.services.providers.sunbird import SunbirdProvider
# from app.core.config import settings

# logger = logging.getLogger(__name__)

# # Lazy singleton providers (one instance per process)
# _SUNBIRD: Optional[SunbirdProvider] = None
# _HUGGINGFACE: Optional[HuggingFaceProvider] = None


# def _sunbird() -> SunbirdProvider:
#     global _SUNBIRD
#     if _SUNBIRD is None:
#         _SUNBIRD = SunbirdProvider()
#     return _SUNBIRD


# def _huggingface() -> HuggingFaceProvider:
#     global _HUGGINGFACE
#     if _HUGGINGFACE is None:
#         _HUGGINGFACE = HuggingFaceProvider()
#     return _HUGGINGFACE


# def _get_provider(provider_id: str) -> BaseProvider:
#     if provider_id == "sunbird":
#         return _sunbird()
#     return _huggingface()


# async def route_translation(
#     text: str,
#     source_lang: str,
#     target_lang: str,
#     preferred_provider: Provider = Provider.auto,
# ) -> TranslationResult:
#     """
#     Translate text from source_lang to target_lang.

#     If preferred_provider is Provider.auto, selects the highest-quality model.
#     Falls back to NLLB-200 if the primary provider raises an exception.
#     """
#     # 1. Select primary model
#     entry: ModelEntry = get_model_fast(source_lang, target_lang)

#     # Override provider if caller specified one
#     if preferred_provider != Provider.auto:
#         provider_id = preferred_provider.value
#     else:
#         provider_id = entry.provider

#     primary_provider = _get_provider(provider_id)

#     # 2. Attempt primary
#     try:
#         return await primary_provider.translate(
#             text=text,
#             source_lang=source_lang,
#             target_lang=target_lang,
#             model_id=entry.model_id,
#         )
#     except Exception as exc:
#         logger.error(
#             "Primary provider '%s' failed for %s→%s: %s – falling back to NLLB",
#             provider_id, source_lang, target_lang, exc,
#         )

#     # 3. Fallback: NLLB-200 via HuggingFace
#     fallback_model = settings.default_model_id
#     try:
#         return await _huggingface().translate(
#             text=text,
#             source_lang=source_lang,
#             target_lang=target_lang,
#             model_id=fallback_model,
#         )
#     except Exception as exc2:
#         logger.error("NLLB fallback also failed: %s", exc2)
#         raise RuntimeError(
#             f"All providers failed for {source_lang}→{target_lang}. "
#             f"Last error: {exc2}"
#         ) from exc2
