# Text to Speech

```
POST /api/v1/speech/tts
```

Synthesise text as audio.

## Request

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Text to synthesise. Max 2,000 characters. |
| `language` | string | Yes | Language code, e.g. `lug` |
| `voice_id` | integer | No | Specific voice ID. Auto-selected if omitted. |

**Supported languages and voice IDs:**

| Language | Code | Voice ID |
|---|---|---|
| Luganda | `lug` | 248 |
| Acholi | `ach` | 241 |
| Runyankole | `nyn` | 243 |
| Ateso | `teo` | 242 |
| Lugbara | `lgg` | 245 |
| Swahili | `sw` | 246 |

## Response

| Field | Type | Description |
|---|---|---|
| `audio_url` | string | Signed URL to download audio (expires ~2 min) |
| `content_type` | string | `audio/mpeg` |
| `language` | string | Language code |
| `model_used` | string | TTS model used |
| `latency_ms` | int | Processing time in ms |

!!! warning "Audio URL expires in 2 minutes"
    Download the audio immediately after receiving the URL.

## Example

```python
tts = client.synthesise("Oli otya?", language="lug")

# Download the audio
import httpx
audio = httpx.get(tts.audio_url).content
with open("output.mp3", "wb") as f:
    f.write(audio)
```
