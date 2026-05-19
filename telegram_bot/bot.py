"""
Sellex Telegram Bot — дублирует ключевые инсайты и дайджесты.
Запуск: python bot.py
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_URL = os.environ.get("SELLEX_API_URL", "http://localhost:8000/api/v1")
API_TOKEN = os.environ.get("SELLEX_API_TOKEN", "")  # Токен руководителя

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


async def api_get(path: str) -> dict | list | None:
    """Выполнить GET-запрос к Sellex API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{API_URL}{path}", headers=HEADERS)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"API error {path}: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Дашборд", callback_data="overview")],
        [InlineKeyboardButton("👥 Менеджеры", callback_data="managers")],
        [InlineKeyboardButton("🏆 Рейтинг", callback_data="ranking")],
    ]
    await update.message.reply_text(
        "👋 *Sellex — аналитика отдела продаж*\n\n"
        "Выберите раздел или используйте команды:\n"
        "/overview — общий дашборд\n"
        "/managers — список менеджеров\n"
        "/ranking — рейтинг за период\n"
        "/digest — дайджест дня",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    data = await api_get("/analytics/overview")
    if not data:
        await msg.reply_text("❌ Не удалось получить данные. Проверьте подключение к API.")
        return

    def fmt(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}М ₽"
        if n >= 1_000:
            return f"{n/1_000:.0f}К ₽"
        return f"{n} ₽"

    text = (
        f"📊 *Дашборд отдела продаж*\n\n"
        f"👥 Менеджеров: *{data['total_managers']}*\n"
        f"💰 Выручка за месяц: *{fmt(data['total_revenue_month'])}*\n"
        f"📈 Конверсия: *{data['avg_conversion_rate']:.1f}%*\n"
        f"🎯 Выполнение плана: *{data['plan_completion_avg']:.0f}%*\n"
        f"🏆 Топ-менеджер: *{data.get('top_performer') or '—'}*\n"
        f"⚠️ Сделок под риском: *{data['at_risk_deals']}*"
    )
    await msg.reply_text(text, parse_mode="Markdown")


async def managers_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    data = await api_get("/managers/")
    if not data:
        await msg.reply_text("❌ Не удалось получить список менеджеров.")
        return

    lines = ["👥 *Менеджеры*\n"]
    for m in data:
        stats = m.get("stats") or {}
        plan = stats.get("plan_completion", 0)
        emoji = "🟢" if plan >= 100 else "🟡" if plan >= 70 else "🔴"
        lines.append(f"{emoji} *{m['full_name']}* — {plan:.0f}% плана")

    await msg.reply_text("\n".join(lines), parse_mode="Markdown")


async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    data = await api_get("/analytics/ranking")
    if not data:
        await msg.reply_text("❌ Не удалось получить рейтинг.")
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = ["🏆 *Рейтинг менеджеров*\n"]
    for item in data:
        medal = medals.get(item["rank"], f"#{item['rank']}")
        rev = item["revenue"]
        rev_str = f"{rev/1_000_000:.1f}М ₽" if rev >= 1_000_000 else f"{rev/1_000:.0f}К ₽"
        lines.append(f"{medal} {item['full_name']} — {rev_str} ({item['plan_completion']:.0f}%)")

    await msg.reply_text("\n".join(lines), parse_mode="Markdown")


async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    overview_data = await api_get("/analytics/overview")
    ranking_data = await api_get("/analytics/ranking")
    managers_data = await api_get("/managers/")

    if not all([overview_data, ranking_data, managers_data]):
        await msg.reply_text("❌ Не удалось собрать дайджест.")
        return

    # Найти менеджеров с риском
    at_risk = [m["full_name"] for m in managers_data if (m.get("stats") or {}).get("plan_completion", 100) < 70]

    def fmt(n):
        return f"{n/1_000_000:.1f}М ₽" if n >= 1_000_000 else f"{n/1_000:.0f}К ₽"

    text = (
        f"📋 *Дайджест дня — Sellex*\n\n"
        f"*Отдел в целом:*\n"
        f"• Выручка: {fmt(overview_data['total_revenue_month'])}\n"
        f"• Средний план: {overview_data['plan_completion_avg']:.0f}%\n"
        f"• Конверсия: {overview_data['avg_conversion_rate']:.1f}%\n\n"
        f"*Топ-3 менеджера:*\n"
    )
    for item in (ranking_data or [])[:3]:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        text += f"{medals.get(item['rank'], '')} {item['full_name']} — {item['plan_completion']:.0f}%\n"

    if at_risk:
        text += f"\n⚠️ *Требуют внимания:*\n"
        for name in at_risk[:3]:
            text += f"• {name}\n"

    text += "\n_Данные носят рекомендательный характер._"
    await msg.reply_text(text, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "overview":
        await overview(update, context)
    elif query.data == "managers":
        await managers_list(update, context)
    elif query.data == "ranking":
        await ranking(update, context)


def main():
    if not BOT_TOKEN:
        print("⚠️  TELEGRAM_BOT_TOKEN не задан. Бот не запустится.")
        print("   Установите переменную в .env и перезапустите.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("overview", overview))
    app.add_handler(CommandHandler("managers", managers_list))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(CommandHandler("digest", digest))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Sellex Telegram Bot запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
