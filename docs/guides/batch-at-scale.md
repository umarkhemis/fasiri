# Batch Processing at Scale

How to efficiently translate thousands or millions of texts using Fasiri.

## Batch limits

| Limit | Value |
|---|---|
| Max items per batch call | 50 |
| Max text length per item | 5,000 characters |
| Rate limit (batch endpoint) | 10 requests/minute |
| Effective throughput | 500 translations/minute |

## Basic batch pattern

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

texts = [
    "Good morning",
    "Thank you very much",
    "How are you?",
    # ... more texts
]

batch = client.translate_batch([
    {"id": str(i), "text": text, "target": "lug"}
    for i, text in enumerate(texts)
])

for item in batch:
    if item.success:
        print(f"{item.id}: {item.translated_text}")
    else:
        print(f"{item.id}: FAILED - {item.error}")
```

## Processing large datasets

For more than 50 texts, split into chunks:

```python
import time
from fasiri import Fasiri, RateLimitError

client = Fasiri(api_key="fsri_...")

def translate_large_dataset(
    texts: list[str],
    target: str,
    chunk_size: int = 50,
) -> list[str]:
    """
    Translate any number of texts with automatic chunking and retry.
    Returns translations in the same order as inputs.
    """
    results = {}

    # Split into chunks of 50
    chunks = [texts[i:i+chunk_size] for i in range(0, len(texts), chunk_size)]
    total_chunks = len(chunks)

    for chunk_num, chunk in enumerate(chunks, 1):
        print(f"Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} items)...")

        # Build batch items with global index as ID
        start_idx = (chunk_num - 1) * chunk_size
        items = [
            {"id": str(start_idx + i), "text": text, "target": target}
            for i, text in enumerate(chunk)
        ]

        # Retry on rate limit
        while True:
            try:
                batch = client.translate_batch(items)
                for item in batch:
                    if item.success:
                        results[int(item.id)] = item.translated_text
                    else:
                        results[int(item.id)] = ""  # or original text
                break
            except RateLimitError as e:
                print(f"Rate limited. Waiting {e.retry_after}s...")
                time.sleep(e.retry_after)

        # Respect rate limit: 10 batch calls/minute = 1 every 6 seconds
        if chunk_num < total_chunks:
            time.sleep(6)

    # Return in original order
    return [results.get(i, "") for i in range(len(texts))]

# Usage
texts = ["Hello"] * 500   # 500 texts
translated = translate_large_dataset(texts, target="sw")
print(f"Translated {len(translated)} texts")
```

## Async concurrent processing

For maximum speed, use async with controlled concurrency:

```python
import asyncio
from fasiri import Fasiri

async def translate_at_scale(
    texts: list[str],
    target: str,
    max_concurrent_batches: int = 3,
) -> list[str]:
    """
    Translate texts using concurrent async batch calls.
    max_concurrent_batches controls parallelism (stay within rate limits).
    """
    chunk_size = 50
    chunks = [texts[i:i+chunk_size] for i in range(0, len(texts), chunk_size)]
    semaphore = asyncio.Semaphore(max_concurrent_batches)
    results = {}

    async def process_chunk(chunk_idx: int, chunk: list[str]):
        async with semaphore:
            async with Fasiri(api_key="fsri_...") as client:
                start = chunk_idx * chunk_size
                items = [
                    {"id": str(start + i), "text": t, "target": target}
                    for i, t in enumerate(chunk)
                ]
                batch = await client.async_translate_batch(items)
                for item in batch:
                    if item.success:
                        results[int(item.id)] = item.translated_text

    await asyncio.gather(*[
        process_chunk(i, chunk)
        for i, chunk in enumerate(chunks)
    ])

    return [results.get(i, "") for i in range(len(texts))]

# Usage
texts = ["Good morning"] * 1000
translated = asyncio.run(translate_at_scale(texts, target="yo"))
```

## CSV file translation

```python
import csv
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

def translate_csv(
    input_file: str,
    output_file: str,
    text_column: str,
    target_lang: str,
):
    # Read input
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames + [f"{text_column}_{target_lang}"]

    # Translate in batches
    texts = [row[text_column] for row in rows]
    chunks = [texts[i:i+50] for i in range(0, len(texts), 50)]
    translations = []

    for chunk in chunks:
        items = [{"id": str(i), "text": t, "target": target_lang}
                 for i, t in enumerate(chunk)]
        batch = client.translate_batch(items)
        chunk_results = {int(r.id): r.translated_text or "" for r in batch}
        translations.extend([chunk_results[i] for i in range(len(chunk))])

    # Write output
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row, translation in zip(rows, translations):
            row[f"{text_column}_{target_lang}"] = translation
            writer.writerow(row)

    print(f"Translated {len(rows)} rows -> {output_file}")

# Usage
translate_csv("products.csv", "products_translated.csv",
              text_column="description", target_lang="sw")
```

## Performance benchmarks

Approximate throughput on a stable connection:

| Mode | Texts/minute |
|---|---|
| Single translate (sequential) | ~40 |
| Batch (50 items, sequential) | ~500 |
| Batch (3 concurrent, async) | ~1,500 |
| Batch (5 concurrent, async) | ~2,000 |

!!! warning "Stay within rate limits"
    The batch endpoint allows 10 requests/minute per key. At 50 items per batch, that is 500 translations/minute before hitting limits. Use multiple API keys or contact us for higher limits.
