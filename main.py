"""
АвтоДиагност — FastAPI Backend (Groq, с автовыбором модели)
"""
import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from groq import Groq

app = FastAPI(title="АвтоДиагност API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-8b-8192",
    "gemma2-9b-it",
]

SYSTEM_PROMPT = """Ты — АвтоДиагност, AI-агент по диагностике автомобилей. Говоришь по-русски.

ВАЖНО: Отвечай ТОЛЬКО валидным JSON. Никакого текста до или после. Без markdown.

Формат: {"message": "текст", "quick_replies": [], "stage": 0, "result_card": null}

Этапы: 0=приветствие, 1=уточни авто (по одному вопросу), 2=опыт пользователя, 3=сам или сервис, 4=итог.

На этапе 4 если сервис — заполни result_card с полями АВТОМОБИЛЬ, СИМПТОМЫ, КОГДА, ПРИЧИНА, ЧТО ПРОВЕРИТЬ, ЦЕНА РАБОТЫ, ЦЕНА ЗАПЧАСТЕЙ и copy_text.
Если сам — инструкция в message, result_card=null.
Один вопрос за раз. Цены по России 2024."""


class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: List[Message] = []

class SessionRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = "anon"


def safe_parse(text: str) -> dict:
    text = text.strip().replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


def call_groq(messages: list) -> dict:
    last_error = None
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=0.7, max_tokens=1500,
            )
            return safe_parse(response.choices[0].message.content)
        except Exception as e:
            print(f"Model {model} failed: {e}")
            last_error = e
    raise last_error


@app.post("/session/start")
async def start_session(req: SessionRequest):
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Поприветствуй пользователя и попроси описать проблему с авто."}
        ]
        return call_groq(messages)
    except Exception as e:
        print(f"Error: {e}")
        return {"message": "👋 Привет! Я АвтоДиагност.\n\nОпишите что случилось с автомобилем — можно просто: «стучит», «не заводится», «горит лампочка».", "quick_replies": ["Стук / вибрация", "Не заводится", "Горит лампочка", "Другая проблема"], "stage": 0, "result_card": None}


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in req.history[:-1]:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": req.message})
        return call_groq(messages)
    except Exception as e:
        print(f"Error: {e}")
        return {"message": "Что-то пошло не так. Напишите ещё раз 🙏", "quick_replies": [], "stage": 1, "result_card": None}


@app.get("/health")
async def health():
    return {"status": "ok"}
