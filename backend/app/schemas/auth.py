from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    company_name: str       # название компании → новый тенант
    full_name: str          # имя руководителя
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v

    @field_validator("company_name")
    @classmethod
    def company_name_length(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Название компании слишком короткое")
        return v.strip()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str
    role: str
    full_name: str

class UserMe(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    telegram_id: Optional[str] = None

class TelegramAuthRequest(BaseModel):
    """Аутентификация через Telegram initData (если аккаунт уже привязан)."""
    init_data: str

class TelegramLoginAndLinkRequest(BaseModel):
    """Привязка Telegram-аккаунта к существующему web-аккаунту."""
    init_data: str      # от Telegram.WebApp.initData
    email: EmailStr     # credentials web-аккаунта
    password: str
