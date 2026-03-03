# Моти-ассистент: MCP-сервер и Telegram-бот

Проект из двух частей: **MCP-сервер** с меню десертов моти (SQLite + HTTP API) и **Telegram-бот**, который подключается к серверу и использует OpenAI для выбора и вызова инструментов.

## Структура проекта

```
VPf08-MCP-server/
├── mcp_server/           # MCP-сервер (mochi-mcp)
│   ├── server.py         # FastAPI, запуск: python server.py
│   ├── db.py             # SQLite, инициализация из mochi.json
│   ├── tools.py          # MCP-инструменты и безопасный калькулятор
│   ├── mochi.json        # Данные десертов (при первом запуске копируются в БД)
│   ├── mochi.db          # Создаётся автоматически при первом запуске
│   └── requirements.txt
├── telegram_bot/         # Telegram-бот
│   ├── bot.py            # Обработка сообщений, вызов OpenAI и MCP
│   ├── config.py         # Загрузка TELEGRAM_API_TOKEN, OPENAI_API_KEY из .env
│   ├── mcp_client.py     # HTTP-вызовы к MCP-серверу
│   └── requirements.txt
├── .env.example          # Пример настроек
├── .env                  # Ваши ключи (создать вручную)
└── README.md
```

## 1. Установка зависимостей

### MCP-сервер

```bash
cd mcp_server
pip install -r requirements.txt
```

### Telegram-бот

```bash
cd telegram_bot
pip install -r requirements.txt
```

## 2. Настройка .env

Скопируйте `.env.example` в `.env` (в корень проекта или в папку `telegram_bot`) и заполните:

- **TELEGRAM_API_TOKEN** — токен от [@BotFather](https://t.me/BotFather).
- **OPENAI_API_KEY** — ключ OpenAI для Chat Completions (GPT-4o-mini).
- **MCP_SERVER_URL** — по умолчанию `http://127.0.0.1:8765` (если сервер на той же машине).

Пример:

```
TELEGRAM_API_TOKEN=1234567890:ABCdef...
OPENAI_API_KEY=sk-...
MCP_SERVER_URL=http://127.0.0.1:8765
```

## 3. Запуск

### Шаг 1: Запустить MCP-сервер

Из корня проекта:

```bash
cd mcp_server
python server.py
```

Сервер поднимется на `http://0.0.0.0:8765`. При первом запуске создаётся `mochi.db` и таблица заполняется из `mochi.json` (файл ищется в `mcp_server/mochi.json`, затем в корне проекта: `mochi.json`, `assortment_mochi.json`).

### Шаг 2: Запустить бота

В **другом** терминале:

```bash
cd telegram_bot
python bot.py
```

После этого можно писать боту в Telegram.

## Примеры запросов в боте

- «Покажи все моти»
- «Найди моти клубника»
- «Что есть с кокосом?»
- «Добавь десерт моти Нутелла, описание: шоколад и орехи, 190 руб, категория шоколадный»
- «Посчитай 3*150»

## MCP-инструменты (сервер)

| Инструмент | Описание |
|------------|----------|
| `list_mochi` | Список всех десертов |
| `find_mochi_by_name` | Поиск по названию (параметр `name`) |
| `find_mochi_by_ingredient` | Поиск по ингредиенту в описании (`ingredient`) |
| `add_mochi` | Добавить десерт (`name`, `description`, `category`, `price`) |
| `calculate` | Безопасное вычисление выражения (`expression`) |

- Список инструментов в формате MCP JSON Schema: **GET** `http://127.0.0.1:8765/tools`
- Вызов: **POST** `http://127.0.0.1:8765/call` с телом `{"tool": "имя", "arguments": {...}}`

## Требования

- Python 3.10+
- Доступ в интернет (OpenAI API, Telegram)

Если появятся ошибки при запуске — проверьте наличие `.env`, корректность ключей и что MCP-сервер запущен до старта бота.
