# Languages Endpoint

```
GET /api/v1/languages
```

No authentication required. Returns all supported languages with their capabilities.

## Response

```json
{
  "languages": [
    {
      "code": "lug",
      "name": "Luganda",
      "native_name": "Oluganda",
      "region": "East Africa",
      "family": "Niger-Congo",
      "supports_translation": true,
      "supports_stt": true,
      "supports_tts": true,
      "tts_voice_id": 248,
      "best_provider": "sunbird",
      "quality_score": 0.92
    }
  ],
  "total": 30
}
```

See [Supported Languages](../getting-started/languages.md) for the complete table.
