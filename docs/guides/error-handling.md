# Error Handling

Building a resilient application means handling errors gracefully. This guide covers all error types you may encounter when using Fasiri and how to handle them.

## Exception hierarchy

All Fasiri exceptions inherit from `FasiriError`:

```
FasiriError
|-- AuthenticationError     (HTTP 401)
|-- RateLimitError          (HTTP 429)
|-- UnsupportedLanguageError (HTTP 422)
+-- ProviderError           (HTTP 503)
```

## Basic error handling

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
    print(result.translated_text)

except AuthenticationError as e:
    # Invalid or expired API key
    print(f"Authentication failed: {e}")
    print(f"Error code: {e.code}")

except RateLimitError as e:
    # Too many requests - wait and retry
    import time
    print(f"Rate limited. Retrying in {e.retry_after} seconds...")
    time.sleep(e.retry_after)

except UnsupportedLanguageError as e:
    # Language pair not supported by any provider
    print(f"Language not supported: {e}")

except ProviderError as e:
    # All providers failed - transient error
    print(f"Translation unavailable: {e}")
    # Show original text or cached translation to user

except FasiriError as e:
    # Catch-all for any other Fasiri error
    print(f"Fasiri error [{e.code}]: {e}")
```

## Retry logic

For transient errors (provider failures, network issues), implement exponential backoff:

```python
import time
from fasiri import Fasiri, ProviderError, RateLimitError

client = Fasiri(api_key="fsri_...")

def translate_with_retry(text, target, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.translate(text, target=target)

        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(e.retry_after)
            else:
                raise

        except ProviderError:
            if attempt < max_retries - 1:
                wait = 2 ** attempt   # 1s, 2s, 4s
                time.sleep(wait)
            else:
                raise

    return None
```

## HTTP error reference

| HTTP Status | Exception | Common causes |
|---|---|---|
| `401` | `AuthenticationError` | Missing, invalid, or expired API key |
| `422` | `UnsupportedLanguageError` | Language code not recognised, pair not supported |
| `429` | `RateLimitError` | Exceeded 60 requests/minute (or 10 batch/minute) |
| `503` | `ProviderError` | All providers failed for this language pair |
| `500` | `ProviderError` | Internal server error |

## Accessing error details

All exceptions expose `.code` and `.status_code`:

```python
try:
    result = client.translate("Hello", target="xyz")
except FasiriError as e:
    print(e.code)         # e.g. "UNSUPPORTED_LANGUAGE"
    print(e.status_code)  # e.g. 422
    print(str(e))         # Human-readable message
```

`RateLimitError` additionally exposes `.retry_after` (seconds to wait before retrying).
