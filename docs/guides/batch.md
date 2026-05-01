# Batch Translation

Translate multiple texts in a single API call - more efficient than calling `/translate` in a loop.

## Usage

```python
results = client.translate_batch([
    {"id": "1", "text": "Good morning",   "target": "lug"},
    {"id": "2", "text": "How are you?",   "target": "yo"},
    {"id": "3", "text": "Thank you",      "target": "tw"},
    {"id": "4", "text": "See you later",  "target": "sw"},
])

print(f"{results.succeeded}/{results.total} succeeded")
print(f"Total time: {results.total_latency_ms}ms")

for item in results:
    if item.success:
        print(f"[{item.id}] {item.translated_text} ({item.provider})")
    else:
        print(f"[{item.id}] FAILED: {item.error}")
```

## Filtering Results

```python
# Only successful translations
for item in results.successful():
    print(item.translated_text)

# Only failed items
for item in results.errors():
    print(f"{item.id}: {item.error}")
```

## REST API

```bash
curl -X POST http://localhost:8000/api/v1/translate/batch \
  -H "Authorization: Bearer fsri_..." \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "1", "text": "Hello",        "target_lang": "lug"},
      {"id": "2", "text": "Good morning", "target_lang": "yo"}
    ],
    "provider": "auto"
  }'
```
