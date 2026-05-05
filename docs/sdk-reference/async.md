# Async Usage

Fasiri has full async support for use with `asyncio`, `FastAPI`, `Django Async`, and any other async framework.

## Context manager (recommended)

The cleanest way to use the async client is as an async context manager. This ensures the underlying HTTP connection pool is properly closed:

```python
import asyncio
from fasiri import Fasiri

async def main():
    async with Fasiri(api_key="fsri_...") as client:
        result = await client.async_translate("Hello", target="lug")
        print(result)  # "Oli otya?"

asyncio.run(main())
```

## Available async methods

Every sync method has an async counterpart:

| Sync | Async |
|---|---|
| `client.translate()` | `await client.async_translate()` |
| `client.translate_batch()` | `await client.async_translate_batch()` |

!!! note
    `transcribe()` and `synthesise()` do not yet have async versions. They run synchronously. Full async speech methods are on the roadmap.

## Concurrent batch translation

The real power of async is running multiple independent calls concurrently:

```python
import asyncio
from fasiri import Fasiri

async def translate_all():
    async with Fasiri(api_key="fsri_...") as client:

        # Run 5 translations concurrently - much faster than sequential
        results = await asyncio.gather(
            client.async_translate("Good morning",  target="lug"),
            client.async_translate("Thank you",     target="yo"),
            client.async_translate("Welcome",       target="ha"),
            client.async_translate("How are you?",  target="sw"),
            client.async_translate("Goodbye",       target="ig"),
        )

        for result in results:
            print(result)

asyncio.run(translate_all())
```

## FastAPI integration

```python
from fastapi import FastAPI, Depends, HTTPException
from fasiri import Fasiri, FasiriError
import os

app = FastAPI()

# Create a single client instance at startup
_client: Fasiri | None = None

@app.on_event("startup")
async def startup():
    global _client
    _client = Fasiri(api_key=os.environ["FASIRI_API_KEY"])

@app.on_event("shutdown")
async def shutdown():
    pass  # client closes connections automatically

def get_client() -> Fasiri:
    return _client

@app.post("/translate")
async def translate(
    text: str,
    target: str,
    client: Fasiri = Depends(get_client),
):
    try:
        result = await client.async_translate(text, target=target)
        return {
            "translated": result.translated_text,
            "provider":   result.provider,
            "score":      result.quality_score,
        }
    except FasiriError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Django async view

```python
# views.py
from django.http import JsonResponse
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

async def translate_view(request):
    text   = request.GET.get("text", "")
    target = request.GET.get("target", "sw")

    result = await client.async_translate(text, target=target)

    return JsonResponse({
        "translated_text": result.translated_text,
        "provider": result.provider,
    })
```

## Processing large datasets concurrently

For translating thousands of texts efficiently, use batch + semaphore to control concurrency:

```python
import asyncio
from fasiri import Fasiri

async def bulk_translate(texts: list[str], target: str, concurrency: int = 5):
    """
    Translate a large list of texts using concurrent batch calls.
    concurrency controls how many batch requests run simultaneously.
    """
    # Split into batches of 50 (API maximum)
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    batches = list(chunks(
        [{"id": str(i), "text": t, "target": target}
         for i, t in enumerate(texts)],
        50
    ))

    semaphore = asyncio.Semaphore(concurrency)
    results = {}

    async def process_batch(batch):
        async with semaphore:
            async with Fasiri(api_key="fsri_...") as client:
                br = await client.async_translate_batch(batch)
                for item in br:
                    if item.success:
                        results[item.id] = item.translated_text

    await asyncio.gather(*[process_batch(b) for b in batches])
    return [results.get(str(i), "") for i in range(len(texts))]

# Usage
texts = ["Hello"] * 200  # 200 texts
translated = asyncio.run(bulk_translate(texts, target="lug"))
```

## Error handling in async code

```python
import asyncio
from fasiri import Fasiri, RateLimitError, ProviderError

async def translate_with_retry(text, target, max_retries=3):
    async with Fasiri(api_key="fsri_...") as client:
        for attempt in range(max_retries):
            try:
                return await client.async_translate(text, target=target)

            except RateLimitError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(e.retry_after)
                else:
                    raise

            except ProviderError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
```
