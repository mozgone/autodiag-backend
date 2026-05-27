"""
Заполняет базу данных демо-данными для презентации дашборда.
Запускается командой: python -m app.utils.seed_demo
"""
import asyncio
import calendar
import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.manager import Manager, Team
from app.models.deal import Deal, Activity
from app.models.metrics import MetricSnapshot, Recommendation

DEMO_MANAGERS = [
    {"name": "Алексей Петров", "email": "petrov@sellex.demo", "plan": 500000, "perf": 0.85},
    {"name": "Мария Иванова", "email": "ivanova@sellex.demo", "plan": 450000, "perf": 1.05},
    {"name": "Дмитрий Козлов", "email": "kozlov@sellex.demo", "plan": 400000, "perf": 0.62},
    {"name": "Ольга Смирнова", "email": "smirnova@sellex.demo", "plan": 350000, "perf": 0.95},
    {"name": "Иван Новиков", "email": "novikov@sellex.demo", "plan": 300000, "perf": 1.12},
]

STAGES = [("Новый лид", 0), ("Квалификация", 1), ("Презентация", 2), ("КП отправлено", 3), ("Переговоры", 4), ("Договор", 5)]

async def _seed_managers_for_tenant(db: AsyncSession, tenant_id: uuid.UUID, team_id: uuid.UUID) -> None:
    """Засеивает 5 демо-менеджеров с метриками и рекомендациями для указанного тенанта."""
    rng = random.Random(tenant_id.int % (2**32))
    for idx, m_data in enumerate(DEMO_MANAGERS):
        mgr_id = uuid.uuid4()
        mgr = Manager(
            id=mgr_id,
            tenant_id=tenant_id,
            team_id=team_id,
            full_name=m_data["name"],
            email=f"{m_data['email'].split('@')[0]}_{str(tenant_id)[:6]}@sellex.demo",
            monthly_plan=m_data["plan"],
            crm_id=f"crm_{idx+1}",
        )
        db.add(mgr)
        await db.flush()

        perf = m_data["perf"]
        calls = int(rng.uniform(20, 60) * perf)
        deals_created = rng.randint(10, 20)
        deals_won = int(deals_created * rng.uniform(0.2, 0.5) * perf)
        revenue = deals_won * rng.uniform(50000, 150000) * perf

        def _snap(period_type: str, period_start: datetime, divisor: float) -> MetricSnapshot:
            return MetricSnapshot(
                tenant_id=tenant_id,
                manager_id=mgr_id,
                period_type=period_type,
                period_start=period_start,
                calls_count=max(1, int(calls * rng.uniform(0.8, 1.2) / divisor)),
                calls_duration_avg=rng.uniform(120, 600),
                calls_quality_avg=round(rng.uniform(5.0, 9.0) * perf, 1),
                deals_created=max(0, int(deals_created * rng.uniform(0.7, 1.3) / divisor)),
                deals_won=max(0, int(deals_won * rng.uniform(0.5, 1.5) / divisor)),
                deals_lost=rng.randint(0, 2),
                conversion_rate=round(rng.uniform(15, 45) * perf, 1),
                avg_deal_size=round(rng.uniform(40000, 150000), -3),
                revenue=round(revenue / divisor * rng.uniform(0.7, 1.3), -3),
                crm_fill_rate=round(rng.uniform(55, 95) * min(perf, 1), 1),
                overdue_tasks=max(0, int(rng.uniform(0, 5) * (1 - perf + 0.5))),
                activities_count=max(1, int((calls + rng.randint(5, 20)) / divisor)),
                plan_completion_forecast=round(perf * 100 * rng.uniform(0.9, 1.1), 1),
            )

        # Недельные снимки — последние 12 недель
        for week in range(12):
            # week=11 (последний): period_start = now - 1 нед., соответствует текущей неделе
            period_start = datetime.utcnow() - timedelta(weeks=12 - week)
            db.add(_snap("weekly", period_start, 4.0))

        # Дневные снимки — последние 30 дней
        for d in range(30):
            period_start = datetime.utcnow() - timedelta(days=29 - d)
            db.add(_snap("daily", period_start, 22.0))

        # Месячные снимки — последние 12 месяцев
        now = datetime.utcnow()
        y, m_num = now.year, now.month
        months = []
        for _ in range(12):
            months.insert(0, (y, m_num))
            m_num -= 1
            if m_num == 0:
                m_num, y = 12, y - 1
        for yr, mn in months:
            period_start = datetime(yr, mn, 1)
            db.add(_snap("monthly", period_start, 1.0))

        if perf >= 1.0:
            db.add(Recommendation(
                tenant_id=tenant_id, manager_id=mgr_id,
                rec_type="strength", priority=1,
                title="Перевыполнение плана",
                content=f"{m_data['name']} стабильно перевыполняет план. Рекомендуем рассмотреть наставничество над менее опытными коллегами.",
            ))
        elif perf < 0.75:
            db.add(Recommendation(
                tenant_id=tenant_id, manager_id=mgr_id,
                rec_type="alert", priority=3,
                title="Риск невыполнения плана",
                content=f"Прогноз выполнения плана: {int(perf*100)}%. Необходимо срочно увеличить количество контактов и проработать застрявшие сделки.",
            ))
        else:
            db.add(Recommendation(
                tenant_id=tenant_id, manager_id=mgr_id,
                rec_type="growth", priority=2,
                title="Зона роста: конверсия",
                content="Есть потенциал для улучшения конверсии на этапе 'КП отправлено'. Рекомендуем более активный follow-up через 2-3 дня после отправки.",
            ))


async def seed_demo_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Засеивает демо-данные (команда + менеджеры) для нового тенанта."""
    from sqlalchemy import select as sa_select
    existing = await db.execute(sa_select(Manager).where(Manager.tenant_id == tenant_id).limit(1))
    if existing.scalar_one_or_none():
        return  # уже есть данные

    team = Team(
        tenant_id=tenant_id,
        name="Отдел продаж",
        monthly_plan=2000000,
    )
    db.add(team)
    await db.flush()

    await _seed_managers_for_tenant(db, tenant_id, team.id)
    await db.commit()


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        existing = await db.execute(select(Tenant).where(Tenant.slug == "demo"))
        if existing.scalar_one_or_none():
            print("⚠️  Демо-данные уже загружены, пропускаем.")
            return

        # Тенант
        tenant = Tenant(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Демо Компания",
            slug="demo",
            is_active=True,
            crm_type="mock",
            consent_confirmed=True,
        )
        db.add(tenant)

        # Пользователь-руководитель
        admin = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
            tenant_id=tenant.id,
            email="admin@sellex.demo",
            password_hash=hash_password("demo1234"),
            full_name="Сергей Руководитель",
            role=UserRole.HEAD_OF_SALES,
        )
        db.add(admin)

        # Команда
        team = Team(
            id=uuid.UUID("00000000-0000-0000-0000-000000000020"),
            tenant_id=tenant.id,
            name="Отдел продаж",
            monthly_plan=2000000,
        )
        db.add(team)
        await db.flush()

        await _seed_managers_for_tenant(db, tenant.id, team.id)

        await db.commit()
        print("✅ Демо-данные успешно загружены!")
        print("   Логин: admin@sellex.demo")
        print("   Пароль: demo1234")

if __name__ == "__main__":
    asyncio.run(seed())
