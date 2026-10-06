"""
Core configuration using Pydantic Settings v2.
Reads from environment variables / .env file.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute paths to backend and root directory .env files
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent

# Load environment variables into os.environ before Pydantic Settings initialization
load_dotenv(BACKEND_DIR / ".env", override=True)
load_dotenv(ROOT_DIR / ".env", override=False)


class Settings(BaseSettings):
    """
    All application configuration is centralised here.
    Environment variables are loaded automatically from .env files.
    """

    model_config = SettingsConfigDict(
        env_file=(
            str(BACKEND_DIR / ".env"),
            str(ROOT_DIR / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Supabase ──────────────────────────────────────────────
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # ── JWT ───────────────────────────────────────────────────
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # ── AI / Gemini ─────────────────────────────────────────────
    gemini_api_key: str = ""

    # ── Application ───────────────────────────────────────────
    app_name: str = "AI Financial Intelligence Platform"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True

    # ── Server ────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── CORS ──────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ── Logging ───────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = ""

    # ── Derived helpers ───────────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    Use this everywhere instead of instantiating Settings() directly.
    """
    return Settings()


# Module-level singleton for convenience imports
settings = get_settings()
