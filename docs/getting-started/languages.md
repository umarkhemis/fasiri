# Supported Languages

Fasiri supports 30+ African languages across translation, speech-to-text (STT), and text-to-speech (TTS).

## Language table

| Code | Language | Native Name | Region | Translate | STT | TTS | Provider |
|---|---|---|---|---|---|---|---|
| `lug` | Luganda | Oluganda | East Africa | ✅ | ✅ | ✅ | <span class="badge-sunbird">SUNBIRD</span> |
| `ach` | Acholi | Acholi | East Africa | ✅ | ✅ | ✅ | <span class="badge-sunbird">SUNBIRD</span> |
| `nyn` | Runyankole | Runyankore | East Africa | ✅ | ✅ | ✅ | <span class="badge-sunbird">SUNBIRD</span> |
| `teo` | Ateso | Ateso | East Africa | ✅ | ✅ | ✅ | <span class="badge-sunbird">SUNBIRD</span> |
| `lgg` | Lugbara | Lugbara | East Africa | ✅ | ✅ | ✅ | <span class="badge-sunbird">SUNBIRD</span> |
| `sw` | Swahili | Kiswahili | East Africa | ✅ | ✅ | ✅ | <span class="badge-sunbird">SUNBIRD</span> / <span class="badge-hf">HF</span> |
| `rw` | Kinyarwanda | Ikinyarwanda | East Africa | ✅ | ✅ | - | <span class="badge-hf">HF</span> |
| `xog` | Lusoga | Olusoga | East Africa | ✅ | ✅ | - | <span class="badge-sunbird">SUNBIRD</span> |
| `myx` | Lumasaba | Lumasaaba | East Africa | ✅ | ✅ | - | <span class="badge-sunbird">SUNBIRD</span> |
| `laj` | Lango | Lango | East Africa | ✅ | ✅ | - | <span class="badge-sunbird">SUNBIRD</span> |
| `adh` | Jopadhola | Dhopadhola | East Africa | ✅ | ✅ | - | <span class="badge-sunbird">SUNBIRD</span> |
| `am` | Amharic | አማርኛ | East Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `so` | Somali | Soomaali | East Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `om` | Oromo | Oromoo | East Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `yo` | Yoruba | Yorùbá | West Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `ha` | Hausa | Hausa | West Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `ig` | Igbo | Igbo | West Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `tw` | Twi | Twi | West Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `wo` | Wolof | Wolof | West Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `ff` | Fula | Fulfulde | West Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `zu` | Zulu | IsiZulu | Southern Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `xh` | Xhosa | IsiXhosa | Southern Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `af` | Afrikaans | Afrikaans | Southern Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `sn` | Shona | ChiShona | Southern Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `st` | Sotho | Sesotho | Southern Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `tn` | Tswana | Setswana | Southern Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `ar` | Arabic | العربية | North Africa | ✅ | - | - | <span class="badge-hf">HF</span> |
| `en` | English | English | Global | ✅ | ✅ | - | All |
| `fr` | French | Français | Global | ✅ | - | - | <span class="badge-hf">HF</span> |
| `pt` | Portuguese | Português | Global | ✅ | - | - | <span class="badge-hf">HF</span> |

## TTS Voice IDs

For text-to-speech, each language has a specific voice:

| Language | Code | Voice ID | Voice |
|---|---|---|---|
| Acholi | `ach` | `241` | Female |
| Ateso | `teo` | `242` | Female |
| Runyankole | `nyn` | `243` | Female |
| Lugbara | `lgg` | `245` | Female |
| Swahili | `sw` | `246` | Male |
| Luganda | `lug` | `248` | Female |

## Programmatic access

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

# Get all languages
languages = client.languages()

# Filter to translation-only
translatable = client.translation_languages()

# Filter to speech-capable
speech = client.speech_languages()

# Check a specific language
for lang in languages:
    if lang.code == "lug":
        print(lang.supports_tts)    # True
        print(lang.tts_voice_id)    # 248
        print(lang.best_provider)   # sunbird
        print(lang.quality_score)   # 0.92
```

## REST API

```bash
curl https://api.fasiri.betatechlabs.io/api/v1/languages
```

```json
{
  "languages": [
    {
      "code": "lug",
      "name": "Luganda",
      "native_name": "Oluganda",
      "region": "East Africa",
      "family": "Niger-Congo",
      "supports_translation": true,
      "supports_stt": true,
      "supports_tts": true,
      "tts_voice_id": 248,
      "best_provider": "sunbird",
      "quality_score": 0.92
    }
  ],
  "total": 30
}
```

!!! note "Language coverage is growing"
    We add new languages regularly. Follow the [changelog](../changelog.md) or watch the GitHub repo for updates.
