<div align="center">
  <h1>🌍 Fasiri</h1>
  <p><strong>Unified translation and speech API for 30+ African languages</strong></p>
  <p>
    <a href="https://pypi.org/project/fasiri"><img src="https://img.shields.io/pypi/v/fasiri?color=blue&label=PyPI" alt="PyPI"></a>
    <a href="https://pypi.org/project/fasiri"><img src="https://img.shields.io/pypi/pyversions/fasiri" alt="Python versions"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
    <a href="https://docs.fasiri.ai"><img src="https://img.shields.io/badge/docs-fasiri.ai-blue" alt="Docs"></a>
  </p>
</div>

---

**Fasiri** (*Swahili: to interpret*) is a unified REST API and Python SDK that brings together the best African language AI providers — [Sunbird AI](https://sunbird.ai), [Khaya AI](https://khaya.ai), and [Helsinki-NLP](https://huggingface.co/Helsinki-NLP) — behind a single, consistent interface.

Translate text, transcribe audio, and synthesise speech across Luganda, Yoruba, Swahili, Acholi, Twi, and 25+ more African languages with one API key and one endpoint.

---

## Features

-  **30+ African languages** — Ugandan, West African, East African, North African
-  **Multi-provider routing** — Sunbird → Khaya → HuggingFace with automatic fallback
-  **Translation** — single and batch, with auto language detection
-  **Speech-to-Text** — transcribe audio in Luganda, Acholi, Swahili, and more
-  **Text-to-Speech** — synthesise natural speech in Ugandan languages
-  **Python SDK** — sync and async, installable via `pip install fasiri`
-  **OpenAPI docs** — interactive Swagger UI at `/docs`
-  **API key auth** — issue keys instantly, no OAuth required

---

## Supported Languages

| Code  | Language   | Region       | Translate | STT | TTS |
|-------|------------|--------------|:---------:|:---:|:---:|
| `lug` | Luganda    | East Africa  | ✅        | ✅  | ✅  |
| `ach` | Acholi     | East Africa  | ✅        | ✅  | ✅  |
| `teo` | Ateso      | East Africa  | ✅        | ✅  | ✅  |
| `nyn` | Runyankore | East Africa  | ✅        | ✅  | ✅  |
| `lgg` | Lugbara    | East Africa  | ✅        | ✅  | ✅  |
| `yo`  | Yoruba     | West Africa  | ✅        | ❌  | ❌  |
| `tw`  | Twi        | West Africa  | ✅        | ❌  | ❌  |
| `ee`  | Ewe        | West Africa  | ✅        | ❌  | ❌  |
| `gaa` | Ga         | West Africa  | ✅        | ❌  | ❌  |
| `dag` | Dagbani    | West Africa  | ✅        | ❌  | ❌  |
| `ki`  | Kikuyu     | East Africa  | ✅        | ❌  | ❌  |
| `luo` | Luo        | East Africa  | ✅        | ❌  | ❌  |
| `mer` | Kimeru     | East Africa  | ✅        | ❌  | ❌  |
| `kus` | Kusaal     | West Africa  | ✅        | ❌  | ❌  |
| `sw`  | Swahili    | East Africa  | ✅        | ✅  | ❌  |
| `fr`  | French     | Francophone  | ✅        | ❌  | ❌  |
| `ar`  | Arabic     | North Africa | ✅        | ❌  | ❌  |
| `af`  | Afrikaans  | South Africa | ✅        | ❌  | ❌  |
| `en`  | English    | Global       | ✅        | ✅  | ❌  |

---

## Provider Architecture

```
Request (en→lug)          Request (en→yo)          Request (en→sw)
       │                         │                         │
       ▼                         ▼                         ▼
  ┌─────────┐              ┌─────────┐              ┌─────────────┐
  │ Sunbird │              │  Khaya  │              │ HuggingFace │
  │   AI    │              │   AI    │              │ Helsinki-NLP│
  └────┬────┘              └────┬────┘              └──────┬──────┘
       │ fail?                  │ fail?                    │ fail?
       ▼                        ▼                          ▼
  ┌─────────┐              ┌─────────────┐           ┌──────────┐
  │  Khaya  │              │ HuggingFace │           │   503    │
  │fallback │              │  fallback   │           │ returned │
  └─────────┘              └─────────────┘           └──────────┘
```

---

## API Quick Start

### 1. Start the server

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
cp .env.example .env
# Fill in your provider keys in .env

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for interactive API docs.

### 2. Issue an API key

```bash
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app"}'
```

Response:
```json
{
  "api_key": "fsri_abc123...",
  "name": "my-app",
  "expires_at": "2027-05-01T00:00:00Z"
}
```

### 3. Translate

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Authorization: Bearer fsri_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning",
    "target_lang": "lug",
    "source_lang": "en",
    "provider": "auto"
  }'
