#!/bin/bash
# Запуск Sellex: миграция схемы → демо-данные (если первый запуск) → сервер
set -e

echo "============================================"
echo "  Sellex — запуск приложения"
echo "============================================"

# Полный сброс БД только при RESET_DB=1 (экстренное исправление)
if [ "${RESET_DB:-0}" = "1" ]; then
  echo "⚠️  RESET_DB=1 — полная очистка БД..."
  python -c "
import sys, os
sys.path.insert(0, '.')
db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
import psycopg2
conn = psycopg2.connect(db_url, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()
tables = ['call_analyses','recommendations','metric_snapshots','activities','deals','managers','teams','users','tenants']
for t in tables:
    cur.execute(f'DROP TABLE IF EXISTS {t} CASCADE')
    print(f'   Удалена: {t}', flush=True)
conn.close()
print('   ✅ Таблицы очищены', flush=True)
"
fi

echo "📦 Применение схемы БД (CREATE TABLE IF NOT EXISTS + миграции колонок)..."
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from app.core.database import engine, Base
import app.models

async def migrate():
    async with engine.begin() as conn:
        # Создаём отсутствующие таблицы (существующие не трогает)
        await conn.run_sync(Base.metadata.create_all)

    # Добавляем новые колонки, если их нет (безопасно для production)
    import psycopg2
    import os
    db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
    pg = psycopg2.connect(db_url, connect_timeout=15)
    pg.autocommit = True
    cur = pg.cursor()

    migrations = [
        # Tenant: колонки синхронизации
        \"ALTER TABLE tenants ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP\",
        \"ALTER TABLE tenants ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20)\",
        \"ALTER TABLE tenants ADD COLUMN IF NOT EXISTS sync_error TEXT\",
        # Manager: crm_id для upsert
        \"ALTER TABLE managers ADD COLUMN IF NOT EXISTS crm_id VARCHAR(100)\",
    ]
    for sql in migrations:
        cur.execute(sql)
    pg.close()
    print('   ✅ Схема применена', flush=True)

asyncio.run(migrate())
"

echo "🌱 Загрузка начальных данных (пропускается если уже есть)..."
python -m app.utils.demo_data

echo "🚀 Запуск сервера на порту ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
