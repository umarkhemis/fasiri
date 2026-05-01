# Speech Workflows

## Voice message transcription and translation

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

def process_voice_message(audio_path: str, language: str) -> dict:
    """Transcribe a voice message and translate to English."""
    with open(audio_path, "rb") as f:
        audio = f.read()

    stt = client.transcribe(audio, language=language)

    if language != "en":
        translation = client.translate(stt.transcript, target="en")
        english_text = translation.translated_text
    else:
        english_text = stt.transcript

    return {
        "transcript":   stt.transcript,
        "english":      english_text,
        "language":     language,
        "latency_ms":   stt.latency_ms,
    }

result = process_voice_message("message.wav", language="lug")
print(result["english"])
```

## Generate audio responses

```python
def audio_reply(text_in_english: str, target_language: str) -> str | None:
    """Translate a reply and return an audio URL."""
    tts_langs = {l.code for l in client.speech_languages() if l.supports_tts}
    if target_language not in tts_langs:
        return None

    if target_language != "en":
        text = client.translate(text_in_english, target=target_language).translated_text
    else:
        text = text_in_english

    tts = client.synthesise(text, language=target_language)
    return tts.audio_url
```
