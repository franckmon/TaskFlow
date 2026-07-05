# Task Flow

**English** | [Русский](README.ru.md)

Task management service with enforced business rules on the backend, JWT authentication, and a React client

[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)

## Tech stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, python-jose, passlib |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Axios |
| **Database** | SQLite |
| **Testing** | pytest, pytest-cov, Vitest, Testing Library, Playwright |
| **Quality** | ruff, mypy, GitHub Actions, uv |

**Python dependencies:** `requirements.txt` (runtime) and `requirements-dev.txt` (dev/test) for pip; `pyproject.toml` + `uv.lock` for [uv](https://docs.astral.sh/uv/).

## Architecture

### Backend

Layered design with a domain module for business rules:

```text
HTTP (routers)
    → services        orchestration, transactions
    → repositories    SQLAlchemy queries
    → models          ORM mapping
domain/               status rules, ownership, logic
```

| Directory | Responsibility |
|-----------|----------------|
| `app/api/` | Route handlers, request/response mapping, OpenAPI |
| `app/services/` | Use cases, coordinates repositories and domain |
| `app/repositories/` | Data access, filtering, pagination |
| `app/domain/` | Status transitions, ownership, validation rules |
| `app/schemas/` | Pydantic request/response and query models |
| `app/core/` | Config, security, DB session, CORS, rate limiting, health |

### Frontend

Feature-oriented structure: API client layer, React hooks for data fetching, presentational components, and a thin auth context

```text
components/  → UI
hooks/       → useAuth, useTasks, useDebouncedValue
api/         → HTTP client, endpoints, error mapping
contexts/    → session state
```

## Security

| Area | Implementation |
|------|----------------|
| **Authentication** | JWT (HS256), token stored client-side, `/auth/me` for session validation |
| **Authorization** | Role checked on backend; delete restricted to `admin` |
| **Rate limiting** | `POST /auth/login` — 5 requests/minute per IP |
| **Client IP** | `X-Forwarded-For` / `X-Real-IP` honored only from trusted proxies |
| **CORS** | Explicit origin list; wildcard forbidden in production |
| **Validation** | Pydantic v2 on all inputs; structured error responses |
| **Brute force** | Failed login attempts count toward the same IP limit |

Disable rate limiting in dev/test: `RATELIMIT_ENABLED=false`

## Installation

Python **3.12+** required. Choose pip or [uv](https://docs.astral.sh/uv/).

### Option 1: pip

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

`requirements-dev.txt` includes `requirements.txt` via `-r requirements.txt`.

### Option 2: uv

**Production (runtime only):**

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Or sync from `pyproject.toml` without dev tools:

```bash
uv sync --no-group dev
```

**Development (tests, migrations, linting):**

```bash
uv sync
```

**Run commands without activating the venv:**

```bash
uv run pytest -q
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Run locally

```bash
git clone https://github.com/franckmon/TaskFlow.git
cd task-flow

# Backend
cp .env.example .env && set -a && source .env && set +a
alembic upgrade head
uvicorn app.main:app --reload          # http://localhost:8000  |  /docs
# with uv: uv run uvicorn app.main:app --reload

# Frontend
cd frontend
npm ci && cp .env.example .env
npm run dev                             # http://localhost:3000
```

Default admin (`.env.example`): `admin` / `admin`

## CI pipeline

Triggered on push and pull request to `main` / `master`:

| Job | What it checks |
|-----|----------------|
| Backend · Tests | Alembic migrations + `pytest --cov=app` |
| Backend · Code quality | `ruff check`, `ruff format --check`, `mypy app` |
| Frontend · Unit tests | `vitest --run` |
| Quality gate | All three jobs above must succeed |
| Smoke · E2E | Playwright smoke suite (runs only after quality gate) |

```bash
# Run locally
pytest -q                              # backend
uv run pytest -                        # backend(with uv)
cd frontend && npm run test -- --run   # frontend
cd frontend && npm run test:smoke      # e2e smoke
```

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Obtain JWT |
| `GET` | `/auth/me` | Current user |
| `GET` | `/tasks` | List (filter, search, sort, paginate) |
| `POST` | `/tasks` | Create task |
| `PUT` | `/tasks/{id}` | Update task |
| `DELETE` | `/tasks/{id}` | Delete task (admin only) |
| `GET` | `/health` | Health check |

Documentation: `http://localhost:8000/docs`.

## Project layout

```text
task-flow/
├── app/                  # FastAPI application
├── frontend/             # React client
├── tests/                # Backend test suite
├── alembic/              # Database migrations
├── scripts/              # Seed utilities
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── uv.lock
└── .github/workflows/    # CI configuration
```
