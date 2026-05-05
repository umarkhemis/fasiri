#!/usr/bin/env python3
"""
Fasiri API - Stress / Load Test
====================================
Fires concurrent requests to measure throughput, latency, and error rates.

Usage:
    python stress_test.py                          # 10 concurrent, 50 total
    python stress_test.py --concurrency 20 --total 200
    python stress_test.py --url https://fasiri-bu9u.onrender.com --key fsri_...
    python stress_test.py --endpoint batch         # stress batch endpoint only
"""
from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import List

import httpx

BASE_URL    = "https://fasiri-bu9u.onrender.com"
API_KEY     = None
CONCURRENCY = 10
TOTAL       = 50


@dataclass
class Result:
    status_code: int
    latency_ms: float
    error: str = ""
    provider: str = ""
    model: str = ""


@dataclass
class Stats:
    results: List[Result] = field(default_factory=list)

    @property
    def total(self): return len(self.results)

    @property
    def passed(self): return sum(1 for r in self.results if r.status_code == 200)

    @property
    def failed(self): return sum(1 for r in self.results if r.status_code not in (200, 503))

    @property
    def errors_503(self): return sum(1 for r in self.results if r.status_code == 503)

    @property
    def rate_limited(self): return sum(1 for r in self.results if r.status_code == 429)

    @property
    def latencies(self): return [r.latency_ms for r in self.results if r.status_code == 200]

    @property
    def p50(self): return statistics.median(self.latencies) if self.latencies else 0

    @property
    def p95(self):
        if not self.latencies: return 0
        s = sorted(self.latencies)
        return s[int(len(s) * 0.95)]

    @property
    def p99(self):
        if not self.latencies: return 0
        s = sorted(self.latencies)
        return s[int(len(s) * 0.99)]

    @property
    def avg(self): return statistics.mean(self.latencies) if self.latencies else 0

    @property
    def min_lat(self): return min(self.latencies) if self.latencies else 0

    @property
    def max_lat(self): return max(self.latencies) if self.latencies else 0


# ── Test payloads ─────────────────────────────────────────────────────────────

TRANSLATE_PAYLOADS = [
    {"text": "Hello, how are you?",      "target_lang": "lug"},
    {"text": "Good morning everyone",    "target_lang": "ach"},
    {"text": "Thank you very much",      "target_lang": "nyn"},
    {"text": "Welcome to Fasiri",      "target_lang": "teo"},
    {"text": "My name is Fasiri API",  "target_lang": "lgg"},
    {"text": "How are you today?",       "target_lang": "sw"},
    {"text": "Good evening",             "target_lang": "yo"},
    {"text": "I am very happy",          "target_lang": "ha"},
]

BATCH_PAYLOAD = {
    "items": [
        {"id": "1", "text": "Hello",        "target_lang": "lug"},
        {"id": "2", "text": "Good morning", "target_lang": "ach"},
        {"id": "3", "text": "Thank you",    "target_lang": "nyn"},
        {"id": "4", "text": "Welcome",      "target_lang": "sw"},
        {"id": "5", "text": "Goodbye",      "target_lang": "yo"},
    ]
}


# ── Async worker ──────────────────────────────────────────────────────────────

async def call_translate(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    request_num: int,
) -> Result:
    payload = TRANSLATE_PAYLOADS[request_num % len(TRANSLATE_PAYLOADS)]
    async with semaphore:
        t0 = time.monotonic()
        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/translate",
                json=payload,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=40,
            )
            ms = (time.monotonic() - t0) * 1000
            if resp.status_code == 200:
                body = resp.json()
                return Result(
                    status_code=200,
                    latency_ms=ms,
                    provider=body.get("provider", ""),
                    model=body.get("model_used", "").split("/")[-1],
                )
            else:
                return Result(
                    status_code=resp.status_code,
                    latency_ms=ms,
                    error=resp.text[:100],
                )
        except Exception as e:
            ms = (time.monotonic() - t0) * 1000
            return Result(status_code=0, latency_ms=ms, error=str(e)[:100])


async def call_batch(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    _: int,
) -> Result:
    async with semaphore:
        t0 = time.monotonic()
        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/translate/batch",
                json=BATCH_PAYLOAD,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=60,
            )
            ms = (time.monotonic() - t0) * 1000
            return Result(status_code=resp.status_code, latency_ms=ms)
        except Exception as e:
            ms = (time.monotonic() - t0) * 1000
            return Result(status_code=0, latency_ms=ms, error=str(e)[:100])


# ── Progress bar ──────────────────────────────────────────────────────────────

def progress_bar(done: int, total: int, width: int = 40) -> str:
    pct   = done / total
    filled = int(pct * width)
    bar   = "█" * filled + "░" * (width - filled)
    return f"  [{bar}] {done}/{total} ({pct*100:.0f}%)"


# ── Main ──────────────────────────────────────────────────────────────────────

