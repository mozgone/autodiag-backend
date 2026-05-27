"""
Сервис синхронизации данных из CRM в аналитическое хранилище.
Создаёт снимки за день, неделю и месяц для каждого менеджера.
"""
import calendar
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.manager import Manager
from app.models.metrics import MetricSnapshot, Recommendation
from app.models.call_analysis import CallAnalysis
from app.models.tenant import Tenant
from app.connectors.base import BaseCRMConnector
from app.services.analysis_pipeline import process_manager_communications

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_connector(tenant: Tenant) -> BaseCRMConnector:
    if tenant.crm_type == "amocrm":
        config = json.loads(tenant.crm_config or "{}")
        from app.connectors.amocrm import AmoCRMConnector
        return AmoCRMConnector(
            subdomain=config["subdomain"],
            access_token=config["access_token"],
        )
    from app.connectors.mock import MockCRMConnector
    return MockCRMConnector()


def _month_range(year: int, month: int):
    """Возвращает (start, end) для заданного месяца."""
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, 1), datetime(year, month, last_day, 23, 59, 59)


def _prev_months(n: int) -> List[tuple]:
    """Возвращает список (year, month) за последние n месяцев (от старого к новому)."""
    result = []
    y, m = datetime.utcnow().year, datetime.utcnow().month
    for _ in range(n):
        result.insert(0, (y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return result


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


# ── Snapshot computation ───────────────────────────────────────────────────────

def _compute_snapshot(
    deals: List[Dict],
    activities: List[Dict],
    manager: Manager,
    period_start: datetime,
    period_end: datetime,
    tenant_id,
    period_type: str = "weekly",
) -> MetricSnapshot:
    period_deals = [
        d for d in deals
        if (dt := _parse_dt(d.get("created_at"))) and period_start <= dt < period_end
    ]
    period_acts = [
        a for a in activities
        if (dt := _parse_dt(a.get("created_at"))) and period_start <= dt < period_end
    ]

    won = [d for d in period_deals if d.get("is_won") is True]
    lost = [d for d in period_deals if d.get("is_won") is False]
    created = len(period_deals)

    revenue = sum(float(d.get("amount") or 0) for d in won)
    avg_deal = (revenue / len(won)) if won else 0.0
    conversion = (len(won) / created * 100) if created > 0 else 0.0

    calls = [a for a in period_acts if a.get("type") == "call"]
    call_durs = [int(c.get("duration_seconds") or 0) for c in calls]
    calls_dur_avg = (sum(call_durs) / len(call_durs)) if call_durs else 0.0

    # Качество звонков: среднее из quality_score активностей
    quality_scores = [float(a["quality_score"]) for a in period_acts if a.get("quality_score")]
    calls_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0.0

    # Заполненность CRM: сделки с суммой И контактом
    with_price = [d for d in period_deals if float(d.get("amount") or 0) > 0]
    with_contact = [d for d in period_deals if d.get("has_contact")]
    filled_count = len([d for d in period_deals
                        if float(d.get("amount") or 0) > 0 or d.get("has_contact")])
    crm_fill = (filled_count / created * 100) if created > 0 else 0.0

    monthly_plan = max(float(manager.monthly_plan or 0), 1.0)
    multipliers = {"daily": 30.0, "weekly": 4.33, "monthly": 1.0}
    monthly_est = revenue * multipliers.get(period_type, 4.33)
    plan_pct = round(monthly_est / monthly_plan * 100, 1)

    return MetricSnapshot(
        tenant_id=tenant_id,
        manager_id=manager.id,
        period_type=period_type,
        period_start=period_start,
        calls_count=len(calls) if calls else len(period_acts),
        calls_duration_avg=round(calls_dur_avg, 1),
        calls_quality_avg=calls_quality,
        deals_created=created,
        deals_won=len(won),
        deals_lost=len(lost),
        conversion_rate=round(conversion, 1),
        avg_deal_size=round(avg_deal),
        revenue=round(revenue),
        crm_fill_rate=round(crm_fill, 1),
        overdue_tasks=0,
        activities_count=len(period_acts),
        plan_completion_forecast=plan_pct,
    )


def _make_recommendations(
    manager: Manager,
    snaps: List[MetricSnapshot],
    tenant_id,
) -> List[Recommendation]:
    if not snaps:
        return []
    last = snaps[-1]
    plan_pct = last.plan_completion_forecast
    conv = last.conversion_rate
    recs: List[Recommendation] = []

    if plan_pct >= 100:
        recs.append(Recommendation(
            tenant_id=tenant_id, manager_id=manager.id,
            rec_type="strength", priority=1,
            title="Перевыполнение плана",
            content=(
                f"{manager.full_name} выполняет план на {plan_pct:.0f}%. "
                "Рассмотрите роль наставника для менее опытных коллег."
            ),
        ))
    elif plan_pct < 60:
        recs.append(Recommendation(
            tenant_id=tenant_id, manager_id=manager.id,
            rec_type="alert", priority=3,
            title="Риск невыполнения плана",
            content=(
                f"Прогноз выполнения плана: {plan_pct:.0f}%. "
                "Необходимо срочно увеличить количество активностей и проработать застрявшие сделки."
            ),
        ))
    else:
        recs.append(Recommendation(
            tenant_id=tenant_id, manager_id=manager.id,
            rec_type="growth", priority=2,
            title="Зона роста: конверсия",
            content=(
                f"Конверсия: {conv:.1f}%. "
                "Есть потенциал улучшения через более активный follow-up после отправки КП."
            ),
        ))

    if last.crm_fill_rate > 0 and last.crm_fill_rate < 60:
        recs.append(Recommendation(
            tenant_id=tenant_id, manager_id=manager.id,
            rec_type="alert", priority=2,
            title="Низкое качество заполнения CRM",
            content=(
                f"Только {last.crm_fill_rate:.0f}% сделок содержат сумму. "
                "Заполнение бюджета сделки обязательно для точного прогноза."
            ),
        ))
    return recs


# ── Main sync ─────────────────────────────────────────────────────────────────

async def sync_tenant(db: AsyncSession, tenant: Tenant) -> dict:
    """
    Синхронизирует данные из CRM для тенанта.
    Создаёт снимки за последние 30 дней, 12 недель, 12 месяцев.
    """
    connector = get_connector(tenant)

    try:
        ok = await connector.test_connection()
    except Exception as e:
        raise ValueError(f"Ошибка подключения к CRM: {e}")
    if not ok:
        raise ValueError("Не удалось подключиться к CRM. Проверьте токен и поддомен.")

    crm_managers = await connector.get_managers()
    if not crm_managers:
        raise ValueError("В CRM не найдено ни одного менеджера.")

    # Берём данные за последний год (покрывает все периоды)
    since = datetime.utcnow() - timedelta(days=365)

    # Полная очистка старых данных — удаляем снимки, рекомендации и всех менеджеров
    # (включая демо-менеджеров), чтобы не было дублей при подключении реальной CRM
    await db.execute(delete(CallAnalysis).where(CallAnalysis.tenant_id == tenant.id))
    await db.execute(delete(MetricSnapshot).where(MetricSnapshot.tenant_id == tenant.id))
    await db.execute(delete(Recommendation).where(Recommendation.tenant_id == tenant.id))
    await db.execute(delete(Manager).where(Manager.tenant_id == tenant.id))
    await db.flush()

    # Создаём менеджеров из CRM
    db_managers: List[Manager] = []
    for cm in crm_managers:
        mgr = Manager(
            tenant_id=tenant.id,
            crm_id=str(cm["id"]),
            full_name=cm["name"],
            email=cm.get("email") or None,
            monthly_plan=float(cm.get("plan") or 0),
        )
        db.add(mgr)
        await db.flush()
        db_managers.append(mgr)

    total_deals = 0
    now = datetime.utcnow()

    for mgr in db_managers:
        try:
            deals = await connector.get_deals(mgr.crm_id, since)
            activities = await connector.get_activities(mgr.crm_id, since)
        except Exception as e:
            logger.warning("Ошибка загрузки данных для %s: %s", mgr.full_name, e)
            deals, activities = [], []

        total_deals += len(deals)
        weekly_snaps: List[MetricSnapshot] = []

        # ── Дневные снимки: последние 30 дней ─────────────────────────────────
        for d in range(30):
            day = now - timedelta(days=29 - d)
            p_start = datetime(day.year, day.month, day.day, 0, 0, 0)
            p_end = datetime(day.year, day.month, day.day, 23, 59, 59)
            snap = _compute_snapshot(deals, activities, mgr, p_start, p_end, tenant.id, "daily")
            db.add(snap)

        # ── Недельные снимки: последние 12 недель ──────────────────────────────
        for w in range(12):
            p_start = now - timedelta(weeks=11 - w)
            p_end = p_start + timedelta(weeks=1)
            snap = _compute_snapshot(deals, activities, mgr, p_start, p_end, tenant.id, "weekly")
            db.add(snap)
            weekly_snaps.append(snap)

        # ── Месячные снимки: последние 12 месяцев ─────────────────────────────
        for year, month in _prev_months(12):
            p_start, p_end = _month_range(year, month)
            snap = _compute_snapshot(deals, activities, mgr, p_start, p_end, tenant.id, "monthly")
            db.add(snap)

        # Рекомендации на основе последних недельных снимков
        for rec in _make_recommendations(mgr, weekly_snaps, tenant.id):
            db.add(rec)

        # ── Communication quality analysis (calls + chats) ────────────────────
        try:
            call_analyses = await process_manager_communications(
                db, connector, mgr, tenant.id, since
            )
            for ca in call_analyses:
                db.add(ca)

            # Update calls_quality_avg in weekly snapshots with analyzed scores
            if call_analyses and weekly_snaps:
                avg_quality = sum(ca.overall_score for ca in call_analyses) / len(call_analyses)
                for snap in weekly_snaps:
                    snap.calls_quality_avg = round(avg_quality, 1)
        except Exception as e:
            logger.warning("Communication analysis не выполнен для %s: %s", mgr.full_name, e)

        # AI-анализ чатов и полей CRM
        try:
            notes_data = await connector.get_notes(mgr.crm_id, since, limit=30)
            fields_data = await connector.get_deals_with_fields(mgr.crm_id, since)

            notes_texts = [n["text"] for n in notes_data if n.get("text")]

            # Процент заполненности по каждому полю
            field_fill: Dict[str, float] = {}
            if fields_data:
                all_field_names = {
                    cf["name"]
                    for d in fields_data
                    for cf in d.get("custom_fields", [])
                }
                for fname in all_field_names:
                    total = sum(
                        1 for d in fields_data
                        for cf in d.get("custom_fields", []) if cf["name"] == fname
                    )
                    filled = sum(
                        1 for d in fields_data
                        for cf in d.get("custom_fields", [])
                        if cf["name"] == fname and not cf["is_empty"]
                    )
                    field_fill[fname] = round(filled / total * 100, 1) if total else 0.0

            last_snap = weekly_snaps[-1] if weekly_snaps else None
            if last_snap:
                stats_for_ai = {
                    "deals_created": last_snap.deals_created,
                    "deals_won": last_snap.deals_won,
                    "revenue": last_snap.revenue,
                    "conversion_rate": last_snap.conversion_rate,
                    "plan_completion_forecast": last_snap.plan_completion_forecast,
                    "calls_count": last_snap.calls_count,
                    "crm_fill_rate": last_snap.crm_fill_rate,
                }
                from app.services.analysis_agent import analyze_manager
                ai_recs = await analyze_manager(
                    mgr.full_name, stats_for_ai, notes_texts, field_fill
                )
                for r in ai_recs:
                    db.add(Recommendation(
                        tenant_id=tenant.id,
                        manager_id=mgr.id,
                        rec_type=r.get("type", "growth"),
                        title=str(r.get("title", ""))[:499],
                        content=str(r.get("content", "")),
                        priority=max(1, min(3, int(r.get("priority", 2)))),
                    ))
        except Exception as e:
            logger.warning("AI-анализ не выполнен для %s: %s", mgr.full_name, e)

        # ── Анализ звонков и чатов (3-агентный пайплайн) ──────────────────────
        try:
            call_analyses = await process_manager_communications(
                db, connector, mgr, tenant.id, since
            )
            for ca in call_analyses:
                db.add(ca)
            # Обновляем качество звонков на основе реального анализа
            if call_analyses and weekly_snaps:
                call_items = [ca for ca in call_analyses if ca.item_type == "call"]
                if call_items:
                    avg_quality = round(
                        sum(ca.overall_score for ca in call_items) / len(call_items), 1
                    )
                    for snap in weekly_snaps:
                        snap.calls_quality_avg = avg_quality
        except Exception as e:
            logger.warning("Анализ коммуникаций не выполнен для %s: %s", mgr.full_name, e)

    tenant.last_sync_at = datetime.utcnow()
    tenant.sync_status = "ok"
    tenant.sync_error = None
    await db.commit()

    return {
        "managers_synced": len(db_managers),
        "deals_fetched": total_deals,
        "synced_at": tenant.last_sync_at.isoformat(),
    }
