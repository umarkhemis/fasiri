# Providers Overview

Fasiri routes requests to the best available provider for each language pair.

## Sunbird AI
**Languages:** Luganda, Acholi, Ateso, Runyankore, Lugbara  
**Capabilities:** Translation, STT, TTS  
**Register:** [api.sunbird.ai](https://api.sunbird.ai/auth/register)

Built specifically for Ugandan languages. Get a JWT token:
```bash
curl -X POST https://api.sunbird.ai/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@email.com&password=yourpassword"
```
Set `SUNBIRD_API_KEY=<access_token>` in `.env`.

---

## Khaya AI
**Languages:** Yoruba, Twi, Ewe, Ga, Fante, Dagbani, Kikuyu, Luo, Kimeru, Kusaal  
**Capabilities:** Translation only  
**Register:** [translation.ghananlp.org](https://translation.ghananlp.org/signup)

Purpose-built for West/East African languages via GhanaNLP API v2.  
Set `KHAYA_API_KEY=<subscription_key>` in `.env`.

---

## HuggingFace
**Languages:** Swahili, French, Arabic, Afrikaans, multilingual fallback  
**Capabilities:** Translation only  
**Register:** [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

Uses verified Helsinki-NLP models. Acts as last-resort fallback.  
Set `HUGGINGFACE_API_KEY=<token>` in `.env`.

---

## Fallback Chain

```
en → lug:  Sunbird → Khaya → HuggingFace → 503
en → yo:   Khaya → HuggingFace → 503
en → sw:   HuggingFace → 503
```
