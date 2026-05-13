# Quick Start

Get up and running in under 5 minutes.

## Option A - Fasiri Cloud

### Step 1 - Get a free API key

```bash
curl -X POST https://fasiri-bu9u.onrender.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "quickstart"}'
```

Copy the `api_key` from the response.

### Step 2 - Install and translate

```bash
pip install fasiri
```

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

# English -> Luganda
print(client.translate("Good morning", target="lug"))   # Wasuze otya

# English -> Yoruba
print(client.translate("How are you?", target="yo"))    # Bawo ni

# English -> Swahili
print(client.translate("Thank you", target="sw"))       # Asante
```

---

## Option B - Direct mode (your own provider keys)

No Fasiri account needed. Use your existing Sunbird, Khaya, or HuggingFace keys.

```bash
pip install fasiri
```

```python
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider

client = Fasiri(
    providers=[
        SunbirdProvider(api_key="eyJ..."),       # your Sunbird JWT
        KhayaProvider(api_key="your-khaya-key"), # your Khaya key
    ]
)

print(client.translate("Good morning", target="lug"))  # Wasuze otya
print(client.translate("How are you?", target="yo"))   # Bawo ni
```

See [Direct Mode](../guides/direct-mode.md) for how to get provider keys.

---

## Batch translation

```python
results = client.translate_batch([
    {"id": "1", "text": "Good morning",   "target": "lug"},
    {"id": "2", "text": "How are you?",   "target": "yo"},
    {"id": "3", "text": "Thank you",      "target": "tw"},
    {"id": "4", "text": "See you later",  "target": "sw"},
])

print(f"{results.succeeded}/{results.total} succeeded")

for item in results:
    if item.success:
        print(f"[{item.id}] {item.translated_text} ({item.provider})")
    else:
        print(f"[{item.id}] Failed: {item.error}")
```

---

## Speech

```python
# Transcribe audio
stt = client.transcribe("speech.wav", language="lug")
print(stt.transcript)

# Synthesise speech
tts = client.synthesise("Oli otya?", language="lug")
print(tts.audio_url)
```

---

## Async usage

```python
import asyncio
from fasiri import Fasiri

async def main():
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Good morning", target="lug")
        print(result)

asyncio.run(main())
```

---

## Inspect the result

```python
result = client.translate("Hello", target="lug")

print(result.translated_text)       # Oli otya
print(result.detected_source_lang)  # en
print(result.provider)              # sunbird
print(result.model_used)            # sunbird/translate
print(result.quality_score)         # 0.92
print(result.latency_ms)            # 1823
print(result.characters_translated) # 5
```

---

## Next steps

- [Translation guide](../guides/translation.md)
- [Direct mode guide](../guides/direct-mode.md)
- [Batch translation](../guides/batch.md)
- [Error handling](../guides/error-handling.md)
- [Async usage](../sdk-reference/async.md)
