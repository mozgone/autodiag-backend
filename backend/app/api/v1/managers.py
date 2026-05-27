import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.manager import Manager
from app.models.metrics import MetricSnapshot, Recommendation
from app.models.call_analysis import CallAnalysis

router = APIRouter()

_PERIOD_TYPE = {
    "day":   "daily",
    "week":  "weekly",
    "month": "monthly",
    "year":  "monthly",
}
_PERIOD_LIMIT = {"day": 30, "week": 12, "month": 12, "year": 12}
_PERIOD_FMT   = {"day": "%d.%m", "week": "%d.%m", "month": "%b %Y", "year": "%b %Y"}


def _build_stats(snapshots: list) -> dict:
    if not snapshots:
        return {}
    latest = snapshots[-1]
    return {
        "calls_count":        latest.calls_count,
        "calls_quality_avg":  latest.calls_quality_avg,
        "calls_duration_avg": latest.calls_duration_avg,
        "activities_count":   latest.activities_count,
        "deals_created":      latest.deals_created,
        "deals_won":          latest.deals_won,
        "conversion_rate":    latest.conversion_rate,
        "revenue":            latest.revenue,
        "plan_completion":    latest.plan_completion_forecast,
        "crm_fill_rate":      latest.crm_fill_rate,
        "overdue_tasks":      latest.overdue_tasks,
        "trend": (
            "up" if len(snapshots) > 1 and latest.revenue > snapshots[-2].revenue
            else "stable"
        ),
    }


@router.get("/")
async def list_managers(
    period: str = Query("week", enum=["day", "week", "month", "year"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pt = _PERIOD_TYPE[period]
    mgrs_res = await db.execute(
        select(Manager).where(
            Manager.tenant_id == current_user.tenant_id,
            Manager.is_active == True,
        )
    )
    managers = mgrs_res.scalars().all()
    output = []
    for m in managers:
        snaps_res = await db.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.manager_id == m.id, MetricSnapshot.period_type == pt)
            .order_by(MetricSnapshot.period_start)
        )
        snaps = snaps_res.scalars().all()
        output.append({
            "id":           str(m.id),
            "full_name":    m.full_name,
            "email":        m.email,
            "team_id":      str(m.team_id) if m.team_id else None,
            "monthly_plan": m.monthly_plan,
            "is_active":    m.is_active,
            "avatar_url":   m.avatar_url,
            "created_at":   m.created_at.isoformat(),
            "stats":        _build_stats(snaps),
        })
    return output


@router.get("/{manager_id}")
async def get_manager(
    manager_id: str,
    period: str = Query("week", enum=["day", "week", "month", "year"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Manager).where(
            Manager.id == manager_id,
            Manager.tenant_id == current_user.tenant_id,
        )
    )
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Manager not found")

    pt    = _PERIOD_TYPE[period]
    limit = _PERIOD_LIMIT[period]
    fmt   = _PERIOD_FMT[period]

    snaps_res = await db.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.manager_id == m.id, MetricSnapshot.period_type == pt)
        .order_by(MetricSnapshot.period_start)
        .limit(limit)
    )
    snaps = snaps_res.scalars().all()

    recs_res = await db.execute(
        select(Recommendation)
        .where(Recommendation.manager_id == m.id)
        .order_by(Recommendation.priority.desc(), Recommendation.created_at.desc())
    )
    recs = recs_res.scalars().all()

    weekly_history = [
        {
            "week":       i + 1,
            "revenue":    s.revenue,
            "calls":      s.calls_count,
            "conversion": s.conversion_rate,
            "crm_fill":   s.crm_fill_rate,
            "period":     s.period_start.strftime(fmt),
        }
        for i, s in enumerate(snaps)
    ]

    return {
        "id":           str(m.id),
        "full_name":    m.full_name,
        "email":        m.email,
        "team_id":      str(m.team_id) if m.team_id else None,
        "monthly_plan": m.monthly_plan,
        "is_active":    m.is_active,
        "avatar_url":   m.avatar_url,
        "created_at":   m.created_at.isoformat(),
        "stats":        _build_stats(snaps),
        "weekly_history": weekly_history,
        "recommendations": [
            {
                "id":         str(r.id),
                "rec_type":   r.rec_type,
                "title":      r.title,
                "content":    r.content,
                "priority":   r.priority,
                "is_read":    r.is_read,
                "created_at": r.created_at.isoformat(),
            }
            for r in recs
        ],
    }


@router.get("/{manager_id}/calls")
async def get_manager_calls(
    manager_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return call/chat analysis records for a manager, ordered by item_date desc."""
    # Verify manager belongs to the current tenant
    res = await db.execute(
        select(Manager).where(
            Manager.id == manager_id,
            Manager.tenant_id == current_user.tenant_id,
        )
    )
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Manager not found")

    calls_res = await db.execute(
        select(CallAnalysis)
        .where(CallAnalysis.manager_id == m.id)
        .order_by(CallAnalysis.item_date.desc().nullslast(), CallAnalysis.created_at.desc())
        .limit(limit)
    )
    calls = calls_res.scalars().all()

    def _parse_json_list(raw: str | None) -> list:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    return [
        {
            "id":                  str(ca.id),
            "item_type":           ca.item_type,
            "item_date":           ca.item_date.isoformat() if ca.item_date else None,
            "duration_seconds":    ca.duration_seconds,
            "overall_score":       ca.overall_score,
            "score_greeting":      ca.score_greeting,
            "score_needs":         ca.score_needs,
            "score_presentation":  ca.score_presentation,
            "score_objections":    ca.score_objections,
            "score_closing":       ca.score_closing,
            "score_next_step":     ca.score_next_step,
            "verdict":             ca.verdict,
            "summary":             ca.summary,
            "strengths":           _parse_json_list(ca.strengths),
            "improvements":        _parse_json_list(ca.improvements),
            "transcript":          (ca.transcript or "")[:500] if ca.transcript else None,
        }
        for ca in calls
    ]
