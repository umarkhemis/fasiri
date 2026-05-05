# Installation

## Requirements

- Python 3.9 or higher
- An API key (see [Authentication](authentication.md))

## Install the SDK

Install the official Fasiri Python SDK from PyPI:

```bash
pip install fasiri
```

To upgrade to the latest version:

```bash
pip install --upgrade fasiri
```

### Verify the installation

```python
import fasiri
print(fasiri.__version__)  # 1.0.0
```

---

## Install for async usage

The SDK supports both synchronous and asynchronous usage out of the box. No extra dependencies are required - `httpx` (which ships with the SDK) handles both modes.

```bash
pip install fasiri
```

```python
import asyncio
from fasiri import Fasiri

async def main():
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="lug")
        print(result)

asyncio.run(main())
```

---

## Self-hosted API server

If you want to run the Fasiri API server yourself rather than using the hosted version at `https://fasiri-bu9u.onrender.com`, follow these steps.

### Prerequisites

- Python 3.9+
- Git
- API keys for at least one provider (Sunbird AI, Khaya AI, or HuggingFace)

### Clone the repository

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
```

### Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your provider API keys. At minimum you need one of the following:

- `SUNBIRD_API_KEY` - for Ugandan language translation, STT, and TTS
- `KHAYA_API_KEY` - for West African language translation
- `HUGGINGFACE_API_KEY` - for Swahili, French, Arabic, and multilingual fallback

See [Environment Variables](../self-hosting/env.md) for the full reference.

### Start the server

```bash
uvicorn app.main:app --reload
```

The API will start at `https://fasiri-bu9u.onrender.com`. Visit `https://fasiri-bu9u.onrender.com/docs` for the interactive Swagger UI.

### Point the SDK at your local server

```python
from fasiri import Fasiri

client = Fasiri(
    api_key="fsri_...",
    base_url="https://fasiri-bu9u.onrender.com",
)
```

---

## Docker

The fastest way to run the server in production is with Docker Compose:

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
cp .env.example .env
# Fill in your provider keys in .env

docker compose up --build
```

See [Docker deployment](../self-hosting/docker.md) for the full guide.

---

## Dependencies

The Fasiri SDK has a single runtime dependency:

| Package | Version | Purpose |
|---|---|---|
| `httpx` | >=0.27.0 | HTTP client (sync + async) |

The API server has additional dependencies listed in `requirements.txt`.
