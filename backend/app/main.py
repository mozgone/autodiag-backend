"""
Sellex — FastAPI Backend
Мультитенантная система анализа отдела продаж.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import router as api_router

app = FastAPI(
    title="Sellex API",
    version=settings.APP_VERSION,
    description="Система анализа менеджеров по продажам с ИИ-агентами",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production заменить на список доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

@app.get("/")
async def root():
    return {"message": "Sellex API. Документация: /docs"}
