# Translation

Translate text between any supported language pair.

## Basic Usage

```python
result = client.translate("Hello, how are you?", target="sw")
print(result.translated_text)  # "Habari, ukoje?"
print(result.provider)          # "huggingface"
print(result.quality_score)     # 0.80
print(result.latency_ms)        # 1243
```

## Parameters

| Parameter  | Type   | Required | Description                                      |
|------------|--------|----------|--------------------------------------------------|
| `text`     | `str`  | ✅       | Text to translate (max 5,000 characters)         |
| `target`   | `str`  | ✅       | Target language code e.g. `"lug"`, `"yo"`        |
| `source`   | `str`  | ❌       | Source language code. Auto-detected if omitted   |
| `provider` | `str`  | ❌       | `"auto"` (default), `"sunbird"`, `"khaya"`, `"huggingface"` |

## Provider Selection

With `provider="auto"` (default), Fasiri automatically picks the best provider:

| Language pair     | Primary provider  | Fallback         |
|-------------------|-------------------|------------------|
| `en ↔ lug/ach/teo/nyn/lgg` | Sunbird AI | Khaya → HuggingFace |
| `en ↔ yo/tw/ee/gaa/dag/ki/luo` | Khaya AI | HuggingFace |
| `en ↔ sw/fr/ar/af` | HuggingFace | — |

## REST API

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Authorization: Bearer fsri_..." \
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
  "model_used": "sunbird/translate",
  "provider": "sunbird",
  "quality_score": 0.92,
  "latency_ms": 1823,
  "characters_translated": 12
}
```
