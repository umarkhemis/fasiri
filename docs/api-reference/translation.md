# Translation API

## POST /api/v1/translate

Translate a single piece of text.

### Request

```
POST /api/v1/translate
Authorization: Bearer fsri_...
Content-Type: application/json
```

**Request body:**

| Field | Type | Required | Description |
|---|---|:---:|---|
| `text` | string | Yes | Text to translate. Maximum 5,000 characters. |
| `target_lang` | string | Yes | Target language code, e.g. `"lug"`, `"yo"`, `"sw"`. |
| `source_lang` | string | No | Source language code. Auto-detected if omitted. |
| `provider` | string | No | Provider override: `"auto"` (default), `"sunbird"`, `"khaya"`, `"huggingface"`. |

**Example request:**

```bash
curl -X POST https://api.fasiri-ai.com/api/v1/translate \
  -H "Authorization: Bearer fsri_..." \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning, how are you today?",
    "target_lang": "lug",
    "source_lang": "en",
    "provider": "auto"
  }'
```

### Response

**200 OK:**

```json
{
  "translated_text": "Wasuze otya, oli otya leero?",
  "detected_source_lang": "en",
  "target_lang": "lug",
  "model_used": "sunbird/translate",
  "provider": "sunbird",
  "quality_score": 0.92,
  "latency_ms": 1823,
  "characters_translated": 33
}
```

| Field | Type | Description |
|---|---|---|
| `translated_text` | string | The translated text. |
| `detected_source_lang` | string | Detected or provided source language code. |
| `target_lang` | string | Target language code as requested. |
| `model_used` | string | The specific model or endpoint used. |
| `provider` | string | Provider that served the translation. |
| `quality_score` | float | Estimated translation quality, 0.0 to 1.0. |
| `latency_ms` | integer | Time taken to translate in milliseconds. |
| `characters_translated` | integer | Number of characters in the source text. |

**Error responses:**

| Status | Code | Description |
|---|---|---|
| `401` | `INVALID_API_KEY` | Authentication failed. |
| `422` | `VALIDATION_ERROR` | Missing or invalid request fields. |
| `503` | `PROVIDER_ERROR` | All providers failed. |

---

## POST /api/v1/translate/batch

Translate multiple texts in a single request. More efficient than calling `/translate` in a loop.

### Request

```
POST /api/v1/translate/batch
Authorization: Bearer fsri_...
Content-Type: application/json
```

**Request body:**

| Field | Type | Required | Description |
|---|---|:---:|---|
| `items` | array | Yes | List of translation items. Maximum 50 items per request. |
| `provider` | string | No | Provider override applied to all items. Default: `"auto"`. |

Each item in `items`:

| Field | Type | Required | Description |
|---|---|:---:|---|
| `id` | string | Yes | Your identifier for this item. Returned in response. |
| `text` | string | Yes | Text to translate. |
| `target_lang` | string | Yes | Target language code. |
| `source_lang` | string | No | Source language code. Auto-detected if omitted. |

**Example request:**

```bash
curl -X POST https://api.fasiri-ai.com/api/v1/translate/batch \
  -H "Authorization: Bearer fsri_..." \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "1", "text": "Good morning",   "target_lang": "lug"},
      {"id": "2", "text": "How are you?",   "target_lang": "yo"},
      {"id": "3", "text": "Thank you",      "target_lang": "tw"}
    ],
    "provider": "auto"
  }'
```

### Response

**200 OK:**

```json
{
  "results": [
    {
      "id": "1",
      "translated_text": "Wasuze otya",
      "detected_source_lang": "en",
      "target_lang": "lug",
      "model_used": "sunbird/translate",
      "provider": "sunbird",
      "quality_score": 0.92,
      "error": null
    },
    {
      "id": "2",
      "translated_text": "Bawo ni",
      "detected_source_lang": "en",
      "target_lang": "yo",
      "model_used": "khaya/translate-v2",
      "provider": "khaya",
      "quality_score": 0.85,
      "error": null
    },
    {
      "id": "3",
      "translated_text": "Medaase",
      "detected_source_lang": "en",
      "target_lang": "tw",
      "model_used": "khaya/translate-v2",
      "provider": "khaya",
      "quality_score": 0.85,
      "error": null
    }
  ],
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "total_latency_ms": 3241
}
```

Individual items that fail include an `error` message and null translation fields. The overall request still returns HTTP 200 - check the `failed` count and individual `error` fields.
