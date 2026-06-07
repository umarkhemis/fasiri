"""
Fasiri - centralised settings.
All values are read from environment variables (or a .env file via pydantic-settings).
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Database (Neon Postgres) ─────────────────────────────────────────────
    # postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require
    database_url: str = Field(default="", alias="DATABASE_URL")

    # ── Provider credentials ─────────────────────────────────────────────────
    huggingface_api_key: str = Field(default="", alias="HUGGINGFACE_API_KEY")
    sunbird_api_key: str = Field(default="", alias="SUNBIRD_API_KEY")
    khaya_api_key: str = Field(default="", alias="KHAYA_API_KEY")

    # ── Fasiri internal auth ──────────────────────────────────────────────────
    fasiri_secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        alias="FASIRI_SECRET_KEY",
    )
    api_key_ttl_seconds: int = Field(default=31_536_000, alias="API_KEY_TTL_SECONDS")

    # Permanent keys that survive restarts — set these in Render/Neon env vars.
    # FASIRI_DEMO_KEY  : used by the public demo (read: translate/speech)
    # FASIRI_ADMIN_KEY : used by fasiri_platform to issue new keys (write: key creation)
    # They should be DIFFERENT keys for proper access control.
    fasiri_demo_key: str = Field(default="", alias="FASIRI_DEMO_KEY")
    fasiri_admin_key: str = Field(default="", alias="FASIRI_ADMIN_KEY")

    # ── Rate-limiting ─────────────────────────────────────────────────────────
    rate_limit_rpm: int = Field(default=60, alias="RATE_LIMIT_RPM")
    rate_limit_batch_rpm: int = Field(default=10, alias="RATE_LIMIT_BATCH_RPM")
    # Max new keys creatable per IP per hour (key-creation endpoint)
    rate_limit_keys_per_ip: int = Field(default=5, alias="RATE_LIMIT_KEYS_PER_IP")

    # ── Redis (optional - for rate-limit counters) ────────────────────────────
    redis_url: str = Field(default="", alias="REDIS_URL")

    # ── Provider base URLs ────────────────────────────────────────────────────
    sunbird_base_url: str = Field(
        default="https://api.sunbird.ai", alias="SUNBIRD_BASE_URL"
    )
    huggingface_base_url: str = Field(
        default="https://router.huggingface.co/hf-inference/models",
        alias="HUGGINGFACE_BASE_URL",
    )
    khaya_base_url: str = Field(
        default="https://translation.ghananlp.org/v2", alias="KHAYA_BASE_URL"
    )

    # ── Fallback model ────────────────────────────────────────────────────────
    default_model_id: str = Field(
        default="Helsinki-NLP/opus-mt-en-mul", alias="DEFAULT_MODEL_ID"
    )

    # ── Misc ──────────────────────────────────────────────────────────────────
    base_url: str = Field(default="https://api.fasiri-ai.com", alias="BASE_URL")
    debug: bool = Field(default=False, alias="DEBUG")
    http_timeout: int = Field(default=30, alias="HTTP_TIMEOUT")
    http_timeout_stt: int = Field(default=60, alias="HTTP_TIMEOUT_STT")

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()
