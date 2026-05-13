# Python SDK Reference

The Fasiri Python SDK provides a unified interface for African language translation,
speech-to-text, and text-to-speech - in both cloud and direct mode.

## Installation

```bash
pip install fasiri
```

## Import

```python
# Cloud mode
from fasiri import Fasiri

# Direct mode
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider, HuggingFaceProvider
```

---

## The Fasiri class

All API operations are methods on the `Fasiri` class.

### Constructor

```python
Fasiri(
    api_key: str | None = None,
    providers: list | None = None,
    base_url: str | None = None,
    timeout: int = 30,
)
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `api_key` | str | Fasiri Cloud key (`fsri_...`). Falls back to `FASIRI_API_KEY` env var. |
| `providers` | list | Direct mode provider list. When set, `api_key` is not required. |
| `base_url` | str | API base URL override. Falls back to `FASIRI_BASE_URL` env var. |
| `timeout` | int | HTTP timeout in seconds. Default: 30. |

Pass either `api_key` (cloud mode) or `providers` (direct mode). Not both.

**Cloud mode:**

```python
client = Fasiri(api_key="fsri_...")

# From environment variable
import os
os.environ["FASIRI_API_KEY"] = "fsri_..."
client = Fasiri()
```

**Direct mode:**

```python
from fasiri.providers import SunbirdProvider, KhayaProvider, HuggingFaceProvider

client = Fasiri(
    providers=[
        SunbirdProvider(api_key="eyJ..."),
        KhayaProvider(api_key="your-key"),
        HuggingFaceProvider(api_key="hf_..."),
    ]
)
```

---

## Methods

### translate

```python
client.translate(
    text: str,
    target: str,
    source: str | None = None,
    provider: str = "auto",
) -> TranslationResult
```

Translate text to the target language.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | str | - | Text to translate. |
| `target` | str | - | Target language code e.g. `"lug"`, `"yo"`, `"sw"`. |
| `source` | str | `None` | Source language. Auto-detected if omitted. |
| `provider` | str | `"auto"` | Cloud mode only: `"auto"`, `"sunbird"`, `"khaya"`, `"huggingface"`. |

### async_translate

Async equivalent of `translate`.

### translate_batch

```python
client.translate_batch(
    items: list[dict],
    provider: str = "auto",
) -> BatchResult
```

Translate multiple texts. Each item needs `"id"`, `"text"`, `"target"`.
In direct mode async batch, items run concurrently.

### async_translate_batch

Async equivalent of `translate_batch`. Runs items concurrently in direct mode.

### transcribe

```python
client.transcribe(
    audio: bytes | str,
    language: str,
) -> STTResult
```

Transcribe audio. Pass a file path or raw bytes.
Direct mode: requires `SunbirdProvider`.

### synthesise / synthesize

```python
client.synthesise(
    text: str,
    language: str,
    voice_id: int | None = None,
) -> TTSResult
```

Convert text to speech. Both spellings accepted.
Direct mode: requires `SunbirdProvider`.

### languages

```python
client.languages() -> list[Language]
```

Return all supported languages with capabilities.

### translation_languages

```python
client.translation_languages() -> list[Language]
```

Return only languages that support translation.

### speech_languages

```python
client.speech_languages() -> list[Language]
```

Return only languages that support STT or TTS.

---

## Async context manager

Use `async with` for efficient connection pooling:

```python
async with Fasiri(api_key="fsri_...") as client:
    result = await client.async_translate("Hello", target="lug")
```

---

## See also

- [Data Types](types.md) - TranslationResult, BatchResult, Language, etc.
- [Exceptions](exceptions.md) - Error handling
- [Async Usage](async.md) - Full async guide
- [Direct Mode](../guides/direct-mode.md) - Using providers directly
