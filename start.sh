#!/bin/bash
# Скрипт запуска Sellex: инициализация БД → демо-данные → сервер
set -e

echo "============================================"
echo "  Sellex — запуск приложения"
echo "============================================"

echo "📦 Очистка и инициализация БД (psycopg2)..."
python -c "
import sys, os
sys.path.insert(0, '.')

db_url = os.environ.get('DATABASE_URL', '')
# Приводим к psycopg2-формату
db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

import psycopg2
print('   Подключение...', flush=True)
conn = psycopg2.connect(db_url, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

tables = ['recommendations','metric_snapshots','activities','deals','managers','teams','users','tenants']
for t in tables:
    cur.execute(f'DROP TABLE IF EXISTS {t} CASCADE')
    print(f'   Удалена: {t}', flush=True)

conn.close()
print('   ✅ Таблицы очищены', flush=True)
"

echo "📦 Создание схемы (SQLAlchemy)..."
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from app.core.database import engine, Base
import app.models
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('   ✅ Схема создана', flush=True)
asyncio.run(init())
"

echo "🌱 Загрузка демо-данных..."
python -m app.utils.demo_data

echo "🚀 Запуск сервера на порту ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
