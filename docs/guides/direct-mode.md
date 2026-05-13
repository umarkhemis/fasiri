# Direct Mode

Direct mode lets you use the Fasiri SDK with your own provider API keys.
Requests go straight from your application to the provider - nothing passes through
Fasiri servers. You handle your own provider billing. Fasiri is just the routing
and abstraction layer.

This is the same model that LangChain uses with OpenAI, Anthropic, and other providers.

---

## When to use direct mode

Use direct mode when:

- You already have a Sunbird AI, Khaya AI, or HuggingFace account
- You want zero dependency on Fasiri infrastructure
- You are building a self-hosted application
- You need to stay within your existing provider contracts

Use Fasiri Cloud when:

- You want zero setup - one key, everything works
- You do not have existing provider accounts
- You want Fasiri to handle fallback routing and reliability

---

## Setup

Install the SDK:

```bash
pip install fasiri
```

Import the providers you want:

```python
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider, HuggingFaceProvider
```

Create the client with your provider keys:

```python
client = Fasiri(
    providers=[
        SunbirdProvider(api_key="eyJ..."),         # your Sunbird JWT
        KhayaProvider(api_key="your-khaya-key"),    # your Khaya subscription key
        HuggingFaceProvider(api_key="hf_..."),      # your HuggingFace token
    ]
)
```

You can pass one provider or all three. Fasiri routes to the best available one
for each language pair.

---

## Getting provider keys

### Sunbird AI

Sunbird AI provides translation, STT, and TTS for Ugandan languages (Luganda, Acholi,
Ateso, Runyankore, Lugbara).

Register and get a token:

```bash
# 1. Register
curl -X POST https://api.sunbird.ai/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourname",
    "email": "you@example.com",
    "password": "yourpassword"
  }'

# 2. Get JWT token (starts with "ey...")
curl -X POST https://api.sunbird.ai/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=yourpassword"
```

Copy the `access_token` from the response.

```python
from fasiri.providers import SunbirdProvider

provider = SunbirdProvider(api_key="eyJ...")
```

Note: Sunbird tokens expire. When you get a 401 error, refresh your token by
calling `POST https://api.sunbird.ai/auth/token` again.

---

### Khaya AI

Khaya AI provides translation for West and East African languages (Yoruba, Twi, Ewe,
Ga, Dagbani, Kikuyu, Luo, Kimeru, Kusaal, Fante, Gurune).

