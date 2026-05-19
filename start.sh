#!/bin/bash
# Скрипт запуска Sellex: инициализация БД → демо-данные → сервер
set -e

echo "============================================"
echo "  Sellex — запуск приложения"
echo "============================================"

# Пересоздаём схему БД (drop_all + create_all чтобы применить актуальную схему)
echo "📦 Инициализация схемы базы данных..."
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from app.core.database import engine, Base
import app.models
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print('   ✅ Схема готова')
asyncio.run(init())
"

# Загружаем демо-данные
echo "🌱 Загрузка демо-данных..."
python -m app.utils.demo_data

echo "🚀 Запуск сервера на порту ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
