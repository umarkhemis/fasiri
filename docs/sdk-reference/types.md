# Data Types

All objects returned by the Fasiri SDK.

---

## TranslationResult

Returned by [`client.translate()`](client.md#translate).

```python
@dataclass
class TranslationResult:
    translated_text:      str
    detected_source_lang: str
    target_lang:          str
    model_used:           str
    provider:             str
    quality_score:        float
    latency_ms:           int
    characters_translated: int
```

### Fields

| Field | Type | Description |
|---|---|---|
| `translated_text` | `str` | The translated text |
| `detected_source_lang` | `str` | Source language (detected or provided) |
| `target_lang` | `str` | Target language code |
| `model_used` | `str` | Exact model that performed translation |
| `provider` | `str` | Provider used: `"sunbird"` or `"huggingface"` |
| `quality_score` | `float` | Estimated translation quality (0.0-1.0) |
| `latency_ms` | `int` | Time taken in milliseconds |
| `characters_translated` | `int` | Source character count |

### String representation

`str(result)` returns `translated_text`:

```python
result = client.translate("Hello", target="lug")
print(result)   # "Oli otya?"
print(f"Translation: {result}")  # "Translation: Oli otya?"
```

---

## BatchResult

Returned by [`client.translate_batch()`](client.md#translate_batch).

```python
@dataclass
class BatchResult:
    results:          list[BatchItemResult]
    total:            int
    succeeded:        int
    failed:           int
    total_latency_ms: int
```

### Fields

| Field | Type | Description |
|---|---|---|
| `results` | `list[BatchItemResult]` | All results in input order |
| `total` | `int` | Total number of items |
| `succeeded` | `int` | Number of successful translations |
| `failed` | `int` | Number of failed translations |
| `total_latency_ms` | `int` | Total wall time in milliseconds |

### Methods

| Method | Returns | Description |
|---|---|---|
| `successful()` | `list[BatchItemResult]` | Only successful results |
| `errors()` | `list[BatchItemResult]` | Only failed results |
| `__iter__()` | iterator | Iterate over all results |
| `__len__()` | `int` | Total number of results |

```python
batch = client.translate_batch([...])

# Iterate all
for item in batch:
    print(item.id, item)

# Successful only
for item in batch.successful():
    print(item.translated_text)

# Failed only
for item in batch.errors():
    print(f"[{item.id}] failed: {item.error}")
```

---

## BatchItemResult

Individual item within a `BatchResult`.

```python
@dataclass
class BatchItemResult:
    id:                   str
    translated_text:      str | None
    detected_source_lang: str | None
    target_lang:          str
    model_used:           str | None
    provider:             str | None
    quality_score:        float | None
    error:                str | None
```

### Properties

| Property | Returns | Description |
|---|---|---|
| `success` | `bool` | `True` if `error is None` |

### String representation

`str(item)` returns `translated_text` on success, or `"[ERROR] <message>"` on failure.

```python
item = batch.results[0]

if item.success:
    print(item.translated_text)
else:
    print(f"Failed: {item.error}")

# String shorthand
print(str(item))
```

---

## STTResult

Returned by [`client.transcribe()`](client.md#transcribe).

```python
@dataclass
class STTResult:
    transcript:   str
    detected_lang: str | None
    language:     str
    model_used:   str
    provider:     str
    latency_ms:   int
```

### String representation

`str(stt)` returns `transcript`.

---

## TTSResult

Returned by [`client.synthesise()`](client.md#synthesise--synthesize).

```python
@dataclass
class TTSResult:
    audio_url:    str | None
    audio_base64: str | None
    content_type: str
    language:     str
    model_used:   str
    provider:     str
    latency_ms:   int
```

!!! warning "Audio URL expires"
    `audio_url` is a signed URL that expires in ~2 minutes. Download immediately:

    ```python
    import httpx

    tts = client.synthesise("Oli otya?", language="lug")
    audio_bytes = httpx.get(tts.audio_url).content
    with open("output.mp3", "wb") as f:
        f.write(audio_bytes)
    ```

---

## Language

Returned in the list from [`client.languages()`](client.md#languages).

```python
@dataclass
class Language:
    code:                 str
    name:                 str
    native_name:          str
    region:               str
    family:               str
    supports_translation: bool
    supports_stt:         bool
    supports_tts:         bool
    tts_voice_id:         int | None
    best_provider:        str
    quality_score:        float
```

### repr

```python
lang = next(l for l in client.languages() if l.code == "lug")
print(repr(lang))
# <Language lug: Luganda [translate, stt, tts]>
```
