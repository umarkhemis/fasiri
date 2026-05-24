# Translation Guide

This guide covers everything you need to know about translating text with Fasiri, from basic usage to advanced provider control.

## Basic translation

The simplest translation request specifies the text and the target language. The source language is automatically detected.

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

result = client.translate("Good morning", target="lug")
print(result.translated_text)  # "Wasuze otya"
```

## Specifying the source language

If you already know the source language, provide it explicitly. This slightly improves speed and accuracy by skipping auto-detection.

```python
result = client.translate(
    text="Good morning",
    target="lug",
    source="en",
)
```

## Understanding the result

Every translation returns a `TranslationResult` object with full metadata:

```python
result = client.translate("Hello", target="yo")

print(result.translated_text)       # "Bawo"
print(result.detected_source_lang)  # "en"
print(result.target_lang)           # "yo"
print(result.model_used)            # "khaya/translate-v2"
print(result.provider)              # "khaya"
print(result.quality_score)         # 0.85
print(result.latency_ms)            # 1243
print(result.characters_translated) # 5
```

### Quality scores

Quality scores indicate the expected translation accuracy based on the provider and model:

| Score range | Meaning |
|---|---|
| 0.90 - 1.00 | Excellent - specialised provider for this language pair |
| 0.80 - 0.89 | Good - dedicated translation model |
| 0.70 - 0.79 | Decent - general purpose model with reasonable coverage |
| 0.60 - 0.69 | Acceptable - multilingual fallback model |
| Below 0.60 | Poor - use with caution |

You can use quality scores in your application to decide whether to show a translation, flag it for review, or request a different provider.

```python
result = client.translate("Complex medical terminology", target="sw")

if result.quality_score < 0.70:
    print("Warning: translation quality may be low")
    print(f"Translated by: {result.provider}")
```

## Choosing a provider

By default, Fasiri selects the best provider automatically (`provider="auto"`). You can override this to force a specific provider.

```python
# Force Sunbird AI (best for Ugandan languages)
result = client.translate("Hello", target="lug", provider="sunbird")

# Force Khaya AI (best for West African languages)
result = client.translate("Hello", target="yo", provider="khaya")

# Force HuggingFace
result = client.translate("Hello", target="sw", provider="huggingface")
```

!!! note "Provider availability"
    If you force a specific provider that does not support the requested language pair, Fasiri will return an error rather than silently falling back. Use `provider="auto"` to get automatic fallback behaviour.

## Provider routing logic

With `provider="auto"`, Fasiri routes requests using this priority order:

```
1. Sunbird AI   - if both source and target are in {en, lug, ach, teo, nyn, lgg}
2. Khaya AI     - if the language pair is in Khaya's supported set
3. HuggingFace  - for all other pairs (Helsinki-NLP models + multilingual fallback)
```

If the primary provider fails (network error, timeout, API outage), Fasiri automatically retries with the next provider in the chain.

## Translating long texts

The maximum input length varies by provider. Fasiri enforces the most restrictive limit:

| Provider | Max characters |
|---|---|
| Sunbird AI | 5,000 |
| Khaya AI | 1,000 |
| HuggingFace | 512 tokens |

For long documents, split the text into paragraphs and use batch translation:

```python
paragraphs = long_text.split("\n\n")

results = client.translate_batch([
    {"id": str(i), "text": para, "target": "lug"}
    for i, para in enumerate(paragraphs)
    if para.strip()
])

translated_paragraphs = [
    r.translated_text for r in results if r.success
]

translated_document = "\n\n".join(translated_paragraphs)
```

## Via the REST API

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

Response:

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

## Best practices

**Always handle errors.** Providers can be temporarily unavailable. Wrap translation calls in try/except blocks and have a fallback plan - even if that means displaying the original text.

**Cache translations where possible.** If you are translating the same strings repeatedly (UI labels, static content), cache the results. This reduces latency, cost, and load on providers.

**Use batch for multiple strings.** A single batch call is always faster than multiple individual calls. See the [Batch Translation guide](batch.md).

**Specify source language when known.** Auto-detection adds a small overhead. If you know the source language (e.g. your app only accepts English input), always pass `source="en"`.

**Monitor quality scores.** Log quality scores alongside translations. If you see consistently low scores for a language pair, that is a signal to investigate whether a better provider or model is available.