async def run_stress(endpoint: str, concurrency: int, total: int) -> Stats:
    stats = Stats()
    semaphore = asyncio.Semaphore(concurrency)
    worker = call_translate if endpoint == "translate" else call_batch

    print(f"\n  Endpoint:    POST /api/v1/{endpoint}")
    print(f"  Concurrency: {concurrency} simultaneous requests")
    print(f"  Total:       {total} requests")
    print(f"  Target:      {BASE_URL}\n")

    completed = 0
    wall_start = time.monotonic()

    async with httpx.AsyncClient() as client:
        tasks = [worker(client, semaphore, i) for i in range(total)]

        # Process with live progress
        for coro in asyncio.as_completed(tasks):
            result = await coro
            stats.results.append(result)
            completed += 1
            # Update progress every 5 or on completion
            if completed % 5 == 0 or completed == total:
                bar = progress_bar(completed, total)
                ok  = stats.passed
                err = stats.failed + stats.errors_503
                rl  = stats.rate_limited
                sys.stdout.write(
                    f"\r{bar}  ✅{ok} ❌{err} 🚦{rl}"
                )
                sys.stdout.flush()

    wall_ms = (time.monotonic() - wall_start) * 1000
    rps = total / (wall_ms / 1000)
    print(f"\n\n  Total wall time: {wall_ms/1000:.2f}s  ({rps:.1f} req/s)")
    return stats


def print_stats(stats: Stats):
    print("\n" + "═" * 55)
    print("  STRESS TEST RESULTS")
    print("═" * 55)

    # Counts
    print(f"\n  Requests:")
    print(f"    Total:        {stats.total}")
    print(f"    ✅ 200 OK:    {stats.passed}  ({stats.passed/stats.total*100:.1f}%)")
    print(f"    ❌ Errors:    {stats.failed}  ({stats.failed/stats.total*100:.1f}%)")
    print(f"    ⚠️  503s:      {stats.errors_503}  (provider unavailable)")
    print(f"    🚦 429s:      {stats.rate_limited}  (rate limited)")

    # Latency (successful only)
    if stats.latencies:
        print(f"\n  Latency (successful requests only):")
        print(f"    Min:   {stats.min_lat:.0f}ms")
        print(f"    Avg:   {stats.avg:.0f}ms")
        print(f"    p50:   {stats.p50:.0f}ms")
        print(f"    p95:   {stats.p95:.0f}ms")
        print(f"    p99:   {stats.p99:.0f}ms")
        print(f"    Max:   {stats.max_lat:.0f}ms")

        # Latency histogram
        print(f"\n  Latency distribution:")
        buckets = [(0,500), (500,1000), (1000,2000), (2000,5000), (5000,99999)]
        labels  = ["<500ms", "500ms-1s", "1s-2s", "2s-5s", ">5s"]
        for (lo, hi), label in zip(buckets, labels):
            count = sum(1 for l in stats.latencies if lo <= l < hi)
            pct   = count / len(stats.latencies) * 100
            bar   = "█" * int(pct / 2)
            print(f"    {label:<12}  {bar:<25}  {count:3d} ({pct:.0f}%)")
    else:
        print(f"\n  ⚠️  No successful requests - check your API keys and server.")

    # Provider breakdown
    providers = {}
    for r in stats.results:
        if r.provider:
            providers[r.provider] = providers.get(r.provider, 0) + 1
    if providers:
        print(f"\n  Provider distribution:")
        for prov, count in sorted(providers.items(), key=lambda x: -x[1]):
            pct = count / stats.total * 100
            print(f"    {prov:<15}  {count:3d} ({pct:.0f}%)")

    # Sample errors
    errors = [r for r in stats.results if r.error][:5]
    if errors:
        print(f"\n  Sample errors:")
        for e in errors:
            print(f"    HTTP {e.status_code}: {e.error}")

    print("═" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fasiri stress test")
    parser.add_argument("--url",         default="https://fasiri-bu9u.onrender.com")
    parser.add_argument("--key",         default=None)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--total",       type=int, default=50)
    parser.add_argument("--endpoint",    default="translate",
                        choices=["translate", "batch"])
    args = parser.parse_args()

    BASE_URL    = args.url.rstrip("/")
    API_KEY     = args.key
    CONCURRENCY = args.concurrency
    TOTAL       = args.total

    if not API_KEY:
        # Auto-issue a key
        try:
            r = httpx.post(
                f"{BASE_URL}/api/v1/auth/keys",
                json={"name": "stress-test"},
                timeout=10,
            )
            if r.status_code == 201:
                API_KEY = r.json()["api_key"]
                print(f"  Auto-issued key: {API_KEY[:24]}...")
            else:
                print(f"❌ Could not auto-issue key: HTTP {r.status_code}")
                sys.exit(1)
        except httpx.ConnectError:
            print(f"❌ Cannot connect to {BASE_URL} - is the server running?")
            sys.exit(1)

    print(f"\n{'═'*55}")
    print(f"  Fasiri API - Stress Test")
    print(f"{'═'*55}")

    stats = asyncio.run(run_stress(args.endpoint, CONCURRENCY, TOTAL))
    print_stats(stats)

    # Exit code
    success_rate = stats.passed / stats.total if stats.total else 0
    # Account for 503s as "not our fault" - only count hard errors
    hard_fail_rate = stats.failed / stats.total if stats.total else 0
    if hard_fail_rate > 0.05:
        print(f"\n  ❌ Hard failure rate {hard_fail_rate*100:.1f}% exceeds 5% threshold")
        sys.exit(1)
    else:
        print(f"\n  ✅ Stress test passed")
        sys.exit(0)
