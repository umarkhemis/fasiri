# Quick Start

## 1. Install

```bash
pip install fasiri
```

## 2. Create a client

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")
```

## 3. Translate

```python
# English → Luganda
result = client.translate("Good morning", target="lug")
print(result)  # "Wasuze otya"

# English → Yoruba
result = client.translate("How are you?", target="yo")
print(result)  # "Báwo ni"

# English → Swahili (auto-detects source language)
result = client.translate("Thank you very much", target="sw")
print(result)  # "Asante sana"
```

## 4. Batch translate

```python
results = client.translate_batch([
    {"id": "1", "text": "Good morning",  "target": "lug"},
    {"id": "2", "text": "How are you?",  "target": "yo"},
    {"id": "3", "text": "Thank you",     "target": "tw"},
])

print(f"{results.succeeded}/{results.total} succeeded")

for item in results:
    if item.success:
        print(f"  [{item.id}] {item.translated_text}")
```

## 5. Speech

```python
# Transcribe audio
stt = client.transcribe("speech.wav", language="lug")
print(stt.transcript)

# Synthesise speech
tts = client.synthesise("Oli otya?", language="lug")
print(tts.audio_url)
```

## 6. Check available languages

```python
for lang in client.languages():
    print(f"{lang.code}: {lang.name}")
```

## What's next?

- [Translation guide](../guides/translation.md)
- [Batch translation](../guides/batch.md)
- [Error handling](../guides/errors.md)
- [Async usage](../sdk/async.md)
