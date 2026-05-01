# Exceptions

Fasiri raises typed exceptions so you can handle different failure modes precisely.

## Exception hierarchy

```
FasiriError (base)
├── AuthenticationError     HTTP 401
├── RateLimitError          HTTP 429
├── UnsupportedLanguageError HTTP 422
└── ProviderError           HTTP 503
```

## Import

```python
from fasiri import (
    FasiriError,
    AuthenticationError,
    RateLimitError,
    UnsupportedLanguageError,
    ProviderError,
)
```

---

## FasiriError

Base class for all Fasiri exceptions.

```python
class FasiriError(Exception):
    message:     str
    code:        str   # machine-readable error code
    status_code: int   # HTTP status code
```

---

## AuthenticationError

Raised when the API key is missing, invalid, or expired.

```python
try:
    client = Fasiri()  # no key set
except AuthenticationError as e:
    print(e.code)  # "MISSING_API_KEY"

try:
    result = client.translate("Hello", target="lug")
except AuthenticationError as e:
    print(e.code)         # "INVALID_API_KEY"
    print(e.status_code)  # 401
```

---

## RateLimitError

Raised when the rate limit is exceeded.

```python
class RateLimitError(FasiriError):
    retry_after: int   # seconds to wait before retrying
```

```python
import time
from fasiri import RateLimitError

try:
    result = client.translate("Hello", target="lug")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
    time.sleep(e.retry_after)
    result = client.translate("Hello", target="lug")  # retry
```

---

## UnsupportedLanguageError

Raised when a language or language pair is not supported.

```python
from fasiri import UnsupportedLanguageError

try:
    result = client.translate("Hello", target="xx")
except UnsupportedLanguageError as e:
    print(e)  # "Language not supported..."
```

---

## ProviderError

Raised when all providers fail to translate the text. Usually transient — retry with exponential backoff.

```python
import time
from fasiri import ProviderError

for attempt in range(3):
    try:
        result = client.translate("Hello", target="lug")
        break
    except ProviderError:
        time.sleep(2 ** attempt)
```

---

## Catching all Fasiri errors

```python
from fasiri import FasiriError

try:
    result = client.translate("Hello", target="lug")
except FasiriError as e:
    print(f"Fasiri error [{e.code}]: {e}")
    print(f"HTTP status: {e.status_code}")
```
