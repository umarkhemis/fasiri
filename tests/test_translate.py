"""
Fasiri – Full test suite.

Run with:
    pytest tests/ -v
    pytest tests/ -v --tb=short          # concise tracebacks
    pytest tests/test_translate.py -v    # single file

Tests cover:
  1. Auth & API key management
  2. Single translation (routing, fallback, error cases)
  3. Batch translation
  4. Speech (STT + TTS)
  5. Languages endpoint
  6. Rate limiting
  7. Registry correctness
  8. SDK data-class behaviour
"""
from __future__ import annotations

import io
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.security import create_key, get_dev_key, hash_api_key, _KEY_STORE
from app.core.registry import (
    LANGUAGE_REGISTRY,
    get_best_model,
    get_model_fast,
    list_languages,
)
from app.services.providers.base import TranslationResult, STTResult, TTSResult


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def client():
    """Synchronous TestClient for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def api_key():
    """A fresh API key for tests."""
    return get_dev_key()


@pytest.fixture(scope="module")
def auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture
def mock_translation():
    """Returns a fake TranslationResult for provider mocking."""
    return TranslationResult(
        translated_text="Habari, ukoje?",
        model_used="Helsinki-NLP/opus-mt-en-sw",
        provider="huggingface",
        quality_score=0.85,
        latency_ms=250,
    )


@pytest.fixture
def mock_sunbird_translation():
    return TranslationResult(
        translated_text="Oli otya?",
        model_used="sunbird/nllb_translate",
        provider="sunbird",
        quality_score=0.92,
        latency_ms=180,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Authentication & Key Management
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthentication:

    def test_missing_key_returns_401(self, client):
        resp = client.post("/api/v1/translate", json={
            "text": "Hello", "target_lang": "sw"
        })
        assert resp.status_code == 401
        body = resp.json()
        assert body["detail"]["code"] == "MISSING_API_KEY"

    def test_invalid_key_returns_401(self, client):
        resp = client.post(
            "/api/v1/translate",
            json={"text": "Hello", "target_lang": "sw"},
            headers={"Authorization": "Bearer fsri_invalid0000000000000000000000000000000000"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "INVALID_API_KEY"

    def test_malformed_key_returns_401(self, client):
        resp = client.post(
            "/api/v1/translate",
            json={"text": "Hello", "target_lang": "sw"},
            headers={"Authorization": "Bearer notakeyatall"},
        )
        assert resp.status_code == 401

    def test_issue_new_key(self, client):
        resp = client.post("/api/v1/auth/keys", json={"name": "test-key"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["api_key"].startswith("fsri_")
        assert body["name"] == "test-key"
        assert "expires_at" in body
        assert body["note"]

    def test_key_me_endpoint(self, client, auth_headers):
        resp = client.get("/api/v1/auth/keys/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "name" in body
        assert "created_at" in body
        assert "expires_at" in body
        assert isinstance(body["requests_total"], int)

    def test_issued_key_is_usable(self, client):
        # Issue a key, use it immediately
        resp = client.post("/api/v1/auth/keys", json={"name": "functional-test"})
        new_key = resp.json()["api_key"]

        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = TranslationResult(
                translated_text="Test", model_used="test", provider="test",
                quality_score=0.5, latency_ms=10,
            )
            resp2 = client.post(
                "/api/v1/translate",
                json={"text": "Hello", "target_lang": "sw"},
                headers={"Authorization": f"Bearer {new_key}"},
            )
        assert resp2.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Single Translation
# ═══════════════════════════════════════════════════════════════════════════════

class TestTranslation:

    def test_basic_translation(self, client, auth_headers, mock_translation):
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = mock_translation
            resp = client.post(
                "/api/v1/translate",
                json={"text": "Hello, how are you?", "target_lang": "sw"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["translated_text"] == "Habari, ukoje?"
        assert body["target_lang"] == "sw"
        assert body["model_used"] == "Helsinki-NLP/opus-mt-en-sw"
        assert body["quality_score"] == 0.85
        assert body["characters_translated"] == len("Hello, how are you?")

    def test_auto_detect_source_language(self, client, auth_headers, mock_translation):
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = mock_translation
            resp = client.post(
                "/api/v1/translate",
                json={"text": "Hello", "target_lang": "sw"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert "detected_source_lang" in resp.json()

    def test_explicit_source_language(self, client, auth_headers, mock_translation):
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = mock_translation
            resp = client.post(
                "/api/v1/translate",
                json={"text": "Bonjour", "target_lang": "sw", "source_lang": "fr"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert resp.json()["detected_source_lang"] == "fr"

    def test_same_language_returns_400(self, client, auth_headers):
        resp = client.post(
            "/api/v1/translate",
            json={"text": "Hello", "target_lang": "en", "source_lang": "en"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "SAME_LANGUAGE"

    def test_empty_text_returns_422(self, client, auth_headers):
        resp = client.post(
            "/api/v1/translate",
            json={"text": "", "target_lang": "sw"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_text_too_long_returns_422(self, client, auth_headers):
        resp = client.post(
            "/api/v1/translate",
            json={"text": "x" * 5001, "target_lang": "sw"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_provider_override_sunbird(self, client, auth_headers, mock_sunbird_translation):
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = mock_sunbird_translation
            resp = client.post(
                "/api/v1/translate",
                json={"text": "Hello", "target_lang": "lug", "provider": "sunbird"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert resp.json()["provider"] == "sunbird"

    def test_provider_error_returns_503(self, client, auth_headers):
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("All providers failed")
            resp = client.post(
                "/api/v1/translate",
                json={"text": "Hello", "target_lang": "sw"},
                headers=auth_headers,
            )
        assert resp.status_code == 503
        assert resp.json()["detail"]["code"] == "PROVIDER_ERROR"

    def test_response_has_latency_ms(self, client, auth_headers, mock_translation):
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = mock_translation
            resp = client.post(
                "/api/v1/translate",
                json={"text": "Hello", "target_lang": "sw"},
                headers=auth_headers,
            )
        assert "latency_ms" in resp.json()
        assert isinstance(resp.json()["latency_ms"], int)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Batch Translation
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchTranslation:

    def _make_batch_result(self, items):
        return [
            TranslationResult(
                translated_text=f"Translated: {item['text']}",
                model_used="Helsinki-NLP/opus-mt-en-sw",
                provider="huggingface",
                quality_score=0.85,
                latency_ms=100,
            )
            for item in items
        ]

    def test_batch_basic(self, client, auth_headers):
        items = [
            {"id": "1", "text": "Good morning", "target_lang": "sw"},
            {"id": "2", "text": "Thank you",    "target_lang": "yo"},
            {"id": "3", "text": "How are you?", "target_lang": "ha"},
        ]
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = TranslationResult(
                translated_text="ok", model_used="m", provider="p",
                quality_score=0.8, latency_ms=50,
            )
            resp = client.post(
                "/api/v1/translate/batch",
                json={"items": items},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert body["succeeded"] == 3
        assert body["failed"] == 0
        assert len(body["results"]) == 3

    def test_batch_partial_failure(self, client, auth_headers):
        items = [
            {"id": "ok",  "text": "Hello", "target_lang": "sw"},
            {"id": "bad", "text": "Hello", "target_lang": "xx"},
        ]
        call_count = 0

        async def side_effect(text, source_lang, target_lang, preferred_provider):
            nonlocal call_count
            call_count += 1
            if target_lang == "sw":
                return TranslationResult(
                    translated_text="Habari", model_used="m", provider="p",
                    quality_score=0.8, latency_ms=50,
                )
            raise ValueError("Unsupported language pair")

        with patch("app.api.translate.route_translation", side_effect=side_effect):
            resp = client.post(
                "/api/v1/translate/batch",
                json={"items": items},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert body["succeeded"] == 1
        assert body["failed"] == 1
        results = {r["id"]: r for r in body["results"]}
        assert results["ok"]["error"] is None
        assert results["bad"]["error"] is not None

    def test_batch_too_many_items_returns_422(self, client, auth_headers):
        items = [
            {"id": str(i), "text": "hello", "target_lang": "sw"}
            for i in range(51)
        ]
        resp = client.post(
            "/api/v1/translate/batch",
            json={"items": items},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_batch_empty_returns_422(self, client, auth_headers):
        resp = client.post(
            "/api/v1/translate/batch",
            json={"items": []},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_batch_response_has_total_latency(self, client, auth_headers):
        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = TranslationResult(
                translated_text="ok", model_used="m", provider="p",
                quality_score=0.8, latency_ms=50,
            )
            resp = client.post(
                "/api/v1/translate/batch",
                json={"items": [{"id": "1", "text": "hi", "target_lang": "sw"}]},
                headers=auth_headers,
            )
        assert "total_latency_ms" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Speech (STT + TTS)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSpeech:

    FAKE_AUDIO = b"RIFF" + b"\x00" * 100   # minimal WAV-ish header

    def test_stt_basic(self, client, auth_headers):
        mock_result = STTResult(
            transcript="Oli otya",
            detected_lang="lug",
            model_used="sunbird/stt",
            provider="sunbird",
            latency_ms=300,
        )
        with patch.object(
            __import__("app.services.providers.sunbird", fromlist=["SunbirdProvider"])
            .SunbirdProvider, "speech_to_text", new_callable=AsyncMock
        ) as mock:
            mock.return_value = mock_result
            resp = client.post(
                "/api/v1/speech/stt",
                files={"audio": ("test.wav", self.FAKE_AUDIO, "audio/wav")},
                data={"language": "lug"},
                headers={"Authorization": auth_headers["Authorization"]},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["transcript"] == "Oli otya"
        assert body["language"] == "lug"
        assert body["provider"] == "sunbird"

    def test_stt_unsupported_language(self, client, auth_headers):
        resp = client.post(
            "/api/v1/speech/stt",
            files={"audio": ("test.wav", self.FAKE_AUDIO, "audio/wav")},
            data={"language": "yo"},   # Yoruba not in STT
            headers={"Authorization": auth_headers["Authorization"]},
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "UNSUPPORTED_LANGUAGE"

    def test_stt_file_too_large(self, client, auth_headers):
        big_audio = b"x" * (11 * 1024 * 1024)  # 11 MB
        resp = client.post(
            "/api/v1/speech/stt",
            files={"audio": ("big.wav", big_audio, "audio/wav")},
            data={"language": "lug"},
            headers={"Authorization": auth_headers["Authorization"]},
        )
        assert resp.status_code == 413

    def test_tts_basic(self, client, auth_headers):
        mock_result = TTSResult(
            audio_url="https://cdn.sunbird.ai/tts/abc123.mp3",
            audio_base64=None,
            content_type="audio/mpeg",
            model_used="sunbird/tts",
            provider="sunbird",
            latency_ms=400,
        )
        with patch.object(
            __import__("app.services.providers.sunbird", fromlist=["SunbirdProvider"])
            .SunbirdProvider, "text_to_speech", new_callable=AsyncMock
        ) as mock:
            mock.return_value = mock_result
            resp = client.post(
                "/api/v1/speech/tts",
                json={"text": "Oli otya?", "language": "lug"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["audio_url"] == "https://cdn.sunbird.ai/tts/abc123.mp3"
        assert body["language"] == "lug"
        assert body["provider"] == "sunbird"

    def test_tts_unsupported_language(self, client, auth_headers):
        resp = client.post(
            "/api/v1/speech/tts",
            json={"text": "Hello", "language": "ig"},   # Igbo not in TTS
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "UNSUPPORTED_LANGUAGE"

    def test_tts_text_too_long(self, client, auth_headers):
        resp = client.post(
            "/api/v1/speech/tts",
            json={"text": "x" * 2001, "language": "lug"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Languages Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestLanguages:

    def test_languages_returns_200(self, client):
        resp = client.get("/api/v1/languages")
        assert resp.status_code == 200

    def test_languages_structure(self, client):
        resp = client.get("/api/v1/languages")
        body = resp.json()
        assert "languages" in body
        assert "total" in body
        assert body["total"] > 0
        assert len(body["languages"]) == body["total"]

    def test_languages_fields(self, client):
        resp = client.get("/api/v1/languages")
        lang = resp.json()["languages"][0]
        required = [
            "code", "name", "native_name", "region", "family",
            "supports_translation", "supports_stt", "supports_tts",
            "best_provider", "quality_score",
        ]
        for field in required:
            assert field in lang, f"Missing field: {field}"

    def test_swahili_in_languages(self, client):
        resp = client.get("/api/v1/languages")
        codes = {l["code"] for l in resp.json()["languages"]}
        assert "sw" in codes

    def test_tts_languages_have_voice_ids(self, client):
        resp = client.get("/api/v1/languages")
        for lang in resp.json()["languages"]:
            if lang["supports_tts"]:
                assert lang["tts_voice_id"] is not None, (
                    f"{lang['code']} has TTS but no voice_id"
                )

    def test_languages_no_auth_required(self, client):
        # Languages endpoint is public
        resp = client.get("/api/v1/languages")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Rate Limiting
# ═══════════════════════════════════════════════════════════════════════════════

class TestRateLimiting:

    def test_rate_limit_eventually_triggers(self, client):
        import time
        from app.middleware import ratelimit as rl
        from app.core.config import settings as cfg

        fresh_key = create_key("rate-limit-test-2")
        headers = {"Authorization": f"Bearer {fresh_key}"}
        bucket = "rate-limit-test-2:translate"

        # Pre-fill the in-memory window to exactly the limit
        rl._WINDOWS[bucket].clear()
        now = time.monotonic()
        for _ in range(cfg.rate_limit_rpm):
            rl._WINDOWS[bucket].append(now)

        with patch("app.api.translate.route_translation", new_callable=AsyncMock) as mock:
            mock.return_value = TranslationResult(
                translated_text="ok", model_used="m", provider="p",
                quality_score=0.8, latency_ms=10,
            )
            resp = client.post(
                "/api/v1/translate",
                json={"text": "Hello", "target_lang": "sw"},
                headers=headers,
            )
        assert resp.status_code == 429
        assert resp.json()["detail"]["code"] == "RATE_LIMIT_EXCEEDED"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Registry Correctness
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistry:

    def test_all_languages_in_registry(self):
        assert len(LANGUAGE_REGISTRY) >= 20

    def test_core_languages_present(self):
        required = ["en", "sw", "yo", "ha", "ig", "zu", "lug", "nyn", "ach", "teo"]
        for code in required:
            assert code in LANGUAGE_REGISTRY, f"Missing: {code}"

    def test_get_best_model_en_sw(self):
        entry = get_best_model("en", "sw")
        assert entry is not None
        assert entry.quality_score > 0.5
        assert "sw" in entry.target_langs or "*" in entry.target_langs

    def test_get_best_model_prefers_specialist_over_nllb(self):
        entry = get_best_model("en", "sw")
        assert entry.model_id != "facebook/nllb-200-distilled-600M"

    def test_get_best_model_sunbird_for_luganda(self):
        entry = get_best_model("en", "lug")
        assert entry.provider == "sunbird"

    def test_nllb_fallback_for_unknown_pair(self):
        # ha (Hausa) has no verified Helsinki model — routes to NLLB-200
        entry = get_best_model("en", "ha")
        assert entry.provider == "huggingface"
        assert "nllb" in entry.model_id.lower()

    def test_unverified_lang_uses_nllb(self):
        # ig, zu, rw, am all route through NLLB (no verified HF inference model)
        for lang in ["ig", "zu", "rw", "am"]:
            entry = get_best_model("en", lang)
            assert entry.provider == "huggingface", f"{lang} should be huggingface"
            assert "nllb" in entry.model_id.lower(), f"{lang} should use NLLB"

    def test_model_fast_consistent_with_best(self):
        for src in ["en", "sw", "fr"]:
            for tgt in ["sw", "lug", "yo", "ha"]:
                if src != tgt:
                    fast = get_model_fast(src, tgt)
                    best = get_best_model(src, tgt)
                    assert fast.model_id == best.model_id

    def test_quality_scores_in_range(self):
        from app.core.registry import MODEL_REGISTRY
        for entry in MODEL_REGISTRY:
            assert 0.0 <= entry.quality_score <= 1.0, (
                f"{entry.model_id} quality_score out of range"
            )

    def test_all_providers_valid(self):
        from app.core.registry import MODEL_REGISTRY
        valid = {"sunbird", "huggingface", "nllb"}
        for entry in MODEL_REGISTRY:
            assert entry.provider in valid, f"Unknown provider: {entry.provider}"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Health & System Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestSystem:

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "version" in body
        assert "providers" in body
        assert "sunbird" in body["providers"]
        assert "huggingface" in body["providers"]

    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Fasiri API"
        assert "docs" in body

    def test_process_time_header(self, client):
        resp = client.get("/health")
        assert "X-Process-Time-Ms" in resp.headers

    def test_openapi_schema_accessible(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "Fasiri API"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. SDK Data Class Behaviour (unit tests – no HTTP)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSDKDataClasses:

    def test_translation_result_str(self):
        from fasiri import TranslationResult as SDKResult
        r = SDKResult(
            translated_text="Habari",
            detected_source_lang="en",
            target_lang="sw",
            model_used="m",
            provider="p",
            quality_score=0.85,
            latency_ms=200,
            characters_translated=5,
        )
        assert str(r) == "Habari"

    def test_batch_item_success_property(self):
        from fasiri import BatchItemResult as SDKBatch
        good = SDKBatch(id="1", translated_text="ok", detected_source_lang="en",
                        target_lang="sw", model_used="m", provider="p",
                        quality_score=0.8, error=None)
        bad  = SDKBatch(id="2", translated_text=None, detected_source_lang=None,
                        target_lang="sw", model_used=None, provider=None,
                        quality_score=None, error="fail")
        assert good.success is True
        assert bad.success is False
        assert str(bad) == "[ERROR] fail"

    def test_language_repr(self):
        from fasiri import Language as SDKLang
        lang = SDKLang(
            code="sw", name="Swahili", native_name="Kiswahili",
            region="East Africa", family="Niger-Congo",
            supports_translation=True, supports_stt=True, supports_tts=True,
            tts_voice_id=246, best_provider="sunbird", quality_score=0.92,
        )
        r = repr(lang)
        assert "sw" in r
        assert "translate" in r
        assert "stt" in r
        assert "tts" in r

    def test_sdk_missing_key_raises(self):
        import os
        from fasiri import Fasiri, AuthenticationError
        original = os.environ.pop("FASIRI_API_KEY", None)
        try:
            with pytest.raises(AuthenticationError):
                Fasiri()
        finally:
            if original:
                os.environ["FASIRI_API_KEY"] = original

    def test_batch_result_iteration(self):
        from fasiri import BatchResult, BatchItemResult as SDKBatch
        items = [
            SDKBatch(id="1", translated_text="Habari", detected_source_lang="en",
                     target_lang="sw", model_used="m", provider="p",
                     quality_score=0.85, error=None),
            SDKBatch(id="2", translated_text=None, detected_source_lang=None,
                     target_lang="yo", model_used=None, provider=None,
                     quality_score=None, error="timeout"),
        ]
        batch = BatchResult(results=items, total=2, succeeded=1, failed=1,
                            total_latency_ms=300)
        assert len(batch) == 2
        assert len(batch.successful()) == 1
        assert len(batch.errors()) == 1
        ids = [r.id for r in batch]
        assert ids == ["1", "2"]

    def test_translation_result_quality_score(self):
        from fasiri import TranslationResult as SDKResult
        r = SDKResult(
            translated_text="test", detected_source_lang="en", target_lang="sw",
            model_used="m", provider="p", quality_score=0.92,
            latency_ms=100, characters_translated=4,
        )
        assert 0.0 <= r.quality_score <= 1.0
