"""
Fasiri - language auto-detection.

Primary:  langdetect (works offline, fast)
Fallback: Sunbird /tasks/language_id (better for Ugandan languages)

Returns a BCP-47 code compatible with LANGUAGE_REGISTRY.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# langdetect code -> Fasiri code mapping
_LANGDETECT_MAP = {
    "sw": "sw",
    "yo": "yo",
    "ha": "ha",
    "ig": "ig",
    "zu": "zu",
    "rw": "rw",
    "am": "am",
    "so": "so",
    "af": "af",
    "sn": "sn",
    "st": "st",
    "tn": "tn",
    "ar": "ar",
    "en": "en",
    "fr": "fr",
    "pt": "pt",
}

# Sunbird language_id output -> Fasiri code
_SUNBIRD_MAP = {
    "eng": "en",
    "lug": "lug",
    "nyn": "nyn",
    "lgg": "lgg",
    "ach": "ach",
    "teo": "teo",
    "swa": "sw",
    "kin": "rw",
    "xog": "xog",
    "myx": "myx",
    "laj": "laj",
    "adh": "adh",
}


def detect_language(text: str) -> str:
    """
    Detect the language of `text`.
    Returns an Fasiri language code (e.g. 'en', 'sw', 'lug').
    Falls back to 'en' if detection fails.
    """
    try:
        from langdetect import detect, LangDetectException  # type: ignore
        raw = detect(text)
        mapped = _LANGDETECT_MAP.get(raw, raw)
        logger.debug("langdetect: %s -> %s", raw, mapped)
        return mapped
    except Exception as exc:
        logger.warning("Language detection failed: %s - defaulting to 'en'", exc)
        return "en"


def map_sunbird_lang(sunbird_code: str) -> str:
    return _SUNBIRD_MAP.get(sunbird_code, sunbird_code)
