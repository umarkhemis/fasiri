# fasiri

> **Fasiri** - Unified translation and speech API for 30+ African languages.

The official Python SDK for the [Fasiri API](https://fasiri-bu9u.onrender.com).
A single interface to translate, transcribe, and synthesise speech across
African languages powered by Sunbird AI, Khaya AI, and Helsinki-NLP.

---

## Installation

```bash
pip install fasiri
```

Requires Python 3.9+.

---

## Quick Start

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

# Translate English → Luganda
result = client.translate("Good morning", target="lug")
print(result)  # "Wasuze otya"

# Translate English → Yoruba
result = client.translate("How are you?", target="yo")
print(result)  # "Báwo ni"

# Translate English → Swahili
result = client.translate("Thank you very much", target="sw")
print(result)  # "Asante sana"
```

---

## Authentication

Get your API key from the [Fasiri dashboard](https://fasiri-bu9u.onrender.com/dashboard)
or issue one locally:

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app"}'
```

Set it as an environment variable to avoid hardcoding:

```bash
export FASIRI_API_KEY=fsri_...
```

```python
from fasiri import Fasiri

client = Fasiri()  # reads FASIRI_API_KEY from environment
```

---

## Supported Languages

| Code  | Language   | Region       | Translation | STT | TTS | Provider   |
|-------|------------|--------------|:-----------:|:---:|:---:|------------|
| `lug` | Luganda    | East Africa  | ✅          | ✅  | ✅  | Sunbird    |
| `ach` | Acholi     | East Africa  | ✅          | ✅  | ✅  | Sunbird    |
| `teo` | Ateso      | East Africa  | ✅          | ✅  | ✅  | Sunbird    |
| `nyn` | Runyankore | East Africa  | ✅          | ✅  | ✅  | Sunbird    |
| `lgg` | Lugbara    | East Africa  | ✅          | ✅  | ✅  | Sunbird    |
| `yo`  | Yoruba     | West Africa  | ✅          | ❌  | ❌  | Khaya      |
| `tw`  | Twi        | West Africa  | ✅          | ❌  | ❌  | Khaya      |
| `ee`  | Ewe        | West Africa  | ✅          | ❌  | ❌  | Khaya      |
| `gaa` | Ga         | West Africa  | ✅          | ❌  | ❌  | Khaya      |
| `dag` | Dagbani    | West Africa  | ✅          | ❌  | ❌  | Khaya      |
| `ki`  | Kikuyu     | East Africa  | ✅          | ❌  | ❌  | Khaya      |
| `luo` | Luo        | East Africa  | ✅          | ❌  | ❌  | Khaya      |
| `sw`  | Swahili    | East Africa  | ✅          | ✅  | ❌  | HuggingFace|
| `fr`  | French     | Francophone  | ✅          | ❌  | ❌  | HuggingFace|
| `ar`  | Arabic     | North Africa | ✅          | ❌  | ❌  | HuggingFace|
| `af`  | Afrikaans  | South Africa | ✅          | ❌  | ❌  | HuggingFace|
| `en`  | English    | Global       | ✅          | ✅  | ❌  | All        |

Full list: `client.languages()`

---

## Translation

### Single Translation

```python
result = client.translate(
    text="Hello, how are you?",
    target="sw",        # target language code
    source="en",        # optional - auto-detected if omitted
    provider="auto",    # "auto" | "sunbird" | "khaya" | "huggingface"
)

print(result.translated_text)     # "Habari, ukoje?"
print(result.provider)             # "huggingface"
print(result.model_used)           # "Helsinki-NLP/opus-mt-en-sw"
print(result.quality_score)        # 0.80
print(result.latency_ms)           # 1243
print(result.characters_translated) # 19
```

### Batch Translation

Translate multiple texts in a single API call:

```python
results = client.translate_batch([
    {"id": "1", "text": "Good morning",   "target": "lug"},
    {"id": "2", "text": "Thank you",      "target": "yo"},
    {"id": "3", "text": "How are you?",   "target": "tw"},
    {"id": "4", "text": "See you later",  "target": "sw"},
])

print(f"{results.succeeded}/{results.total} succeeded")

for item in results:
    if item.success:
        print(f"[{item.id}] {item.translated_text}")
    else:
        print(f"[{item.id}] ERROR: {item.error}")
```

---

## Speech

### Speech-to-Text (Transcription)

```python
# From a file path
result = client.transcribe("meeting.wav", language="lug")
print(result.transcript)

# From bytes
with open("audio.mp3", "rb") as f:
    audio_bytes = f.read()

result = client.transcribe(audio_bytes, language="ach")
print(result.transcript)
print(result.detected_lang)   # detected language code
print(result.latency_ms)
```

### Text-to-Speech (Synthesis)

```python
result = client.synthesise("Oli otya?", language="lug")

print(result.audio_url)    # URL to the generated audio file
print(result.provider)     # "sunbird"
print(result.latency_ms)
```

American spelling also works:
```python
result = client.synthesize("Wasuze otya", language="lug")
```

---

## Languages

```python
# All languages
languages = client.languages()
for lang in languages:
    print(lang)
# <Language lug: Luganda [translate, stt, tts]>
# <Language yo: Yoruba [translate]>
# ...

# Only translation languages
for lang in client.translation_languages():
    print(f"{lang.code}: {lang.name} via {lang.best_provider}")

# Only speech languages
for lang in client.speech_languages():
    print(f"{lang.code}: STT={lang.supports_stt} TTS={lang.supports_tts}")
```

---

## Async Usage

All methods have async equivalents:

```python
import asyncio
from fasiri import Fasiri

async def main():
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="lug")
        print(result)

        batch = await client.async_translate_batch([
            {"id": "1", "text": "Good morning", "target": "yo"},
            {"id": "2", "text": "Thank you",    "target": "tw"},
        ])
        print(f"{batch.succeeded}/{batch.total} succeeded")

asyncio.run(main())
```

---

## Error Handling

```python
from fasiri import (
    Fasiri,
    AuthenticationError,
    RateLimitError,
    UnsupportedLanguageError,
    ProviderError,
    FasiriError,
)

client = Fasiri(api_key="fsri_...")

try:
    result = client.translate("Hello", target="lug")

except AuthenticationError as e:
    print(f"Invalid API key: {e}")

except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")

except UnsupportedLanguageError as e:
    print(f"Language not supported: {e}")

except ProviderError as e:
    print(f"All providers failed: {e}")

except FasiriError as e:
    print(f"Fasiri error [{e.code}]: {e}")
```

---

## Configuration

| Parameter  | Environment Variable | Default                  | Description              |
|------------|---------------------|--------------------------|--------------------------|
| `api_key`  | `FASIRI_API_KEY`    | -                        | Your Fasiri API key      |
| `base_url` | `FASIRI_BASE_URL`   | `https://fasiri-bu9u.onrender.com`  | API base URL             |
| `timeout`  | -                   | `30`                     | HTTP timeout in seconds  |

---

## License

MIT © [Beta-Tech Labs](https://betatechlabs.io)
