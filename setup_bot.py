"""
Скрипт настройки Telegram-бота Sellex.
Запустить ОДИН РАЗ после деплоя.
Использует только стандартную библиотеку Python — ничего устанавливать не нужно.
"""
import json
import sys
import urllib.request
import urllib.error

BOT_TOKEN = "8940848872:AAECYeZwptVkZ1MelxWg__aspQ7GFYp16yE"

print("=" * 55)
print("  Sellex — настройка Telegram-бота")
print("=" * 55)
print()

APP_URL = input(
    "Введите URL вашего приложения\n"
    "(пример: https://sellex-app.onrender.com): "
).strip().rstrip("/")

if not APP_URL.startswith("https://"):
    print("❌ URL должен начинаться с https://")
    sys.exit(1)

MINI_APP_URL = f"{APP_URL}/tg"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg(method: str, **data) -> dict:
    url = f"{API}/{method}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
    except Exception as e:
        print(f"Ошибка сети: {e}")
        sys.exit(1)


# 1. Получаем информацию о боте
print("\n⏳ Проверяем бот...")
resp = tg("getMe")
if not resp.get("ok"):
    print(f"❌ Ошибка: {resp}")
    sys.exit(1)

bot = resp["result"]
username = bot["username"]
bot_name = bot["first_name"]
print(f"✅ Бот найден: {bot_name} (@{username})")

# 2. Устанавливаем команды
print("\n⏳ Устанавливаем команды...")
r = tg("setMyCommands", commands=[
    {"command": "start",    "description": "Главное меню"},
    {"command": "app",      "description": "Открыть Sellex Mini App"},
    {"command": "overview", "description": "Дашборд отдела продаж"},
    {"command": "managers", "description": "Список менеджеров"},
    {"command": "ranking",  "description": "Рейтинг менеджеров"},
    {"command": "digest",   "description": "Дайджест дня"},
])
print("✅ Команды установлены" if r.get("ok") else f"⚠️  {r}")

# 3. Устанавливаем кнопку меню → Mini App
print(f"\n⏳ Устанавливаем кнопку меню (Mini App)...")
r = tg("setChatMenuButton", menu_button={
    "type": "web_app",
    "text": "📊 Открыть Sellex",
    "web_app": {"url": MINI_APP_URL},
})
print(f"✅ Кнопка меню → {MINI_APP_URL}" if r.get("ok") else f"⚠️  {r}")

# 4. Устанавливаем описание бота
r = tg("setMyDescription",
    description=f"Sellex — аналитика отдела продаж. Откройте Mini App для просмотра дашборда и инсайтов по менеджерам.")
print("✅ Описание бота обновлено" if r.get("ok") else f"⚠️  {r}")

# 5. Итог
print()
print("=" * 55)
print("  ✅ Настройка завершена!")
print("=" * 55)
print()
print("Добавьте в Render → sellex-app → Environment:")
print()
print(f"  TELEGRAM_BOT_USERNAME = {username}")
print(f"  APP_URL               = {APP_URL}")
print(f"  MINI_APP_URL          = {MINI_APP_URL}")
print()
print(f"Ссылка на бота:     https://t.me/{username}")
print(f"Ссылка на Mini App: {MINI_APP_URL}")
