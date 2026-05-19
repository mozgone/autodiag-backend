#!/bin/bash
# Скрипт запуска Sellex: инициализация БД → демо-данные → сервер
set -e

echo "============================================"
echo "  Sellex — запуск приложения"
echo "============================================"

echo "📦 Инициализация схемы базы данных..."
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from sqlalchemy import text
from app.core.database import engine, Base
import app.models

async def init():
    async with engine.begin() as conn:
        # Удаляем все таблицы в нужном порядке с CASCADE
        tables = [
            'recommendations', 'metric_snapshots', 'activities',
            'deals', 'managers', 'teams', 'users', 'tenants'
        ]
        for t in tables:
            await conn.execute(text(f'DROP TABLE IF EXISTS {t} CASCADE'))
        await conn.run_sync(Base.metadata.create_all)
    print('   ✅ Схема готова')

asyncio.run(init())
"

echo "🌱 Загрузка демо-данных..."
python -m app.utils.demo_data

echo "🚀 Запуск сервера на порту ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
