# Translate a Document

Translate a multi-paragraph document using batch processing:

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

def translate_document(text: str, target: str) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    items = [
        {"id": str(i), "text": p, "target": target}
        for i, p in enumerate(paragraphs)
    ]

    batch = client.translate_batch(items)
    translated = {int(r.id): r.translated_text for r in batch.successful()}

    return "\n\n".join(
        translated.get(i, paragraphs[i])
        for i in range(len(paragraphs))
    )

with open("document.txt") as f:
    text = f.read()

result = translate_document(text, target="sw")
print(result)
```
