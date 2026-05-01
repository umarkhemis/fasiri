# Speech to Text

```
POST /api/v1/speech/stt
```

Transcribe an audio file in a supported African language.

## Request

Multipart form data:

| Field | Type | Required | Description |
|---|---|---|---|
| `audio` | file | Yes | Audio file (WAV, MP3, OGG, WebM). Max 10MB. |
| `language` | string | Yes | Language code of the audio, e.g. `lug` |

**Supported languages:** `lug`, `ach`, `nyn`, `teo`, `lgg`, `sw`, `en`, `rw`, `xog`, `myx`

## Response

| Field | Type | Description |
|---|---|---|
| `transcript` | string | Transcribed text |
| `detected_lang` | string | Detected language code |
| `language` | string | Requested language |
| `model_used` | string | Model that processed the audio |
| `provider` | string | Provider used |
| `latency_ms` | int | Processing time in ms |

## Example

```python
with open("audio.wav", "rb") as f:
    stt = client.transcribe(f.read(), language="lug")

print(stt.transcript)
print(stt.latency_ms)
```
