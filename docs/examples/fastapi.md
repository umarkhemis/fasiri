# FastAPI Integration

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fasiri import Fasiri, FasiriError
import os

app = FastAPI(title="My Multilingual API")
client = Fasiri(api_key=os.environ["FASIRI_API_KEY"])

class TranslateRequest(BaseModel):
    text: str
    target: str
    source: str | None = None

class TranslateResponse(BaseModel):
    translated_text: str
    provider: str
    quality_score: float

@app.post("/translate", response_model=TranslateResponse)
async def translate(body: TranslateRequest):
    result = await client.async_translate(
        body.text,
        target=body.target,
        source=body.source,
    )
    return TranslateResponse(
        translated_text=result.translated_text,
        provider=result.provider,
        quality_score=result.quality_score,
    )
```

See [Async Usage](../sdk-reference/async.md) for more patterns.
