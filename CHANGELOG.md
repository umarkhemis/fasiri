# Changelog

## [1.1.0] - 2026-05-10

### Added
- Direct mode - call Sunbird AI, Khaya AI, and HuggingFace with your own API keys
- `fasiri.providers` subpackage with `SunbirdProvider`, `KhayaProvider`, `HuggingFaceProvider`
- `BaseDirectProvider` abstract class for building custom providers
- `DirectRouter` for automatic provider selection and fallback in direct mode
- Async batch translation runs concurrently in direct mode
- STT and TTS work in direct mode via SunbirdProvider
- `Fasiri.__repr__` shows mode and provider names

### Changed
- `Fasiri` constructor now accepts `providers=` list for direct mode
- SDK version bumped to 1.1.0
- Improved error messages when no API key is provided - now shows both options

## [1.0.0] - 2026-05-01

### Added
- Initial release
- Fasiri Cloud mode with hosted API
- Translation (single and batch)
- Speech-to-Text and Text-to-Speech
- Python SDK with sync and async support
- Provider routing: Sunbird AI, Khaya AI, HuggingFace

### Changed
- Renamed project from AfriLang to Fasiri
- API key prefix changed from `afrlk_` to `fsri_`
- Sunbird endpoint corrected to `/tasks/translate`
- Removed NLLB-200 (no longer supported by hf-inference)
- Added Khaya AI as third provider for West African languages
