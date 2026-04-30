# PZIO backend image (SAD §2.2 / §7.1.4 — three-tier app, one container per layer).
# Slim base keeps the image small; psycopg[binary] ships its own libpq so we don't
# need build tools in the final image.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install the package by copying the source first (setuptools needs the `pzio`
# package present at install time because pyproject.toml uses `find` + include).
COPY pyproject.toml ./
COPY pzio ./pzio
RUN pip install .

# Forced backups (POST /api/admin/backups) write here; mount a volume to persist.
RUN mkdir -p /app/backups
ENV BACKUP_DIR=/app/backups

EXPOSE 8000

CMD ["uvicorn", "pzio.main:app", "--host", "0.0.0.0", "--port", "8000"]
