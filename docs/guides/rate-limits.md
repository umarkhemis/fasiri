# Rate Limits

Fasiri enforces rate limits to ensure fair usage and API stability.

## Default limits

| Endpoint | Limit |
|---|---|
| `POST /api/v1/translate` | 60 requests/minute per API key |
| `POST /api/v1/translate/batch` | 10 requests/minute per API key |
| `POST /api/v1/speech/stt` | 60 requests/minute per API key |
| `POST /api/v1/speech/tts` | 60 requests/minute per API key |

Limits are per API key, using a **sliding window** algorithm.

## Rate limit headers

When you are rate limited, the response includes:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 42
Content-Type: application/json

{
  "detail": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 60 requests/minute exceeded. Retry after 42 seconds.",
    "retry_after_seconds": 42
  }
}
```

## Handling rate limits

=== "Python SDK"

    ```python
    import time
    from fasiri import Fasiri, RateLimitError

    client = Fasiri(api_key="fsri_...")

    def translate_safe(text, target):
        while True:
            try:
                return client.translate(text, target=target)
            except RateLimitError as e:
                print(f"Rate limited. Waiting {e.retry_after}s...")
                time.sleep(e.retry_after)
    ```

=== "Async with retry"

    ```python
    import asyncio
    from fasiri import Fasiri, RateLimitError

    client = Fasiri(api_key="fsri_...")

    async def translate_with_retry(text, target, max_attempts=5):
        for attempt in range(max_attempts):
            try:
                return await client.async_translate(text, target=target)
            except RateLimitError as e:
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(e.retry_after)
    ```

## Best practices

!!! tip "Use batch translation"
    Instead of 50 individual translate calls, make one batch call:
    ```python
    # Bad - 50 API calls, hits rate limit fast
    results = [client.translate(text, target="lug") for text in texts]

    # Good - 1 API call for up to 50 items
    batch = client.translate_batch([
        {"id": str(i), "text": text, "target": "lug"}
        for i, text in enumerate(texts)
    ])
    ```

!!! tip "Cache translations"
    Cache results for repeated translations of the same text:
    ```python
    from functools import lru_cache

    @lru_cache(maxsize=1000)
    def cached_translate(text, target):
        return client.translate(text, target=target).translated_text
    ```

!!! tip "Spread requests over time"
    For bulk processing, add a small delay between batches:
    ```python
    import time

    for i, chunk in enumerate(chunks(texts, 50)):
        batch = client.translate_batch(chunk)
        if i < len(chunks) - 1:
            time.sleep(6)  # 10 batches/minute = one batch every 6 seconds
    ```
