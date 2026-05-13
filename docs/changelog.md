# Changelog

## v1.1.0 (2026-05-10)

### Added
- Direct mode - call Sunbird AI, Khaya AI, and HuggingFace with your own API keys
- `fasiri.providers` subpackage with `SunbirdProvider`, `KhayaProvider`, `HuggingFaceProvider`
- `BaseDirectProvider` abstract base class for building custom provider adapters
- `DirectRouter` for automatic provider selection and fallback in direct mode
- Async batch translation runs concurrently in direct mode
- STT and TTS work in direct mode via `SunbirdProvider`
- New documentation section: Direct Mode guide
- New documentation section: Providers reference

### Changed
- `Fasiri` constructor now accepts `providers=` list for direct mode
- SDK version bumped to 1.1.0
- Improved error messages when no API key is provided - shows both cloud and direct mode options

---

## v1.0.0 (2026-05-01)

### Added
- Initial release
- Fasiri Cloud mode with hosted API at fasiri-bu9u.onrender.com
- Translation: single and batch, with auto language detection
- Speech-to-Text for Ugandan languages and Swahili
- Text-to-Speech for Ugandan languages
- Python SDK with sync and async support
- Provider routing: Sunbird AI, Khaya AI, HuggingFace with automatic fallback
- Health check endpoint with per-provider status
- Dual Khaya API key support for rate-limit failover

### Changed
- Renamed project from AfriLang to Fasiri
- API key prefix changed from `afrlk_` to `fsri_`
- Sunbird endpoint corrected from `/tasks/nllb_translate` to `/tasks/translate`
- Removed NLLB-200 (no longer supported by hf-inference free tier in 2025)
- Added Khaya AI as third provider for West African languages
