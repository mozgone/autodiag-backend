# Sellex — Система анализа отдела продаж

Мультитенантное веб-приложение с группой ИИ-агентов для анализа работы менеджеров по продажам.

---

## Что это такое?

Sellex подключается к вашей CRM, собирает данные о действиях менеджеров и даёт руководителю персонализированные инсайты:
- 📊 Дашборд с KPI отдела (выручка, конверсия, план)
- 👥 Карточки менеджеров с радар-диаграммой компетенций
- 🤖 ИИ-рекомендации (сильные стороны, зоны роста, алерты)
- 📱 Telegram-бот с ежедневным дайджестом
- 🔌 Подключаемые коннекторы к CRM (встроена демо-версия и amoCRM)

---

## Как запустить (самый простой способ — через Docker)

### Шаг 1: Установите необходимые программы

**Docker Desktop** — программа для запуска контейнеров:
- Windows/Mac: https://www.docker.com/products/docker-desktop/
- После установки убедитесь, что Docker запущен (значок в трее)

**Git** (скорее всего уже установлен):
- Windows: https://git-scm.com/download/win
- Mac: `xcode-select --install`

### Шаг 2: Скачайте проект

Откройте терминал (на Mac — Terminal, на Windows — PowerShell) и выполните:

```bash
git clone https://github.com/mozgone/autodiag-backend.git sellex
cd sellex
git checkout claude/build-sellex-app-U21Wy
```

### Шаг 3: Настройте конфигурацию

```bash
# Скопируйте файл настроек
cp .env.example .env
```

Откройте файл `.env` в любом текстовом редакторе. По умолчанию всё настроено для запуска без реальной CRM и без OpenAI — система будет использовать демо-данные.

### Шаг 4: Запустите приложение

```bash
docker compose up --build
```

Первый запуск займёт 3-5 минут (скачиваются зависимости). Дождитесь строки:
```
backend-1  | INFO:     Application startup complete.
```

### Шаг 5: Загрузите демо-данные

В новом окне терминала:

```bash
docker compose exec backend python -m app.utils.demo_data
```

Вы увидите:
```
✅ Демо-данные успешно загружены!
   Логин: admin@sellex.demo
   Пароль: demo1234
```

### Шаг 6: Откройте приложение

- **Веб-интерфейс**: http://localhost:3000
- **API-документация**: http://localhost:8000/docs
- **Логин**: admin@sellex.demo
- **Пароль**: demo1234

---

## Запуск без Docker (для разработчиков)

Если Docker не подходит, можно запустить вручную.

### Требования
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Бэкенд

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Установить зависимости
pip install -r requirements.txt

# Создать таблицы в базе данных
# (предварительно создайте БД: createdb sellex)
python -c "
import asyncio
from app.core.database import engine, Base
import app.models
asyncio.run(engine.begin().__aenter__().__class__.run_sync(Base.metadata.create_all))
"

# Или через alembic:
# alembic upgrade head

# Загрузить демо-данные
python -m app.utils.demo_data

# Запустить сервер
uvicorn app.main:app --reload --port 8000
```

### Фронтенд

```bash
cd frontend

# Установить зависимости
npm install --legacy-peer-deps

# Запустить в режиме разработки
npm start
```

Откройте http://localhost:3000

### Telegram-бот (необязательно)

```bash
cd telegram_bot
pip install -r requirements.txt

# Создайте .env с токеном бота (см. инструкцию ниже)
python bot.py
```

---

## Как подключить OpenAI (для ИИ-рекомендаций)

По умолчанию система генерирует рекомендации по шаблонам — бесплатно.

Для настоящих ИИ-рекомендаций:
1. Зарегистрируйтесь на https://platform.openai.com
2. Создайте API-ключ в разделе API Keys
3. Добавьте в `.env`:
   ```
   OPENAI_API_KEY=sk-...ваш-ключ...
   ```
4. Перезапустите бэкенд

Расходы: GPT-4o-mini стоит ~$0.15 за 1 млн токенов — практически бесплатно для небольшого отдела.

---

## Как подключить Telegram-бот

1. Напишите @BotFather в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте токен вида `1234567890:AAH...`
4. Добавьте в `.env`:
   ```
   TELEGRAM_BOT_TOKEN=1234567890:AAH...
   ```
5. Запустите с профилем telegram:
   ```bash
   docker compose --profile telegram up
   ```

---

## Как подключить реальную amoCRM

1. В веб-интерфейсе Sellex перейдите в **Настройки**
2. Выберите тип CRM: **amoCRM**
3. Введите поддомен вашей amoCRM (например, `mycompany` для mycompany.amocrm.ru)
4. Введите Access Token (получить в настройках amoCRM → Интеграции)
5. Подтвердите согласие сотрудников и нажмите **Подключить CRM**

---

## Структура проекта

```
sellex/
├── backend/              # FastAPI (Python)
│   ├── app/
│   │   ├── core/         # Настройки, БД, безопасность
│   │   ├── models/       # Модели данных (SQLAlchemy)
│   │   ├── schemas/      # Схемы запросов/ответов (Pydantic)
│   │   ├── api/v1/       # API-эндпоинты
│   │   ├── agents/       # ИИ-агенты
│   │   ├── connectors/   # Коннекторы к CRM
│   │   └── utils/        # Утилиты (загрузка демо-данных)
│   └── requirements.txt
├── frontend/             # React (TypeScript)
│   └── src/
│       ├── pages/        # Страницы: Login, Dashboard, Managers...
│       ├── components/   # Компоненты: карточки, графики
│       ├── api/          # Клиент для запросов к API
│       └── store/        # Глобальное состояние (Zustand)
├── telegram_bot/         # Telegram-бот
├── docker-compose.yml    # Конфигурация для Docker
└── .env.example          # Шаблон настроек
```

---

## Роли пользователей

| Роль | Доступ |
|------|--------|
| `owner` | Всё, включая биллинг |
| `admin` | Управление аккаунтом |
| `head_of_sales` | Полный доступ к аналитике |
| `team_lead` | Аналитика своей команды |
| `manager` | Только свои рекомендации |

---

## Важные дисклеймеры

- Все выводы системы носят **рекомендательный характер** и не являются окончательными суждениями о работе сотрудников.
- Перед подключением реальных данных сотрудников необходимо **получить их согласие** на обработку персональных данных.
- Система является **обработчиком данных** — ответственность оператора несёт компания-клиент.

---

## Частые проблемы

**Порт 5432 уже занят** — остановите локальный PostgreSQL или измените порт в `docker-compose.yml`.

**Ошибка "Cannot connect to database"** — подождите 10-15 секунд после старта, пока PostgreSQL инициализируется.

**Фронтенд показывает пустые данные** — убедитесь, что загружены демо-данные (шаг 5).

**npm install завершается с ошибкой** — используйте флаг `--legacy-peer-deps`.
