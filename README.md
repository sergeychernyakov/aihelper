# aihelper

Telegram-проект с двумя ботами на Python:
- `TranslatorBot` (`translator_bot.py`) — RU/UA переводчик с поддержкой текста, фото, документов, голоса и видео.
- `DietBot` (`diet_bot.py`) — диетологический ассистент с обработкой текста/медиа и генерацией ответов.

Оба бота работают через OpenAI API, хранят диалоги в SQLite и поддерживают оплату через Telegram invoices.

## Что есть в коде

- Базовые команды: `/start`, `/ping`, `/balance`, `/invoice`, `/finish`.
- Хранение диалогов и баланса в `db/aihelper.db`.
- Автообновление треда OpenAI раз в 1 час.
- Локализация `en`, `ru`, `ua` (папка `locale/`).
- Рассылка постов: `recipe_poster.py`.
- Утилита TTS: `text_to_speech.py`.

## Поддерживаемые типы сообщений и ограничения

Ограничения заданы в `lib/constraints_checker.py`.

- `text` — без отдельного лимита в коде обработчика.
- `photo` — `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, до 5 MB, максимум 2000px по стороне.
- `voice` — `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, `.webm`, `.oga`, до 5 MB.
- `document` — `.txt`, `.tex`, `.docx`, `.doc`, `.html`, `.rtf`, `.rtfd`, `.pdf`, `.pptx`, `.tar`, `.zip`, до 5 MB.
- `video` — `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, до 20 MB.

## Требования

- Python 3.9+ (в `Dockerfile` используется Python 3.9).
- Системные зависимости для `textract`/media (если запускать без Docker): `ffmpeg`, `poppler`, `antiword`, `tesseract` и др.

## Установка (локально)

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Переменные окружения

Создайте `.env` в корне проекта.

Минимально необходимые:

```dotenv
OPENAI_API_KEY=

TRANSLATOR_TELEGRAM_BOT_TOKEN=
TRANSLATOR_ASSISTANT_ID=

DIET_TELEGRAM_BOT_TOKEN=
DIET_ASSISTANT_ID=
```

Дополнительно (по используемым функциям):

```dotenv
OPENAI_ORGANIZATION_ID=
LANGUAGE=en

TRANSLATOR_YOOKASSA_API_TOKEN=
TRANSLATOR_STRIPE_API_TOKEN=

DIET_YOOKASSA_API_TOKEN=
DIET_STRIPE_API_TOKEN=

EMAIL=
PASSWORD=
```

## База данных и миграции

По умолчанию используется SQLite: `db/aihelper.db`.

```bash
python3 -m alembic upgrade head
```

Создание новой миграции:

```bash
python3 -m alembic revision --autogenerate -m "your message"
```

## Запуск

Запуск каждого бота отдельно:

```bash
python3 translator_bot.py
python3 diet_bot.py
```

`start_bots.sh` рассчитан на контейнерный путь `/aihelper` (используется в Docker).

## Docker

```bash
docker build -t aihelper .
docker run --rm -it --env-file .env -v "$(pwd):/aihelper" aihelper
```

## Рассылка рецептов

```bash
python3 recipe_poster.py
```

Скрипт использует `DIET_TELEGRAM_BOT_TOKEN` и `DIET_ASSISTANT_ID`.

## Тесты

```bash
python3 -m unittest discover -s tests
```

Если зависимости не установлены, тесты упадут с `ModuleNotFoundError` (например `openai`, `telegram`, `tiktoken`, `sqlalchemy`).

## Структура проекта

- `lib/telegram/bots/` — классы ботов.
- `lib/telegram/message_handlers/` — обработчики типов сообщений.
- `lib/openai/` — интеграция с OpenAI, run manager, токенайзер.
- `db/` — SQLAlchemy engine и модели.
- `alembic/` — миграции базы.
- `tests/` — unit-тесты.
