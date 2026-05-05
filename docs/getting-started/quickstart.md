# Quick Start

This guide takes you from zero to your first successful translation in under five minutes.

## Step 1 - Install the SDK

```bash
pip install fasiri
```

## Step 2 - Get an API key

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "quickstart"}'
```

Copy the `api_key` value from the response.

## Step 3 - Make your first translation

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

result = client.translate("Good morning", target="lug")
print(result.translated_text)  # "Wasuze otya"
```

That is it. The client automatically selects Sunbird AI for Luganda and falls back to other providers if needed.

---

## Translating to other languages

```python
# Yoruba (West Africa) - uses Khaya AI
result = client.translate("How are you?", target="yo")
print(result)  # "Bawo ni"

# Swahili (East Africa) - uses HuggingFace Helsinki-NLP
result = client.translate("Thank you very much", target="sw")
print(result)  # "Asante sana"

# Acholi (Uganda) - uses Sunbird AI
result = client.translate("Welcome", target="ach")
print(result)

# Twi (Ghana) - uses Khaya AI
result = client.translate("Good night", target="tw")
print(result)
```

---

## Translating a batch

When you have multiple texts to translate, use batch translation instead of looping over single requests. It is faster and more efficient.

```python
results = client.translate_batch([
    {"id": "1", "text": "Good morning",   "target": "lug"},
    {"id": "2", "text": "How are you?",   "target": "yo"},
    {"id": "3", "text": "Thank you",      "target": "tw"},
    {"id": "4", "text": "See you later",  "target": "sw"},
])

print(f"{results.succeeded}/{results.total} translations succeeded")

for item in results:
    if item.success:
        print(f"  [{item.id}] {item.translated_text} (via {item.provider})")
    else:
        print(f"  [{item.id}] Failed: {item.error}")
```

---

## Speech-to-Text

Transcribe an audio file in Luganda:

```python
stt = client.transcribe("meeting_recording.wav", language="lug")
print(stt.transcript)
print(f"Detected language: {stt.detected_lang}")
print(f"Transcribed in {stt.latency_ms}ms")
```

---

## Text-to-Speech

Synthesise spoken audio from Luganda text:

```python
tts = client.synthesise("Oli otya?", language="lug")
print(tts.audio_url)   # URL to the generated audio file
```

---

## Inspecting results

Every translation result includes metadata you can use to make decisions in your application:

```python
result = client.translate("Hello", target="lug")

print(result.translated_text)      # The translation
print(result.detected_source_lang) # Auto-detected source language
print(result.provider)             # Which provider was used
print(result.model_used)           # Which model within that provider
print(result.quality_score)        # Float between 0 and 1
print(result.latency_ms)           # How long the request took
print(result.characters_translated) # Input character count
```

---

## Using the REST API directly

If you are not using Python, you can call the REST API directly from any language.

**Translate:**

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/translate \
  -H "Authorization: Bearer fsri_..." \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning",
    "target_lang": "lug",
    "source_lang": "en",
    "provider": "auto"
  }'
```

**List languages:**

```bash
curl https://fasiri-bu9u.onrender.com/api/v1/languages \
  -H "Authorization: Bearer fsri_..."
```

**Health check:**

```bash
curl https://fasiri-bu9u.onrender.com/health
```

---

## Next steps

- [Full translation guide](../guides/translation.md) - provider selection, quality scores, and best practices
- [Batch translation at scale](../guides/batch-at-scale.md) - handling large volumes efficiently
- [Error handling](../guides/error-handling.md) - building resilient applications
- [Async usage](../sdk-reference/async.md) - using the async client in FastAPI and other async frameworks
- [All supported languages](languages.md) - complete language list with capabilities
