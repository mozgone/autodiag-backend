import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.tenant import Tenant
from app.models.manager import Manager
from app.services.sync_service import sync_tenant

router = APIRouter()


class CRMConnectRequest(BaseModel):
    crm_type: str           # mock | amocrm
    subdomain: Optional[str] = None
    access_token: Optional[str] = None
    consent: bool = False


async def _get_tenant(db: AsyncSession, tenant_id) -> Tenant:
    res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.post("/connect")
async def connect_crm(
    req: CRMConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(db, current_user.tenant_id)

    if req.crm_type == "mock":
        tenant.crm_type = "mock"
        tenant.crm_config = None
        tenant.consent_confirmed = True

    elif req.crm_type == "amocrm":
        if not req.subdomain or not req.access_token:
            raise HTTPException(
                status_code=400,
                detail="Для amoCRM необходимо указать поддомен и токен доступа",
            )
        if not req.consent:
            raise HTTPException(
                status_code=400,
                detail="Необходимо подтвердить согласие на обработку персональных данных",
            )
        tenant.crm_type = "amocrm"
        tenant.crm_config = json.dumps({
            "subdomain": req.subdomain.strip(),
            "access_token": req.access_token.strip(),
        })
        tenant.consent_confirmed = True

    else:
        raise HTTPException(status_code=400, detail=f"CRM '{req.crm_type}' не поддерживается")

    tenant.sync_status = "syncing"
    tenant.sync_error = None
    await db.commit()

    # Синхронизируем данные сразу после подключения
    try:
        stats = await sync_tenant(db, tenant)
    except ValueError as e:
        tenant.sync_status = "error"
        tenant.sync_error = str(e)
        await db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        tenant.sync_status = "error"
        tenant.sync_error = "Внутренняя ошибка синхронизации"
        await db.commit()
        raise HTTPException(status_code=500, detail="Ошибка синхронизации данных")

    return {"status": "connected", "crm_type": req.crm_type, **stats}


@router.post("/sync")
async def sync_crm(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Повторная синхронизация данных из подключённой CRM."""
    tenant = await _get_tenant(db, current_user.tenant_id)

    if not tenant.crm_type:
        raise HTTPException(status_code=400, detail="CRM не подключена")

    tenant.sync_status = "syncing"
    await db.commit()

    try:
        stats = await sync_tenant(db, tenant)
    except ValueError as e:
        tenant.sync_status = "error"
        tenant.sync_error = str(e)
        await db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        tenant.sync_status = "error"
        tenant.sync_error = "Внутренняя ошибка синхронизации"
        await db.commit()
        raise HTTPException(status_code=500, detail="Ошибка синхронизации")

    return {"status": "ok", **stats}


@router.get("/status")
async def crm_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(db, current_user.tenant_id)

    managers_count_res = await db.execute(
        select(func.count(Manager.id)).where(
            Manager.tenant_id == tenant.id,
            Manager.is_active == True,
        )
    )
    managers_count = managers_count_res.scalar() or 0

    return {
        "crm_type": tenant.crm_type,
        "is_connected": bool(tenant.sync_status == "ok"),
        "last_sync": tenant.last_sync_at.isoformat() if tenant.last_sync_at else None,
        "sync_status": tenant.sync_status,
        "sync_error": tenant.sync_error,
        "managers_count": managers_count,
    }
