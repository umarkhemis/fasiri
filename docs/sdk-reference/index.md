# Python SDK Reference

The Fasiri Python SDK provides a clean, type-safe interface to the Fasiri API.

## Installation

```bash
pip install fasiri
```

## Import

```python
from fasiri import Fasiri
```

## The Fasiri class

`Fasiri` is the main client class. All API operations are methods on this class.

### Constructor

```python
Fasiri(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: int = 30,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | str | `None` | Your Fasiri API key. Falls back to `FASIRI_API_KEY` environment variable. |
| `base_url` | str | `"https://fasiri-bu9u.onrender.com"` | API base URL. Override for self-hosted deployments. |
| `timeout` | int | `30` | HTTP request timeout in seconds. |

**Example:**

```python
from fasiri import Fasiri

# Explicit key
client = Fasiri(api_key="fsri_...")

# From environment variable
import os
os.environ["FASIRI_API_KEY"] = "fsri_..."
client = Fasiri()

# Self-hosted server
client = Fasiri(
    api_key="fsri_...",
    base_url="https://fasiri-bu9u.onrender.com",
)

# Longer timeout for STT (audio transcription is slow)
client = Fasiri(api_key="fsri_...", timeout=60)
```

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

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | str | - | Text to translate. Max 5,000 characters. |
| `target` | str | - | Target language code, e.g. `"lug"`, `"yo"`, `"sw"`. |
| `source` | str | `None` | Source language code. Auto-detected if omitted. |
| `provider` | str | `"auto"` | Provider: `"auto"`, `"sunbird"`, `"khaya"`, `"huggingface"`. |

**Returns:** `TranslationResult`

### async_translate

Async equivalent of `translate`. Use inside `async def` functions.

```python
await client.async_translate(text, target, source, provider)
```

### translate_batch

```python
client.translate_batch(
    items: list[dict],
    provider: str = "auto",
) -> BatchResult
```

Translate multiple texts in one request.

Each item dict must have `"id"`, `"text"`, and `"target"`. Optionally include `"source"`.

**Returns:** `BatchResult`

### async_translate_batch

Async equivalent of `translate_batch`.

### transcribe

```python
client.transcribe(
    audio: bytes | str,
    language: str,
) -> STTResult
```

Transcribe audio to text. Pass a file path (str) or raw audio bytes.

**Returns:** `STTResult`

### synthesise / synthesize

```python
client.synthesise(
    text: str,
    language: str,
    voice_id: int | None = None,
) -> TTSResult
```

Convert text to speech. Both spellings are accepted.

**Returns:** `TTSResult`

### languages

```python
client.languages() -> list[Language]
```

Return all supported languages.

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

## Async context manager

Use `async with` for efficient connection pooling in async applications:

```python
async with Fasiri(api_key="fsri_...") as client:
    result = await client.async_translate("Hello", target="lug")
```

## See also

- [Data Types](types.md) - TranslationResult, BatchResult, Language, etc.
- [Exceptions](exceptions.md) - Error types and handling
- [Async Usage](async.md) - Full async guide
