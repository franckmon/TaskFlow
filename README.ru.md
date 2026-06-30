# Task Flow

[English](README.md) | **Русский**

Сервис управления задачами: бизнес-правила на backend, JWT-аутентификация, React-клиент

[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)

## Стек

| Слой | Технологии |
|------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, python-jose, passlib |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Axios |
| **База данных** | SQLite |
| **Тестирование** | pytest, pytest-cov, Vitest, Testing Library, Playwright |
| **Качество кода** | ruff, mypy, GitHub Actions, uv |

**Python-зависимости:** `requirements.txt` (runtime) и `requirements-dev.txt` (dev/test) для pip; `pyproject.toml` + `uv.lock` для [uv](https://docs.astral.sh/uv/).

## Архитектура

### Backend

Слоистая архитектура с domain модулем для бизнес-правил:

```text
HTTP (routers)
    → services        оркестрация, транзакции
    → repositories    SQLAlchemy-запросы
    → models          ORM-маппинг
domain/               правила статусов, владение, логика
```

| Каталог | Назначение |
|---------|------------|
| `app/api/` | Обработчики маршрутов, маппинг запросов/ответов, OpenAPI |
| `app/services/` | Сценарии использования, координация repositories и domain |
| `app/repositories/` | Доступ к данным, фильтрация, пагинация |
| `app/domain/` | Переходы статусов, владение, правила валидации |
| `app/schemas/` | Pydantic-модели запросов, ответов и query-параметров |
| `app/core/` | Конфигурация, security, сессия БД, CORS, rate limiting, health |

### Frontend

Feature-ориентированная структура: API-клиент, React hooks для загрузки данных, презентационные компоненты, тонкий auth context

```text
components/  → UI
hooks/       → useAuth, useTasks, useDebouncedValue
api/         → HTTP-клиент, эндпоинты, маппинг ошибок
contexts/    → состояние сессии
```

## Безопасность

| Область | Реализация |
|---------|------------|
| **Аутентификация** | JWT, токен на клиенте, `/auth/me` для проверки сессии |
| **Авторизация** | Роль проверяется на backend; удаление только у `admin` |
| **Rate limiting** | `POST /auth/login` — 5 запросов/минуту на IP |
| **IP клиента** | `X-Forwarded-For` / `X-Real-IP` только от доверенных прокси |
| **CORS** | Явный список origin; wildcard запрещён в production |
| **Валидация** | Pydantic v2 на всех входах; структурированные ошибки |
| **Brute force** | Неудачные попытки входа учитываются в лимите IP |

Отключить rate limiting в dev/test: `RATELIMIT_ENABLED=false`

## Установка

Требуется Python **3.12+**. Выберите pip или [uv](https://docs.astral.sh/uv/).

### Вариант 1: pip

**Production:**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Development:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` подключает `requirements.txt` через `-r requirements.txt`.

### Вариант 2: uv

**Production:**

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Или синхронизация из `pyproject.toml` без dev-зависимостей:

```bash
uv sync --no-group dev
```

**Development:**

```bash
uv sync
```

**Запуск без активации venv:**

```bash
uv run pytest -q
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Локальный запуск

```bash
git clone https://github.com/franckmon/task-flow.git
cd task-flow

# Backend
cp .env.example .env && set -a && source .env && set +a
alembic upgrade head
uvicorn app.main:app --reload          # http://localhost:8000  |  /docs
# с uv: uv run uvicorn app.main:app --reload

# Frontend
cd frontend
npm ci && cp .env.example .env
npm run dev                             # http://localhost:3000
```

Админ по умолчанию (`.env.example`): `admin` / `admin`

## CI pipeline

Запускается при push и pull request в `main` / `master`:

| Job | Что проверяет |
|-----|---------------|
| Backend · Tests | Миграции Alembic + `pytest --cov=app` |
| Backend · Code quality | `ruff check`, `ruff format --check`, `mypy app` |
| Frontend · Unit tests | `vitest --run` |
| Quality gate | Все три job выше должны пройти |
| Smoke · E2E | Playwright smoke (только после quality gate) |

```bash
# Локально
pytest -q                              # backend
uv run pytest -                        # backend(с uv)
cd frontend && npm run test -- --run   # frontend
cd frontend && npm run test:smoke      # e2e smoke
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/auth/login` | Получить JWT |
| `GET` | `/auth/me` | Текущий пользователь |
| `GET` | `/tasks` | Список (фильтр, поиск, сортировка, пагинация) |
| `POST` | `/tasks` | Создать задачу |
| `PUT` | `/tasks/{id}` | Обновить задачу |
| `DELETE` | `/tasks/{id}` | Удалить задачу (только admin) |
| `GET` | `/health` | Health check |

Документация: `http://localhost:8000/docs`.

## Структура проекта

```text
task-flow/
├── app/                  # FastAPI-приложение
├── frontend/             # React-клиент
├── tests/                # Backend-тесты
├── alembic/              # Миграции БД
├── scripts/              # Утилиты seed
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── uv.lock
└── .github/workflows/    # CI-конфигурация
```
