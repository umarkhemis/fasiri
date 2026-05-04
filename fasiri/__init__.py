"""
fasiri – Official Python SDK for the Fasiri African Language API.

Quick start::

    from fasiri import Fasiri

    client = Fasiri(api_key="fsri_...")

    # Translate
    result = client.translate("Hello, how are you?", target="sw")
    print(result)  # Habari, ukoje?

    # Batch
    batch = client.translate_batch([
        {"id": "1", "text": "Good morning", "target": "lug"},
        {"id": "2", "text": "Thank you",    "target": "yo"},
    ])
    for item in batch:
        print(item.id, item)

    # Speech-to-Text
    stt = client.transcribe("speech.wav", language="lug")
    print(stt.transcript)

    # Text-to-Speech
    tts = client.synthesise("Oli otya?", language="lug")
    print(tts.audio_url)

    # List languages
    for lang in client.languages():
        print(lang)
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

__version__ = "1.0.0"
