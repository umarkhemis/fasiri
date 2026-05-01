"""
Fasiri – centralised settings.
All values are read from environment variables (or a .env file via pydantic-settings).
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Provider credentials ────────────────────────────────────────────────
    huggingface_api_key: str = Field(default="", alias="HUGGINGFACE_API_KEY")
    sunbird_api_key: str = Field(default="", alias="SUNBIRD_API_KEY")
    khaya_api_key: str = Field(default="", alias="KHAYA_API_KEY")

    # ── Fasiri internal auth ─────────────────────────────────────────────────
    # Secret used to sign/verify Fasiri API keys  (openssl rand -hex 32)
    fasiri_secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        alias="FASIRI_SECRET_KEY",
    )
    # How long issued API keys stay valid (seconds). Default = 1 year.
    api_key_ttl_seconds: int = Field(default=31_536_000, alias="API_KEY_TTL_SECONDS")

    # ── Rate-limiting (requests per minute per API key) ──────────────────────
    rate_limit_rpm: int = Field(default=60, alias="RATE_LIMIT_RPM")
    rate_limit_batch_rpm: int = Field(default=10, alias="RATE_LIMIT_BATCH_RPM")

    # ── Redis (optional – used for rate-limit counters) ──────────────────────
    redis_url: str = Field(default="", alias="REDIS_URL")

    # ── Provider base URLs ───────────────────────────────────────────────────
    sunbird_base_url: str = Field(
        default="https://api.sunbird.ai", alias="SUNBIRD_BASE_URL"
    )
    huggingface_base_url: str = Field(
        default="https://router.huggingface.co/hf-inference/models",
        alias="HUGGINGFACE_BASE_URL",
    )
    khaya_base_url: str = Field(
        default="https://translation-api.ghananlp.org/v2", alias="KHAYA_BASE_URL"
    )

    # ── Fallback model ───────────────────────────────────────────────────────
    default_model_id: str = Field(
        default="Helsinki-NLP/opus-mt-en-mul", alias="DEFAULT_MODEL_ID"
    )

    # ── Misc ─────────────────────────────────────────────────────────────────
    base_url: str = Field(default="http://localhost:8000", alias="BASE_URL")
    debug: bool = Field(default=False, alias="DEBUG")

    # HTTP timeouts (seconds)
    http_timeout: int = Field(default=30, alias="HTTP_TIMEOUT")
    http_timeout_stt: int = Field(default=60, alias="HTTP_TIMEOUT_STT")

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()
