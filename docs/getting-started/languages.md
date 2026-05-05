# Supported Languages

Fasiri supports 19+ African languages across translation, speech-to-text, and text-to-speech capabilities.

## Full Language Table

| Code | Language | Region | Family | Translation | STT | TTS | Provider |
|---|---|---|---|:---:|:---:|:---:|---|
| `lug` | Luganda | East Africa | Bantu | Yes | Yes | Yes | Sunbird AI |
| `ach` | Acholi | East Africa | Nilotic | Yes | Yes | Yes | Sunbird AI |
| `teo` | Ateso | East Africa | Nilotic | Yes | Yes | Yes | Sunbird AI |
| `nyn` | Runyankore | East Africa | Bantu | Yes | Yes | Yes | Sunbird AI |
| `lgg` | Lugbara | East Africa | Central Sudanic | Yes | Yes | Yes | Sunbird AI |
| `yo` | Yoruba | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `tw` | Twi | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `ee` | Ewe | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `gaa` | Ga | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `fat` | Fante | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `dag` | Dagbani | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `gur` | Gurune | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `ki` | Kikuyu | East Africa | Bantu | Yes | No | No | Khaya AI |
| `luo` | Luo | East Africa | Nilotic | Yes | No | No | Khaya AI |
| `mer` | Kimeru | East Africa | Bantu | Yes | No | No | Khaya AI |
| `kus` | Kusaal | West Africa | Niger-Congo | Yes | No | No | Khaya AI |
| `sw` | Swahili | East Africa | Bantu | Yes | Yes | No | HuggingFace |
| `fr` | French | Francophone Africa | Romance | Yes | No | No | HuggingFace |
| `ar` | Arabic | North Africa | Semitic | Yes | No | No | HuggingFace |
| `af` | Afrikaans | South Africa | Germanic | Yes | No | No | HuggingFace |
| `en` | English | Global | Germanic | Yes | Yes | No | All providers |

## Translation Pairs

Fasiri supports translation between English and any of the African languages above. Direct translation between two non-English African languages (e.g. Luganda to Yoruba) is not currently supported - requests must pivot through English.

Supported direction patterns:

- English to African language: `en -> lug`, `en -> yo`, `en -> sw`, etc.
- African language to English: `lug -> en`, `yo -> en`, `sw -> en`, etc.

## Speech Coverage

Speech capabilities are currently limited to Sunbird AI's supported languages. These are the five main languages of Uganda plus English.

| Language | STT | TTS | Notes |
|---|:---:|:---:|---|
| Luganda (`lug`) | Yes | Yes | Female voice (voice ID 248) |
| Acholi (`ach`) | Yes | Yes | Female voice (voice ID 241) |
| Ateso (`teo`) | Yes | Yes | Female voice (voice ID 242) |
| Runyankore (`nyn`) | Yes | Yes | Female voice (voice ID 243) |
| Lugbara (`lgg`) | Yes | Yes | Female voice (voice ID 245) |
| Swahili (`sw`) | Yes | No | STT via Sunbird, TTS not available |
| English (`en`) | Yes | No | STT via Sunbird |

## Checking languages at runtime

Use the SDK or REST API to get the current language list, which includes real-time capability information:

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

# All languages
languages = client.languages()
for lang in languages:
    print(f"{lang.code}: {lang.name} ({lang.region})")

# Translation-capable languages only
for lang in client.translation_languages():
    print(f"{lang.code}: {lang.name} via {lang.best_provider}")

# Speech-capable languages only
for lang in client.speech_languages():
    caps = []
    if lang.supports_stt: caps.append("STT")
    if lang.supports_tts: caps.append("TTS")
    print(f"{lang.code}: {lang.name} - {', '.join(caps)}")
```

Via REST:

```bash
curl https://fasiri-bu9u.onrender.com/api/v1/languages \
  -H "Authorization: Bearer fsri_..."
```
