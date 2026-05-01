# Building a Multilingual App

This guide walks through adding African language support to a real web application — a customer support platform that needs to serve users in Uganda, Nigeria, and Tanzania.

## The goal

- Accept support tickets in any language
- Auto-detect the language and translate to English for the support team
- Reply in the user's original language
- Support voice messages from users

## Setup

```bash
pip install fasiri python-dotenv
```

```python
# config.py
from dotenv import load_dotenv
from fasiri import Fasiri

load_dotenv()
client = Fasiri()  # reads FASIRI_API_KEY from environment
```

## Step 1 - Receive a ticket in any language

```python
# tickets.py
from fasiri import Fasiri, FasiriError

client = Fasiri()

def receive_ticket(user_id: str, message: str) -> dict:
    """
    Accept a support ticket in any language.
    Auto-detects the source language.
    """
    try:
        # Translate to English for the support team
        # source_lang omitted — Fasiri auto-detects
        translation = client.translate(message, target="en")

        return {
            "user_id":       user_id,
            "original_text": message,
            "english_text":  translation.translated_text,
            "user_language": translation.detected_source_lang,
            "provider":      translation.provider,
        }

    except FasiriError as e:
        return {
            "user_id":       user_id,
            "original_text": message,
            "english_text":  message,  # fallback: show original
            "user_language": "unknown",
            "error":         str(e),
        }

# Example
ticket = receive_ticket("user_123", "Nkwagala obuyambi")
print(ticket["english_text"])    # "I need help"
print(ticket["user_language"])   # "lug"
```

## Step 2 - Reply in the user's language

```python
def reply_to_ticket(ticket: dict, reply_in_english: str) -> str:
    """
    Translate a support reply into the user's language.
    """
    user_lang = ticket.get("user_language", "en")

    if user_lang == "en" or user_lang == "unknown":
        return reply_in_english

    try:
        result = client.translate(
            reply_in_english,
            target=user_lang,
            source="en",
        )
        return result.translated_text

    except FasiriError:
        return reply_in_english  # fallback to English

# Example
reply = reply_to_ticket(
    ticket,
    "Thank you for contacting us. We will resolve your issue within 24 hours."
)
print(reply)  # "Webale kutuwanjako. Tunarekebisha tatizo lako ndani ya saa 24."
```

## Step 3 - Handle voice messages

```python
def process_voice_ticket(user_id: str, audio_bytes: bytes, language: str) -> dict:
    """
    Transcribe a voice message and translate it to English.
    """
    # Step 1: Transcribe
    stt = client.transcribe(audio_bytes, language=language)

    # Step 2: Translate to English
    if language != "en":
        translation = client.translate(stt.transcript, target="en")
        english_text = translation.translated_text
    else:
        english_text = stt.transcript

    return {
        "user_id":       user_id,
        "transcript":    stt.transcript,
        "english_text":  english_text,
        "user_language": language,
    }
```

## Step 4 - Batch process overnight tickets

```python
def process_overnight_tickets(tickets: list[dict]) -> list[dict]:
    """
    Translate a backlog of tickets efficiently using batch API.
    """
    # Build batch items
    items = [
        {
            "id":     ticket["id"],
            "text":   ticket["original_text"],
            "target": "en",
            # source omitted — auto-detect
        }
        for ticket in tickets
        if ticket.get("user_language") != "en"
    ]

    if not items:
        return tickets

    # One API call for up to 50 tickets
    batch = client.translate_batch(items)

    # Map results back to tickets
    result_map = {r.id: r for r in batch.results}

    for ticket in tickets:
        result = result_map.get(ticket["id"])
        if result and result.success:
            ticket["english_text"]  = result.translated_text
            ticket["user_language"] = result.detected_source_lang

    print(f"Processed {batch.succeeded}/{batch.total} tickets")
    return tickets
```

## Step 5 - Send audio replies (TTS)

```python
import httpx

def send_audio_reply(reply_text: str, user_language: str) -> str | None:
    """
    Convert a text reply to audio for users who prefer voice.
    Returns the audio URL or None if TTS not supported for this language.
    """
    # Check if TTS is supported for this language
    tts_langs = {l.code for l in client.speech_languages() if l.supports_tts}
    if user_language not in tts_langs:
        return None

    tts = client.synthesise(reply_text, language=user_language)
    return tts.audio_url

# Example
audio_url = send_audio_reply(
    "Webale kutuwanjako.",
    user_language="sw",
)
if audio_url:
    print(f"Audio reply: {audio_url}")
```

## Complete example: Django view

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from fasiri import Fasiri, FasiriError

client = Fasiri()

@csrf_exempt
@require_POST
def submit_ticket(request):
    data = json.loads(request.body)
    user_id = data.get("user_id")
    message = data.get("message", "")

    try:
        translation = client.translate(message, target="en")

        ticket = {
            "user_id":       user_id,
            "original_text": message,
            "english_text":  translation.translated_text,
            "user_language": translation.detected_source_lang,
        }

        # save_ticket(ticket)  # your database call

        return JsonResponse({"status": "received", "ticket": ticket})

    except FasiriError as e:
        return JsonResponse({"error": str(e)}, status=500)
```

## Language detection tips

!!! tip "Provide source_lang when you know it"
    If your UI asks users to select their language, pass it explicitly. Auto-detection is good but explicit is always faster and more reliable:
    ```python
    # If user selected "Luganda" in your UI
    client.translate(text, target="en", source="lug")
    ```

!!! tip "Validate language support before processing"
    ```python
    supported_codes = {l.code for l in client.translation_languages()}
    if user_language not in supported_codes:
        # fallback to English or prompt user
        pass
    ```
