# Authentication

Fasiri uses API keys to authenticate requests. Every request to a protected endpoint must include a valid key in the `Authorization` header.

## API key format

All Fasiri API keys follow this format:

```
fsri_<40 hex characters>
```

Example:

```
fsri_e2b54ad9405c8712cd23a568754eef0872f3fa18
```

Keys are case-sensitive. Store them securely and never commit them to source control.

---

## Getting an API key

### Via the REST API

Send a POST request to the auth endpoint. No authentication is required for this endpoint:

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-application"}'
```

Response:

```json
{
  "api_key": "fsri_e2b54ad9405c8712cd23a568754eef0872f3fa18",
  "name": "my-application",
  "created_at": "2026-05-01T10:00:00Z",
  "expires_at": "2027-05-01T10:00:00Z"
}
```

!!! warning "Save your key immediately"
    The plain-text key is returned **once only** and is never stored in retrievable form. If you lose it, you must issue a new key.

---

## Using your key

### In HTTP requests

Pass the key in the `Authorization` header using the `Bearer` scheme:

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/translate \
  -H "Authorization: Bearer fsri_..." \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning",
    "target_lang": "lug"
  }'
```

### In the Python SDK

Pass the key directly to the client constructor:

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")
```

Or set it as an environment variable and let the SDK pick it up automatically:

```bash
export FASIRI_API_KEY=fsri_...
```

```python
from fasiri import Fasiri

client = Fasiri()  # reads FASIRI_API_KEY from environment
```

Using environment variables is the recommended approach in production since it keeps secrets out of your source code.

### In a .env file

```bash
# .env
FASIRI_API_KEY=fsri_...
```

```python
from dotenv import load_dotenv
from fasiri import Fasiri

load_dotenv()
client = Fasiri()
```

---

## Inspecting your key

To check the metadata for the currently authenticated key:

```bash
curl https://fasiri-bu9u.onrender.com/api/v1/auth/keys/me \
  -H "Authorization: Bearer fsri_..."
```

Response:

```json
{
  "name": "my-application",
  "created_at": "2026-05-01T10:00:00Z",
  "expires_at": "2027-05-01T10:00:00Z",
  "requests_total": 142
}
```

---

## Key expiry and rotation

By default, keys expire after one year. When a key expires, all requests made with it will return HTTP 401.

To rotate a key, simply issue a new one via the auth endpoint and update your application configuration. There is no limit on the number of keys you can issue.

---

## Authentication errors

| HTTP Status | Code | Meaning |
|---|---|---|
| `401` | `MISSING_API_KEY` | No Authorization header was provided |
| `401` | `INVALID_API_KEY` | The key does not exist or has expired |
| `429` | `RATE_LIMIT_EXCEEDED` | Too many requests - slow down and retry |

See [Error Handling](../guides/error-handling.md) for details on handling these in your application.
