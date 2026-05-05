# Exceptions

All Fasiri exceptions can be imported from the top-level `fasiri` package:

```python
from fasiri import (
    FasiriError,
    AuthenticationError,
    RateLimitError,
    UnsupportedLanguageError,
    ProviderError,
)
```

## FasiriError

Base class for all Fasiri exceptions.

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `message` | str | Human-readable error description. |
| `code` | str | Machine-readable error code, e.g. `"INVALID_API_KEY"`. |
| `status_code` | int | HTTP status code from the API. |

## AuthenticationError

Raised when the API key is missing, invalid, or expired.

**HTTP status:** 401

**Error codes:**
- `MISSING_API_KEY` - No Authorization header provided
- `INVALID_API_KEY` - Key does not exist or has expired

```python
from fasiri import Fasiri, AuthenticationError

try:
    client = Fasiri(api_key="fsri_invalid")
    result = client.translate("Hello", target="lug")
except AuthenticationError as e:
    print(e.code)    # "INVALID_API_KEY"
    print(e.status_code)  # 401
```

## RateLimitError

Raised when the rate limit is exceeded.

**HTTP status:** 429

**Additional attribute:** `retry_after` (int) - seconds to wait before retrying.

```python
from fasiri import Fasiri, RateLimitError
import time

try:
    result = client.translate("Hello", target="lug")
except RateLimitError as e:
    print(f"Rate limited. Wait {e.retry_after} seconds.")
    time.sleep(e.retry_after)
```

## UnsupportedLanguageError

Raised when a language code is not recognised or a language pair is not supported.

**HTTP status:** 422

```python
from fasiri import Fasiri, UnsupportedLanguageError

try:
    result = client.translate("Hello", target="xyz")
except UnsupportedLanguageError as e:
    print(f"Language not supported: {e}")
```

## ProviderError

Raised when all providers fail to translate the requested text. This is typically a transient error caused by provider outages or network issues.

**HTTP status:** 503

```python
from fasiri import Fasiri, ProviderError

try:
    result = client.translate("Hello", target="lug")
except ProviderError as e:
    # Show original text or cached result to user
    print(f"Translation temporarily unavailable: {e}")
```
