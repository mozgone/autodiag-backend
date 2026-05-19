import re
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    verify_password, create_access_token, decode_token,
    hash_password, verify_telegram_init_data,
)
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, UserMe,
    TelegramAuthRequest, TelegramLoginAndLinkRequest,
)

router = APIRouter()
bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _make_token(user: User) -> TokenResponse:
    token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role,
    })
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
        full_name=user.full_name,
    )


# ─── Обычная авторизация ─────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    return _make_token(user)


@router.get("/me", response_model=UserMe)
async def me(current_user: User = Depends(get_current_user)):
    return UserMe(
        id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        telegram_id=current_user.telegram_id,
    )


# ─── Регистрация новой компании ──────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Email уже занят?
    existing_email = await db.execute(select(User).where(User.email == req.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # Уникальный slug для тенанта
    base_slug = re.sub(r"[^a-z0-9]", "-", req.company_name.lower())[:40].strip("-") or "company"
    slug = base_slug
    existing_slug = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if existing_slug.scalar_one_or_none():
        slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"

    # Создаём тенант
    tenant = Tenant(
        name=req.company_name,
        slug=slug,
        is_active=True,
        crm_type="mock",
        consent_confirmed=False,
    )
    db.add(tenant)
    await db.flush()

    # Создаём пользователя-руководителя
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role=UserRole.HEAD_OF_SALES,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _make_token(user)


# ─── Telegram Mini App ───────────────────────────────────────────────────────

def _check_tg_token():
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram bot не настроен")


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(req: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Авторизация через Telegram initData.
    Работает только если пользователь уже привязал Telegram к своему аккаунту.
    """
    _check_tg_token()
    tg_user = verify_telegram_init_data(req.init_data, settings.TELEGRAM_BOT_TOKEN)
    if not tg_user:
        raise HTTPException(status_code=401, detail="Невалидная подпись Telegram")

    telegram_id = str(tg_user["id"])
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="not_linked",  # фронтенд покажет форму привязки
        )
    return _make_token(user)


@router.post("/telegram/link", response_model=TokenResponse)
async def telegram_login_and_link(
    req: TelegramLoginAndLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Объединённый endpoint: логин по web-credentials + привязка Telegram.
    Вызывается из Mini App когда аккаунт ещё не привязан.
    """
    _check_tg_token()
    tg_user = verify_telegram_init_data(req.init_data, settings.TELEGRAM_BOT_TOKEN)
    if not tg_user:
        raise HTTPException(status_code=401, detail="Невалидная подпись Telegram")

    telegram_id = str(tg_user["id"])

    # Проверяем что этот Telegram ID ещё не привязан к другому аккаунту
    already_linked = await db.execute(select(User).where(User.telegram_id == telegram_id))
    if already_linked.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Этот Telegram уже привязан к другому аккаунту")

    # Логин по web-credentials
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    # Привязываем Telegram
    user.telegram_id = telegram_id
    await db.commit()
    await db.refresh(user)
    return _make_token(user)


@router.delete("/telegram/link", status_code=204)
async def telegram_unlink(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Отвязать Telegram от текущего аккаунта."""
    current_user.telegram_id = None
    await db.commit()
