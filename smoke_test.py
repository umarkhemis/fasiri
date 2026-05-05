#!/usr/bin/env python3
"""
Fasiri - Quick Smoke Test
=============================
Runs in ~10 seconds. Tests one call per provider and prints a clear diagnosis.
Run this first whenever something breaks.

Usage:
    python smoke_test.py
    python smoke_test.py --url https://fasiri-bu9u.onrender.com
"""
from __future__ import annotations

import argparse
import sys
import time
import httpx

BASE_URL = "https://fasiri-bu9u.onrender.com"

def check(label: str, ok: bool, detail: str = "") -> bool:
    icon = "✅" if ok else "❌"
    print(f"  {icon}  {label}")
    if detail:
        print(f"       {detail}")
    return ok


def main():
    all_ok = True

    print(f"\n{'─'*50}")
    print(f"  Fasiri Smoke Test  →  {BASE_URL}")
    print(f"{'─'*50}\n")

    # ── 1. Server reachable ────────────────────────────────────────────────
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=5)
        if not check("Server reachable", r.status_code == 200,
                     f"status={r.json().get('status')}"):
            all_ok = False
            print("\n  ❌  Server is not running. Start with:")
            print(f"      uvicorn app.main:app --reload")
            sys.exit(1)

        providers = r.json().get("providers", {})
        hf_mode = providers.get("huggingface", "unknown")
        sb_mode = providers.get("sunbird", "unknown")
        print(f"       huggingface={hf_mode}  sunbird={sb_mode}")
        if hf_mode == "stub":
            print(f"  ⚠️   HUGGINGFACE_API_KEY not set - HF calls will fail")
        if sb_mode == "stub":
            print(f"  ⚠️   SUNBIRD_API_KEY not set - Sunbird calls will fail")
            print(f"       Run: python get_sunbird_token.py")
    except httpx.ConnectError:
        print(f"  ❌  Cannot connect to {BASE_URL}")
        print(f"      Start server: uvicorn app.main:app --reload")
        sys.exit(1)

    print()

    # ── 2. Get API key ─────────────────────────────────────────────────────
    r = httpx.post(f"{BASE_URL}/api/v1/auth/keys",
                   json={"name": "smoke-test"}, timeout=5)
    if not check("Issue API key", r.status_code == 201):
        sys.exit(1)
    key = r.json()["api_key"]
    headers = {"Authorization": f"Bearer {key}"}
    print(f"       key={key[:24]}...\n")

    # ── 3. Sunbird: English → Luganda ──────────────────────────────────────
    t0 = time.monotonic()
    r = httpx.post(f"{BASE_URL}/api/v1/translate",
                   json={"text": "Hello, how are you?",
                         "target_lang": "lug", "source_lang": "en",
                         "provider": "sunbird"},
                   headers=headers, timeout=30)
    ms = int((time.monotonic() - t0) * 1000)

    if r.status_code == 200:
        body = r.json()
        all_ok &= check(
            f"Sunbird  en→lug  [{ms}ms]",
            bool(body.get("translated_text")),
            f'"{body.get("translated_text", "")}"  '
            f'model={body.get("model_used","").split("/")[-1]}  '
            f'score={body.get("quality_score")}'
        )
    elif r.status_code == 503:
        detail = r.json().get("detail", {})
        msg = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        check(f"Sunbird  en→lug  [{ms}ms]", False,
              f"503 - {msg[:120]}\n"
              f"       → Check SUNBIRD_API_KEY is a valid JWT (starts with ey...)\n"
              f"       → Run: python get_sunbird_token.py")
        all_ok = False
    else:
        check(f"Sunbird  en→lug  [{ms}ms]", False,
              f"HTTP {r.status_code}: {r.text[:120]}")
        all_ok = False

    # ── 4. Sunbird: Luganda → English ──────────────────────────────────────
    t0 = time.monotonic()
    r = httpx.post(f"{BASE_URL}/api/v1/translate",
                   json={"text": "Oli otya?",
                         "target_lang": "en", "source_lang": "lug",
                         "provider": "sunbird"},
                   headers=headers, timeout=30)
    ms = int((time.monotonic() - t0) * 1000)

    if r.status_code == 200:
        body = r.json()
        all_ok &= check(
            f"Sunbird  lug→en  [{ms}ms]",
            bool(body.get("translated_text")),
            f'"{body.get("translated_text", "")}"'
        )
    else:
        check(f"Sunbird  lug→en  [{ms}ms]", False,
              f"HTTP {r.status_code}: {r.text[:100]}")
        all_ok = False

    print()

    # ── 5. HuggingFace: English → Swahili ─────────────────────────────────
    t0 = time.monotonic()
    r = httpx.post(f"{BASE_URL}/api/v1/translate",
                   json={"text": "Good morning, how are you?",
                         "target_lang": "sw", "source_lang": "en"},
                   headers=headers, timeout=40)
    ms = int((time.monotonic() - t0) * 1000)

    if r.status_code == 200:
        body = r.json()
        all_ok &= check(
            f"HuggingFace  en→sw  [{ms}ms]",
            bool(body.get("translated_text")),
            f'"{body.get("translated_text", "")}"  '
            f'model={body.get("model_used","").split("/")[-1]}'
        )
    elif r.status_code == 503:
        detail = r.json().get("detail", {})
        msg = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        check(f"HuggingFace  en→sw  [{ms}ms]", False,
              f"503 - {msg[:120]}\n"
              f"       → Check HUGGINGFACE_API_KEY in .env\n"
              f"       → Check HUGGINGFACE_BASE_URL = "
              f"https://router.huggingface.co/hf-inference/models")
        all_ok = False
    else:
        check(f"HuggingFace  en→sw  [{ms}ms]", False,
              f"HTTP {r.status_code}: {r.text[:120]}")
        all_ok = False

    # ── 6. HuggingFace: English → Yoruba ──────────────────────────────────
    t0 = time.monotonic()
    r = httpx.post(f"{BASE_URL}/api/v1/translate",
                   json={"text": "Thank you", "target_lang": "yo"},
                   headers=headers, timeout=40)
    ms = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        body = r.json()
        all_ok &= check(
            f"HuggingFace  en→yo  [{ms}ms]",
            bool(body.get("translated_text")),
            f'"{body.get("translated_text", "")}"'
        )
    else:
        check(f"HuggingFace  en→yo  [{ms}ms]", False,
              f"HTTP {r.status_code}: {r.text[:80]}")
        all_ok = False

    print()

    # ── 7. Batch ───────────────────────────────────────────────────────────
    t0 = time.monotonic()
    r = httpx.post(f"{BASE_URL}/api/v1/translate/batch",
                   json={"items": [
                       {"id": "1", "text": "Hello", "target_lang": "lug"},
                       {"id": "2", "text": "Good morning", "target_lang": "sw"},
                   ]},
                   headers=headers, timeout=40)
    ms = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        body = r.json()
        all_ok &= check(
            f"Batch  2 items  [{ms}ms]",
            body["succeeded"] > 0,
            f"succeeded={body['succeeded']}  failed={body['failed']}"
        )
    else:
        check(f"Batch [{ms}ms]", False, f"HTTP {r.status_code}: {r.text[:100]}")
        all_ok = False

    print()

    # ── 8. TTS ─────────────────────────────────────────────────────────────
    t0 = time.monotonic()
    r = httpx.post(f"{BASE_URL}/api/v1/speech/tts",
                   json={"text": "Oli otya?", "language": "lug"},
                   headers=headers, timeout=30)
    ms = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        body = r.json()
        has_audio = bool(body.get("audio_url") or body.get("audio_base64"))
        all_ok &= check(
            f"TTS  lug  [{ms}ms]",
            has_audio,
            f"audio_url={body.get('audio_url','')[:60]}"
        )
    elif r.status_code == 503:
        check(f"TTS  lug  [{ms}ms]", False,
              f"503 - Sunbird unavailable. Check SUNBIRD_API_KEY.")
        all_ok = False
    else:
        check(f"TTS  lug  [{ms}ms]", False, f"HTTP {r.status_code}")
        all_ok = False

    print()

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"{'─'*50}")
    if all_ok:
        print(f"  ✅  All checks passed - Fasiri is fully operational")
    else:
        print(f"  ❌  Some checks failed - see details above")
        print(f"\n  Quick fixes:")
        print(f"    Sunbird 503/405 → python get_sunbird_token.py")
        print(f"    HuggingFace 503 → check HUGGINGFACE_API_KEY in .env")
        print(f"    HuggingFace 404 → set HUGGINGFACE_BASE_URL=")
        print(f"                      https://router.huggingface.co/hf-inference/models")
    print(f"{'─'*50}\n")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://fasiri-bu9u.onrender.com")
    args = parser.parse_args()
    BASE_URL = args.url.rstrip("/")
    main()
