from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

import hmac as _hmac
import hashlib as _hashlib
import json as _json
from urllib.parse import parse_qsl as _parse_qsl

def verify_telegram_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Проверяет подпись initData от Telegram Mini App (HMAC-SHA256).
    Возвращает dict с данными пользователя или None если подпись невалидна.
    """
    parsed = dict(_parse_qsl(init_data, keep_blank_values=True))
    hash_value = parsed.pop("hash", None)
    if not hash_value:
        return None
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = _hmac.new(b"WebAppData", bot_token.encode(), _hashlib.sha256).digest()
    computed = _hmac.new(secret_key, data_check_string.encode(), _hashlib.sha256).hexdigest()
    if not _hmac.compare_digest(computed, hash_value):
        return None
    return _json.loads(parsed.get("user", "{}"))
