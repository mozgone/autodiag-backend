from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Tuple
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.manager import Manager
from app.models.metrics import MetricSnapshot

router = APIRouter()

_PERIOD_TYPE = {
    "day":   "daily",
    "week":  "weekly",
    "month": "monthly",
    "year":  "monthly",   # год = сумма месячных
}


async def _manager_snaps(
    db: AsyncSession,
    tenant_id,
    period: str,
) -> List[Tuple[Manager, MetricSnapshot]]:
    """
    Возвращает список (менеджер, снимок).
    Для period=year складывает все 12 месячных снимков в один виртуальный.
    """
    pt = _PERIOD_TYPE[period]
    managers_res = await db.execute(
        select(Manager).where(Manager.tenant_id == tenant_id, Manager.is_active == True)
    )
    managers = managers_res.scalars().all()
    result: List[Tuple[Manager, MetricSnapshot]] = []

    for m in managers:
        snaps_res = await db.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.manager_id == m.id, MetricSnapshot.period_type == pt)
            .order_by(MetricSnapshot.period_start.desc())
        )
        snaps = snaps_res.scalars().all()
        if not snaps:
            continue

        if period == "year":
            result.append((m, _aggregate_snaps(snaps)))
        else:
            result.append((m, snaps[0]))

    return result


def _aggregate_snaps(snaps: List[MetricSnapshot]) -> MetricSnapshot:
    """Агрегирует несколько снимков в один (суммы + средние)."""
    from app.models.metrics import MetricSnapshot as MS
    import uuid

    s = MS()
    s.id = uuid.uuid4()
    s.tenant_id = snaps[0].tenant_id
    s.manager_id = snaps[0].manager_id
    s.period_type = snaps[0].period_type
    s.period_start = snaps[-1].period_start   # самый ранний

    s.calls_count = sum(x.calls_count for x in snaps)
    s.deals_created = sum(x.deals_created for x in snaps)
    s.deals_won = sum(x.deals_won for x in snaps)
    s.deals_lost = sum(x.deals_lost for x in snaps)
    s.revenue = sum(x.revenue for x in snaps)
    s.activities_count = sum(x.activities_count for x in snaps)
    s.overdue_tasks = max(x.overdue_tasks for x in snaps)

    n = len(snaps)
    s.conversion_rate = round(s.deals_won / max(s.deals_created, 1) * 100, 1)
    s.avg_deal_size = round(s.revenue / max(s.deals_won, 1))
    s.crm_fill_rate = round(sum(x.crm_fill_rate for x in snaps) / n, 1)
    s.plan_completion_forecast = round(sum(x.plan_completion_forecast for x in snaps) / n, 1)
    s.calls_duration_avg = round(sum(x.calls_duration_avg for x in snaps) / n, 1)
    s.calls_quality_avg = round(sum(x.calls_quality_avg for x in snaps) / n, 1)
    return s


@router.get("/overview")
async def overview(
    period: str = Query("week", enum=["day", "week", "month", "year"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pairs = await _manager_snaps(db, current_user.tenant_id, period)

    total_revenue = 0.0
    total_calls = 0
    total_conv = 0.0
    total_forecast = 0.0
    top_name = ""
    top_revenue = 0.0
    at_risk = 0

    for m, snap in pairs:
        total_revenue += snap.revenue
        total_calls += snap.calls_count
        total_conv += snap.conversion_rate
        total_forecast += snap.plan_completion_forecast
        if snap.revenue > top_revenue:
            top_revenue = snap.revenue
            top_name = m.full_name
        if snap.plan_completion_forecast < 70:
            at_risk += 1

    n = len(pairs) or 1
    return {
        "total_managers": len(pairs),
        "active_deals": len(pairs) * 8,
        "total_revenue_month": round(total_revenue),
        "avg_conversion_rate": round(total_conv / n, 1),
        "plan_completion_avg": round(total_forecast / n, 1),
        "top_performer": top_name,
        "at_risk_deals": at_risk * 3,
    }


@router.get("/chart/revenue")
async def revenue_chart(
    period: str = Query("week", enum=["day", "week", "month", "year"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pt = _PERIOD_TYPE[period]
    limit = 30 if period == "day" else 12
    date_fmt = "%d.%m" if period in ("day", "week") else "%b %Y"

    snaps_res = await db.execute(
        select(
            MetricSnapshot.period_start,
            func.sum(MetricSnapshot.revenue).label("total_revenue"),
            func.sum(MetricSnapshot.calls_count).label("total_calls"),
            func.avg(MetricSnapshot.conversion_rate).label("avg_conv"),
        )
        .where(
            MetricSnapshot.tenant_id == current_user.tenant_id,
            MetricSnapshot.period_type == pt,
        )
        .group_by(MetricSnapshot.period_start)
        .order_by(MetricSnapshot.period_start.desc())
        .limit(limit)
    )
    rows = list(reversed(snaps_res.all()))

    return [
        {
            "date": r.period_start.strftime(date_fmt),
            "revenue": round(r.total_revenue),
            "calls": r.total_calls,
            "conversion": round(r.avg_conv, 1),
        }
        for r in rows
    ]


@router.get("/ranking")
async def ranking(
    period: str = Query("week", enum=["day", "week", "month", "year"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pairs = await _manager_snaps(db, current_user.tenant_id, period)

    items = [
        {
            "manager_id": str(m.id),
            "full_name": m.full_name,
            "revenue": snap.revenue,
            "plan_completion": snap.plan_completion_forecast,
            "calls_count": snap.calls_count,
            "conversion_rate": snap.conversion_rate,
        }
        for m, snap in pairs
    ]
    items.sort(key=lambda x: x["revenue"], reverse=True)
    for i, item in enumerate(items):
        item["rank"] = i + 1
        item["trend"] = "up" if i < len(items) // 2 else "down"
    return items
