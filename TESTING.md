# Fasiri - Testing Guide

## Scripts at a glance

| Script | Purpose | Time |
|---|---|---|
| `smoke_test.py` | Quick pass/fail per provider | ~10s |
| `test_live.py` | Full endpoint coverage | ~2-3 min |
| `stress_test.py` | Concurrency / latency / throughput | configurable |
| `get_sunbird_token.py` | Get/refresh your Sunbird JWT | ~5s |
| `pytest tests/` | Unit + integration tests (mocked) | ~15s |

---

## 1. First-time setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install httpx rich   # extra test deps

# Copy and fill in your .env
cp env.example .env

# Get your Sunbird JWT (interactive)
python get_sunbird_token.py

# Start the server
uvicorn app.main:app --reload
```

---

## 2. Smoke test - run this first

Always run this after changing `.env` or restarting the server.

```bash
python smoke_test.py
```

**Expected output (both providers working):**
```
  Server reachable         status=ok  huggingface=live  sunbird=live
  Issue API key             key=fsri_a1b2c3d4...
  Sunbird  en→lug  [820ms]  "Oli otya?"
  Sunbird  lug→en  [750ms]  "How are you?"
  HuggingFace  en→sw  [1240ms]  "Habari yako?"
  HuggingFace  en→yo  [1300ms]  "E dupe"
  Batch  2 items  [1100ms]  succeeded=2  failed=0
  TTS  lug  [900ms]  audio_url=https://storage.googleapis.com/...
  All checks passed
```

**Common failures:**

| Error | Cause | Fix |
|---|---|---|
| `Sunbird 503 - 405 Method Not Allowed` | Bad/missing JWT | `python get_sunbird_token.py` |
| `HuggingFace 503 - 404 Not Found` | Wrong base URL | Set `HUGGINGFACE_BASE_URL=https://router.huggingface.co/hf-inference/models` |
| `HuggingFace 503 - model loading` | Cold start | Wait 20s and retry |
| `Server reachable ` | Server not running | `uvicorn app.main:app --reload` |

---

## 3. Full test suite

Tests every endpoint with validation, edge cases, and the Python SDK.

```bash
# Run all suites
python test_live.py

# With a specific URL and key
python test_live.py --url https://fasiri-bu9u.onrender.com --key fsri_yourkey

# Skip slow suites
python test_live.py --skip ratelimit stt

# Skip multiple
python test_live.py --skip stt tts ratelimit sdk
```

### What each suite tests

**1. System** - `/health`, `/`, `/docs`, `/openapi.json`

**2. Auth** - Issue keys, reject missing/bad keys, inspect key metadata

**3. Languages** - All 32 languages present, STT/TTS flags correct, Sunbird languages tagged

**4. Translation** - 12 test cases across all supported language pairs:
- Sunbird: en→lug, en→nyn, en→ach, en→teo, en→lgg, lug→en
- HuggingFace: en→sw, en→yo, en→ha, en→ig, en→zu
- Auto-detect: French → Swahili
- Validation: empty text, too long, same language

**5. Batch** - 6-item batch, partial failure handling, size limits

**6. TTS** - All 6 Sunbird TTS voices (lug, ach, nyn, teo, lgg, sw), validation

**7. STT** - Silent WAV upload for lug/ach/sw, unsupported language, file too large

**8. Debug** - Provider connectivity check (requires `DEBUG=true`)

**9. Rate limiting** - Confirms 429 fires after limit exceeded

**10. SDK** - Python SDK `translate()`, `translate_batch()`, `languages()`

---

## 4. Stress test

```bash
# Default: 10 concurrent, 50 total requests
python stress_test.py

# Heavy load
python stress_test.py --concurrency 25 --total 200

# Batch endpoint only
python stress_test.py --endpoint batch --concurrency 5 --total 30

# Against deployed API
python stress_test.py --url https://your-api.com --key fsri_...
```

**Expected output:**
```
  Endpoint:    POST /api/v1/translate
  Concurrency: 10 simultaneous requests
  Total:       50 requests

  [████████████████████████████████████████] 50/50 (100%)  ✅47 ❌0 🚦0

  Total wall time: 18.4s  (2.7 req/s)

  Requests:
    Total:        50
     200 OK:    47  (94.0%)
     Errors:    0   (0.0%)
      503s:      3   (provider unavailable)
     429s:      0   (rate limited)

  Latency (successful requests only):
    Min:   620ms
    Avg:   1840ms
    p50:   1750ms
    p95:   3200ms
    p99:   4100ms
    Max:   4800ms
```

---

## 5. Unit tests (mocked, no server needed)

```bash
# All 52 unit tests
pytest tests/ -v

# Single test class
pytest tests/test_translate.py::TestTranslation -v

# With coverage
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 6. Refreshing your Sunbird token

Sunbird JWTs expire. When you see `405` errors:

```bash
# Interactive
python get_sunbird_token.py

# Non-interactive (CI/CD)
python get_sunbird_token.py \
  --email you@example.com \
  --password yourpassword \
  --env-file .env

# Just print token, don't write .env
python get_sunbird_token.py --no-write
```

The script automatically updates `SUNBIRD_API_KEY` in your `.env` and verifies the token works.

---

## 7. Debug endpoint

With `DEBUG=true` in `.env`:

```bash
# Show env config (values masked)
curl https://fasiri-bu9u.onrender.com/api/v1/debug/env

# Live provider connectivity check
curl https://fasiri-bu9u.onrender.com/api/v1/debug/providers
```

The `/debug/providers` response tells you exactly what's wrong and how to fix it.