```

Response:
```json
{
  "translated_text": "Wasuze otya",
  "detected_source_lang": "en",
  "target_lang": "lug",
  "model_used": "sunbird/nllb_translate",
  "provider": "sunbird",
  "quality_score": 0.92,
  "latency_ms": 1823,
  "characters_translated": 12
}
```

### 4. Batch translate

```bash
curl -X POST http://localhost:8000/api/v1/translate/batch \
  -H "Authorization: Bearer fsri_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "1", "text": "Good morning", "target_lang": "lug"},
      {"id": "2", "text": "How are you?", "target_lang": "yo"},
      {"id": "3", "text": "Thank you",    "target_lang": "tw"}
    ],
    "provider": "auto"
  }'
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

# Batch
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

# List languages
for lang in client.languages():
    print(lang)
```

### Async

```python
import asyncio
from fasiri import Fasiri

async def main():
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="sw")
        print(result)

asyncio.run(main())
```

### Error handling

```python
from fasiri import (
    Fasiri, AuthenticationError, RateLimitError,
    UnsupportedLanguageError, ProviderError
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
    print("All providers failed — try again later")
```

---

## REST API Reference

| Method | Endpoint                   | Description               | Auth |
|--------|----------------------------|---------------------------|------|
| `POST` | `/api/v1/translate`        | Translate text            | ✅   |
| `POST` | `/api/v1/translate/batch`  | Batch translate            | ✅   |
| `POST` | `/api/v1/speech/stt`       | Speech-to-Text            | ✅   |
| `POST` | `/api/v1/speech/tts`       | Text-to-Speech            | ✅   |
| `GET`  | `/api/v1/languages`        | List supported languages  | ✅   |
| `POST` | `/api/v1/auth/keys`        | Issue API key             | ❌   |
| `GET`  | `/api/v1/auth/keys/me`     | Inspect current key       | ✅   |
| `GET`  | `/health`                  | Health check              | ❌   |

Full interactive docs at **`/docs`** (Swagger UI) and **`/redoc`** (ReDoc).

---

## Environment Variables

| Variable                | Required | Description                                     |
|-------------------------|----------|-------------------------------------------------|
| `SUNBIRD_API_KEY`       | ✅       | JWT token from api.sunbird.ai (Ugandan langs)   |
| `KHAYA_API_KEY`         | ✅       | Subscription key from translation.ghananlp.org  |
| `KHAYA_API_KEY_SECONDARY` | —      | Secondary Khaya key for rate-limit failover     |
| `HUGGINGFACE_API_KEY`   | ✅       | Free token from huggingface.co/settings/tokens  |
| `FASIRI_SECRET_KEY`     | ✅       | Random secret for API key signing               |
| `REDIS_URL`             | —        | Redis URL for distributed rate limiting         |
| `DEBUG`                 | —        | Enable debug logging (default: `false`)         |
| `HTTP_TIMEOUT`          | —        | Request timeout in seconds (default: `30`)      |

See `.env.example` for the full list.

---

## Deployment

### Docker

```bash
docker-compose up --build
```

### Manual

```bash
# Production (4 workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Development (auto-reload)
uvicorn app.main:app --reload
```

---

## Project Structure

```
fasiri/
├── app/
│   ├── api/                  # FastAPI route handlers
│   │   ├── auth.py           # API key issuance
│   │   ├── translate.py      # Translation endpoints
│   │   ├── speech.py         # STT / TTS endpoints
│   │   └── languages.py      # Language listing
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── registry.py       # Language & model registry
│   │   └── security.py       # API key generation & validation
│   ├── middleware/
│   │   └── auth.py           # Auth dependency
│   ├── services/
│   │   ├── routing.py        # Provider selection & fallback
│   │   └── providers/
│   │       ├── base.py       # BaseProvider ABC
│   │       ├── sunbird.py    # Sunbird AI adapter
│   │       ├── khaya.py      # Khaya AI adapter
│   │       └── huggingface.py # HuggingFace adapter
│   └── main.py               # FastAPI app & lifespan
├── sdk/
│   └── fasiri_sdk/
│       ├── __init__.py       # Public API exports
│       └── client.py         # Fasiri Python client
├── docs/                     # MkDocs documentation source
├── tests/                    # Pytest test suite
├── .env.example              # Environment variable template
├── pyproject.toml            # PyPI package config
├── docker-compose.yml
└── README.md
```

---

## Contributing

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/
```

---

## License

MIT © [Beta-Tech Labs](https://beta-techlabs.com)
