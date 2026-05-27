"""
Мок-коннектор — генерирует реалистичные демо-данные без подключения к реальной CRM.
Используется по умолчанию для демонстрации дашборда.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.connectors.base import BaseCRMConnector

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
