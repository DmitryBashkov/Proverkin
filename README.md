# Proverkin :: микросервисная версия

Перепись исходного `Proverkin` (одиночный aiogram-бот + SQLite) на четыре изолированных сервиса плюс Postgres. Стиль и структура каждого сервиса намеренно близки к оригиналу: `config_data/`, `handlers/`, `service/`, `database/`, `utils/`, `messages.py`, статические методы коннектора, многострочные SQL.

## Архитектура

```
                   ┌──────────────┐
                   │   Telegram   │
                   └──────┬───────┘
                  webhook │
                          ▼
   ┌──────────────────────────────────────┐
   │           bot_service (aiogram)       │
   │  HTTP API: send/edit/delete/answer    │
   │  Telegram → quiz_service по HTTP      │
   └──────────────────────────┬───────────┘
                              │ HTTP
                              ▼
   ┌──────────────────────────────────────┐
   │         quiz_service (aiohttp)        │
   │  бизнес-логика, APScheduler, FSM,     │
   │  логирование результатов              │
   └─────┬────────────────────────────┬───┘
         │ Postgres                   │ HTTP (admin)
         ▼                            ▼
   ┌──────────────┐         ┌────────────────────┐
   │   postgres   │ ◄───────┤ generator_service  │
   │              │         │  OpenRouter, очередь│
   └──────┬───────┘         └────────────────────┘
          │
          │ Postgres
          ▼
   ┌──────────────────────────────────────┐
   │         web_gui (Flask + Jinja)       │
   │  CRUD users/sets/привязки/очередь     │
   └──────────────────────────────────────┘
```

### Сервисы

| Сервис | Стек | Порт (внутр.) | Роль |
|---|---|---|---|
| `bot_service` | aiogram 3 + aiohttp | 8000 | Telegram webhook + HTTP API (send/edit/delete/answer). Никакой бизнес-логики. |
| `quiz_service` | aiohttp + APScheduler + psycopg | 8001 | Планирование квизов, прохождение, логирование. Берёт вопросы из БД и из очереди генератора. |
| `generator_service` | aiohttp + psycopg + OpenRouter | 8002 | Фоном поддерживает очередь сгенерированных вопросов для каждого `set`. |
| `web_gui` | Flask + Jinja, чистый HTML/CSS | 8080 | Админка: пользователи, наборы, привязки, очередь, логи. |
| `postgres` | postgres:16-alpine | 5432 | Единое хранилище. |

Сервисы общаются только по HTTP по DNS-именам compose. Постоянное состояние — только в Postgres.

### Очередь генератора

Очередь — таблица `generation_queue` в Postgres. Когда у `set'а` заполнены `generator_prompt` и `target_pool_size > 0`, generator_service фоном пополняет очередь до целевого размера. В web-gui админ может одобрить (item → `questions` + `answers`) или отклонить элемент.

## Запуск

```bash
cp .env.example .env
# заполни TG_BOT_TOKEN, TG_WEBHOOK_URL, OPENROUTER_API_KEY и пароли

docker compose up -d --build
```

Проверка:
- web-gui: http://localhost:8080/ (basic auth — `WEB_ADMIN_USER` / `WEB_ADMIN_PASSWORD`)
- bot_service health: http://localhost:8000/healthz
- quiz_service health: http://localhost:8001/healthz

### Telegram webhook

Telegram должен достучаться до `bot_service:8000/telegram/webhook` по HTTPS. Варианты:
- nginx с TLS перед bot_service (рекомендуется в проде);
- Cloudflare Tunnel;
- ngrok / localtunnel для разработки.

`bot_service` сам выставляет webhook на старте, если задан `TG_WEBHOOK_URL`.

## Миграция данных из старой версии

```bash
cd migration
pip install -r requirements.txt
python sqlite_to_postgres.py \
    --sqlite /path/to/old/proverkin.sqlite \
    --dsn postgresql://proverkin:proverkin@localhost:5432/proverkin
```

Скрипт идемпотентен: повторный запуск ничего не дублирует благодаря `on conflict do nothing` и пересчитывает sequence-ы в конце.

## Структура

```
proverkin-ms/
├── bot_service/         # тонкий I/O-сервис aiogram
│   ├── handlers/        # tg-handlers (только команды + callback)
│   ├── api/             # HTTP API (send/edit/delete/answer + webhook)
│   ├── utils/           # quiz_client (HTTP до quiz_service)
│   └── ...
├── quiz_service/        # бизнес-логика
│   ├── api/             # HTTP API: events/start, /restart, /quiz, /callback
│   ├── service/         # quiz, question, keyboards, messages
│   ├── database/        # PostgresConnector (статические методы)
│   └── utils/           # schedulers, bot_client, state_store
├── generator_service/
│   ├── service/         # openrouter client + worker (replenish loop)
│   ├── prompts/         # системные промпты
│   └── api/
├── web_gui/             # Flask + Jinja
│   ├── routes/          # users, sets, user_sets, queue, logs, dashboard
│   ├── database/        # Admin (расширение PostgresConnector)
│   └── templates/, static/
├── db/init.sql          # схема Postgres
├── migration/           # sqlite → postgres
├── docker-compose.yml
└── .env.example
```

## Принципы переписи

- Структура папок и стиль кода (статические методы, многострочные SQL через `\` + `'''...'''`, кириллические комментарии, `parse_mode = 'HTML'`, `linesep + '- '`) повторяет оригинал. Куски кода, где это было осмысленно, перенесены без изменений.
- `SQLite3Connector` → `PostgresConnector`: те же сигнатуры (`add_user`, `update_question_type`, `get_users_set_list`, `get_log_data`, `add_log` и т.д.), внутри psycopg.
- `service/quiz.py` сохранил структуру: `schedule_quiz` → `check_for_quiz` → `start_quiz` → `send_question` → handler ответа. FSM из aiogram заменена на собственный `state_store` (in-memory dict с asyncio.Lock).
- `keyboards/builder.py` остался как `service/keyboards.py`, но возвращает `dict` (структура `rows`), а bot_service конвертирует в `InlineKeyboardMarkup`. Так bot_service вообще не знает про доменные данные.
- Callback data сериализуется собственными `encode_callback / decode_callback` (Telegram ограничивает 64 байтами).

## Что осталось за рамками первой итерации

- Excel-экспорт/импорт вопросов (`/edit` и связанные хендлеры) — сейчас выпиливается из бота (нет смысла, если все управление переехало в web-gui). При желании верну в web_gui отдельной страницей.
- Yandex GPT rewriter (тестовая фича для трёх chat_id) — не переносил, если нужно — сделаю.
- Любой `IsAdmin`-фильтр в боте: теперь все админ-действия выполняются в web-gui под Basic Auth.
