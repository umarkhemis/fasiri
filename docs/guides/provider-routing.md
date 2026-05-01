# Provider Routing

Fasiri automatically routes each request to the best available model.

## Routing logic

1. The registry maps language pairs to models with quality scores
2. The router picks the highest-scoring model for the pair
3. If the primary provider fails, it falls back to HuggingFace

## Quality scores by provider

| Provider | Languages | Score |
|---|---|---|
| Sunbird AI | lug, nyn, ach, teo, lgg | 0.92 |
| Helsinki-NLP opus-mt | sw, yo, ha, ig, zu, rw | 0.78-0.85 |
| opus-mt-en-mul | 100+ language fallback | 0.62 |

## Override routing

```python
# Force Sunbird AI
result = client.translate("Hello", target="lug", provider="sunbird")

# Force HuggingFace
result = client.translate("Hello", target="sw", provider="huggingface")

# Auto (default)
result = client.translate("Hello", target="lug")
```

## REST API provider override

```json
{
  "text": "Hello",
  "target_lang": "lug",
  "provider": "sunbird"
}
```
