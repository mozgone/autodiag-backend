"""
Sellex Telegram Bot
Дублирует аналитику и открывает Mini App для просмотра дашборда.
"""
import os
import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_URL    = os.environ.get("SELLEX_API_URL", "http://localhost:8000/api/v1")
API_TOKEN  = os.environ.get("SELLEX_API_TOKEN", "")   # JWT-токен руководителя
MINI_APP_URL = os.environ.get("MINI_APP_URL", "")     # https://yourapp.up.railway.app/tg

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


async def api_get(path: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{API_URL}{path}", headers=HEADERS)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"API error {path}: {e}")
        return None


def mini_app_keyboard(text: str = "📊 Открыть Sellex") -> InlineKeyboardMarkup | None:
    """Кнопка для открытия Mini App (требует HTTPS-URL)."""
    if not MINI_APP_URL:
        return None
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text, web_app=WebAppInfo(url=MINI_APP_URL))
    ]])


# ─── Команды ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = mini_app_keyboard()
    text = (
        "👋 *Sellex — аналитика отдела продаж*\n\n"
        "Доступные команды:\n"
        "/overview — общий дашборд\n"
        "/managers — список менеджеров\n"
        "/ranking — рейтинг за период\n"
        "/digest — дайджест дня\n\n"
        "Или откройте полный дашборд кнопкой ниже 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=kb or InlineKeyboardMarkup([]))


async def open_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /app — отправляет кнопку открытия Mini App."""
    kb = mini_app_keyboard("🚀 Открыть Sellex")
    if kb:
        await update.message.reply_text("Нажмите, чтобы открыть:", reply_markup=kb)
    else:
        await update.message.reply_text("Mini App не настроен. Обратитесь к администратору.")


async def overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    data = await api_get("/analytics/overview")
    if not data:
        await msg.reply_text("❌ Не удалось получить данные.")
        return

    def fmt(n):
        return f"{n/1_000_000:.1f}М ₽" if n >= 1_000_000 else f"{n/1_000:.0f}К ₽"

    plan = data['plan_completion_avg']
    plan_bar = "🟢" if plan >= 100 else "🟡" if plan >= 70 else "🔴"
    text = (
        f"📊 *Дашборд отдела продаж*\n\n"
        f"👥 Менеджеров: *{data['total_managers']}*\n"
        f"💰 Выручка за месяц: *{fmt(data['total_revenue_month'])}*\n"
        f"📈 Конверсия: *{data['avg_conversion_rate']:.1f}%*\n"
        f"{plan_bar} Выполнение плана: *{plan:.0f}%*\n"
        f"🏆 Топ-менеджер: *{data.get('top_performer') or '—'}*\n"
        f"⚠️ Сделок под риском: *{data['at_risk_deals']}*"
    )
    await msg.reply_text(text, parse_mode="Markdown", reply_markup=mini_app_keyboard())


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

    await msg.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=mini_app_keyboard())


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
    ov = await api_get("/analytics/overview")
    rank = await api_get("/analytics/ranking")
    mgrs = await api_get("/managers/")
    if not all([ov, rank, mgrs]):
        await msg.reply_text("❌ Не удалось собрать дайджест.")
        return

    at_risk = [m["full_name"] for m in mgrs if (m.get("stats") or {}).get("plan_completion", 100) < 70]

    def fmt(n):
        return f"{n/1_000_000:.1f}М ₽" if n >= 1_000_000 else f"{n/1_000:.0f}К ₽"

    plan = ov['plan_completion_avg']
    text = (
        f"📋 *Дайджест — Sellex*\n\n"
        f"*Отдел в целом:*\n"
        f"• Выручка: {fmt(ov['total_revenue_month'])}\n"
        f"• План: {plan:.0f}% {'✅' if plan >= 100 else '⚠️' if plan >= 70 else '🔴'}\n"
        f"• Конверсия: {ov['avg_conversion_rate']:.1f}%\n\n"
        f"*Топ-3:*\n"
    )
    for item in (rank or [])[:3]:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        text += f"{medals.get(item['rank'], '')} {item['full_name']} — {item['plan_completion']:.0f}%\n"

    if at_risk:
        text += f"\n⚠️ *Требуют внимания:*\n" + "\n".join(f"• {n}" for n in at_risk[:3])

    text += "\n\n_Данные носят рекомендательный характер._"
    await msg.reply_text(text, parse_mode="Markdown", reply_markup=mini_app_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    handlers = {"overview": overview, "managers": managers_list, "ranking": ranking}
    if query.data in handlers:
        await handlers[query.data](update, context)


def main():
    if not BOT_TOKEN:
        print("⚠️  TELEGRAM_BOT_TOKEN не задан.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("app",      open_app))
    app.add_handler(CommandHandler("overview", overview))
    app.add_handler(CommandHandler("managers", managers_list))
    app.add_handler(CommandHandler("ranking",  ranking))
    app.add_handler(CommandHandler("digest",   digest))
    app.add_handler(CallbackQueryHandler(button_handler))

    print(f"🤖 Sellex Bot запущен. Mini App: {MINI_APP_URL or 'не настроен'}")
    app.run_polling()


if __name__ == "__main__":
    main()
