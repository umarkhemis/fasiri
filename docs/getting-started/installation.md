# Installation

## Requirements

- Python 3.9 or higher
- An API key (Fasiri Cloud) or provider keys (direct mode)

## Install the SDK

```bash
pip install fasiri
```

To upgrade:

```bash
pip install --upgrade fasiri
```

Verify:

```python
import fasiri
print(fasiri.__version__)  # 1.1.0
```

---

## Choose your mode

Fasiri SDK supports two modes. Both use the same interface.

### Cloud mode

Get a free Fasiri key - one key covers all providers:

```bash
curl -X POST https://api.fasiri-ai.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app"}'
```

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")
result = client.translate("Good morning", target="lug")
print(result)  # Wasuze otya
```

### Direct mode

Use your own provider keys - no Fasiri account needed:

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
result = client.translate("Good morning", target="lug")
print(result)  # Wasuze otya
```

See the [Direct Mode guide](../guides/direct-mode.md) for setup instructions.

---

## Self-hosted API server

To run the Fasiri API server yourself:

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
cp .env.example .env
# Add your provider keys to .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Point the SDK at your local server:

```python
client = Fasiri(
    api_key="fsri_...",
    base_url="http://localhost:8000",
)
```

---

## Docker

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
cp .env.example .env
docker compose up --build
```

---

## Dependencies

The SDK has a single runtime dependency:

| Package | Version | Purpose |
|---|---|---|
| `httpx` | >=0.27.0 | HTTP client (sync and async) |
