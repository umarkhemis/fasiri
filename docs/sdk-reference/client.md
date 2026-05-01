# Fasiri Client

The `Fasiri` class is the main entry point for the Python SDK.

## Import

```python
from fasiri import Fasiri
```

## Constructor

```python
Fasiri(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: int = 30,
)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | `FASIRI_API_KEY` env var | Your Fasiri API key |
| `base_url` | `str` | Fasiri production URL | Override for self-hosted instances |
| `timeout` | `int` | `30` | HTTP timeout in seconds |

### Raises

- `AuthenticationError` — if no API key is provided and `FASIRI_API_KEY` is not set

### Examples

```python
from fasiri import Fasiri

# From environment variable (recommended)
client = Fasiri()

# Explicit key
client = Fasiri(api_key="fsri_...")

# Custom timeout for slow networks
client = Fasiri(api_key="fsri_...", timeout=60)

# Self-hosted instance
client = Fasiri(
    api_key="fsri_...",
    base_url="https://api.mycompany.com",
)
```

---

## Methods

### `translate()`

```python
def translate(
    text: str,
    target: str,
    source: str | None = None,
    provider: str = "auto",
) -> TranslationResult
```

Translate text to a target language.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `text` | `str` | ✅ | Text to translate (max 5,000 chars) |
| `target` | `str` | ✅ | Target language code, e.g. `"lug"`, `"sw"` |
| `source` | `str` | - | Source language code. Auto-detected if omitted. |
| `provider` | `str` | - | `"auto"`, `"sunbird"`, or `"huggingface"` |

**Returns:** [`TranslationResult`](types.md#translationresult)

```python
result = client.translate("Hello", target="lug")
print(result)                 # "Oli otya?"
print(result.quality_score)   # 0.92
print(result.provider)        # "sunbird"
```

---

### `translate_batch()`

```python
def translate_batch(
    items: list[dict],
    provider: str = "auto",
) -> BatchResult
```

Translate multiple texts in a single request (up to 50 items).

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `items` | `list[dict]` | ✅ | List of translation items. Each dict needs `id`, `text`, `target` |
| `provider` | `str` | - | Provider override |

Each item must have:

| Key | Type | Required | Description |
|---|---|---|---|
| `id` | `str` | ✅ | Client-supplied ID to match results to inputs |
| `text` | `str` | ✅ | Text to translate |
| `target` | `str` | ✅ | Target language code (also accepts `target_lang`) |
| `source` | `str` | - | Source language code (also accepts `source_lang`) |

**Returns:** [`BatchResult`](types.md#batchresult)

```python
batch = client.translate_batch([
    {"id": "1", "text": "Good morning", "target": "yo"},
    {"id": "2", "text": "Thank you",    "target": "sw"},
])

print(batch.succeeded)        # 2
print(batch.failed)           # 0

for item in batch:
    print(item.id, item)      # "1  E kaaro" / "2  Asante"
```

---

### `transcribe()`

```python
def transcribe(
    audio: bytes | str,
    language: str,
) -> STTResult
```

Transcribe audio to text (Speech-to-Text).

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `audio` | `bytes` or `str` | Raw audio bytes, or a file path |
| `language` | `str` | Language code of the audio (e.g. `"lug"`) |

**Returns:** [`STTResult`](types.md#sttresult)

```python
# From file path
stt = client.transcribe("recording.wav", language="lug")
print(stt.transcript)

# From bytes
with open("audio.mp3", "rb") as f:
    stt = client.transcribe(f.read(), language="sw")
```

---

### `synthesise()` / `synthesize()`

```python
def synthesise(
    text: str,
    language: str,
    voice_id: int | None = None,
) -> TTSResult
```

Convert text to speech (Text-to-Speech).

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `text` | `str` | Text to synthesise (max 2,000 chars) |
| `language` | `str` | Language code (e.g. `"lug"`) |
| `voice_id` | `int` | Specific voice ID. Auto-selected if omitted. |

**Returns:** [`TTSResult`](types.md#ttsresult)

```python
tts = client.synthesise("Oli otya?", language="lug")
print(tts.audio_url)
# "https://cdn.sunbird.ai/tts/abc123.mp3"
```

!!! note "Audio URL expiry"
    The signed audio URL expires in approximately 2 minutes. Download the audio immediately.

---

### `languages()`

```python
def languages() -> list[Language]
```

Return all supported languages with their capabilities.

```python
langs = client.languages()

for lang in langs:
    print(f"{lang.code}: {lang.name}")
    print(f"  STT: {lang.supports_stt}")
    print(f"  TTS: {lang.supports_tts}")
    print(f"  Provider: {lang.best_provider}")
```

---

### `translation_languages()`

```python
def translation_languages() -> list[Language]
```

Return only languages that support translation.

---

### `speech_languages()`

```python
def speech_languages() -> list[Language]
```

Return only languages that support STT or TTS.

---

## Async usage

All methods have async equivalents. See [Async Usage](async.md).

```python
async with Fasiri(api_key="fsri_...") as client:
    result = await client.async_translate("Hello", target="lug")
    batch  = await client.async_translate_batch([...])
```
