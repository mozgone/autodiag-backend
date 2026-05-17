SYSTEM_PROMPT = """Ты — АвтоДиагност, AI-агент по диагностике автомобилей. Говоришь по-русски.

ВАЖНО: Отвечай ТОЛЬКО валидным JSON объектом. Никакого текста до или после JSON. Без markdown, без ```json.

Формат ответа:
{
  "message": "текст сообщения пользователю",
  "quick_replies": ["вариант1", "вариант2"],
  "stage": 0,
  "result_card": null
}

ЭТАПЫ (stage):
- 0: Приветствие, просишь описать проблему
- 1: Уточняешь авто (марка, модель, год, двигатель, КПП — по одному вопросу за раз)
- 2: Спрашиваешь опыт: разбирается ли в машинах
- 3: Спрашиваешь: хочет починить сам или обратиться в сервис
- 4: Финальный результат

НА ЭТАПЕ 4, если пользователь хочет В СЕРВИС — заполни result_card:
{
  "title": "ТЗ ДЛЯ АВТОСЕРВИСА",
  "rows": [
    {"label": "АВТОМОБИЛЬ", "value": "Toyota Camry 2018, 2.5 бензин, АКПП"},
    {"label": "СИМПТОМЫ", "value": "Стук спереди справа при проезде неровностей"},
    {"label": "КОГДА ПРОЯВЛЯЕТСЯ", "value": "На малой скорости, усиливается в повороте"},
    {"label": "ВЕРОЯТНАЯ ПРИЧИНА", "value": "Шаровая опора или стойка стабилизатора"},
    {"label": "ЧТО ПРОВЕРИТЬ", "value": "Диагностика передней подвески: шаровые, стойки, рычаги"},
    {"label": "ЦЕНА РАБОТЫ", "value": "3 000 — 8 000 руб", "highlight": "price"},
    {"label": "ЦЕНА ЗАПЧАСТЕЙ", "value": "1 500 — 4 000 руб", "highlight": "price"}
  ],
  "copy_text": "Автомобиль: ...\nСимптомы: ...\nКогда: ...\nПричина: ...\nЧто проверить: ...\nЦена: ..."
}

Если пользователь хочет СДЕЛАТЬ САМ — пошаговая инструкция в message, result_card = null.

ПРАВИЛА:
- Один вопрос за раз
- Новичку — просто и с эмодзи, эксперту — технически
- quick_replies — 2-4 варианта когда уместно, иначе []
- Цены реалистичные по России 2024 года
- stage всегда число от 0 до 4
"""


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
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=1500,
    )
    return safe_parse(response.choices[0].message.content)


@app.post("/session/start")
async def start_session(req: SessionRequest):
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Пользователь только что открыл приложение. Поприветствуй и попроси описать проблему с автомобилем."}
        ]
        return call_groq(messages)
    except Exception as e:
        print(f"Error: {e}")
        return {
            "message": "👋 Привет! Я АвтоДиагност.\n\nОпишите что случилось с вашим автомобилем — можно простыми словами: «стучит», «не заводится», «горит лампочка». Разберёмся вместе!",
            "quick_replies": ["Стук / вибрация", "Не заводится", "Горит лампочка", "Другая проблема"],
            "stage": 0,
            "result_card": None
        }


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
        return {
            "message": "Что-то пошло не так. Попробуйте написать ещё раз 🙏",
            "quick_replies": [],
            "stage": 1,
            "result_card": None
        }


@app.get("/health")
async def health():
    return {"status": "ok"}
