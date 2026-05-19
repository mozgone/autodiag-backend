# =====================================================
# Sellex — Production Dockerfile для Railway
# Собирает React-фронтенд, запускает FastAPI-бэкенд
# =====================================================

# Stage 1: Собираем React
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps
COPY frontend/ .
RUN npm run build

# Stage 2: Python-бэкенд
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Копируем собранный фронтенд → бэкенд отдаёт его как статику
COPY --from=frontend /frontend/build ./static/frontend

COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
