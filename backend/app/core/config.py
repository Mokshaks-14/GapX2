import logging
import secrets
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_FILE = BASE_DIR / "database.db"
DEV_JWT_SECRET = "super-secret-key-gapx-ai-development-123456"

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """All settings can be overridden with environment variables or backend/.env."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "GapX AI API"
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # set to "production" when deploying

    # Security
    JWT_SECRET: str = DEV_JWT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Comma-separated list of frontend origins allowed to call the API
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Comma-separated list of emails that are granted admin rights on login
    ADMIN_EMAILS: str = ""

    # Google Sign-In (OAuth client ID from Google Cloud console). Empty = Google login disabled.
    GOOGLE_CLIENT_ID: str = ""

    # One-click demo account (handy for local development; disable in production)
    ALLOW_DEMO_LOGIN: bool = True

    # Database: always resolves to backend/database.db unless overridden
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"

    # AI providers (optional — a built-in offline engine is used when none is configured)
    GEMINI_API_KEY: Optional[str] = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENAI_API_KEY: Optional[str] = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Code execution. Judge0 runs code in an isolated sandbox and should be used in production.
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: Optional[str] = ""
    # Running submitted code directly on this machine is only safe for local development.
    ALLOW_LOCAL_CODE_EXECUTION: bool = True

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def admin_emails(self) -> List[str]:
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()

if settings.JWT_SECRET == DEV_JWT_SECRET:
    if settings.is_production:
        # Never sign production tokens with a publicly known key.
        settings.JWT_SECRET = secrets.token_urlsafe(48)
        logger.warning("JWT_SECRET not set: generated a random one. Sessions reset on every restart.")
    else:
        logger.warning("Using the development JWT_SECRET. Set JWT_SECRET in backend/.env before deploying.")
