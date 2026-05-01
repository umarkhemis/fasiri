# Authentication

Fasiri uses API keys for authentication. Every request must include a key in the `Authorization` header.

## Get an API Key

### Via the API (self-hosted)

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

!!! warning "Save your key"
    The plain-text key is returned **once only**. Store it securely — it cannot be retrieved again.

## Using Your Key

### HTTP Header

```bash
curl -X POST https://api.fasiri.ai/api/v1/translate \
  -H "Authorization: Bearer fsri_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "target_lang": "lug"}'
```

### Python SDK

```python
from fasiri import Fasiri

# Explicit
client = Fasiri(api_key="fsri_abc123...")

# Via environment variable (recommended)
import os
os.environ["FASIRI_API_KEY"] = "fsri_abc123..."
client = Fasiri()
```

### Environment Variable

```bash
export FASIRI_API_KEY=fsri_abc123...
```

```python
from fasiri import Fasiri
client = Fasiri()  # picks up FASIRI_API_KEY automatically
```

## Key Format

All Fasiri API keys start with `fsri_` followed by 40 hex characters:

```
fsri_e2b54ad9405c8712cd23a568754eef0872f3fa18
```

## Inspect Your Key

```bash
curl http://localhost:8000/api/v1/auth/keys/me \
  -H "Authorization: Bearer fsri_..."
```

Response:
```json
{
  "name": "my-app",
  "created_at": "2026-05-01T00:00:00Z",
  "expires_at": "2027-05-01T00:00:00Z",
  "requests_total": 142
}
```
