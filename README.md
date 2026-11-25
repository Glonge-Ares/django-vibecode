# ExamPrep — веб-приложение для подготовки к экзаменам

Учебная платформа для подготовки к экзаменам: экзамены с подсчётом очков и
таймером, карточки для запоминания терминов (аналог Quizlet), ведение
истории попыток, администрирование контента через Django admin.

Контейнеризовано целиком (Docker Compose: Django + PostgreSQL), снабжено
MCP-сервером и конфигурацией AI-агента (opencode): `AGENTS.md`,
Skill `exam-prep-dev` и `opencode.json`.

## Стек

| Компонент | Технология |
| --- | --- |
| Backend | Django 5.2 (серверные шаблоны, без JS-фреймворков) |
| База данных | PostgreSQL 16 |
| Контейнеризация | Docker, Docker Compose |
| Тесты | `django.test` (23 теста) |
| Интеграция с ИИ | opencode + MCP-сервер (Python, MCP SDK 2.x) |

## Быстрый старт

Требования: Docker и Docker Compose.

```bash
docker compose up --build
```

Приложение: **http://localhost:8000**, PostgreSQL (для внешних инструментов):
`localhost:5432`, база `exam_prep`, пользователь `exam`/`exam`.

Контейнер `web` сам дожидается Postgres и выполняет миграции при каждом
запуске (`entrypoint.sh`). Демо-данные и учётки создаются отдельно
(идемпотентно, повторный запуск безопасен):

```bash
docker compose exec web python manage.py seed_exams       # 3 экзамена, 13 вопросов
docker compose exec web python manage.py seed_flashcards  # 2 колоды по 8 карточек
docker compose exec web python manage.py createsuperuser   # или создать demo-учётки ниже
```

Демо-учётки:

| Логин | Пароль | Роль |
| --- | --- | --- |
| `admin` | `admin12345` | суперпользователь (админка `/admin/`) |
| `student` | `student12345` | обычный студент |

## Основные команды

```bash
docker compose up --build              # сборка и запуск (db + web)
docker compose down                     # остановить (данные сохраняются)
docker compose down -v                  # остановить и удалить данные БД
docker compose logs -f web              # логи приложения
docker compose exec web python manage.py test        # тесты (23)
docker compose exec web python manage.py shell       # Django shell
docker compose exec web python manage.py makemigrations  # сгенерировать миграции
```

## Структура проекта

```
django_project/
├── AGENTS.md                  # инструкции для AI-агентов (загружаются opencode)
├── opencode.json              # конфигурация opencode: MCP-сервер, инструкции
├── .opencode/skills/exam-prep-dev/SKILL.md  # Skill для агентов
├── docker-compose.yml         # сервисы db и web
├── Dockerfile                 # образ приложения (python:3.13-slim)
├── entrypoint.sh              # ожидание БД + migrate при старте
├── config/                    # проект Django (settings, urls)
├── accounts/                  # регистрация (форма, представление, тесты)
├── exams/                     # приложение экзаменов (викторины)
│   ├── models.py              # Exam, Question, Choice, Attempt, Answer
│   ├── views.py               # список/запуск/сдача/результаты
│   ├── admin.py, tests.py     # админка, тесты
│   └── management/commands/seed_exams.py
├── flashcards/                # приложение карточек (аналог Quizlet)
│   ├── models.py              # Deck, Card, DeckResult
│   ├── views.py               # список/изучение/оценка карточек
│   ├── admin.py, tests.py
│   └── management/commands/seed_flashcards.py
├── mcp_server/server.py       # MCP-сервер (инструменты доступа к данным)
├── templates/, static/        # шаблоны и стили (CSS без сборки)
├── report/                    # отчёт по лабораторной работе (docx/pdf, генератор)
└── .venv-mcp/                 # venv для MCP-сервера на хосте (не коммитится)
```

## Возможности приложения

**Экзамены** (`/`): список опубликованных экзаменов; прохождение с
одиночным выбором, множественным выбором и кратким ответом; ограничение по
времени с обратным отсчётом; автоматическая проверка; история попыток и
разбор ошибок (`/attempts/`).

**Карточки** (`/flashcards/`): колоды терминов; просмотр карточек с
переворотом; режим изучения по одной карточке со случайным порядком,
самооценкой «знал/не знал» и итогом; история сессий по колоде.

**Аутентификация**: вход/выход, регистрация (`/accounts/register/`) с полем
e-mail. Письма не отправляются (SMTP не настроен): адрес сохраняется как есть,
подтверждение не требуется, после регистрации пользователь сразу авторизован.

**Админка** (`/admin/`): управление экзаменами, вопросами, колодами,
карточками; просмотр попыток и результатов.

## MCP-сервер и AI-агент

`mcp_server/server.py` — собственный MCP-сервер (Python, транспорт stdio,
ORM Django → Postgres на `127.0.0.1:5432`). Зарегистрирован в `opencode.json`
под именем `exam-db`. Инструменты: `list_exams`, `get_exam`, `list_questions`
(полный ключ ответов), `exam_stats`, `get_attempt`, `get_db_schema`,
`list_users`.

```bash
python3 -m venv .venv-mcp          # или: uv venv .venv-mcp
.venv-mcp/bin/pip install -r requirements.txt mcp
```

Конфигурация агента:

- **`AGENTS.md`** — карта проекта, команды, модель данных, принятые соглашения.
- **Skill `.opencode/skills/exam-prep-dev/SKILL.md`** — пошаговые чек-листы
  развития проекта (новый тип вопроса, потоки представлений, флешкарты, БД).
- **`opencode.json`** — подключение MCP-сервера и загрузка `AGENTS.md`.

Запуск агента выполняется из корня проекта:

```bash
cd django_project && opencode
```

## Тестирование

```bash
docker compose exec web python manage.py test
```

31 тест: правила выставления оценок, поток сдачи экзамена, права доступа к
результатам, поток изучения карточек, идемпотентность команд сидирования,
регистрация (сохранение e-mail, дубликаты, валидация паролей).
