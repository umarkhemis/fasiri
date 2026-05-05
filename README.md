<div align="center">
  <img src="docs/assets/fasiri-logo.png" alt="Fasiri" width="280"/>
  <p><strong>Unified translation and speech API for 30+ African languages</strong></p>
  <p>
    <a href="https://pypi.org/project/fasiri"><img src="https://img.shields.io/pypi/v/fasiri?color=2D7D46&label=PyPI" alt="PyPI"></a>
    <a href="https://pypi.org/project/fasiri"><img src="https://img.shields.io/pypi/pyversions/fasiri" alt="Python versions"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
    <a href="https://umarkhemis.github.io/fasiri"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-blue" alt="Docs"></a>
    <a href="https://fasiri-bu9u.onrender.com/health"><img src="https://img.shields.io/badge/API-live-2D7D46" alt="API status"></a>
  </p>
</div>

---

**Fasiri** (Swahili: *to interpret*) is a unified REST API and Python SDK that brings together the best African language AI providers behind a single, consistent interface.

Translate text, transcribe audio, and synthesise speech across Luganda, Yoruba, Swahili, Acholi, Twi, and 25+ more African languages with one API key and one endpoint.

- **API base URL:** `https://fasiri-bu9u.onrender.com`
- **Interactive docs:** `https://fasiri-bu9u.onrender.com/docs`
- **Documentation:** `https://umarkhemis.github.io/fasiri`

---

## Features

- 30+ African languages - Ugandan, West African, East African, North African
- Multi-provider routing - Sunbird AI, Khaya AI, HuggingFace with automatic fallback
- Translation - single and batch, with auto language detection
- Speech-to-Text - transcribe audio in Luganda, Acholi, Swahili, and more
- Text-to-Speech - synthesise natural speech in Ugandan languages
- Python SDK - sync and async, installable via `pip install fasiri`
- OpenAPI docs - interactive Swagger UI at `/docs`
- API key auth - issue keys instantly, no OAuth required

---

## Supported Languages

| Code | Language | Region | Translate | STT | TTS | Provider |
|---|---|---|:---:|:---:|:---:|---|
| `lug` | Luganda | East Africa | Yes | Yes | Yes | Sunbird AI |
| `ach` | Acholi | East Africa | Yes | Yes | Yes | Sunbird AI |
| `teo` | Ateso | East Africa | Yes | Yes | Yes | Sunbird AI |
| `nyn` | Runyankore | East Africa | Yes | Yes | Yes | Sunbird AI |
| `lgg` | Lugbara | East Africa | Yes | Yes | Yes | Sunbird AI |
| `yo` | Yoruba | West Africa | Yes | No | No | Khaya AI |
| `tw` | Twi | West Africa | Yes | No | No | Khaya AI |
| `ee` | Ewe | West Africa | Yes | No | No | Khaya AI |
| `gaa` | Ga | West Africa | Yes | No | No | Khaya AI |
| `dag` | Dagbani | West Africa | Yes | No | No | Khaya AI |
| `ki` | Kikuyu | East Africa | Yes | No | No | Khaya AI |
| `luo` | Luo | East Africa | Yes | No | No | Khaya AI |
| `sw` | Swahili | East Africa | Yes | Yes | No | HuggingFace |
| `fr` | French | Francophone | Yes | No | No | HuggingFace |
| `ar` | Arabic | North Africa | Yes | No | No | HuggingFace |
| `af` | Afrikaans | South Africa | Yes | No | No | HuggingFace |
| `en` | English | Global | Yes | Yes | No | All |

---

## Provider Architecture

```
Request: en -> lug   ->  Sunbird AI (primary)  ->  Khaya/HuggingFace (fallback)
Request: en -> yo    ->  Khaya AI (primary)     ->  HuggingFace (fallback)
Request: en -> sw    ->  HuggingFace Helsinki   ->  multilingual fallback
```

---

## Python SDK

### Install

```bash
pip install fasiri
```

### Usage

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

# Single translation
result = client.translate("Good morning", target="lug")
print(result)  # "Wasuze otya"

# Batch translation
batch = client.translate_batch([
    {"id": "1", "text": "Hello",      "target": "yo"},
    {"id": "2", "text": "Thank you",  "target": "tw"},
    {"id": "3", "text": "Good night", "target": "sw"},
])
for item in batch:
    print(f"{item.id}: {item}")

# Speech-to-Text
stt = client.transcribe("audio.wav", language="lug")
print(stt.transcript)

# Text-to-Speech
tts = client.synthesise("Oli otya?", language="lug")
print(tts.audio_url)

# Async
import asyncio

async def main():
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="sw")
        print(result)

asyncio.run(main())
```

### Error handling

```python
from fasiri import (
    Fasiri,
    AuthenticationError,
    RateLimitError,
    UnsupportedLanguageError,
    ProviderError,
)

try:
    result = client.translate("Hello", target="lug")
except AuthenticationError:
    print("Check your API key")
except RateLimitError as e:
    print(f"Retry after {e.retry_after}s")
except UnsupportedLanguageError:
    print("Language pair not supported")
except ProviderError:
    print("All providers failed - try again later")
```

---

## REST API Quick Start

### 1. Start the server (or use the hosted version)

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or use the hosted API at `https://fasiri-bu9u.onrender.com`.

### 2. Issue an API key

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app"}'
```

### 3. Translate

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/translate \
  -H "Authorization: Bearer fsri_..." \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning",
    "target_lang": "lug",
    "source_lang": "en"
  }'
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUNBIRD_API_KEY` | Yes | JWT from api.sunbird.ai (Ugandan languages) |
| `KHAYA_API_KEY` | Yes | Subscription key from translation.ghananlp.org |
| `HUGGINGFACE_API_KEY` | Yes | Free token from huggingface.co/settings/tokens |
| `FASIRI_SECRET_KEY` | Yes | Secret for API key signing (openssl rand -hex 32) |
| `REDIS_URL` | No | Redis for distributed rate limiting |
| `DEBUG` | No | Enable debug logging (default: false) |

See `.env.example` for the full list.

---

## Project Structure

```
fasiri/
|-- app/
|   |-- api/              # FastAPI route handlers
|   |-- core/             # Config, registry, security
|   |-- middleware/       # Auth dependency
|   |-- services/
|   |   |-- routing.py    # Provider selection and fallback
|   |   +-- providers/
|   |       |-- sunbird.py
|   |       |-- khaya.py
|   |       +-- huggingface.py
|   +-- main.py
|-- fasiri/               # Python SDK package
|   |-- __init__.py
|   +-- client.py
|-- docs/                 # MkDocs documentation
|-- tests/
|-- .env.example
|-- pyproject.toml
+-- README.md
```

---

## License

MIT - Beta-Tech Labs
