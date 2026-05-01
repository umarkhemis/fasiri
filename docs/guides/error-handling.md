# Error Handling

## Exception types

```python
from fasiri import (
    FasiriError,
    AuthenticationError,   # 401 - bad/missing key
    RateLimitError,        # 429 - rate limited
    UnsupportedLanguageError, # 422 - language not supported
    ProviderError,         # 503 - all providers failed
)
```

## Retry pattern

```python
import time
from fasiri import Fasiri, RateLimitError, ProviderError

client = Fasiri(api_key="fsri_...")

def translate_with_retry(text: str, target: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return client.translate(text, target=target).translated_text

        except RateLimitError as e:
            time.sleep(e.retry_after)

        except ProviderError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # exponential backoff

        except (AuthenticationError, UnsupportedLanguageError):
            raise  # do not retry these
```

See [Error Reference](../api-reference/errors.md) for all error codes.
