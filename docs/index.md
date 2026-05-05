# Fasiri Documentation

## What is Fasiri?

**Fasiri** (Swahili: *to interpret*) is a unified REST API and Python SDK that connects your application to the best African language AI providers available. Instead of integrating with Sunbird AI, Khaya AI, and HuggingFace separately, you make one call to Fasiri and it handles provider selection, fallback routing, and error recovery automatically.

Fasiri is designed for developers building applications that need to communicate across African languages - whether that is a healthcare platform serving rural communities, an agricultural advisory service, a government citizen portal, or a multilingual chatbot.

---

## Capabilities

**Translation**

Translate text between English and 19+ African languages with automatic provider routing and quality scoring. Supports single requests and batch translation.

[Get started with translation](guides/translation.md)

**Speech-to-Text**

Transcribe audio recordings in Luganda, Acholi, Ateso, Runyankore, Lugbara, and Swahili with high accuracy models from Sunbird AI.

[Get started with STT](guides/speech-workflows.md)

**Text-to-Speech**

Synthesise natural-sounding speech in Ugandan languages using Sunbird AI voice models.

[Get started with TTS](guides/speech-workflows.md)

**Python SDK**

A clean, synchronous and asynchronous Python client with full type hints and comprehensive error handling. Install with `pip install fasiri`.

[Install the SDK](getting-started/installation.md)

---

## How it works

When you send a translation request to Fasiri, the routing engine selects the best provider for the given language pair:

```
Request: translate "Good morning" to Luganda (lug)

  Step 1 - Identify best provider -> Sunbird AI (specialised for Ugandan languages)
  Step 2 - Call Sunbird AI /tasks/translate
  Step 3 - If Sunbird fails -> try Khaya AI (if pair supported)
  Step 4 - If Khaya fails  -> try HuggingFace Helsinki-NLP
  Step 5 - Return result with provider metadata and quality score
```

This means your application keeps working even when individual providers have downtime.

### Provider coverage

| Provider | Languages | Capabilities |
|---|---|---|
| Sunbird AI | Luganda, Acholi, Ateso, Runyankore, Lugbara | Translation, STT, TTS |
| Khaya AI | Yoruba, Twi, Ewe, Ga, Dagbani, Kikuyu, Luo, Kimeru, Kusaal | Translation |
| HuggingFace | Swahili, French, Arabic, Afrikaans, multilingual fallback | Translation |

---

## Quick example

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

# Translate to Luganda
result = client.translate("Good morning", target="lug")
print(result.translated_text)   # "Wasuze otya"
print(result.provider)           # "sunbird"
print(result.quality_score)      # 0.92

# Translate to Yoruba
result = client.translate("How are you?", target="yo")
print(result.translated_text)   # "Bawo ni"
print(result.provider)           # "khaya"

# Translate to Swahili
result = client.translate("Thank you", target="sw")
print(result.translated_text)   # "Asante"
print(result.provider)           # "huggingface"
```

---

## API base URL

All REST API requests go to:

```
https://fasiri-bu9u.onrender.com
```

Interactive API documentation (Swagger UI):

```
https://fasiri-bu9u.onrender.com/docs
```

---

## Next steps

- [Install the Python SDK](getting-started/installation.md)
- [Get an API key](getting-started/authentication.md)
- [View all supported languages](getting-started/languages.md)
- [Read the translation guide](guides/translation.md)
