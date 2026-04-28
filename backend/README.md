# PZIO Backend

REST API for the PZIO Task Management System. Python 3.12+, FastAPI, SQLAlchemy.

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m pzio
```

The server runs on `http://localhost:8000` with auto-reload. A `shell.nix` is also provided at the repo root for Nix users (`nix-shell` from the project root).

Smoke check:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

`/health` is an operational liveness probe (used by Docker, Kubernetes, load balancers and similar tooling). It sits outside the SAD API surface on purpose — the SAD describes the business API, while `/health` is plain ops infrastructure.

## Running tests

From `backend/`:

```bash
pytest
```

Tests use an in-memory SQLite engine via the fixtures in `pzio/tests/conftest.py` — no external services required.

## API documentation

FastAPI auto-generates the API docs from route definitions and Pydantic schemas:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`
- **OpenAPI JSON** — `http://localhost:8000/openapi.json`

Endpoints are grouped by module (Auth, Projects, Tasks, Communication, Admin) using router tags.

## Module structure

The backend is split into five logical modules under `pzio/modules/`. Each module is owned by one subteam and follows the same layout:

```
pzio/modules/<name>/
    __init__.py     # re-exports `router`
    router.py       # FastAPI APIRouter — endpoints live here
    models.py       # SQLAlchemy ORM models (inherit from pzio.db.Base)
    schemas.py      # Pydantic request/response schemas
    service.py      # business logic
    deps.py         # FastAPI dependencies specific to the module
    tests/          # module-level unit tests
```

Only `__init__.py` and `router.py` are required at this stage; add the other files as you implement.

### Adding endpoints to your module

1. Open `pzio/modules/<your_module>/router.py`.
2. Declare endpoints with **full paths from the architecture document** — no router-level prefix is set because several modules own multiple URL roots (e.g. the auth module owns both `/api/auth/*` and `/api/users/*`).

   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session

   from pzio.db import get_db

   router = APIRouter(tags=["YourModule"])


   @router.post("/api/your-module/things", summary="Create a thing", status_code=201)
   def create_thing(payload: ThingCreate, db: Session = Depends(get_db)) -> ThingRead:
       ...
   ```

3. The router is already wired into `main.py` — no changes needed there.
4. Define ORM models in `models.py` inheriting from `Base`. The app calls `Base.metadata.create_all` on startup, so importing the module is enough for the tables to be created.

### API contract

Endpoints, request/response shapes, status codes and error formats are defined in the **Software Architecture Document (SAD)**. Implementations must match the SAD exactly. Any change to the contract has to be agreed with the Tech Lead before code lands.

All `4xx` responses follow a single shape: `{"detail": "<message>"}`. The application takes care of this for both `HTTPException` and Pydantic validation errors.

## Configuration

Settings come from environment variables (or a local `.env` file — see `.env.example`).

| Variable          | Default                                | Notes                                                          |
| ----------------- | -------------------------------------- | -------------------------------------------------------------- |
| `DATABASE_URL`    | `sqlite:///./pzio.db`                  | Override with a Postgres URL in production.                    |
| `JWT_SECRET`      | `dev-secret-change-me-in-production`   | **Must** be overridden in production.                          |
| `JWT_ALGORITHM`   | `HS256`                                |                                                                |
| `JWT_EXPIRES_MIN` | `60`                                   | Access token lifetime in minutes.                              |
| `CORS_ORIGINS`    | `http://localhost:5173`                | Comma-separated list of allowed origins.                       |

## Tech stack

- **Python** 3.12+
- **FastAPI** — REST framework
- **SQLAlchemy 2.x** — ORM
- **Pydantic** / **pydantic-settings** — request/response validation, env-driven config
- **pytest** + **httpx** — tests
- **SQLite** locally; **PostgreSQL** in production
