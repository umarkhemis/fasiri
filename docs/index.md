# Fasiri

> **Fasiri** (*Swahili: to interpret*) — Unified translation and speech API for 30+ African languages.

Fasiri brings together the best African language AI providers behind a single consistent interface. One API key. One endpoint. 30+ languages.

## What can Fasiri do?

| Capability        | Languages                                     | Provider        |
|-------------------|-----------------------------------------------|-----------------|
| **Translation**   | Luganda, Yoruba, Swahili, Twi, Acholi, +15 more | Sunbird + Khaya + HuggingFace |
| **Transcription** | Luganda, Acholi, Ateso, Runyankore, Swahili   | Sunbird AI      |
| **Text-to-Speech**| Luganda, Acholi, Ateso, Runyankore, Lugbara   | Sunbird AI      |

## Quick Example

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

# English → Luganda
print(client.translate("Good morning", target="lug"))   # "Wasuze otya"

# English → Yoruba
print(client.translate("How are you?", target="yo"))    # "Báwo ni"

# English → Swahili
print(client.translate("Thank you", target="sw"))        # "Asante"
```

## Architecture

Fasiri automatically selects the best provider for each language pair and falls back gracefully:

```
en → lug  →  Sunbird AI  (best for Ugandan languages)
en → yo   →  Khaya AI    (best for West African languages)  
en → sw   →  HuggingFace (Helsinki-NLP opus-mt-en-sw)
```

## Next Steps

- [Installation](getting-started/installation.md)
- [Authentication](getting-started/authentication.md)
- [Quick Start](getting-started/quickstart.md)
