# Batch Translation Methods

## `translate_batch()`

```python
batch = client.translate_batch([
    {"id": "1", "text": "Hello",        "target": "lug"},
    {"id": "2", "text": "Good morning", "target": "yo"},
    {"id": "3", "text": "Thank you",    "target": "ha"},
])

# Summary
print(f"{batch.succeeded}/{batch.total} succeeded")

# Iterate all
for item in batch:
    if item.success:
        print(item.translated_text)
    else:
        print(f"Error: {item.error}")

# Successful only
successes = batch.successful()

# Failed only
failures = batch.errors()
```

Returns a [`BatchResult`](types.md#batchresult).

## `async_translate_batch()`

```python
batch = await client.async_translate_batch([...])
```
