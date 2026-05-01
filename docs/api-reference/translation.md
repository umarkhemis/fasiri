# Translation

Translate text between any supported African language pair.

## Endpoint

```
POST /api/v1/translate
```

## Authentication

All requests require a valid API key in the Authorization header:

```
Authorization: Bearer fsri_...
```

## Request

=== "Schema"

    | Field | Type | Required | Description |
    |---|---|---|---|
    | `text` | `string` | ✅ | Text to translate. Max 5,000 characters. |
    | `target_lang` | `string` | ✅ | Target language code, e.g. `"lug"`, `"sw"`, `"yo"` |
    | `source_lang` | `string` | - | Source language code. Auto-detected if omitted. |
    | `provider` | `string` | - | `"auto"` (default), `"sunbird"`, or `"huggingface"` |

=== "Example"

    ```json
    {
      "text": "Hello, how are you?",
      "target_lang": "lug",
      "source_lang": "en",
      "provider": "auto"
    }
    ```

## Response

=== "Schema"

    | Field | Type | Description |
    |---|---|---|
    | `translated_text` | `string` | The translated text |
    | `detected_source_lang` | `string` | Detected or provided source language |
    | `target_lang` | `string` | Target language code |
    | `model_used` | `string` | The specific model that performed the translation |
    | `provider` | `string` | Provider that handled the request |
    | `quality_score` | `float` | Estimated translation quality (0.0-1.0) |
    | `latency_ms` | `integer` | Time taken for translation in milliseconds |
    | `characters_translated` | `integer` | Number of characters in the source text |

=== "Example"

    ```json
    {
      "translated_text": "Oli otya?",
      "detected_source_lang": "en",
      "target_lang": "lug",
      "model_used": "sunbird/nllb_translate",
      "provider": "sunbird",
      "quality_score": 0.92,
      "latency_ms": 820,
      "characters_translated": 19
    }
    ```

## Code examples

=== "Python SDK"

    ```python
    from fasiri import Fasiri

    client = Fasiri(api_key="fsri_...")

    # Basic translation — source auto-detected
    result = client.translate("Hello, how are you?", target="lug")
    print(result)  # "Oli otya?"

    # With explicit source language
    result = client.translate(
        "Bonjour tout le monde",
        target="sw",
        source="fr",
    )

    # Force a specific provider
    result = client.translate(
        "Good morning",
        target="nyn",
        provider="sunbird",
    )

    # Access all metadata
    print(result.translated_text)    # "Agandi?"
    print(result.provider)           # "sunbird"
    print(result.quality_score)      # 0.92
    print(result.latency_ms)         # 750
    ```

=== "cURL"

    ```bash
    curl -X POST https://api.fasiri.betatechlabs.io/api/v1/translate \
      -H "Authorization: Bearer fsri_..." \
      -H "Content-Type: application/json" \
      -d '{
        "text": "Hello, how are you?",
        "target_lang": "lug"
      }'
    ```

=== "JavaScript (fetch)"

    ```javascript
    const response = await fetch(
      "https://api.fasiri.betatechlabs.io/api/v1/translate",
      {
        method: "POST",
        headers: {
          "Authorization": "Bearer fsri_...",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: "Hello, how are you?",
          target_lang: "lug",
        }),
      }
    );

    const data = await response.json();
    console.log(data.translated_text);  // "Oli otya?"
    ```

=== "Python (httpx)"

    ```python
    import httpx

    r = httpx.post(
        "https://api.fasiri.betatechlabs.io/api/v1/translate",
        headers={"Authorization": "Bearer fsri_..."},
        json={"text": "Hello", "target_lang": "lug"},
    )
    print(r.json()["translated_text"])
    ```

## Provider selection

Fasiri automatically selects the best provider for each language pair:

| Language pair | Provider | Quality |
|---|---|---|
| `en` ↔ `lug`, `nyn`, `ach`, `teo`, `lgg` | Sunbird AI | 0.92 |
| `en` ↔ `sw`, `yo`, `ha`, `ig`, `zu`, `rw` | Helsinki-NLP | 0.78-0.85 |
| All other pairs | opus-mt-en-mul | 0.62 |

Set `provider="sunbird"` or `provider="huggingface"` to override routing.

## Errors

| Status | Code | Description |
|---|---|---|
| `400` | `SAME_LANGUAGE` | Source and target language are the same |
| `401` | `INVALID_API_KEY` | Missing or invalid API key |
| `422` | `UNSUPPORTED_LANGUAGE_PAIR` | Language pair not supported |
| `422` | Validation error | Text empty or exceeds 5,000 characters |
| `429` | `RATE_LIMIT_EXCEEDED` | Too many requests — see [Rate Limits](../guides/rate-limits.md) |
| `503` | `PROVIDER_ERROR` | All providers failed — retry with backoff |
