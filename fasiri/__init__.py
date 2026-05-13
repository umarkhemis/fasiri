"""
fasiri - Official Python SDK for the Fasiri African Language API.

Two modes of operation:

**Cloud mode** - use the hosted Fasiri API (free key at fasiri-bu9u.onrender.com)::

    from fasiri import Fasiri

    client = Fasiri(api_key="fsri_...")
    result = client.translate("Good morning", target="lug")
    print(result)  # Wasuze otya

**Direct mode** - call providers directly with your own API keys (free, no Fasiri account)::

    from fasiri import Fasiri
    from fasiri.providers import SunbirdProvider, KhayaProvider, HuggingFaceProvider

    client = Fasiri(
        providers=[
            SunbirdProvider(api_key="eyJ..."),         # your Sunbird JWT
            KhayaProvider(api_key="your-khaya-key"),    # your Khaya subscription key
            HuggingFaceProvider(api_key="hf_..."),      # your HuggingFace token
        ]
    )

    result = client.translate("Good morning", target="lug")
    print(result)          # Wasuze otya
    print(result.provider) # "sunbird"

In direct mode, Fasiri routes requests to the best provider automatically
and falls back if one fails. Requests go straight from your machine to the
provider - you handle your own provider billing.
"""

from .client import (
    Fasiri,
    FasiriError,
    AuthenticationError,
    BatchItemResult,
    BatchResult,
    Language,
    ProviderError,
    RateLimitError,
    STTResult,
    TTSResult,
    TranslationResult,
    UnsupportedLanguageError,
)

__all__ = [
    "Fasiri",
    # Results
    "TranslationResult",
    "BatchResult",
    "BatchItemResult",
    "STTResult",
    "TTSResult",
    "Language",
    # Exceptions
    "FasiriError",
    "AuthenticationError",
    "RateLimitError",
    "UnsupportedLanguageError",
    "ProviderError",
]

__version__ = "1.1.0"
