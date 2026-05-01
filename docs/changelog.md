# Changelog

## v1.0.0 (2026-05-01)

### Added
- **Khaya AI provider** — West/East African language translation (Yoruba, Twi, Ewe, Ga, Dagbani, Kikuyu, Luo, Kimeru, Kusaal)
- **Three-provider routing** — Sunbird → Khaya → HuggingFace with automatic fallback
- **Python SDK** (`pip install fasiri`) with sync and async support
- **Batch translation** endpoint (`POST /api/v1/translate/batch`)
- **Health check** endpoint (`GET /health`) with provider status
- **Dual API key support** for Khaya (primary + secondary for rate-limit failover)

### Changed
- Renamed project from AfriLang → **Fasiri**
- API key prefix changed from `afrlk_` → `fsri_`
- Environment variable prefix changed from `AFRILANG_` → `FASIRI_`
- Sunbird endpoint corrected from `/tasks/nllb_translate` → `/tasks/translate`
- Removed `facebook/nllb-200-distilled-600M` (dropped by hf-inference in 2025)
- HuggingFace provider now only uses verified deployed Helsinki-NLP models

### Fixed
- Sunbird 405 errors caused by wrong endpoint path
- HuggingFace 400 errors caused by NLLB model being unsupported
- Wrong Luganda translations from `opus-mt-en-mul` when used as Ugandan fallback
