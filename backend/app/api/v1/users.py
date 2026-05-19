from fastapi import APIRouter, Depends
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "tenant_id": str(current_user.tenant_id),
    }
