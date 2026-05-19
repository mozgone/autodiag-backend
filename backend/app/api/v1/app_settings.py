from fastapi import APIRouter, Depends
from app.core.config import settings
from app.api.v1.auth import get_current_user

router = APIRouter()

@router.get("/info")
async def app_info(_=Depends(get_current_user)):
    """Возвращает публичные настройки приложения (ссылки на бота, статус интеграций)."""
    mini_app_url = None
    bot_link = None
    if settings.TELEGRAM_BOT_USERNAME:
        bot_link = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}"
        app_url = (settings.APP_URL or "").rstrip("/")
        mini_app_url = f"{app_url}/tg" if app_url else None

    return {
        "bot_username": settings.TELEGRAM_BOT_USERNAME,
        "bot_link": bot_link,
        "mini_app_url": mini_app_url,
        "has_telegram": bool(settings.TELEGRAM_BOT_TOKEN),
        "has_ai": bool(settings.OPENAI_API_KEY),
    }