Register at [translation.ghananlp.org/signup](https://translation.ghananlp.org/signup).
Copy your subscription key from the dashboard.

```python
from fasiri.providers import KhayaProvider

provider = KhayaProvider(api_key="your-subscription-key")
```

Note: Khaya uses an `Ocp-Apim-Subscription-Key` header, not a Bearer token.
The SDK handles this automatically.

---

### HuggingFace

HuggingFace provides translation for Swahili, French, Arabic, and Afrikaans using
verified Helsinki-NLP opus-mt models.

Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
Read access is sufficient.

```python
from fasiri.providers import HuggingFaceProvider

provider = HuggingFaceProvider(api_key="hf_...")
```

---

## Translation

```python
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider, KhayaProvider

client = Fasiri(
    providers=[
        SunbirdProvider(api_key="eyJ..."),
        KhayaProvider(api_key="your-key"),
    ]
)

# Luganda - routed to Sunbird
result = client.translate("Good morning", target="lug")
print(result)          # Wasuze otya
print(result.provider) # sunbird

# Yoruba - routed to Khaya
result = client.translate("How are you?", target="yo")
print(result)          # Bawo ni
print(result.provider) # khaya
```

---

## Batch translation

In direct mode, sync batch processes items sequentially. Async batch runs them
concurrently for much better performance.

```python
# Sync - sequential
results = client.translate_batch([
    {"id": "1", "text": "Good morning",  "target": "lug"},
    {"id": "2", "text": "How are you?",  "target": "yo"},
    {"id": "3", "text": "Thank you",     "target": "tw"},
])

print(f"{results.succeeded}/{results.total} succeeded")
for item in results.successful():
    print(f"[{item.id}] {item.translated_text} via {item.provider}")
```

```python
import asyncio

# Async - concurrent (much faster for large batches)
async def main():
    results = await client.async_translate_batch([
        {"id": "1", "text": "Good morning",  "target": "lug"},
        {"id": "2", "text": "How are you?",  "target": "yo"},
        {"id": "3", "text": "Thank you",     "target": "tw"},
    ])
    print(f"{results.succeeded}/{results.total} succeeded")

asyncio.run(main())
```

---

## Speech-to-Text

STT is only available through SunbirdProvider. If SunbirdProvider is not in your
providers list, `transcribe()` raises `NotImplementedError`.

```python
from fasiri import Fasiri
from fasiri.providers import SunbirdProvider

client = Fasiri(providers=[SunbirdProvider(api_key="eyJ...")])

# From a file path
result = client.transcribe("recording.wav", language="lug")
print(result.transcript)

# From bytes
with open("audio.mp3", "rb") as f:
    result = client.transcribe(f.read(), language="ach")
print(result.transcript)
```

---

## Text-to-Speech

TTS is only available through SunbirdProvider.

```python
result = client.synthesise("Oli otya?", language="lug")
print(result.audio_url)
```

Available TTS languages and voice IDs:

| Language | Code | Voice ID |
|---|---|---|
| Luganda | `lug` | 248 |
| Acholi | `ach` | 241 |
| Ateso | `teo` | 242 |
| Runyankore | `nyn` | 243 |
| Lugbara | `lgg` | 245 |

---

## Using providers directly

You can bypass the Fasiri client entirely and use providers directly:

```python
from fasiri.providers import SunbirdProvider, KhayaProvider

# Sunbird directly
sunbird = SunbirdProvider(api_key="eyJ...")
result = sunbird.translate("Good morning", target_lang="lug")
print(result.translated_text)

# Khaya directly
khaya = KhayaProvider(api_key="your-key")
result = khaya.translate("Good morning", target_lang="yo")
print(result.translated_text)
```

The result is a `DirectTranslationResult` (not `TranslationResult`).
Both have the same fields - `translated_text`, `provider`, `quality_score`, `latency_ms`.

---

## Provider routing logic

When you pass multiple providers, Fasiri picks the best one for each language pair:

```python
client = Fasiri(providers=[
    SunbirdProvider(api_key="eyJ..."),   # handles: lug, ach, teo, nyn, lgg, en
    KhayaProvider(api_key="key"),         # handles: yo, tw, ee, gaa, dag, ki, luo, mer, kus
    HuggingFaceProvider(api_key="hf_"),  # handles: sw, fr, ar, af
])

# Each request goes to the right provider automatically
client.translate("Hello", target="lug") # -> Sunbird
client.translate("Hello", target="yo")  # -> Khaya
client.translate("Hello", target="sw")  # -> HuggingFace
```

If a provider fails, Fasiri tries the next compatible provider automatically.

---

## Error handling

```python
from fasiri import Fasiri, ProviderError, UnsupportedLanguageError
from fasiri.providers import SunbirdProvider

client = Fasiri(providers=[SunbirdProvider(api_key="eyJ...")])

try:
    result = client.translate("Hello", target="lug")

except PermissionError as e:
    # Sunbird token expired - refresh it
    print("Token expired. Get a new one from Sunbird.")

except UnsupportedLanguageError as e:
    # No provider supports this pair
    print(f"Language not supported: {e}")

except ProviderError as e:
    # All providers failed
    print(f"Translation failed: {e}")
```

---

## Comparison: cloud vs direct

| Feature | Cloud mode | Direct mode |
|---|---|---|
| Setup | One `fsri_` key | One key per provider |
| Billing | Fasiri (free now) | Pay providers directly |
| Provider routing | Fasiri handles it | Fasiri SDK handles it |
| Fallback | Automatic | Automatic |
| STT/TTS | Yes | Yes (Sunbird only) |
| Requests go through Fasiri | Yes | No |
| Works offline / self-hosted | No | Yes |
| Interface | Identical | Identical |
