# API Reference

The Fasiri REST API is available at:

```
https://api.fasiri-ai.com
```

All endpoints (except key issuance) require authentication via an API key in the `Authorization` header:

```
Authorization: Bearer fsri_<your-key>
```

Interactive API documentation with a live request builder is available at:

```
https://api.fasiri-ai.com/docs
```

---

## Base URL

```
https://api.fasiri-ai.com
```

All API paths are prefixed with `/api/v1`.

---

## Endpoints

| Method | Path | Description | Auth |
|---|---|---|:---:|
| `POST` | `/api/v1/translate` | Translate text | Yes |
| `POST` | `/api/v1/translate/batch` | Batch translate | Yes |
| `POST` | `/api/v1/speech/stt` | Speech-to-Text | Yes |
| `POST` | `/api/v1/speech/tts` | Text-to-Speech | Yes |
| `GET` | `/api/v1/languages` | List languages | Yes |
| `POST` | `/api/v1/auth/keys` | Issue API key | No |
| `GET` | `/api/v1/auth/keys/me` | Inspect current key | Yes |
| `GET` | `/health` | Health check | No |

---

## Request and response format

All requests and responses use JSON (`Content-Type: application/json`) except for speech endpoints which use `multipart/form-data` for audio uploads.

### Successful response

Successful responses return HTTP 200 with a JSON body.

### Error response

Error responses return the appropriate HTTP status code with a JSON body:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of the error."
  }
}
```

### Validation error (422)

When request body validation fails, FastAPI returns:

```json
{
  "detail": [
    {
      "loc": ["body", "target_lang"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate limits

| Endpoint type | Limit |
|---|---|
| Single translation | 60 requests per minute per API key |
| Batch translation | 10 requests per minute per API key |

When a rate limit is exceeded, the API returns HTTP 429 with a `Retry-After` header indicating how many seconds to wait before retrying.
