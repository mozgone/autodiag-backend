"""
Сервис синхронизации данных из CRM в аналитическое хранилище.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.manager import Manager
from app.models.metrics import MetricSnapshot, Recommendation
from app.models.tenant import Tenant
from app.connectors.base import BaseCRMConnector

logger = logging.getLogger(__name__)

AMO_STATUS_WON = 142
AMO_STATUS_LOST = 143


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


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _compute_snapshot(
    deals: List[Dict],
    activities: List[Dict],
    manager: Manager,
    period_start: datetime,
    period_end: datetime,
    tenant_id,
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

    # CRM fill rate: % сделок с указанной суммой (базовая метрика качества)
    with_price = [d for d in period_deals if float(d.get("amount") or 0) > 0]
    crm_fill = (len(with_price) / created * 100) if created > 0 else 0.0

    monthly_plan = max(float(manager.monthly_plan or 0), 1.0)
    # Недельная выручка → месячная (×4.33)
    monthly_est = revenue * 4.33
    plan_pct = round(monthly_est / monthly_plan * 100, 1)

    return MetricSnapshot(
        tenant_id=tenant_id,
        manager_id=manager.id,
        period_type="weekly",
        period_start=period_start,
        calls_count=len(calls) if calls else len(period_acts),
        calls_duration_avg=round(calls_dur_avg, 1),
        calls_quality_avg=0.0,
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


async def sync_tenant(db: AsyncSession, tenant: Tenant) -> dict:
    """
    Синхронизирует данные из CRM для тенанта.
    Возвращает статистику синхронизации.
    Бросает ValueError с понятным сообщением при ошибке.
    """
    connector = get_connector(tenant)

    # 1. Проверяем подключение
    try:
        ok = await connector.test_connection()
    except Exception as e:
        raise ValueError(f"Ошибка подключения к CRM: {e}")
    if not ok:
        raise ValueError("Не удалось подключиться к CRM. Проверьте токен и поддомен.")

    # 2. Получаем менеджеров
    crm_managers = await connector.get_managers()
    if not crm_managers:
        raise ValueError("В CRM не найдено ни одного менеджера.")

    since = datetime.utcnow() - timedelta(weeks=8)

    # 3. Upsert менеджеров (по crm_id)
    db_managers: List[Manager] = []
    for cm in crm_managers:
        res = await db.execute(
            select(Manager).where(
                Manager.tenant_id == tenant.id,
                Manager.crm_id == str(cm["id"]),
            )
        )
        mgr = res.scalar_one_or_none()
        if mgr is None:
            mgr = Manager(
                tenant_id=tenant.id,
                crm_id=str(cm["id"]),
                full_name=cm["name"],
                email=cm.get("email") or None,
                monthly_plan=float(cm.get("plan") or 0),
            )
            db.add(mgr)
        else:
            mgr.full_name = cm["name"]
            if cm.get("email"):
                mgr.email = cm["email"]
            mgr.is_active = True
        await db.flush()
        db_managers.append(mgr)

    # 4. Очищаем старые снимки и рекомендации
    await db.execute(delete(MetricSnapshot).where(MetricSnapshot.tenant_id == tenant.id))
    await db.execute(delete(Recommendation).where(Recommendation.tenant_id == tenant.id))

    total_deals = 0

    # 5. Для каждого менеджера — загружаем и вычисляем
    for mgr in db_managers:
        try:
            deals = await connector.get_deals(mgr.crm_id, since)
            activities = await connector.get_activities(mgr.crm_id, since)
        except Exception as e:
            logger.warning("Ошибка загрузки данных для %s: %s", mgr.full_name, e)
            deals, activities = [], []

        total_deals += len(deals)
        snaps: List[MetricSnapshot] = []

        for week in range(4):
            p_start = datetime.utcnow() - timedelta(weeks=4 - week)
            p_end = p_start + timedelta(weeks=1)
            snap = _compute_snapshot(deals, activities, mgr, p_start, p_end, tenant.id)
            db.add(snap)
            snaps.append(snap)

        for rec in _make_recommendations(mgr, snaps, tenant.id):
            db.add(rec)

    # 6. Обновляем статус тенанта
    tenant.last_sync_at = datetime.utcnow()
    tenant.sync_status = "ok"
    tenant.sync_error = None
    await db.commit()

    return {
        "managers_synced": len(db_managers),
        "deals_fetched": total_deals,
        "synced_at": tenant.last_sync_at.isoformat(),
    }
