from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Sellex"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "sellex-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sellex:sellex123@localhost:5432/sellex"
    DATABASE_URL_SYNC: str = "postgresql://sellex:sellex123@localhost:5432/sellex"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI (optional — falls back to mock responses if not set)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # amoCRM (optional)
    AMOCRM_CLIENT_ID: Optional[str] = None
    AMOCRM_CLIENT_SECRET: Optional[str] = None
    AMOCRM_REDIRECT_URI: str = "http://localhost:8000/api/v1/crm/amocrm/callback"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
