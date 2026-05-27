"""
Multi-agent pipeline for call/chat quality analysis.

Agent 1 — Transcription: downloads audio and sends to OpenAI Whisper.
            Falls back to existing text if no URL or no API key.
Agent 2 — Analysis: evaluates the transcript against 6 sales competencies.
            Falls back to rule-based scoring when no API key.
Agent 3 — Recommendations: uses analyze_manager() from analysis_agent.py
            (called by sync_service.py, not directly here).
"""
import io
import json
import logging
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.call_analysis import CallAnalysis
from app.models.manager import Manager
from app.connectors.base import BaseCRMConnector

logger = logging.getLogger(__name__)


# ── Agent 1: Transcription ────────────────────────────────────────────────────

async def _transcribe_audio(recording_url: str) -> Optional[str]:
    """Download audio from URL and transcribe with Whisper.
    Returns transcript text or None on failure."""
    if not settings.OPENAI_API_KEY:
        logger.warning("No OPENAI_API_KEY — skipping Whisper transcription for %s", recording_url)
        return None

    try:
        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(recording_url, follow_redirects=True)
            resp.raise_for_status()
            audio_bytes = resp.content
    except Exception as e:
        logger.warning("Audio download failed for %s: %s", recording_url, e)
        return None

    try:
        from openai import AsyncOpenAI  # lazy import
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            default_headers={"HTTP-Referer": "https://sellex.app", "X-Title": "Sellex"},
        )
        # Whisper requires a file-like object with a name
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.mp3"

        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ru",
        )
        return transcript.text
    except Exception as e:
        logger.warning("Whisper transcription failed: %s", e)
        return None


# ── Agent 2: Analysis (AI path) ───────────────────────────────────────────────

ANALYSIS_PROMPT_TEMPLATE = """Ты — ИИ-тренер по продажам. Проанализируй разговор менеджера с клиентом.

ТЕКСТ РАЗГОВОРА:
{transcript}

Оцени работу менеджера по 6 компетенциям (каждая от 0 до 10):

1. ПРИВЕТСТВИЕ И КОНТАКТ — представился ли, установил ли контакт, назвал ли своё имя и компанию
2. ВЫЯВЛЕНИЕ ПОТРЕБНОСТЕЙ — использовал ли открытые вопросы, технику SPIN, активное слушание
3. ПРЕЗЕНТАЦИЯ ЦЕННОСТИ — представил ли выгоды (FAB), говорил ли на языке клиента
4. РАБОТА С ВОЗРАЖЕНИЯМИ — отработал ли возражения, использовал ли технику "да, и...", не спорил ли
5. ДОЖИМ/ЗАКРЫТИЕ — использовал ли техники закрытия, создавал ли срочность, предлагал ли следующий шаг
6. СЛЕДУЮЩИЙ ШАГ — договорился ли о конкретном следующем действии с датой и временем

Ответь ТОЛЬКО валидным JSON (без markdown, без пояснений вне JSON):
{{
  "score_greeting": <0-10>,
  "score_needs": <0-10>,
  "score_presentation": <0-10>,
  "score_objections": <0-10>,
  "score_closing": <0-10>,
  "score_next_step": <0-10>,
  "strengths": ["<конкретная сильная сторона 1>", "<сильная сторона 2>"],
  "improvements": ["<конкретная зона роста 1>", "<зона роста 2>"],
  "summary": "<2-3 предложения: общая оценка разговора>"
}}

Пиши на русском. Будь конкретным, опирайся на факты из текста."""


async def _ai_analyze_transcript(transcript: str) -> Optional[Dict[str, Any]]:
    """Analyze transcript with GPT and return structured scores."""
    if not settings.OPENAI_API_KEY:
        return None

    try:
        from openai import AsyncOpenAI  # lazy import
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            default_headers={"HTTP-Referer": "https://sellex.app", "X-Title": "Sellex"},
        )
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(transcript=transcript[:6000])
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        text = resp.choices[0].message.content.strip()
        # Extract JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in AI response")
        return json.loads(text[start:end])
    except Exception as e:
        logger.warning("AI transcript analysis failed: %s", e)
        return None


# ── Agent 2: Analysis (rule-based fallback) ───────────────────────────────────

