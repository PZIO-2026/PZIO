from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pzio.config import settings
from pzio.db import Base, engine
from pzio.modules.admin import router as admin_router
from pzio.modules.auth import router as auth_router
from pzio.modules.communication import router as communication_router
from pzio.modules.projects import router as projects_router
from pzio.modules.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # MVP: create tables from SQLAlchemy metadata at startup. Once schemas stabilise
    # across modules, swap this for Alembic-managed migrations.
    Base.metadata.create_all(bind=engine)
    yield


openapi_tags = [
    {"name": "Health", "description": "Liveness and readiness probes for ops/integration."},
    {"name": "Auth", "description": "Identity & Authorization — registration, login, OAuth, password reset, profile, admin user management."},
    {"name": "Projects", "description": "Project lifecycle, project membership, sprint planning."},
    {"name": "Tasks", "description": "Backlog work items, Kanban status changes, worklog entries."},
    {"name": "Communication", "description": "Comments, attachments, e-mail notifications via SMTP."},
    {"name": "Admin", "description": "System dictionaries, database backups, audit log access."},
]

app = FastAPI(
    title="PZIO Task Management System",
    description="Backend REST API for the team-project task management system. See documents/4.pdf (SAD) for the canonical API contract.",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # SAD §4 mandates a single-string `detail` on every 4xx response. FastAPI's default
    # for validation errors is a list, so flatten it into one human-readable line.
    parts: list[str] = []
    for err in exc.errors():
        location = ".".join(str(part) for part in err.get("loc", ()) if part != "body")
        message = err.get("msg", "invalid value")
        parts.append(f"{location}: {message}" if location else message)
    detail = "; ".join(parts) if parts else "Invalid request"
    return JSONResponse(status_code=400, content={"detail": detail})


@app.get("/health", tags=["Health"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(communication_router)
app.include_router(admin_router)
