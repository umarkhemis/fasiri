# fasiri

> **Fasiri** (Swahili: *to interpret*) - Unified translation and speech API for 30+ African languages.

The official Python SDK for the Fasiri African Language API.

[![PyPI](https://img.shields.io/pypi/v/fasiri?color=2D7D46&label=PyPI)](https://pypi.org/project/fasiri/)
[![Python](https://img.shields.io/pypi/pyversions/fasiri)](https://pypi.org/project/fasiri/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Installation

```bash
pip install fasiri
```

Requires Python 3.9+.

---

## Two modes of operation

### Mode 1 - Fasiri Cloud

Use the hosted Fasiri API. Get a free key in seconds - no account required.

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

result = client.translate("Good morning", target="lug")
print(result)          # Wasuze otya
print(result.provider) # sunbird
```

Get your free key at [https://fasiri-ai.com/](https://api.fasiri-ai.com/docs).

---

### Mode 2 - Direct mode (bring your own keys)

Call providers directly with your own API keys. No Fasiri account needed.
You handle your own provider billing. Fasiri is just the routing layer - like LangChain for OpenAI.

```python
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider, HuggingFaceProvider

client = Fasiri(
    providers=[
        SunbirdProvider(api_key="eyJ..."),         # Sunbird JWT
        KhayaProvider(api_key="your-khaya-key"),    # Khaya subscription key
        HuggingFaceProvider(api_key="hf_..."),      # HuggingFace token
    ]
)

# Same interface as cloud mode
result = client.translate("Good morning", target="lug")
print(result)          # Wasuze otya
print(result.provider) # sunbird
```

In direct mode, Fasiri automatically picks the best provider for each language pair
and falls back if one fails. Requests go from your machine straight to the provider.

---

## Getting provider keys

### Sunbird AI (Ugandan languages)
Supports: Luganda, Acholi, Ateso, Runyankore, Lugbara

```bash
# 1. Register
curl -X POST https://api.sunbird.ai/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"you","email":"you@example.com","password":"yourpassword"}'

# 2. Get token (JWT starting with "ey...")
curl -X POST https://api.sunbird.ai/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=yourpassword"
```

```python
from fasiri.providers import SunbirdProvider

provider = SunbirdProvider(api_key="eyJ...")
```

---

### Khaya AI (West and East African languages)
Supports: Yoruba, Twi, Ewe, Ga, Dagbani, Kikuyu, Luo, Kimeru, Kusaal

Register at [translation.ghananlp.org/signup](https://translation.ghananlp.org/signup).

```python
from fasiri.providers import KhayaProvider

provider = KhayaProvider(api_key="your-subscription-key")
```

---

### HuggingFace (Swahili, French, Arabic, Afrikaans)

Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

```python
from fasiri.providers import HuggingFaceProvider

provider = HuggingFaceProvider(api_key="hf_...")
```

---

## Supported Languages

| Code | Language | Region | Translate | STT | TTS | Provider |
|---|---|---|:---:|:---:|:---:|---|
| `lug` | Luganda | Uganda | Yes | Yes | Yes | Sunbird |
| `ach` | Acholi | Uganda | Yes | Yes | Yes | Sunbird |
| `teo` | Ateso | Uganda | Yes | Yes | Yes | Sunbird |
| `nyn` | Runyankore | Uganda | Yes | Yes | Yes | Sunbird |
| `lgg` | Lugbara | Uganda | Yes | Yes | Yes | Sunbird |
| `yo` | Yoruba | Nigeria | Yes | No | No | Khaya |
| `tw` | Twi | Ghana | Yes | No | No | Khaya |
| `ee` | Ewe | Ghana/Togo | Yes | No | No | Khaya |
| `gaa` | Ga | Ghana | Yes | No | No | Khaya |
| `dag` | Dagbani | Ghana | Yes | No | No | Khaya |
| `ki` | Kikuyu | Kenya | Yes | No | No | Khaya |
| `luo` | Luo | Kenya | Yes | No | No | Khaya |
| `mer` | Kimeru | Kenya | Yes | No | No | Khaya |
| `kus` | Kusaal | Ghana | Yes | No | No | Khaya |
| `sw` | Swahili | East Africa | Yes | Yes | No | HuggingFace |
| `fr` | French | Francophone | Yes | No | No | HuggingFace |
| `ar` | Arabic | North Africa | Yes | No | No | HuggingFace |
| `af` | Afrikaans | South Africa | Yes | No | No | HuggingFace |

---

## Translation

### Single translation

```python
result = client.translate(
    text="Good morning, how are you?",
    target="lug",
    source="en",      # optional - auto-detected if omitted
    provider="auto",  # cloud mode only
)

print(result.translated_text)      # "Wasuze otya, oli otya?"
print(result.provider)              # "sunbird"
print(result.model_used)            # "sunbird/translate"
print(result.quality_score)         # 0.92
print(result.latency_ms)            # 1823
print(result.characters_translated) # 26
```

### Batch translation

```python
results = client.translate_batch([
    {"id": "1", "text": "Good morning",  "target": "lug"},
    {"id": "2", "text": "How are you?",  "target": "yo"},
    {"id": "3", "text": "Thank you",     "target": "tw"},
])

print(f"{results.succeeded}/{results.total} succeeded")

for item in results.successful():
    print(f"[{item.id}] {item.translated_text} (via {item.provider})")

for item in results.errors():
    print(f"[{item.id}] FAILED: {item.error}")
```

---

## Speech

### Speech-to-Text

```python
# From a file path
result = client.transcribe("meeting.wav", language="lug")
print(result.transcript)

# From bytes
with open("audio.mp3", "rb") as f:
    result = client.transcribe(f.read(), language="ach")
print(result.transcript)
```

### Text-to-Speech

```python
result = client.synthesise("Oli otya?", language="lug")
print(result.audio_url)
```

---

## Async usage

All methods have async equivalents:

```python
import asyncio
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider

# Works in both cloud and direct mode
async def main():
    # Cloud mode
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="lug")
        print(result)

    # Direct mode
    client = Fasiri(providers=[
        SunbirdProvider(api_key="eyJ..."),
        KhayaProvider(api_key="your-key"),
    ])
    # Batch runs concurrently in direct mode
    results = await client.async_translate_batch([
        {"id": "1", "text": "Hello",      "target": "lug"},
        {"id": "2", "text": "Thank you",  "target": "yo"},
    ])
    print(f"{results.succeeded}/{results.total} succeeded")

asyncio.run(main())
```

---

## Using individual providers

You can use providers directly without the Fasiri client:

```python
from fasiri.providers import SunbirdProvider

provider = SunbirdProvider(api_key="eyJ...")

# Translate
result = provider.translate("Good morning", target_lang="lug")
print(result)  # Wasuze otya

# STT
with open("audio.wav", "rb") as f:
    stt = provider.speech_to_text(f.read(), language="lug")
print(stt.transcript)

# TTS
tts = provider.text_to_speech("Oli otya?", language="lug")
print(tts.audio_url)
```

---

## Error handling

```python
from fasiri import (
    Fasiri,
    AuthenticationError,
    RateLimitError,
    UnsupportedLanguageError,
    ProviderError,
    FasiriError,
)

try:
    result = client.translate("Hello", target="lug")

except AuthenticationError as e:
    print(f"Invalid API key: {e}")

except RateLimitError as e:
    import time
    time.sleep(e.retry_after)

except UnsupportedLanguageError as e:
    print(f"Language not supported: {e}")

except ProviderError as e:
    print(f"All providers failed: {e}")

except FasiriError as e:
    print(f"Error [{e.code}]: {e}")
```

---

## Changelog

### v1.1.0
- Added direct mode - call providers with your own keys
- Added `SunbirdProvider`, `KhayaProvider`, `HuggingFaceProvider`
- Async batch in direct mode runs concurrently
- Same interface for both cloud and direct modes

### v1.0.0
- Initial release
- Cloud mode with Fasiri hosted API
- Translation, STT, TTS
- Sync and async client

---

## License

MIT - Beta-Tech Labs
