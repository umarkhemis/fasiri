# Changelog

All notable changes to Fasiri are documented here.

## [1.0.0] - 2026-05-01

### Added
- Khaya AI provider for West/East African language translation
- Three-provider fallback routing: Sunbird → Khaya → HuggingFace
- Python SDK (`pip install fasiri`) with sync + async client
- Batch translation endpoint
- Health check with per-provider status
- Dual Khaya API key support for rate-limit failover

### Changed
- Renamed: AfriLang → **Fasiri**
- API key prefix: `afrlk_` → `fsri_`
- Environment variables: `AFRILANG_*` → `FASIRI_*`
- Sunbird endpoint: `/tasks/nllb_translate` → `/tasks/translate`
- Removed NLLB-200 (no longer supported on hf-inference free tier)

### Fixed
- Sunbird 405 errors (wrong endpoint)
- HuggingFace 400 errors (unsupported NLLB model)
- Bad Luganda translations from opus-mt-en-mul fallback
