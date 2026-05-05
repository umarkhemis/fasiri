#!/usr/bin/env python3
"""
Fasiri API - Live Test Script
================================
Tests every endpoint against your running server.

Usage:
    python test_live.py                          # uses defaults
    python test_live.py --url https://fasiri-bu9u.onrender.com
    python test_live.py --key fsri_yourkey
    python test_live.py --url https://your-deployed-api.com --key fsri_...

Requirements:
    pip install httpx rich
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

# ── Try to import rich for pretty output, fall back gracefully ────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL = "https://fasiri-bu9u.onrender.com"
API_KEY  = None   # set via --key or auto-issued below

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭  SKIP"
WARN = "⚠️  WARN"

results = []


def header(title: str):
    line = "─" * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def log(status: str, name: str, detail: str = "", latency_ms: int = 0):
    lat = f"  [{latency_ms}ms]" if latency_ms else ""
    line = f"  {status}  {name}{lat}"
    if detail:
        line += f"\n         {detail}"
    print(line)
    results.append({"status": status, "name": name, "detail": detail})


def post(path: str, body: dict, auth: bool = True, timeout: int = 30) -> tuple[int, dict]:
    headers = {}
    if auth and API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    t0 = time.monotonic()
    try:
        r = httpx.post(f"{BASE_URL}{path}", json=body, headers=headers, timeout=timeout)
        ms = int((time.monotonic() - t0) * 1000)
        try:
            return r.status_code, r.json(), ms
        except Exception:
            return r.status_code, {"raw": r.text}, ms
    except httpx.ConnectError:
        print(f"\n  ❌  Cannot connect to {BASE_URL}")
        print(f"     Is your server running?  uvicorn app.main:app --reload\n")
        sys.exit(1)


def get(path: str, auth: bool = False, timeout: int = 15) -> tuple[int, dict, int]:
    headers = {}
    if auth and API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    t0 = time.monotonic()
    r = httpx.get(f"{BASE_URL}{path}", headers=headers, timeout=timeout)
    ms = int((time.monotonic() - t0) * 1000)
    try:
        return r.status_code, r.json(), ms
    except Exception:
        return r.status_code, {"raw": r.text}, ms


def check(condition: bool, name: str, detail: str = "", latency_ms: int = 0):
    log(PASS if condition else FAIL, name, detail, latency_ms)
    return condition


# ═══════════════════════════════════════════════════════════════════════════════
# 1. System / Health
# ═══════════════════════════════════════════════════════════════════════════════

def test_system():
    header("1. SYSTEM ENDPOINTS")

    # Health check
    code, body, ms = get("/health")
    check(code == 200 and body.get("status") == "ok",
          "GET /health", f"status={body.get('status')}  providers={body.get('providers')}", ms)

    # Root
    code, body, ms = get("/")
    check(code == 200 and "Fasiri" in body.get("name", ""),
          "GET /", f"name={body.get('name')}  version={body.get('version')}", ms)

    # OpenAPI schema
    code, body, ms = get("/openapi.json")
    check(code == 200 and "paths" in body,
          "GET /openapi.json", f"{len(body.get('paths', {}))} endpoints documented", ms)

    # Docs UI
    r = httpx.get(f"{BASE_URL}/docs")
    check(r.status_code == 200,
          "GET /docs (Swagger UI)", f"HTTP {r.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Authentication
# ═══════════════════════════════════════════════════════════════════════════════

def test_auth() -> str | None:
    """Returns a fresh API key on success."""
    header("2. AUTHENTICATION")
    global API_KEY

    # Issue a new key
    code, body, ms = post("/api/v1/auth/keys", {"name": "test-script"}, auth=False)
    if not check(code == 201 and body.get("api_key", "").startswith("fsri_"),
                 "POST /api/v1/auth/keys (issue key)",
                 f"key={body.get('api_key', 'MISSING')[:20]}...", ms):
        return None

    fresh_key = body["api_key"]
    if not API_KEY:
        API_KEY = fresh_key
        print(f"\n  ℹ️   Using freshly issued key: {fresh_key[:24]}...")

    # No auth → 401
    code, body, ms = post("/api/v1/translate", {"text": "hi", "target_lang": "sw"}, auth=False)
    check(code == 401 and body.get("detail", {}).get("code") == "MISSING_API_KEY",
          "POST /translate without key → 401",
          f"code={body.get('detail', {}).get('code')}", ms)

    # Bad key → 401
    bad_headers = {"Authorization": "Bearer fsri_" + "x" * 40}
    r = httpx.post(f"{BASE_URL}/api/v1/translate",
                   json={"text": "hi", "target_lang": "sw"},
                   headers=bad_headers, timeout=10)
    check(r.status_code == 401,
          "POST /translate with invalid key → 401",
          f"HTTP {r.status_code}")

    # Inspect key
    code, body, ms = get("/api/v1/auth/keys/me", auth=True)
    check(code == 200 and "name" in body,
          "GET /auth/keys/me",
          f"name={body.get('name')}  requests={body.get('requests_total')}", ms)

    return fresh_key


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Languages
# ═══════════════════════════════════════════════════════════════════════════════

def test_languages():
    header("3. LANGUAGES ENDPOINT")

    code, body, ms = get("/api/v1/languages")
    if not check(code == 200, "GET /languages", f"HTTP {code}", ms):
        return

    langs = body.get("languages", [])
    check(len(langs) >= 20,
          f"Returns ≥20 languages",
          f"Got {len(langs)} languages")

    codes = {l["code"] for l in langs}
    for required in ["en", "sw", "yo", "ha", "ig", "zu", "lug", "nyn", "ach", "teo"]:
        check(required in codes,
              f"Language '{required}' present",
              f"{'found' if required in codes else 'MISSING'}")

    tts_langs = [l for l in langs if l["supports_tts"]]
    stt_langs = [l for l in langs if l["supports_stt"]]
    check(len(tts_langs) >= 5,
          "TTS-capable languages",
          f"{[l['code'] for l in tts_langs]}")
    check(len(stt_langs) >= 5,
          "STT-capable languages",
          f"{[l['code'] for l in stt_langs]}")

    sunbird_langs = [l for l in langs if l["best_provider"] == "sunbird"]
    check(len(sunbird_langs) > 0,
          "Sunbird languages in registry",
          f"{[l['code'] for l in sunbird_langs]}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Single Translation
# ═══════════════════════════════════════════════════════════════════════════════

def test_translation():
    header("4. SINGLE TRANSLATION")

    test_cases = [
        # (description, source, target, text, provider)
        ("English → Luganda  [Sunbird]",    "en",  "lug", "Hello, how are you?",    "sunbird"),
        ("English → Runyankole [Sunbird]",  "en",  "nyn", "Good morning",           "sunbird"),
        ("English → Acholi [Sunbird]",      "en",  "ach", "Thank you very much",    "sunbird"),
        ("English → Ateso [Sunbird]",       "en",  "teo", "My name is Fasiri",    "sunbird"),
        ("English → Lugbara [Sunbird]",     "en",  "lgg", "Welcome to Uganda",      "sunbird"),
        ("Luganda → English [Sunbird]",     "lug", "en",  "Oli otya?",              "sunbird"),
        ("English → Swahili [HuggingFace]", "en",  "sw",  "Hello, how are you?",    "auto"),
        ("English → Yoruba [HuggingFace]",  "en",  "yo",  "Good morning",           "auto"),
        ("English → Hausa [HuggingFace]",   "en",  "ha",  "Welcome",                "auto"),
        ("English → Igbo [HuggingFace]",    "en",  "ig",  "How are you?",           "auto"),
        ("English → Zulu [HuggingFace]",    "en",  "zu",  "Thank you",              "auto"),
        ("Auto-detect source language",     None,  "sw",  "Bonjour le monde",       "auto"),
    ]

    for desc, src, tgt, text, provider in test_cases:
        body_in = {"text": text, "target_lang": tgt, "provider": provider}
        if src:
            body_in["source_lang"] = src

        code, body, ms = post("/api/v1/translate", body_in, timeout=40)

        if code == 200:
            translated = body.get("translated_text", "")
            model = body.get("model_used", "")
            prov  = body.get("provider", "")
            score = body.get("quality_score", 0)
            check(bool(translated),
                  desc,
                  f'"{translated[:60]}"  model={model.split("/")[-1]}  score={score}',
                  ms)
        elif code == 503:
            log(WARN, desc,
                f"503 - provider unavailable (check your API keys): "
                f"{body.get('detail', {}).get('message', '')[:100]}", ms)
        else:
            log(FAIL, desc, f"HTTP {code}: {json.dumps(body)[:120]}", ms)

    # Validation edge cases
    code, body, ms = post("/api/v1/translate", {"text": "", "target_lang": "sw"})
    check(code == 422, "Empty text → 422", f"HTTP {code}", ms)

    code, body, ms = post("/api/v1/translate",
                          {"text": "x" * 5001, "target_lang": "sw"})
    check(code == 422, "Text > 5000 chars → 422", f"HTTP {code}", ms)

    code, body, ms = post("/api/v1/translate",
                          {"text": "Hello", "target_lang": "en", "source_lang": "en"})
    check(code == 400 and body.get("detail", {}).get("code") == "SAME_LANGUAGE",
          "Same source/target → 400", f"code={body.get('detail', {}).get('code')}", ms)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Batch Translation
# ═══════════════════════════════════════════════════════════════════════════════

def test_batch():
    header("5. BATCH TRANSLATION")

    items = [
        {"id": "greet",   "text": "Hello everyone",     "target_lang": "lug"},
        {"id": "thanks",  "text": "Thank you so much",  "target_lang": "ach"},
        {"id": "morning", "text": "Good morning",       "target_lang": "nyn"},
        {"id": "welcome", "text": "You are welcome",    "target_lang": "teo"},
        {"id": "swahili", "text": "How are you?",       "target_lang": "sw"},
        {"id": "yoruba",  "text": "My name is John",    "target_lang": "yo"},
    ]

    code, body, ms = post("/api/v1/translate/batch", {"items": items}, timeout=60)

    if not check(code == 200, "POST /translate/batch",
                 f"HTTP {code}", ms):
        if code == 503:
            log(WARN, "Batch skipped", "Provider unavailable - check API keys")
        return

    check(body["total"] == len(items),
          f"Batch total == {len(items)}", f"got {body['total']}")
    check(body["succeeded"] + body["failed"] == body["total"],
          "succeeded + failed == total",
          f"{body['succeeded']} succeeded, {body['failed']} failed")

    print(f"\n  {'ID':<12} {'Target':<8} {'Status':<8} Translation")
    print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*40}")
    for r in body["results"]:
        status  = "ok" if r["error"] is None else "ERROR"
        text    = r.get("translated_text") or r.get("error") or ""
        print(f"  {r['id']:<12} {r['target_lang']:<8} {status:<8} {text[:50]}")

    # Validation
    code2, _, ms2 = post("/api/v1/translate/batch", {"items": []})
    check(code2 == 422, "Empty batch → 422", f"HTTP {code2}", ms2)

    big_items = [{"id": str(i), "text": "hi", "target_lang": "sw"} for i in range(51)]
    code3, _, ms3 = post("/api/v1/translate/batch", {"items": big_items})
    check(code3 == 422, ">50 items → 422", f"HTTP {code3}", ms3)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Speech - TTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_tts():
    header("6. TEXT-TO-SPEECH")

    tts_cases = [
        ("lug", "Oli otya? Nkuwa amazima.",   "Luganda"),
        ("ach", "Itye nining?",                "Acholi"),
        ("nyn", "Agandi?",                     "Runyankole"),
        ("teo", "Yoga apei?",                  "Ateso"),
        ("lgg", "Muki opi?",                   "Lugbara"),
        ("sw",  "Habari yako?",                "Swahili"),
    ]

    for lang, text, lang_name in tts_cases:
        code, body, ms = post("/api/v1/speech/tts",
                              {"text": text, "language": lang},
                              timeout=30)
        if code == 200:
            audio_url = body.get("audio_url")
            has_audio = bool(audio_url or body.get("audio_base64"))
            check(has_audio,
                  f"TTS {lang_name} ({lang})",
                  f"audio_url={str(audio_url)[:60] if audio_url else 'base64'}  "
                  f"provider={body.get('provider')}",
                  ms)
        elif code == 422:
            log(WARN, f"TTS {lang_name} ({lang})", f"Unsupported language (422)", ms)
        elif code == 503:
            log(WARN, f"TTS {lang_name} ({lang})", f"Provider unavailable (503) - check SUNBIRD_API_KEY", ms)
        else:
            log(FAIL, f"TTS {lang_name} ({lang})", f"HTTP {code}: {json.dumps(body)[:100]}", ms)

    # Validation
    code, _, ms = post("/api/v1/speech/tts", {"text": "Hello", "language": "yo"})
    check(code == 422, "TTS unsupported language (yo) → 422", f"HTTP {code}", ms)

    code, _, ms = post("/api/v1/speech/tts", {"text": "x" * 2001, "language": "lug"})
    check(code == 422, "TTS text > 2000 chars → 422", f"HTTP {code}", ms)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Speech - STT
# ═══════════════════════════════════════════════════════════════════════════════

def test_stt():
    header("7. SPEECH-TO-TEXT")

    # Generate a minimal valid WAV file in memory (1 second of silence)
    def make_wav(duration_secs: float = 1.0, sample_rate: int = 16000) -> bytes:
        import struct, math
        num_samples = int(sample_rate * duration_secs)
        data = struct.pack(f"<{num_samples}h", *([0] * num_samples))
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", 36 + len(data), b"WAVE",
            b"fmt ", 16, 1, 1,
            sample_rate, sample_rate * 2, 2, 16,
            b"data", len(data),
        )
        return header + data

    silent_wav = make_wav(1.0)

    # Test STT with a silent WAV (we just check the endpoint works, not the transcript)
    for lang in ["lug", "ach", "sw"]:
        files = {"audio": ("test.wav", silent_wav, "audio/wav")}
        data  = {"language": lang}
        headers = {"Authorization": f"Bearer {API_KEY}"}

        t0 = time.monotonic()
        r = httpx.post(f"{BASE_URL}/api/v1/speech/stt",
                       files=files, data=data, headers=headers, timeout=60)
        ms = int((time.monotonic() - t0) * 1000)

        if r.status_code == 200:
            body = r.json()
            transcript = body.get("transcript", "")
            check(True,
                  f"STT {lang} (silent WAV)",
                  f'transcript="{transcript[:50]}"  provider={body.get("provider")}',
                  ms)
        elif r.status_code == 503:
            log(WARN, f"STT {lang}", f"Provider unavailable (503) - check SUNBIRD_API_KEY", ms)
        else:
            log(FAIL, f"STT {lang}", f"HTTP {r.status_code}: {r.text[:120]}", ms)

    # Unsupported language
    files = {"audio": ("test.wav", silent_wav, "audio/wav")}
    r = httpx.post(f"{BASE_URL}/api/v1/speech/stt",
                   files=files, data={"language": "yo"},
                   headers={"Authorization": f"Bearer {API_KEY}"},
                   timeout=10)
    check(r.status_code == 422,
          "STT unsupported language (yo) → 422",
          f"HTTP {r.status_code}")

    # File too large
    big_audio = b"x" * (11 * 1024 * 1024)
    r = httpx.post(f"{BASE_URL}/api/v1/speech/stt",
                   files={"audio": ("big.wav", big_audio, "audio/wav")},
                   data={"language": "lug"},
                   headers={"Authorization": f"Bearer {API_KEY}"},
                   timeout=10)
    check(r.status_code == 413,
          "STT file > 10MB → 413",
          f"HTTP {r.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Debug / Provider Diagnostics
# ═══════════════════════════════════════════════════════════════════════════════

def test_debug():
    header("8. DEBUG / PROVIDER DIAGNOSTICS")
    print("  ℹ️   Requires DEBUG=true in .env\n")

    code, body, ms = get("/api/v1/debug/env")
    if code == 404:
        log(SKIP, "GET /debug/env", "DEBUG=false in .env (enable to use)")
        return

    check(code == 200, "GET /debug/env", "", ms)
    if code == 200:
        hf = body.get("huggingface_api_key", "NOT SET")
        sb = body.get("sunbird_api_key", "NOT SET")
        hf_url = body.get("huggingface_base_url", "")
        sb_jwt = body.get("sunbird_key_looks_like_jwt", False)
        print(f"  ℹ️   HuggingFace key: {hf}")
        print(f"  ℹ️   HuggingFace URL: {hf_url}")
        print(f"  ℹ️   Sunbird key:     {sb}")
        print(f"  ℹ️   Sunbird JWT ok:  {sb_jwt}")
        if not sb_jwt:
            print(f"\n  ⚠️   Sunbird key does not look like a JWT!")
            print(f"      Run: curl -X POST https://api.sunbird.ai/auth/token \\")
            print(f"             -H 'Content-Type: application/x-www-form-urlencoded' \\")
            print(f"             -d 'username=you@example.com&password=yourpassword'")
        if "api-inference" in hf_url:
            print(f"\n  ❌  HUGGINGFACE_BASE_URL is the OLD dead URL!")
            print(f"      Fix in .env: HUGGINGFACE_BASE_URL=https://router.huggingface.co/hf-inference/models")

    code, body, ms = get("/api/v1/debug/providers", timeout=30)
    if code == 200:
        overall = body.get("overall", "unknown")
        providers = body.get("providers", {})
        check(overall == "ok",
              "Provider connectivity check",
              f"overall={overall}", ms)
        for name, info in providers.items():
            status = info.get("status", "unknown")
            icon = "✅" if status == "ok" else ("⚠️ " if status == "loading" else "❌")
            print(f"\n  {icon}  {name.upper()}: {status}")
            if status == "ok":
                print(f"         sample: {info.get('sample_translation', '')[:60]}")
            elif status == "auth_error":
                print(f"         diagnosis: {info.get('diagnosis', '')}")
                print(f"         fix: {info.get('fix', '')}")
            elif info.get("message"):
                print(f"         {info['message']}")
            elif info.get("body"):
                print(f"         response: {info['body'][:120]}")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Rate Limiting
# ═══════════════════════════════════════════════════════════════════════════════

def test_rate_limit():
    header("9. RATE LIMITING")

    # Issue a dedicated key for rate limit testing
    code, body, _ = post("/api/v1/auth/keys", {"name": "rate-limit-test"}, auth=False)
    if code != 201:
        log(SKIP, "Rate limit test", "Could not issue test key")
        return

    test_key = body["api_key"]
    headers  = {"Authorization": f"Bearer {test_key}"}

    # Make requests until we get 429 or we've made 100 (whichever comes first)
    got_429 = False
    count   = 0
    print(f"  ℹ️   Firing requests rapidly until 429 or 100 requests...")
    for i in range(100):
        r = httpx.post(
            f"{BASE_URL}/api/v1/translate",
            json={"text": "Hello", "target_lang": "sw"},
            headers=headers, timeout=10,
        )
        count += 1
        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After", "?")
            check(True, "Rate limit 429 triggered",
                  f"after {count} requests. Retry-After: {retry_after}s")
            got_429 = True
            break

    if not got_429:
        log(WARN, "Rate limit not triggered",
            f"Made {count} requests without 429. "
            f"RATE_LIMIT_RPM might be very high or provider errors are stopping early.")


# ═══════════════════════════════════════════════════════════════════════════════
# 10. SDK Integration (if fasiri SDK is installed)
# ═══════════════════════════════════════════════════════════════════════════════

def test_sdk():
    header("10. PYTHON SDK")

    try:
        from fasiri_sdk import Fasiri, AuthenticationError, UnsupportedLanguageError
    except ImportError:
        log(SKIP, "SDK not installed", "pip install -e sdk/ to run SDK tests")
        return

    # Missing key raises
    try:
        import os
        saved = os.environ.pop("FASIRI_API_KEY", None)
        try:
            Fasiri()
            log(FAIL, "SDK missing key → AuthenticationError", "No exception raised")
        except AuthenticationError:
            log(PASS, "SDK missing key → AuthenticationError")
        finally:
            if saved:
                os.environ["FASIRI_API_KEY"] = saved
    except Exception as e:
        log(FAIL, "SDK auth error test", str(e))

    # Translate
    try:
        client = Fasiri(api_key=API_KEY, base_url=BASE_URL)
        result = client.translate("Hello, how are you?", target="lug")
        check(bool(str(result)),
              "SDK client.translate()",
              f'"{str(result)[:60]}"  score={result.quality_score}')
    except Exception as e:
        log(WARN, "SDK translate", f"{type(e).__name__}: {e}")

    # Batch
    try:
        client = Fasiri(api_key=API_KEY, base_url=BASE_URL)
        batch = client.translate_batch([
            {"id": "a", "text": "Good morning", "target": "ach"},
            {"id": "b", "text": "Thank you",    "target": "nyn"},
        ])
        check(batch.total == 2,
              "SDK client.translate_batch()",
              f"total={batch.total}  succeeded={batch.succeeded}  "
              f"failed={batch.failed}")
    except Exception as e:
        log(WARN, "SDK batch", f"{type(e).__name__}: {e}")

    # Languages
    try:
        client = Fasiri(api_key=API_KEY, base_url=BASE_URL)
        langs = client.languages()
        check(len(langs) >= 20,
              "SDK client.languages()",
              f"{len(langs)} languages returned")
    except Exception as e:
        log(FAIL, "SDK languages", f"{type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════

def summary():
    passed  = sum(1 for r in results if r["status"] == PASS)
    failed  = sum(1 for r in results if r["status"] == FAIL)
    warned  = sum(1 for r in results if r["status"] == WARN)
    skipped = sum(1 for r in results if r["status"] == SKIP)
    total   = len(results)

    print("\n" + "═" * 60)
    print("  RESULTS SUMMARY")
    print("═" * 60)
    print(f"  ✅ Passed:  {passed}")
    print(f"  ❌ Failed:  {failed}")
    print(f"  ⚠️  Warned:  {warned}")
    print(f"  ⏭  Skipped: {skipped}")
    print(f"  ─────────────")
    print(f"  Total:     {total}")

    if failed > 0:
        print(f"\n  FAILED TESTS:")
        for r in results:
            if r["status"] == FAIL:
                print(f"    • {r['name']}")
                if r["detail"]:
                    print(f"      {r['detail']}")

    if warned > 0:
        print(f"\n  WARNINGS (likely provider API key issues):")
        for r in results:
            if r["status"] == WARN:
                print(f"    • {r['name']}: {r['detail'][:100]}")

    print("\n" + "═" * 60)
    return failed == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fasiri API live test script")
    parser.add_argument("--url",  default="https://fasiri-bu9u.onrender.com",
                        help="API base URL (default: https://fasiri-bu9u.onrender.com)")
    parser.add_argument("--key",  default=None,
                        help="Fasiri API key (auto-issued if not provided)")
    parser.add_argument("--skip", nargs="*", default=[],
                        choices=["system","auth","languages","translate",
                                 "batch","tts","stt","debug","ratelimit","sdk"],
                        help="Test suites to skip")
    args = parser.parse_args()

    BASE_URL = args.url.rstrip("/")
    API_KEY  = args.key

    print(f"\n{'═'*60}")
    print(f"  Fasiri API - Live Test Suite")
    print(f"{'═'*60}")
    print(f"  Target:  {BASE_URL}")
    print(f"  Key:     {'provided' if API_KEY else 'will auto-issue'}")
    print(f"{'═'*60}")

    skip = set(args.skip or [])

    if "system"    not in skip: test_system()
    if "auth"      not in skip: test_auth()
    if "languages" not in skip: test_languages()
    if "translate" not in skip: test_translation()
    if "batch"     not in skip: test_batch()
    if "tts"       not in skip: test_tts()
    if "stt"       not in skip: test_stt()
    if "debug"     not in skip: test_debug()
    if "ratelimit" not in skip: test_rate_limit()
    if "sdk"       not in skip: test_sdk()

    ok = summary()
    sys.exit(0 if ok else 1)
