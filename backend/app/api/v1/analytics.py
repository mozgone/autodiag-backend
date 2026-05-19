from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.manager import Manager
from app.models.metrics import MetricSnapshot

router = APIRouter()

@router.get("/overview")
async def overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    managers_result = await db.execute(
        select(Manager).where(Manager.tenant_id == current_user.tenant_id, Manager.is_active == True)
    )
    managers = managers_result.scalars().all()
    total_revenue = 0.0
    total_calls = 0
    total_conv = 0.0
    total_forecast = 0.0
    top_name = ""
    top_revenue = 0.0
    at_risk = 0

    for m in managers:
        snaps_result = await db.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.manager_id == m.id, MetricSnapshot.period_type == "weekly")
            .order_by(MetricSnapshot.period_start.desc())
            .limit(1)
        )
        snap = snaps_result.scalar_one_or_none()
        if snap:
            total_revenue += snap.revenue
            total_calls += snap.calls_count
            total_conv += snap.conversion_rate
            total_forecast += snap.plan_completion_forecast
            if snap.revenue > top_revenue:
                top_revenue = snap.revenue
                top_name = m.full_name
            if snap.plan_completion_forecast < 70:
                at_risk += 1

    n = len(managers) or 1
    return {
        "total_managers": len(managers),
        "active_deals": len(managers) * 8,  # demo approximation
        "total_revenue_month": round(total_revenue, -3),
        "avg_conversion_rate": round(total_conv / n, 1),
        "plan_completion_avg": round(total_forecast / n, 1),
        "top_performer": top_name,
        "at_risk_deals": at_risk * 3,
    }

@router.get("/chart/revenue")
async def revenue_chart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Недельная динамика выручки по всему отделу."""
    snaps_result = await db.execute(
        select(
            MetricSnapshot.period_start,
            func.sum(MetricSnapshot.revenue).label("total_revenue"),
            func.sum(MetricSnapshot.calls_count).label("total_calls"),
            func.avg(MetricSnapshot.conversion_rate).label("avg_conv"),
        )
        .where(MetricSnapshot.tenant_id == current_user.tenant_id, MetricSnapshot.period_type == "weekly")
        .group_by(MetricSnapshot.period_start)
        .order_by(MetricSnapshot.period_start)
    )
    rows = snaps_result.all()
    return [
        {
            "date": r.period_start.strftime("%d.%m"),
            "revenue": round(r.total_revenue, -3),
            "calls": r.total_calls,
            "conversion": round(r.avg_conv, 1),
        }
        for r in rows
    ]

@router.get("/ranking")
async def ranking(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    managers_result = await db.execute(
        select(Manager).where(Manager.tenant_id == current_user.tenant_id, Manager.is_active == True)
    )
    managers = managers_result.scalars().all()
    items = []
    for m in managers:
        snaps_result = await db.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.manager_id == m.id, MetricSnapshot.period_type == "weekly")
            .order_by(MetricSnapshot.period_start.desc())
            .limit(1)
        )
        snap = snaps_result.scalar_one_or_none()
        if snap:
            items.append({
                "manager_id": str(m.id),
                "full_name": m.full_name,
                "revenue": snap.revenue,
                "plan_completion": snap.plan_completion_forecast,
                "calls_count": snap.calls_count,
                "conversion_rate": snap.conversion_rate,
            })
    items.sort(key=lambda x: x["revenue"], reverse=True)
    for i, item in enumerate(items):
        item["rank"] = i + 1
        item["trend"] = "up" if i < len(items) // 2 else "down"
    return items
