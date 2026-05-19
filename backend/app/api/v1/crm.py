from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.tenant import Tenant
from sqlalchemy import select

router = APIRouter()

class CRMConnectRequest(BaseModel):
    crm_type: str  # mock, amocrm, bitrix24
    subdomain: Optional[str] = None
    access_token: Optional[str] = None

@router.post("/connect")
async def connect_crm(
    req: CRMConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if req.crm_type == "mock":
        tenant.crm_type = "mock"
        tenant.crm_config = None
    elif req.crm_type == "amocrm":
        import json
        if not req.subdomain or not req.access_token:
            raise HTTPException(status_code=400, detail="Для amoCRM нужны subdomain и access_token")
        tenant.crm_type = "amocrm"
        tenant.crm_config = json.dumps({"subdomain": req.subdomain, "access_token": req.access_token})
    else:
        raise HTTPException(status_code=400, detail=f"CRM '{req.crm_type}' не поддерживается")

    await db.commit()
    return {"status": "connected", "crm_type": req.crm_type}

@router.get("/status")
async def crm_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    return {
        "crm_type": tenant.crm_type if tenant else "mock",
        "is_connected": True,
        "last_sync": None,
    }
