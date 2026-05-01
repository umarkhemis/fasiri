# Batch Translation

```
POST /api/v1/translate/batch
```

Translate up to 50 texts in a single request. All items are processed concurrently.

## Request

| Field | Type | Required | Description |
|---|---|---|---|
| `items` | array | Yes | Up to 50 translation items |
| `provider` | string | No | Provider override |

Each item requires `id`, `text`, `target_lang`. Optional: `source_lang`.

## Response

| Field | Type | Description |
|---|---|---|
| `results` | array | All results in input order |
| `total` | int | Total items submitted |
| `succeeded` | int | Successful count |
| `failed` | int | Failed count |
| `total_latency_ms` | int | Total wall time in ms |

## Example

```python
batch = client.translate_batch([
    {"id": "1", "text": "Hello",        "target": "lug"},
    {"id": "2", "text": "Good morning", "target": "yo"},
    {"id": "3", "text": "Thank you",    "target": "ha"},
])

print(f"{batch.succeeded}/{batch.total} succeeded")
for item in batch:
    if item.success:
        print(f"{item.id}: {item.translated_text}")
    else:
        print(f"{item.id}: ERROR - {item.error}")
```
