from fastapi import APIRouter
from app.api.v1 import auth, managers, analytics, crm, users, app_settings

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(managers.router, prefix="/managers", tags=["managers"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(crm.router, prefix="/crm", tags=["crm"])
router.include_router(app_settings.router, prefix="/settings", tags=["settings"])
