"""Application configuration loaded from environment variables / .env."""
import logging
import secrets
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "FraudShield AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'fraudshield.db'}"
    AUTO_CREATE_TABLES: bool = True  # dev convenience; use Alembic in production

    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    LOGIN_RATE_WINDOW_MINUTES: int = 15
    LOGIN_RATE_ACCOUNT_LIMIT: int = 10
    LOGIN_RATE_SOURCE_LIMIT: int = 40

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    MODEL_DIR: Path = PROJECT_ROOT / "models"
    APPROVED_THRESHOLD: float = 0.468

    MAX_REQUEST_BYTES: int = 1_048_576
    MAX_PAGE_SIZE: int = 100
    HSTS_MAX_AGE_SECONDS: int = 31_536_000

    ALLOW_PUBLIC_REGISTRATION: bool = False
    INITIAL_ADMIN_EMAIL: Optional[str] = None
    INITIAL_ADMIN_PASSWORD: Optional[str] = None
    INITIAL_ADMIN_NAME: str = "System Administrator"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def _check_security(self) -> "Settings":
        if not self.SECRET_KEY:
            if self.is_production:
                raise ValueError("SECRET_KEY must be set when ENVIRONMENT=production")
            self.SECRET_KEY = secrets.token_urlsafe(48)
            logger.warning(
                "SECRET_KEY not set: generated a temporary key. Tokens become invalid on restart."
            )
        if self.MAX_REQUEST_BYTES < 1:
            raise ValueError("MAX_REQUEST_BYTES must be positive")
        if self.is_production:
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must contain at least 32 characters in production")
            origins = self.cors_origin_list
            if not origins or "*" in origins:
                raise ValueError("Explicit CORS_ORIGINS are required in production")
            if any(not o.startswith("https://") for o in origins):
                raise ValueError("Production CORS_ORIGINS must use HTTPS")
            if any(any(host in o.lower() for host in ("localhost", "127.0.0.1", "0.0.0.0")) for o in origins):
                raise ValueError("Local origins are not allowed in production CORS_ORIGINS")
            if self.AUTO_CREATE_TABLES:
                raise ValueError("AUTO_CREATE_TABLES must be false in production; use Alembic migrations")
            if self.HSTS_MAX_AGE_SECONDS < 0:
                raise ValueError("HSTS_MAX_AGE_SECONDS cannot be negative")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
