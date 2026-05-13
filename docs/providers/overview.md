# Providers Overview

Fasiri supports three AI providers. In cloud mode, Fasiri manages them for you.
In direct mode, you configure them yourself with your own keys.

---

## Sunbird AI

**Languages:** Luganda, Acholi, Ateso, Runyankore, Lugbara (and English)
**Capabilities:** Translation, Speech-to-Text, Text-to-Speech
**Register:** [api.sunbird.ai](https://api.sunbird.ai/auth/register)

Built specifically for Ugandan languages. The only provider offering STT and TTS
for these languages.

**Get a token:**

```bash
curl -X POST https://api.sunbird.ai/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@email.com&password=yourpassword"
```

The `access_token` in the response is a JWT starting with `ey...`. It expires
periodically - refresh it by calling the same endpoint again.

**Direct mode:**

```python
from fasiri.providers import SunbirdProvider

provider = SunbirdProvider(api_key="eyJ...")

result = provider.translate("Good morning", target_lang="lug")
print(result)  # Wasuze otya

stt = provider.speech_to_text(audio_bytes, language="lug")
print(stt.transcript)

tts = provider.text_to_speech("Oli otya?", language="lug")
print(tts.audio_url)
```

---

## Khaya AI

**Languages:** Yoruba, Twi, Ewe, Ga, Fante, Dagbani, Gurune, Kikuyu, Luo, Kimeru, Kusaal
**Capabilities:** Translation only
**Register:** [translation.ghananlp.org/signup](https://translation.ghananlp.org/signup)

GhanaNLP's translation API v2. Purpose-built for West and East African languages.
Uses an `Ocp-Apim-Subscription-Key` header - the SDK handles this automatically.

**Direct mode:**

```python
from fasiri.providers import KhayaProvider

provider = KhayaProvider(api_key="your-subscription-key")

result = provider.translate("Good morning", target_lang="yo")
print(result)  # Bawo ni
```

**Supported pairs:**

All `en -> lang` and `lang -> en` combinations for: `yo, tw, ee, gaa, fat, dag, gur, ki, luo, mer, kus`

---

## HuggingFace

**Languages:** Swahili, French, Arabic, Afrikaans (and Yoruba -> English)
**Capabilities:** Translation only
**Register:** [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

Uses verified Helsinki-NLP opus-mt models. Acts as the fallback layer.

Note: `facebook/nllb-200-distilled-600M` was removed from the hf-inference
provider in 2025 and is no longer supported.

**Direct mode:**

```python
from fasiri.providers import HuggingFaceProvider

provider = HuggingFaceProvider(api_key="hf_...")

result = provider.translate("Good morning", target_lang="sw")
print(result)  # Habari ya asubuhi
```

**Verified deployed models:**

| Pair | Model |
|---|---|
| en -> sw | Helsinki-NLP/opus-mt-en-sw |
| sw -> en | Helsinki-NLP/opus-mt-sw-en |
| en -> fr | Helsinki-NLP/opus-mt-en-fr |
| fr -> en | Helsinki-NLP/opus-mt-fr-en |
| en -> ar | Helsinki-NLP/opus-mt-en-ar |
| ar -> en | Helsinki-NLP/opus-mt-ar-en |
| en -> af | Helsinki-NLP/opus-mt-en-af |
| af -> en | Helsinki-NLP/opus-mt-af-en |
| yo -> en | Helsinki-NLP/opus-mt-yo-en |

---

## Fallback chain

In both cloud and direct mode, if the primary provider fails,
Fasiri tries the next compatible provider automatically.

```
en -> lug:  Sunbird -> (HuggingFace mul fallback)
en -> yo:   Khaya   -> (HuggingFace mul fallback)
en -> sw:   HuggingFace Helsinki -> mul fallback
```

In direct mode, fallback only uses providers you have configured.