def _rule_based_score(transcript: str) -> Dict[str, Any]:
    """Score transcript using keyword-based heuristics (no AI required)."""
    text = transcript.lower()

    # 1. Greeting & contact
    greeting_keywords = ["добрый", "привет", "здравствуй", "меня зовут", "это ", "компания"]
    greeting_hits = sum(1 for kw in greeting_keywords if kw in text)
    score_greeting = min(10.0, greeting_hits * 2.5)

    # 2. Needs discovery — count question marks and SPIN keywords
    question_count = text.count("?")
    spin_keywords = ["расскажите", "что для вас", "как вы", "какие у вас", "что важно", "почему"]
    spin_hits = sum(1 for kw in spin_keywords if kw in text)
    score_needs = min(10.0, question_count * 1.2 + spin_hits * 1.5)

    # 3. Value presentation
    value_keywords = ["выгода", "преимущество", "позволит", "сэкономит", "увеличит",
                      "решит", "помогает", "ценность", "результат"]
    value_hits = sum(1 for kw in value_keywords if kw in text)
    score_presentation = min(10.0, value_hits * 1.8)

    # 4. Objection handling
    obj_keywords = ["понимаю", "именно поэтому", "давайте рассмотрим", "хорошо, что",
                    "согласен", "при этом", "зато"]
    obj_hits = sum(1 for kw in obj_keywords if kw in text)
    score_objections = min(10.0, obj_hits * 2.5)

    # 5. Closing
    close_keywords = ["оформим", "подпишем", "начнём", "готовы", "оплатить",
                      "заключим", "договор", "принять решение"]
    close_hits = sum(1 for kw in close_keywords if kw in text)
    score_closing = min(10.0, close_hits * 2.0)

    # 6. Next step
    next_step_keywords = ["созвонимся", "встретимся", "пришлю", "договорились",
                          "следующий шаг", "во вторник", "в среду", "в четверг",
                          "в пятницу", "завтра", "на следующей неделе", "назначим"]
    next_hits = sum(1 for kw in next_step_keywords if kw in text)
    score_next_step = min(10.0, next_hits * 3.0)

    scores = [score_greeting, score_needs, score_presentation,
              score_objections, score_closing, score_next_step]

    strengths = []
    improvements = []

    if score_greeting >= 6:
        strengths.append("Хорошее приветствие и установление контакта")
    else:
        improvements.append("Улучшить приветствие: назвать имя, компанию, цель звонка")

    if score_needs >= 6:
        strengths.append("Активное выявление потребностей с вопросами")
    else:
        improvements.append("Задавать больше открытых вопросов, выявлять потребности")

    if score_next_step >= 6:
        strengths.append("Чёткий следующий шаг с конкретными договорённостями")
    else:
        improvements.append("Договариваться о конкретном следующем шаге с датой и временем")

    if score_objections < 4:
        improvements.append("Отрабатывать возражения по технике 'да, и...'")

    if score_closing < 4:
        improvements.append("Использовать техники закрытия сделки")

    summary = (
        f"Анализ по ключевым словам (AI недоступен). "
        f"Вопросов задано: {question_count}. "
        f"Приветствие: {'есть' if score_greeting > 3 else 'слабое'}. "
        f"Следующий шаг: {'зафиксирован' if score_next_step > 3 else 'не назначен'}."
    )

    return {
        "score_greeting": round(score_greeting, 1),
        "score_needs": round(score_needs, 1),
        "score_presentation": round(score_presentation, 1),
        "score_objections": round(score_objections, 1),
        "score_closing": round(score_closing, 1),
        "score_next_step": round(score_next_step, 1),
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "summary": summary,
    }


# ── Scoring helpers ────────────────────────────────────────────────────────────

def _compute_overall_and_verdict(result: Dict[str, Any]) -> Dict[str, Any]:
    """Add overall_score and verdict to an analysis result dict."""
    scores = [
        result.get("score_greeting", 0),
        result.get("score_needs", 0),
        result.get("score_presentation", 0),
        result.get("score_objections", 0),
        result.get("score_closing", 0),
        result.get("score_next_step", 0),
    ]
    overall = round(sum(scores) / len(scores), 1)
    if overall >= 7.0:
        verdict = "strong"
    elif overall >= 4.5:
        verdict = "average"
    else:
        verdict = "weak"

    result["overall_score"] = overall
    result["verdict"] = verdict
    return result


