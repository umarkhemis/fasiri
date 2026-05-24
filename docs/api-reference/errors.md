# Error Reference

Fasiri uses standard HTTP status codes and returns structured error objects.

## Error format

Every error response has this shape:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of what went wrong.",
    "details": null
  }
}
```

## Error codes

### Authentication errors (401)

| Code | Description | Fix |
|---|---|---|
| `MISSING_API_KEY` | No Authorization header | Add `Authorization: Bearer fsri_...` to your request |
| `INVALID_API_KEY` | Key is wrong or expired | Verify your key, or issue a new one |

```json
{
  "detail": {
    "code": "MISSING_API_KEY",
    "message": "Authentication required. Pass your Fasiri API key in the Authorization header: Bearer fsri_<your-key>"
  }
}
```

### Validation errors (422)

| Code | Description | Fix |
|---|---|---|
| `SAME_LANGUAGE` | Source and target are identical | Use different source/target languages |
| `UNSUPPORTED_LANGUAGE_PAIR` | Language pair not supported | Check [supported languages](../getting-started/languages.md) |
| `UNSUPPORTED_LANGUAGE` | Language not supported for this feature | Check STT/TTS language support |
| `UNSUPPORTED_MEDIA_TYPE` | Audio format not accepted | Use WAV, MP3, OGG, or WebM |
| `INVALID_VOICE` | No TTS voice for this language | Check TTS-supported languages |

### Size errors (413, 422)

| Code | Description | Limit |
|---|---|---|
| `FILE_TOO_LARGE` | Audio file exceeds size limit | Max 10 MB |
| Validation error | Text too long for translation | Max 5,000 characters |
| Validation error | Text too long for TTS | Max 2,000 characters |
| Validation error | Batch too large | Max 50 items |

### Rate limiting (429)

```json
{
  "detail": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 60 requests/minute exceeded. Retry after 42 seconds.",
    "retry_after_seconds": 42
  }
}
```

The response also includes a `Retry-After` header with the number of seconds to wait.

See [Rate Limits](../guides/rate-limits.md) for details.

### Provider errors (503)

```json
{
  "detail": {
    "code": "PROVIDER_ERROR",
    "message": "All providers failed for en-lug. Last error: ..."
  }
}
```

This means both the primary provider and the fallback failed. Usually a transient issue - retry with exponential backoff.

## Handling errors in Python

=== "SDK exceptions"

    ```python
    from fasiri import (
        Fasiri,
        AuthenticationError,
        RateLimitError,
        UnsupportedLanguageError,
        ProviderError,
        FasiriError,
    )

    client = Fasiri(api_key="fsri_...")

    try:
        result = client.translate("Hello", target="lug")

    except AuthenticationError as e:
        # Bad or missing API key
        print(f"Auth error: {e}")
        print(f"Code: {e.code}")

    except RateLimitError as e:
        # Rate limited - wait and retry
        import time
        print(f"Rate limited. Waiting {e.retry_after}s...")
        time.sleep(e.retry_after)

    except UnsupportedLanguageError as e:
        # Language not supported
        print(f"Language error: {e}")

    except ProviderError as e:
        # All providers failed - retry later
        print(f"Provider error: {e}")

    except FasiriError as e:
        # Catch-all for any Fasiri error
        print(f"Error {e.code}: {e}")
    ```

=== "REST API"

    ```python
    import httpx
    import time

    def translate_with_retry(text, target, max_retries=3):
        for attempt in range(max_retries):
            r = httpx.post(
                "https://api.fasiri-ai.com//api/v1/translate",
                headers={"Authorization": "Bearer fsri_..."},
                json={"text": text, "target_lang": target},
            )

            if r.status_code == 200:
                return r.json()

            elif r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", 10))
                time.sleep(retry_after)

            elif r.status_code == 503:
                time.sleep(2 ** attempt)  # exponential backoff

            else:
                r.raise_for_status()

        raise Exception("Max retries exceeded")
    ```

## Exception hierarchy

```
FasiriError
├── AuthenticationError     # 401 - bad/missing key
├── RateLimitError          # 429 - rate limited
├── UnsupportedLanguageError # 422 - language not supported
└── ProviderError           # 503 - all providers failed
```
