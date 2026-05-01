"""
Fasiri – Model Registry.

Each ModelEntry describes one translation model available for a specific
(source_lang, target_lang) pair.  The router picks the entry with the highest
`quality_score` for a given pair; if no dedicated model exists it falls back
to the NLLB-200 catch-all.

Provider IDs map to concrete adapter classes in app/services/providers/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ── Language metadata ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LanguageInfo:
    code: str           # BCP-47-ish code used by Fasiri
    name: str           # Human-readable English name
    native_name: str    # Name in the language itself
    region: str         # continent sub-region
    family: str         # linguistic family
    sunbird_code: Optional[str] = None   # Sunbird's internal code (if different)
    nllb_code: Optional[str] = None      # NLLB-200 flores200 code


LANGUAGE_REGISTRY: Dict[str, LanguageInfo] = {
    # ── West African ─────────────────────────────────────────────────────────
    "yo": LanguageInfo("yo",  "Yoruba",   "Yorùbá",     "West Africa",    "Niger-Congo",   nllb_code="yor_Latn"),
    "ha": LanguageInfo("ha",  "Hausa",    "Hausa",      "West Africa",    "Afro-Asiatic",  nllb_code="hau_Latn"),
    "ig": LanguageInfo("ig",  "Igbo",     "Igbo",       "West Africa",    "Niger-Congo",   nllb_code="ibo_Latn"),
    "tw": LanguageInfo("tw",  "Twi",      "Twi",        "West Africa",    "Niger-Congo",   nllb_code="twi_Latn"),
    "wo": LanguageInfo("wo",  "Wolof",    "Wolof",      "West Africa",    "Niger-Congo",   nllb_code="wol_Latn"),
    "ff": LanguageInfo("ff",  "Fula",     "Fulfulde",   "West Africa",    "Niger-Congo",   nllb_code="fuv_Latn"),
    # ── East African ─────────────────────────────────────────────────────────
    "sw": LanguageInfo("sw",  "Swahili",  "Kiswahili",  "East Africa",    "Niger-Congo",   sunbird_code="swa", nllb_code="swh_Latn"),
    "am": LanguageInfo("am",  "Amharic",  "አማርኛ",       "East Africa",    "Afro-Asiatic",  nllb_code="amh_Ethi"),
    "om": LanguageInfo("om",  "Oromo",    "Oromoo",     "East Africa",    "Afro-Asiatic",  nllb_code="gaz_Latn"),
    "so": LanguageInfo("so",  "Somali",   "Soomaali",   "East Africa",    "Afro-Asiatic",  nllb_code="som_Latn"),
    "rw": LanguageInfo("rw",  "Kinyarwanda","Ikinyarwanda","East Africa", "Niger-Congo",   sunbird_code="kin", nllb_code="kin_Latn"),
    # ── Ugandan languages (Sunbird-primary) ──────────────────────────────────
    "lug": LanguageInfo("lug","Luganda",  "Oluganda",   "East Africa",    "Niger-Congo",   sunbird_code="lug", nllb_code="lug_Latn"),
    "nyn": LanguageInfo("nyn","Runyankole","Runyankore", "East Africa",    "Niger-Congo",   sunbird_code="nyn", nllb_code="nyn_Latn"),
    "lgg": LanguageInfo("lgg","Lugbara",  "Lugbara",    "East Africa",    "Central Sudanic",sunbird_code="lgg"),
    "ach": LanguageInfo("ach","Acholi",   "Acholi",     "East Africa",    "Nilotic",        sunbird_code="ach"),
    "teo": LanguageInfo("teo","Ateso",    "Ateso",      "East Africa",    "Nilotic",        sunbird_code="teo"),
    "luo": LanguageInfo("luo","Luo",      "Dholuo",     "East Africa",    "Nilotic",        nllb_code="luo_Latn"),
    "xog": LanguageInfo("xog","Lusoga",   "Olusoga",    "East Africa",    "Niger-Congo",    sunbird_code="xog"),
    "myx": LanguageInfo("myx","Lumasaba", "Lumasaaba",  "East Africa",    "Niger-Congo",    sunbird_code="myx"),
    "laj": LanguageInfo("laj","Lango",    "Lango",      "East Africa",    "Nilotic",        sunbird_code="laj"),
    "adh": LanguageInfo("adh","Jopadhola","Dhopadhola", "East Africa",    "Nilotic",        sunbird_code="adh"),
    # ── Southern African ─────────────────────────────────────────────────────
    "zu": LanguageInfo("zu",  "Zulu",     "IsiZulu",    "Southern Africa","Niger-Congo",    nllb_code="zul_Latn"),
    "xh": LanguageInfo("xh",  "Xhosa",   "IsiXhosa",   "Southern Africa","Niger-Congo",    nllb_code="xho_Latn"),
    "af": LanguageInfo("af",  "Afrikaans","Afrikaans",  "Southern Africa","Indo-European",  nllb_code="afr_Latn"),
    "sn": LanguageInfo("sn",  "Shona",   "ChiShona",   "Southern Africa","Niger-Congo",    nllb_code="sna_Latn"),
    "st": LanguageInfo("st",  "Sotho",   "Sesotho",    "Southern Africa","Niger-Congo",    nllb_code="sot_Latn"),
    "tn": LanguageInfo("tn",  "Tswana",  "Setswana",   "Southern Africa","Niger-Congo",    nllb_code="tsn_Latn"),
    # ── North African ────────────────────────────────────────────────────────
    "ar": LanguageInfo("ar",  "Arabic",  "العربية",    "North Africa",   "Afro-Asiatic",   nllb_code="arb_Arab"),
    "ber": LanguageInfo("ber","Tamazight","ⵜⴰⵎⴰⵣⵉⵖⵜ",  "North Africa",  "Afro-Asiatic",   nllb_code="tzm_Tfng"),
    # ── Source/pivot ─────────────────────────────────────────────────────────
    "en":  LanguageInfo("en", "English", "English",    "Global",         "Indo-European",  sunbird_code="eng", nllb_code="eng_Latn"),
    "fr":  LanguageInfo("fr", "French",  "Français",   "Global",         "Indo-European",  nllb_code="fra_Latn"),
    "pt":  LanguageInfo("pt", "Portuguese","Português", "Global",        "Indo-European",  nllb_code="por_Latn"),
}


# ── Model entries ────────────────────────────────────────────────────────────

@dataclass
class ModelEntry:
    model_id: str
    provider: str            # "sunbird" | "huggingface" | "nllb"
    source_langs: List[str]
    target_langs: List[str]
    quality_score: float     # 0.0 – 1.0  (BLEU-normalised estimate)
    avg_latency_ms: int      # rough p50 latency
    supports_batch: bool = True
    notes: str = ""


# Registry: all known dedicated models.
# The router iterates this list and picks the highest quality_score for a pair.
MODEL_REGISTRY: List[ModelEntry] = [

    # ── Sunbird – Ugandan-language expert ────────────────────────────────────
    ModelEntry(
        model_id="sunbird/nllb_translate",
        provider="sunbird",
        # Sunbird /tasks/nllb_translate ONLY supports these 6 codes.
        # For other Ugandan langs (xog, myx, laj, adh, rw) use NLLB fallback.
        source_langs=["en", "lug", "nyn", "lgg", "ach", "teo"],
        target_langs=["en", "lug", "nyn", "lgg", "ach", "teo"],
        quality_score=0.92,
        avg_latency_ms=800,
        notes="State-of-art for Ugandan languages; outperforms GPT-4 on 24/31 Ugandan langs",
    ),

    # ── Helsinki-NLP VERIFIED inference-deployed models ─────────────────────
    # Only models confirmed callable on router.huggingface.co/hf-inference
    # Models that show "not deployed by any Inference Provider" are NOT listed
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-en-sw",
        provider="huggingface",
        source_langs=["en"],
        target_langs=["sw"],
        quality_score=0.80,
        avg_latency_ms=1200,
        notes="Verified deployed on HF Inference API",
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-sw-en",
        provider="huggingface",
        source_langs=["sw"],
        target_langs=["en"],
        quality_score=0.78,
        avg_latency_ms=1200,
        notes="Verified deployed on HF Inference API",
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-yo-en",
        provider="huggingface",
        source_langs=["yo"],
        target_langs=["en"],
        quality_score=0.72,
        avg_latency_ms=1300,
        notes="yo->en confirmed deployed. en->yo not confirmed, falls back to NLLB",
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-en-af",
        provider="huggingface",
        source_langs=["en"],
        target_langs=["af"],
        quality_score=0.80,
        avg_latency_ms=1200,
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-af-en",
        provider="huggingface",
        source_langs=["af"],
        target_langs=["en"],
        quality_score=0.78,
        avg_latency_ms=1200,
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-en-ar",
        provider="huggingface",
        source_langs=["en"],
        target_langs=["ar"],
        quality_score=0.82,
        avg_latency_ms=1200,
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-ar-en",
        provider="huggingface",
        source_langs=["ar"],
        target_langs=["en"],
        quality_score=0.80,
        avg_latency_ms=1200,
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-en-fr",
        provider="huggingface",
        source_langs=["en"],
        target_langs=["fr"],
        quality_score=0.84,
        avg_latency_ms=1100,
    ),
    ModelEntry(
        model_id="Helsinki-NLP/opus-mt-fr-en",
        provider="huggingface",
        source_langs=["fr"],
        target_langs=["en"],
        quality_score=0.84,
        avg_latency_ms=1100,
    ),

    # ── NLLB-200: covers yo, ha, ig, zu, rw, am, so, tw, wo, ff + 190 more ──
    # Hausa (ha), Igbo (ig), Zulu (zu), Yoruba (en->yo), Kinyarwanda (rw),
    # Amharic (am), Somali (so), Twi (tw), Wolof (wo), Fula (ff) and more —
    # Helsinki dedicated models for these either don't exist or are NOT deployed
    # on the HF Inference API. NLLB-200 handles all of them.
    ModelEntry(
        model_id="facebook/nllb-200-distilled-600M",
        provider="huggingface",
        source_langs=["*"],
        target_langs=["*"],
        quality_score=0.65,
        avg_latency_ms=2000,
        notes=(
            "NLLB-200: covers ha, ig, zu, yo, rw, am, so, tw, wo, ff + 190 more. "
            "Used for all pairs where a verified Helsinki model does not exist."
        ),
    ),
]


# ── Lookup helpers ───────────────────────────────────────────────────────────

def get_best_model(source_lang: str, target_lang: str) -> ModelEntry:
    """Return the highest-quality ModelEntry for a given language pair."""
    candidates: List[ModelEntry] = []
    for entry in MODEL_REGISTRY:
        src_match = source_lang in entry.source_langs or "*" in entry.source_langs
        tgt_match = target_lang in entry.target_langs or "*" in entry.target_langs
        if src_match and tgt_match:
            candidates.append(entry)

    if not candidates:
        # Should never happen – NLLB wildcard is always in the registry
        raise ValueError(f"No model found for {source_lang} → {target_lang}")

    return max(candidates, key=lambda e: e.quality_score)


def get_language(code: str) -> Optional[LanguageInfo]:
    return LANGUAGE_REGISTRY.get(code)


def list_languages() -> List[LanguageInfo]:
    return list(LANGUAGE_REGISTRY.values())


# ── Build pair → model index for O(1) lookups ────────────────────────────────
_PAIR_INDEX: Dict[Tuple[str, str], ModelEntry] = {}

def _build_index() -> None:
    codes = list(LANGUAGE_REGISTRY.keys())
    for src in codes:
        for tgt in codes:
            if src != tgt:
                _PAIR_INDEX[(src, tgt)] = get_best_model(src, tgt)

_build_index()


def get_model_fast(source_lang: str, target_lang: str) -> ModelEntry:
    """O(1) version – falls back to linear search for unknown pairs."""
    entry = _PAIR_INDEX.get((source_lang, target_lang))
    if entry:
        return entry
    return get_best_model(source_lang, target_lang)
