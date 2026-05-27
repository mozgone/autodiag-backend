"""
Мок-коннектор — генерирует реалистичные демо-данные без подключения к реальной CRM.
Используется по умолчанию для демонстрации дашборда.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.connectors.base import BaseCRMConnector

# ── Mock call transcripts (varying quality) ───────────────────────────────────

CALL_TRANSCRIPTS = [
    # 1. Хорошо: правильное приветствие, SPIN-вопросы, работа с возражением, назначен следующий шаг
    {
        "id": "mock_call_001",
        "type": "call",
        "recording_url": None,
        "text": (
            "Менеджер: Добрый день! Меня зовут Алексей, компания ТехноСофт. "
            "Удобно ли вам сейчас говорить?\n"
            "Клиент: Да, слушаю вас.\n"
            "Менеджер: Отлично. Я звоню, потому что вы оставляли заявку на автоматизацию отдела продаж. "
            "Расскажите, пожалуйста, какие задачи сейчас стоят перед вашим отделом?\n"
            "Клиент: Ну, у нас проблема с учётом заявок, менеджеры забывают перезванивать.\n"
            "Менеджер: Понимаю. А как сейчас вы контролируете работу менеджеров с клиентами? "
            "Что для вас важно в первую очередь — скорость обработки или качество?\n"
            "Клиент: Скорее качество, мы теряем клиентов из-за долгого ожидания.\n"
            "Менеджер: Именно поэтому наша система ставит автоматические задачи и напоминания. "
            "Это позволит сократить время ответа с нескольких часов до минут. "
            "По данным наших клиентов, конверсия вырастает на 25–30%. "
            "Что думаете, интересно посмотреть как это работает у вас?\n"
            "Клиент: Звучит интересно, но у нас сейчас бюджет ограничен.\n"
            "Менеджер: Хорошо, что вы об этом говорите. Именно поэтому у нас есть тариф "
            "для небольших команд от 3 900 рублей в месяц — это буквально стоимость одного потерянного клиента. "
            "Давайте рассмотрим, как быстро система окупится в вашем случае?\n"
            "Клиент: Ну хорошо, можем встретиться.\n"
            "Менеджер: Отлично! Тогда предлагаю созвониться в среду в 14:00 для онлайн-демо. "
            "Я пришлю ссылку на Zoom. Договорились?\n"
            "Клиент: Договорились.\n"
            "Менеджер: Отлично, до среды!"
        ),
        "duration_seconds": 420,
        "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
    },
    # 2. Хорошо: SPIN, закрытие альтернативой, следующий шаг с датой
    {
        "id": "mock_call_002",
        "type": "call",
        "recording_url": None,
        "text": (
            "Менеджер: Здравствуйте! Это Мария из компании CRM-Про. "
            "Вы раньше интересовались нашей системой, хотела уточнить — актуально?\n"
            "Клиент: Да, мы ещё думаем.\n"
            "Менеджер: Понял. Скажите, что сейчас стоит на первом месте при выборе — "
            "интеграция с существующими системами или простота для команды?\n"
            "Клиент: Интеграция важнее, у нас уже есть 1С.\n"
            "Менеджер: Отлично, у нас есть готовый коннектор к 1С, настраивается за один день. "
            "Расскажите, сколько менеджеров в вашем отделе продаж?\n"
            "Клиент: Пятеро.\n"
            "Менеджер: Для пяти человек у нас как раз оптимальный тариф, "
            "плюс бесплатное обучение команды. "
            "Какие у вас ещё вопросы по интеграции, чтобы я подготовила конкретное решение?\n"
            "Клиент: Нас беспокоит перенос данных.\n"
            "Менеджер: Понимаю это беспокойство — перенос данных мы берём на себя полностью, "
            "с гарантией сохранности. При этом работа команды не прерывается. "
            "Тогда предлагаю: когда вам удобнее провести пилот — на следующей неделе или через две?\n"
            "Клиент: Давайте на следующей неделе.\n"
            "Менеджер: Замечательно! Во вторник в 11:00 — подходит? "
            "Пришлю программу демо и список вопросов заранее.\n"
            "Клиент: Хорошо.\n"
            "Менеджер: Договорились! До вторника!"
        ),
        "duration_seconds": 390,
        "created_at": (datetime.utcnow() - timedelta(days=4)).isoformat(),
    },
    # 3. Средне: есть приветствие и вопросы, но нет работы с возражением, следующий шаг размытый
    {
        "id": "mock_call_003",
        "type": "call",
        "recording_url": None,
        "text": (
            "Менеджер: Добрый день! Это Дмитрий, компания ТехноСофт.\n"
            "Клиент: Слушаю.\n"
            "Менеджер: Вы оставляли заявку. Расскажите немного о вашей ситуации?\n"
            "Клиент: Да, нам нужна CRM для небольшой команды.\n"
            "Менеджер: Понятно. Сколько человек в команде?\n"
            "Клиент: Трое менеджеров.\n"
            "Менеджер: Хорошо. У нас есть тариф на три пользователя. Стоимость — 4 500 в месяц.\n"
            "Клиент: Хм, это дороговато для нас.\n"
            "Менеджер: Ну, это стандартная цена на рынке. Может, подумаете?\n"
            "Клиент: Ладно, я посмотрю на сайте.\n"
            "Менеджер: Хорошо, если будут вопросы — звоните.\n"
            "Клиент: Ладно, спасибо."
        ),
        "duration_seconds": 180,
        "created_at": (datetime.utcnow() - timedelta(days=6)).isoformat(),
    },
    # 4. Средне: хорошая презентация, но нет выявления потребностей, слабый следующий шаг
    {
        "id": "mock_call_004",
        "type": "call",
        "recording_url": None,
        "text": (
            "Менеджер: Привет! Меня зовут Ольга, это ТехноСофт.\n"
            "Клиент: Добрый день.\n"
            "Менеджер: Хочу рассказать о нашей новой CRM-системе. "
            "Она помогает увеличить продажи на 30%, автоматизирует рутину, "
            "интегрируется с почтой, мессенджерами и 1С. "
            "Есть мобильное приложение. Стоимость от 2 000 рублей в месяц.\n"
            "Клиент: Звучит неплохо.\n"
            "Менеджер: Да, наши клиенты очень довольны результатами. "
            "У нас сейчас акция — первый месяц бесплатно.\n"
            "Клиент: Это интересно. Можно подумать?\n"
            "Менеджер: Конечно, подумайте. Можете написать нам на почту.\n"
            "Клиент: Хорошо, напишу."
        ),
        "duration_seconds": 150,
        "created_at": (datetime.utcnow() - timedelta(days=8)).isoformat(),
    },
    # 5. Слабо: нет вопросов, нет следующего шага, клиент уходит с «подумаю»
    {
        "id": "mock_call_005",
        "type": "call",
        "recording_url": None,
        "text": (
            "Менеджер: Алло, здравствуйте.\n"
            "Клиент: Здравствуйте.\n"
            "Менеджер: Вы оставляли заявку на CRM.\n"
            "Клиент: Да, оставлял.\n"
            "Менеджер: У нас CRM-система, очень удобная, всем нравится.\n"
            "Клиент: Понятно.\n"
            "Менеджер: Цена от 2 000 рублей в месяц. Интересно?\n"
            "Клиент: Надо подумать.\n"
            "Менеджер: Хорошо, думайте.\n"
            "Клиент: Ладно, спасибо.\n"
            "Менеджер: Пока."
        ),
        "duration_seconds": 60,
        "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
    },
]

# ── Mock chat threads ─────────────────────────────────────────────────────────

CHAT_THREADS = [
    # 1. Хорошо: проактивный фоллоу-ап, отвечает на вопросы, назначает встречу
    {
        "id": "mock_chat_001",
        "type": "chat",
        "text": (
            "Клиент: Здравствуйте, видел вашу рекламу. Что умеет ваша CRM?\n"
            "Менеджер: Добрый день! Меня зовут Алексей. "
            "Наша CRM автоматизирует весь цикл продаж: сбор заявок, распределение по менеджерам, "
            "контроль звонков и переписки, аналитику по каждому сотруднику. "
            "Расскажите немного о вашем бизнесе — сколько менеджеров в команде?\n"
            "Клиент: Нас пятеро.\n"
            "Менеджер: Отлично! Для команды из 5 человек у нас тариф Team — 6 500 в месяц, "
            "включает обучение и поддержку. Есть ещё вопросы?\n"
            "Клиент: А как с интеграцией с WhatsApp?\n"
            "Менеджер: Интеграция с WhatsApp Business входит в базовый тариф — "
            "все переписки попадают в карточку клиента автоматически. "
            "Хотите, проведём онлайн-демо? Могу в пятницу в 15:00 или в понедельник в 10:00.\n"
            "Клиент: Давайте в пятницу.\n"
            "Менеджер: Отлично! Отправлю ссылку на Zoom в четверг вечером. До встречи!"
        ),
        "messages_count": 8,
        "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
    },
    # 2. Средне: только отвечает на вопросы, не берёт инициативу
    {
        "id": "mock_chat_002",
        "type": "chat",
        "text": (
            "Клиент: Сколько стоит ваша система?\n"
            "Менеджер: От 2 000 рублей в месяц за одного пользователя.\n"
            "Клиент: А есть скидки?\n"
            "Менеджер: Да, при оплате за год скидка 20%.\n"
            "Клиент: Понятно. Спасибо.\n"
            "Менеджер: Пожалуйста, обращайтесь!"
        ),
        "messages_count": 6,
        "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
    },
    # 3. Слабо: односложные ответы, нет инициативы, клиент уходит без договорённостей
    {
        "id": "mock_chat_003",
        "type": "chat",
        "text": (
            "Клиент: Привет, интересует ваш продукт.\n"
            "Менеджер: Ок.\n"
            "Клиент: Что умеет?\n"
            "Менеджер: Много всего.\n"
            "Клиент: Цена?\n"
            "Менеджер: От 2000.\n"
            "Клиент: Подумаю.\n"
            "Менеджер: Хорошо."
        ),
        "messages_count": 8,
        "created_at": (datetime.utcnow() - timedelta(days=7)).isoformat(),
    },
]

MANAGERS_DEMO = [
    {"id": "mgr001", "name": "Алексей Петров", "email": "petrov@demo.com", "plan": 500000},
    {"id": "mgr002", "name": "Мария Иванова", "email": "ivanova@demo.com", "plan": 450000},
    {"id": "mgr003", "name": "Дмитрий Козлов", "email": "kozlov@demo.com", "plan": 400000},
    {"id": "mgr004", "name": "Ольга Смирнова", "email": "smirnova@demo.com", "plan": 350000},
    {"id": "mgr005", "name": "Иван Новиков", "email": "novikov@demo.com", "plan": 300000},
]

DEAL_STAGES = [
    ("Новый лид", 0), ("Квалификация", 1), ("Презентация", 2),
    ("КП отправлено", 3), ("Переговоры", 4), ("Договор", 5), ("Закрыто", 6),
]

class MockCRMConnector(BaseCRMConnector):

    async def test_connection(self) -> bool:
        return True

    async def get_managers(self) -> List[Dict[str, Any]]:
        return MANAGERS_DEMO

    async def get_deals(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        rng = random.Random(manager_id)
        deals = []
        num_deals = rng.randint(12, 25)
        for i in range(num_deals):
            stage_name, stage_order = rng.choice(DEAL_STAGES)
            is_closed = stage_order == 6
            is_won = is_closed and rng.random() > 0.35
            created_days_ago = rng.randint(1, 60)
            deals.append({
                "id": f"{manager_id}_deal_{i}",
                "title": f"Сделка №{1000 + i} — {rng.choice(['ООО Ромашка','АО Техпром','ИП Сидоров','ООО Альфа','ЗАО Бета'])}",
                "stage": stage_name,
                "stage_order": stage_order,
                "amount": round(rng.uniform(20000, 300000), -3),
                "is_won": is_won if is_closed else None,
                "risk_score": round(rng.uniform(0.1, 0.9), 2) if stage_order in [3, 4] else round(rng.uniform(0, 0.3), 2),
                "days_in_stage": rng.randint(1, 14),
                "created_at": (datetime.utcnow() - timedelta(days=created_days_ago)).isoformat(),
                "closed_at": (datetime.utcnow() - timedelta(days=rng.randint(1, 10))).isoformat() if is_closed else None,
            })
        return deals

    async def get_activities(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        rng = random.Random(manager_id + "act")
        activities = []
        num = rng.randint(30, 80)
        for i in range(num):
            act_type = rng.choice(["call", "call", "call", "email", "meeting", "chat"])
            duration = rng.randint(60, 1800) if act_type in ["call", "meeting"] else 0
            activities.append({
                "id": f"{manager_id}_act_{i}",
                "type": act_type,
                "duration_seconds": duration,
                "quality_score": round(rng.uniform(4.0, 9.5), 1),
                "sentiment": rng.choice(["positive", "positive", "neutral", "neutral", "negative"]),
                "created_at": (datetime.utcnow() - timedelta(days=rng.randint(0, 30))).isoformat(),
            })
        return activities

    async def get_notes(self, manager_id: str, since: datetime, limit: int = 50) -> List[Dict[str, Any]]:
        rng = random.Random(manager_id + "notes")
        notes = []
        templates = [
            "Созвонились с клиентом, обсудили условия договора. Клиент заинтересован.",
            "Отправил КП, жду ответа. Клиент сказал решит в течение недели.",
            "Входящий звонок — вопросы по интеграции. Ответил подробно.",
            "Follow-up после встречи. Клиент попросил время подумать.",
            "Провёл демо. Положительная реакция, переходим к согласованию договора.",
        ]
        for i in range(min(limit, rng.randint(5, 20))):
            days_ago = rng.randint(0, 30)
            created = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()
            notes.append({
                "id": f"{manager_id}_note_{i}",
                "type": "call" if rng.random() > 0.4 else "note",
                "text": rng.choice(templates),
                "created_at": created,
            })
        return notes

    async def get_deals_with_fields(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        rng = random.Random(manager_id + "fields")
        deals = await self.get_deals(manager_id, since)
        fields = ["Бюджет", "Источник лида", "Дата следующего контакта", "Отрасль клиента"]
        result = []
        for d in deals[:30]:
            result.append({
                "id": d["id"],
                "title": d["title"],
                "amount": d["amount"],
                "has_contact": rng.random() > 0.2,
                "custom_fields": [
                    {"field_id": str(i), "name": f, "is_empty": rng.random() < 0.35}
                    for i, f in enumerate(fields)
                ],
            })
        return result

    async def get_call_recordings(
        self, manager_id: str, since: datetime, limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Return mock call transcripts — no real audio, text only."""
        # Use manager_id seed so each manager gets a deterministic subset
        rng = random.Random(manager_id + "calls")
        calls = list(CALL_TRANSCRIPTS)
        rng.shuffle(calls)
        # Tag each entry with a manager-specific id to avoid cross-manager dedup clashes
        result = []
        for entry in calls[:limit]:
            item = dict(entry)
            item["id"] = f"{manager_id}_{entry['id']}"
            result.append(item)
        return result

    async def get_chat_messages(
        self, manager_id: str, since: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return mock WhatsApp-style chat conversations."""
        rng = random.Random(manager_id + "chats")
        chats = list(CHAT_THREADS)
        rng.shuffle(chats)
        result = []
        for entry in chats[:limit]:
            item = dict(entry)
            item["id"] = f"{manager_id}_{entry['id']}"
            result.append(item)
        return result
