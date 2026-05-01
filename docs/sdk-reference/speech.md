# Speech Methods

## `transcribe()` - Speech to Text

```python
# From file path
stt = client.transcribe("recording.wav", language="lug")
print(stt.transcript)
print(stt.latency_ms)

# From bytes
with open("audio.mp3", "rb") as f:
    stt = client.transcribe(f.read(), language="sw")
```

Returns an [`STTResult`](types.md#sttresult).

**Supported languages:** `lug`, `ach`, `nyn`, `teo`, `lgg`, `sw`, `en`, `rw`

## `synthesise()` / `synthesize()` - Text to Speech

```python
tts = client.synthesise("Oli otya?", language="lug")

# Audio URL (expires ~2 minutes)
print(tts.audio_url)

# Download immediately
import httpx
audio = httpx.get(tts.audio_url).content
with open("output.mp3", "wb") as f:
    f.write(audio)
```

Returns a [`TTSResult`](types.md#ttsresult).

**Supported languages:** `lug`, `ach`, `nyn`, `teo`, `lgg`, `sw`
