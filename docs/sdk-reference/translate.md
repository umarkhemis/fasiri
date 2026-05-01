# Translation Methods

## `translate()`

```python
result = client.translate(
    text="Hello, how are you?",
    target="lug",
    source="en",      # optional - auto-detected if omitted
    provider="auto",  # "auto" | "sunbird" | "huggingface"
)

print(result)                    # "Oli otya?"
print(result.provider)           # "sunbird"
print(result.quality_score)      # 0.92
print(result.latency_ms)         # 820
print(result.model_used)         # "sunbird/nllb_translate"
```

Returns a [`TranslationResult`](types.md#translationresult).

## `async_translate()`

```python
result = await client.async_translate("Hello", target="lug")
```

See [Async Usage](async.md) for patterns.