def _clamp_score(val) -> float:
    """Clamp a score to [0, 10]."""
    try:
        return max(0.0, min(10.0, float(val)))
    except (TypeError, ValueError):
        return 0.0


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def _analyze_item(
    item: Dict[str, Any],
    manager: Manager,
    tenant_id,
) -> Optional[CallAnalysis]:
    """
    Process a single call or chat item through the 3-agent pipeline.
    Returns a CallAnalysis (unsaved) or None if processing should be skipped.
    """
    crm_id = str(item.get("id") or "")
    item_type = item.get("type", "call")

    # Agent 1: Transcription
    transcript = item.get("text") or None
    recording_url = item.get("recording_url") or None

    if recording_url and not transcript:
        # Try to download and transcribe
        transcript = await _transcribe_audio(recording_url)
        if transcript is None:
            # Download/transcription failed — skip this item silently
            logger.warning(
                "Skipping item %s for manager %s — audio unavailable and no text",
                crm_id, manager.full_name,
            )
            return None

    if not transcript or not transcript.strip():
        logger.warning(
            "Skipping item %s for manager %s — no transcript text available",
            crm_id, manager.full_name,
        )
        return None

    # Agent 2: Analysis
    analysis_result = None
    if settings.OPENAI_API_KEY:
        analysis_result = await _ai_analyze_transcript(transcript)

    if analysis_result is None:
        # Fallback to rule-based scoring
        analysis_result = _rule_based_score(transcript)

    analysis_result = _compute_overall_and_verdict(analysis_result)

    # Parse item_date
    item_date = None
    raw_date = item.get("created_at")
    if raw_date:
        try:
            item_date = datetime.fromisoformat(str(raw_date))
        except Exception:
            item_date = None

    # Build CallAnalysis object
    ca = CallAnalysis(
        tenant_id=tenant_id,
        manager_id=manager.id,
        crm_item_id=crm_id if crm_id else None,
        item_type=item_type,
        item_date=item_date,
        duration_seconds=int(item.get("duration_seconds") or 0),
        transcript=transcript,
        score_greeting=_clamp_score(analysis_result.get("score_greeting")),
        score_needs=_clamp_score(analysis_result.get("score_needs")),
        score_presentation=_clamp_score(analysis_result.get("score_presentation")),
        score_objections=_clamp_score(analysis_result.get("score_objections")),
        score_closing=_clamp_score(analysis_result.get("score_closing")),
        score_next_step=_clamp_score(analysis_result.get("score_next_step")),
        overall_score=_clamp_score(analysis_result.get("overall_score")),
        strengths=json.dumps(analysis_result.get("strengths") or [], ensure_ascii=False),
        improvements=json.dumps(analysis_result.get("improvements") or [], ensure_ascii=False),
        summary=str(analysis_result.get("summary") or ""),
        verdict=str(analysis_result.get("verdict") or "average"),
    )
    return ca


async def process_manager_communications(
    db: AsyncSession,
    connector: BaseCRMConnector,
    manager: Manager,
    tenant_id,
    since: datetime,
) -> List[CallAnalysis]:
    """
    Run the communication analysis pipeline for a single manager.

    Fetches up to 15 call recordings and 10 chat threads, skips already-analyzed
    items (checked via crm_item_id), transcribes audio if needed, and scores
    each conversation against the 6-competency sales framework.

    Returns a list of unsaved CallAnalysis objects.
    The caller is responsible for db.add() / flush / commit.
    """
    results: List[CallAnalysis] = []

    # Gather already-analyzed crm_item_ids for this manager
    try:
        existing_res = await db.execute(
            select(CallAnalysis.crm_item_id).where(
                CallAnalysis.manager_id == manager.id,
                CallAnalysis.crm_item_id.isnot(None),
            )
        )
        already_analyzed = {row[0] for row in existing_res.fetchall()}
    except Exception as e:
        logger.warning("Could not query existing analyses for %s: %s", manager.full_name, e)
        already_analyzed = set()

    # ── Fetch call recordings ─────────────────────────────────────────────────
    call_items: List[Dict[str, Any]] = []
    try:
        call_items = await connector.get_call_recordings(manager.crm_id, since, limit=15)
    except Exception as e:
        logger.warning("get_call_recordings failed for %s: %s", manager.full_name, e)

    for item in call_items:
        crm_id = str(item.get("id") or "")
        if crm_id and crm_id in already_analyzed:
            continue
        try:
            ca = await _analyze_item(item, manager, tenant_id)
            if ca is not None:
                results.append(ca)
        except Exception as e:
            logger.warning(
                "Analysis failed for call item %s (manager %s): %s",
                crm_id, manager.full_name, e,
            )

    # ── Fetch chat threads ────────────────────────────────────────────────────
    chat_items: List[Dict[str, Any]] = []
    try:
        chat_items = await connector.get_chat_messages(manager.crm_id, since, limit=10)
    except Exception as e:
        logger.warning("get_chat_messages failed for %s: %s", manager.full_name, e)

    for item in chat_items:
        crm_id = str(item.get("id") or "")
        if crm_id and crm_id in already_analyzed:
            continue
        try:
            ca = await _analyze_item(item, manager, tenant_id)
            if ca is not None:
                results.append(ca)
        except Exception as e:
            logger.warning(
                "Analysis failed for chat item %s (manager %s): %s",
                crm_id, manager.full_name, e,
            )

    logger.info(
        "process_manager_communications: manager=%s analyzed=%d (calls=%d chats=%d)",
        manager.full_name, len(results), len(call_items), len(chat_items),
    )
    return results
