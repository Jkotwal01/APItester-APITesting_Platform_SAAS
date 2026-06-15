"""
Application configuration using pydantic-settings.
All values are loaded from environment variables or .env file.
Use `settings` singleton throughout the application.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ─── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "AITester"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ─── Database (PostgreSQL via asyncpg) ────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://aitester:password@localhost:5432/aitester"

    # ─── Cache (Redis) ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── AI (Google Gemini) ───────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    AI_MAX_RETRIES: int = 3

    # ─── Test Execution ───────────────────────────────────────────────────────
    MAX_CONCURRENT_TESTS: int = 50
    REQUEST_TIMEOUT_SECONDS: float = 30.0

    # ─── Reports ──────────────────────────────────────────────────────────────
    REPORT_OUTPUT_DIR: str = "./reports"

    # ─── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = "changeme-generate-a-real-secret-key-at-least-32-chars"
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY: str = ""

    # ─── Validators ───────────────────────────────────────────────────────────
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("MAX_CONCURRENT_TESTS")
    @classmethod
    def validate_concurrency(cls, v: int) -> int:
        if v < 1 or v > 500:
            raise ValueError(f"MAX_CONCURRENT_TESTS must be between 1 and 500, got {v}")
        return v

    @field_validator("REQUEST_TIMEOUT_SECONDS")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"REQUEST_TIMEOUT_SECONDS must be positive, got {v}")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        lower = v.lower()
        if lower not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return lower

    # ─── Derived helpers ──────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def database_url_sync(self) -> str:
        """Synchronous DB URL for Alembic migrations (uses psycopg2 driver)."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this anywhere to get the singleton."""
    return Settings()


# Module-level singleton for convenience: `from aitester.core.config import settings`
settings = get_settings()
