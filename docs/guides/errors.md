# Error Handling

## Exception Hierarchy

```
FasiriError
├── AuthenticationError     # 401 — invalid or missing API key
├── RateLimitError          # 429 — too many requests
├── UnsupportedLanguageError # 422 — language pair not supported
└── ProviderError           # 503 — all providers failed
```

## Handling Errors

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
    # Invalid, expired, or missing API key
    print(f"Auth failed: {e}")

except RateLimitError as e:
    # Rate limit exceeded — wait and retry
    import time
    time.sleep(e.retry_after)

except UnsupportedLanguageError as e:
    # Language pair not supported
    print(f"Not supported: {e}")

except ProviderError as e:
    # All providers failed - transient error
    print(f"Provider error: {e}")

except FasiriError as e:
    # Any other Fasiri error
    print(f"Error [{e.code}]: {e}")
```

## HTTP Error Codes

| Status | Exception                | Meaning                          |
|--------|--------------------------|----------------------------------|
| `401`  | `AuthenticationError`    | Invalid or missing API key       |
| `422`  | `UnsupportedLanguageError` | Unsupported language or bad input |
| `429`  | `RateLimitError`         | Rate limit exceeded              |
| `503`  | `ProviderError`          | All translation providers failed |
| `500`  | `ProviderError`          | Internal server error            |
