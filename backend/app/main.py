"""
Sellex — FastAPI Backend
Мультитенантная система анализа отдела продаж.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.api.v1.router import router as api_router

app = FastAPI(
    title="Sellex API",
    version=settings.APP_VERSION,
    description="Система анализа менеджеров по продажам с ИИ-агентами",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

# Отдаём React-фронтенд как статику (в production-сборке)
_frontend = os.path.join(os.path.dirname(__file__), "..", "static", "frontend")
if os.path.isdir(_frontend):
    # Статические файлы React (CSS, JS, медиа)
    _static = os.path.join(_frontend, "static")
    if os.path.isdir(_static):
        app.mount("/static", StaticFiles(directory=_static), name="react_assets")

    # Все остальные маршруты → index.html (SPA-роутинг)
    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        file_path = os.path.join(_frontend, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_frontend, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Sellex API. Документация: /docs"}
