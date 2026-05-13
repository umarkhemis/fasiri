"""
Fasiri direct provider adapters.

Use these when you want to call providers directly with your own API keys,
without going through the Fasiri hosted API.

Example::

    from fasiri import Fasiri
    from fasiri.providers import SunbirdProvider, KhayaProvider, HuggingFaceProvider

    client = Fasiri(
        providers=[
            SunbirdProvider(api_key="your-sunbird-jwt"),
            KhayaProvider(api_key="your-khaya-subscription-key"),
            HuggingFaceProvider(api_key="your-hf-token"),
        ]
    )

    result = client.translate("Good morning", target="lug")
    print(result)  # Wasuze otya
    print(result.provider)  # "sunbird"
"""

from .sunbird import SunbirdProvider
from .khaya import KhayaProvider
from .huggingface import HuggingFaceProvider
from .base import BaseDirectProvider, DirectTranslationResult, DirectSTTResult, DirectTTSResult

__all__ = [
    "SunbirdProvider",
    "KhayaProvider",
    "HuggingFaceProvider",
    "BaseDirectProvider",
    "DirectTranslationResult",
    "DirectSTTResult",
    "DirectTTSResult",
]
