from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

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
