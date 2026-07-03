from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Sellex"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "sellex-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Database (Railway даёт URL вида postgresql://, преобразуем в asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://sellex:sellex123@localhost:5432/sellex"
    DATABASE_URL_SYNC: str = "postgresql://sellex:sellex123@localhost:5432/sellex"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_async_db_url(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        # Render gives postgres:// or postgresql://, both need +asyncpg for SQLAlchemy
        if "+asyncpg" in v:
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis (опционально — не требуется для базовой работы)
    REDIS_URL: Optional[str] = None

    # ИИ через OpenRouter (совместим с OpenAI API)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENAI_MODEL: str = "openai/gpt-4o"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_BOT_USERNAME: Optional[str] = None   # например sellex_analytics_bot (без @)
    APP_URL: Optional[str] = None                 # https://yourapp.up.railway.app

    # amoCRM (опционально)
    AMOCRM_CLIENT_ID: Optional[str] = None
    AMOCRM_CLIENT_SECRET: Optional[str] = None
    AMOCRM_REDIRECT_URI: str = "http://localhost:8000/api/v1/crm/amocrm/callback"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
