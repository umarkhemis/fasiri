# Django Integration

```python
# settings.py
import os
FASIRI_API_KEY = os.environ.get("FASIRI_API_KEY")

# utils/translation.py
from django.conf import settings
from fasiri import Fasiri

_client = None

def get_client() -> Fasiri:
    global _client
    if _client is None:
        _client = Fasiri(api_key=settings.FASIRI_API_KEY)
    return _client

# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from utils.translation import get_client
import json

@csrf_exempt
@require_POST
def translate_view(request):
    data = json.loads(request.body)
    client = get_client()
    result = client.translate(
        data["text"],
        target=data["target_lang"],
    )
    return JsonResponse({"translated_text": str(result)})
```
