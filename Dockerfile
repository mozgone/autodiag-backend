# =====================================================
# Sellex — Production Dockerfile
# Фронтенд уже собран в frontend/build/
# =====================================================

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Копируем pre-built фронтенд → бэкенд отдаёт его как статику
COPY frontend/build/ ./static/frontend/

COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
