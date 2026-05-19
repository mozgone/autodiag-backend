"""
Агент-генератор рекомендаций.
Анализирует метрики менеджера и генерирует персонализированные инсайты через OpenAI.
Если ключа нет — использует шаблонные рекомендации.
"""
import json
from typing import List, Dict, Any, Optional
from app.agents.base import BaseAgent
from app.core.config import settings

TEMPLATES = {
    "strength": [
        ("Отличная конверсия", "Ваша конверсия {conv}% выше среднего по отделу на {delta}%. Продолжайте использовать текущую тактику переговоров."),
        ("Высокая активность", "За последние 7 дней вы совершили {calls} звонков — это лучший результат в команде."),
    ],
    "growth": [
        ("Скорость движения сделок", "Средний срок в стадии «{stage}» составляет {days} дней. Рекомендуем ускорить переход — отраслевой бенчмарк: 3-4 дня."),
        ("Заполнение CRM", "Заполненность карточек клиентов: {crm}%. Пустые поля усложняют прогнозирование — уделите 15 минут в конце дня."),
    ],
    "alert": [
        ("Риск срыва плана", "При текущей динамике прогноз выполнения плана на месяц: {forecast}%. Необходимо {extra} дополнительных сделок."),
        ("Просроченные задачи", "У вас {overdue} просроченных задач в CRM. Это снижает доверие клиентов и усложняет отчётность."),
    ],
}

class RecommendationGenerator(BaseAgent):
    name = "recommendation_generator"

    async def run(self, manager_name: str, stats: Dict[str, Any], avg_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        if settings.OPENAI_API_KEY:
            return await self._generate_with_ai(manager_name, stats, avg_stats)
        return self._generate_from_templates(stats, avg_stats)

    def _generate_from_templates(self, stats: Dict, avg: Dict) -> List[Dict]:
        recs = []
        conv = stats.get("conversion_rate", 0)
        avg_conv = avg.get("conversion_rate", 20)
        if conv > avg_conv:
            recs.append({
                "type": "strength",
                "title": "Отличная конверсия",
                "content": f"Ваша конверсия {conv:.1f}% выше среднего по отделу ({avg_conv:.1f}%). Продолжайте текущую тактику переговоров.",
                "priority": 1,
            })
        crm_fill = stats.get("crm_fill_rate", 100)
        if crm_fill < 75:
            recs.append({
                "type": "growth",
                "title": "Заполнение CRM требует внимания",
                "content": f"Заполненность карточек клиентов: {crm_fill:.0f}%. Рекомендуем уделять 10-15 минут в конце дня для актуализации данных.",
                "priority": 2,
            })
        forecast = stats.get("plan_completion_forecast", 100)
        if forecast < 80:
            recs.append({
                "type": "alert",
                "title": "Риск невыполнения плана",
                "content": f"Прогноз выполнения месячного плана: {forecast:.0f}%. Рекомендуем увеличить количество исходящих контактов и ускорить движение сделок на финальных стадиях.",
                "priority": 3,
            })
        overdue = stats.get("overdue_tasks", 0)
        if overdue > 3:
            recs.append({
                "type": "alert",
                "title": f"Просроченные задачи: {overdue}",
                "content": f"В CRM числится {overdue} просроченных задач. Рекомендуем разобрать их сегодня — это повысит доверие клиентов.",
                "priority": 2,
            })
        calls = stats.get("calls_count", 0)
        avg_calls = avg.get("calls_count", 20)
        if calls >= avg_calls * 1.2:
            recs.append({
                "type": "strength",
                "title": "Высокая активность звонков",
                "content": f"За период вы совершили {calls} звонков — на {calls - avg_calls} больше среднего по команде. Отличный результат!",
                "priority": 1,
            })
        return recs

    async def _generate_with_ai(self, manager_name: str, stats: Dict, avg: Dict) -> List[Dict]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""Ты — ИИ-аналитик продаж. Дай 3-5 рекомендаций для менеджера {manager_name}.

Метрики менеджера: {json.dumps(stats, ensure_ascii=False)}
Средние по отделу: {json.dumps(avg, ensure_ascii=False)}

Ответь ТОЛЬКО валидным JSON-массивом:
[{{"type": "strength|growth|alert|forecast", "title": "...", "content": "...", "priority": 1|2|3}}]
Пиши на русском, конкретно, с числами."""
            resp = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=1000,
            )
            text = resp.choices[0].message.content.strip()
            start = text.find("[")
            end = text.rfind("]") + 1
            return json.loads(text[start:end])
        except Exception as e:
            print(f"OpenAI failed, using templates: {e}")
            return self._generate_from_templates(stats, avg)
