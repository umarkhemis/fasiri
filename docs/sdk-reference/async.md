# Async Usage

The Fasiri SDK supports async/await in both cloud and direct mode.
All sync methods have an async equivalent prefixed with `async_`.

---

## Basic async

```python
import asyncio
from fasiri import Fasiri

async def main():
    client = Fasiri(api_key="fsri_...")

    result = await client.async_translate("Good morning", target="lug")
    print(result)  # Wasuze otya

asyncio.run(main())
```

---

## Async context manager

Use `async with` for connection pooling. Recommended for applications
making many requests:

```python
async def main():
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="lug")
        print(result)
```

---

## Async batch

Async batch translation in direct mode runs all items concurrently,
making it significantly faster than sync batch for large lists:

```python
import asyncio
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider

async def main():
    # Direct mode - concurrent requests
    client = Fasiri(
        providers=[
            SunbirdProvider(api_key="eyJ..."),
            KhayaProvider(api_key="your-key"),
        ]
    )

    results = await client.async_translate_batch([
        {"id": "1", "text": "Good morning",  "target": "lug"},
        {"id": "2", "text": "How are you?",  "target": "yo"},
        {"id": "3", "text": "Thank you",     "target": "tw"},
        {"id": "4", "text": "Welcome",       "target": "nyn"},
        {"id": "5", "text": "Goodbye",       "target": "ach"},
    ])

    print(f"{results.succeeded}/{results.total} succeeded")
    print(f"Total time: {results.total_latency_ms}ms")

    for item in results.successful():
        print(f"[{item.id}] {item.translated_text} via {item.provider}")

asyncio.run(main())
```

---

## FastAPI integration

```python
from fastapi import FastAPI
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider

app = FastAPI()

# Initialise once at startup
fasiri = Fasiri(
    providers=[
        SunbirdProvider(api_key="eyJ..."),
        KhayaProvider(api_key="your-key"),
    ]
)

@app.post("/translate")
async def translate(text: str, target: str):
    result = await fasiri.async_translate(text, target=target)
    return {
        "translation": result.translated_text,
        "provider":    result.provider,
        "quality":     result.quality_score,
    }

@app.post("/batch")
async def batch(items: list[dict]):
    results = await fasiri.async_translate_batch(items)
    return {
        "succeeded": results.succeeded,
        "failed":    results.failed,
        "results":   [
            {"id": r.id, "translation": r.translated_text, "error": r.error}
            for r in results
        ],
    }
```

---

## Async methods reference

| Sync method | Async equivalent |
|---|---|
| `translate()` | `async_translate()` |
| `translate_batch()` | `async_translate_batch()` |
| `transcribe()` | - (not yet async) |
| `synthesise()` | - (not yet async) |
| `languages()` | - (not yet async) |
