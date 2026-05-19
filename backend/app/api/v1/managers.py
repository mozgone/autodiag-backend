from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.manager import Manager
from app.models.metrics import MetricSnapshot, Recommendation

router = APIRouter()

def _build_stats(snapshots: list) -> dict:
    if not snapshots:
        return {}
    latest = snapshots[-1]
    return {
        "calls_count": latest.calls_count,
        "calls_quality_avg": latest.calls_quality_avg,
        "deals_created": latest.deals_created,
        "deals_won": latest.deals_won,
        "conversion_rate": latest.conversion_rate,
        "revenue": latest.revenue,
        "plan_completion": latest.plan_completion_forecast,
        "crm_fill_rate": latest.crm_fill_rate,
        "overdue_tasks": latest.overdue_tasks,
        "trend": "up" if len(snapshots) > 1 and latest.revenue > snapshots[-2].revenue else "stable",
    }

@router.get("/")
async def list_managers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Manager).where(Manager.tenant_id == current_user.tenant_id, Manager.is_active == True)
    )
    managers = result.scalars().all()
    output = []
    for m in managers:
        snaps_result = await db.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.manager_id == m.id, MetricSnapshot.period_type == "weekly")
            .order_by(MetricSnapshot.period_start)
        )
        snaps = snaps_result.scalars().all()
        output.append({
            "id": str(m.id),
            "full_name": m.full_name,
            "email": m.email,
            "team_id": str(m.team_id) if m.team_id else None,
            "monthly_plan": m.monthly_plan,
            "is_active": m.is_active,
            "avatar_url": m.avatar_url,
            "created_at": m.created_at.isoformat(),
            "stats": _build_stats(snaps),
        })
    return output

@router.get("/{manager_id}")
async def get_manager(
    manager_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Manager).where(Manager.id == manager_id, Manager.tenant_id == current_user.tenant_id)
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Manager not found")

    snaps_result = await db.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.manager_id == m.id, MetricSnapshot.period_type == "weekly")
        .order_by(MetricSnapshot.period_start)
    )
    snaps = snaps_result.scalars().all()

    recs_result = await db.execute(
        select(Recommendation)
        .where(Recommendation.manager_id == m.id)
        .order_by(Recommendation.priority.desc(), Recommendation.created_at.desc())
    )
    recs = recs_result.scalars().all()

    weekly_history = [
        {
            "week": i + 1,
            "revenue": s.revenue,
            "calls": s.calls_count,
            "conversion": s.conversion_rate,
            "crm_fill": s.crm_fill_rate,
            "period": s.period_start.strftime("%d.%m"),
        }
        for i, s in enumerate(snaps)
    ]

    return {
        "id": str(m.id),
        "full_name": m.full_name,
        "email": m.email,
        "team_id": str(m.team_id) if m.team_id else None,
        "monthly_plan": m.monthly_plan,
        "is_active": m.is_active,
        "avatar_url": m.avatar_url,
        "created_at": m.created_at.isoformat(),
        "stats": _build_stats(snaps),
        "weekly_history": weekly_history,
        "recommendations": [
            {
                "id": str(r.id),
                "rec_type": r.rec_type,
                "title": r.title,
                "content": r.content,
                "priority": r.priority,
                "is_read": r.is_read,
                "created_at": r.created_at.isoformat(),
            }
            for r in recs
        ],
    }
