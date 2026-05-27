"""AI агент анализа качества коммуникаций и заполнения CRM."""
import json
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


async def analyze_manager(
    manager_name: str,
    stats: Dict[str, Any],
    notes: List[str],          # текст последних заметок/звонков
    field_analysis: Dict[str, float],  # {"название поля": процент заполнения}
) -> List[Dict[str, Any]]:
    """
    Возвращает список рекомендаций для менеджера.
    notes — список строк: текст звонков, заметок из CRM.
    field_analysis — словарь: имя поля → % заполнения (0-100).
    """
    if settings.OPENAI_API_KEY:
        try:
            return await _ai_analyze(manager_name, stats, notes, field_analysis)
        except Exception as e:
            logger.warning("AI analysis failed, using templates: %s", e)
    return _template_analyze(manager_name, stats, field_analysis)


async def _ai_analyze(manager_name, stats, notes, field_analysis):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        default_headers={"HTTP-Referer": "https://sellex.app", "X-Title": "Sellex"},
    )

    notes_text = "\n".join(f"- {n}" for n in notes[:15]) if notes else "Нет данных"
    fields_text = "\n".join(
        f"- {name}: {pct:.0f}% заполнено" for name, pct in field_analysis.items()
    ) if field_analysis else "Нет данных о полях"

    prompt = f"""Ты — ИИ-аналитик отдела продаж. Проанализируй менеджера "{manager_name}".

МЕТРИКИ (текущий период):
- Сделок создано: {stats.get('deals_created', 0)}
- Сделок выиграно: {stats.get('deals_won', 0)}
- Выручка: {stats.get('revenue', 0):,.0f} ₽
- Конверсия: {stats.get('conversion_rate', 0):.1f}%
- Выполнение плана: {stats.get('plan_completion_forecast', 0):.0f}%
- Звонков: {stats.get('calls_count', 0)}

ЗАПОЛНЕНИЕ ПОЛЕЙ В CRM:
{fields_text}

ПОСЛЕДНИЕ ЗАМЕТКИ И ЗВОНКИ:
{notes_text}

Дай 3-5 конкретных рекомендаций. Анализируй:
1. Качество коммуникации по заметкам (тон, follow-up, скорость реакции)
2. Проблемы с заполнением CRM (незаполненные поля → потеря данных)
3. Риски и точки роста по метрикам

Ответь ТОЛЬКО валидным JSON массивом (без markdown):
[{{"type":"strength|growth|alert|forecast","title":"...","content":"...","priority":1|2|3}}]
Пиши на русском, конкретно, с числами из данных выше."""

    resp = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1200,
    )
    text = resp.choices[0].message.content.strip()
    start, end = text.find("["), text.rfind("]") + 1
    return json.loads(text[start:end])


def _template_analyze(manager_name, stats, field_analysis):
    recs = []
    plan = stats.get("plan_completion_forecast", 0)
    conv = stats.get("conversion_rate", 0)
    crm = stats.get("crm_fill_rate", 100)

    if plan >= 100:
        recs.append({"type": "strength", "title": "Перевыполнение плана",
            "content": f"Выполнение плана: {plan:.0f}%. Отличный результат!", "priority": 1})
    elif plan < 60:
        recs.append({"type": "alert", "title": "Риск невыполнения плана",
            "content": f"Прогноз: {plan:.0f}%. Нужно срочно увеличить количество активностей.", "priority": 3})
    else:
        recs.append({"type": "growth", "title": "Потенциал роста",
            "content": f"Конверсия {conv:.1f}%. Усильте follow-up после отправки КП.", "priority": 2})

    # Field analysis recommendations
    empty_fields = [name for name, pct in field_analysis.items() if pct < 50]
    if empty_fields:
        recs.append({"type": "alert", "title": "Незаполненные поля в CRM",
            "content": f"Поля без данных: {', '.join(empty_fields[:3])}. Заполнение важно для точного прогноза.",
            "priority": 2})
    elif crm < 60:
        recs.append({"type": "growth", "title": "Качество заполнения CRM",
            "content": f"Только {crm:.0f}% сделок заполнены полностью. Уделяйте 10-15 мин/день.", "priority": 2})
    return recs
